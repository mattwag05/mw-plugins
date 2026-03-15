#!/usr/bin/env python3
"""
doc-harvest: URL discovery, content cleaning, and CCL organization.

Stdlib-only (no pip dependencies). Subcommands:
  discover <url>    — Find all pages under a URL prefix
  clean             — Clean raw markdown (stdin -> stdout)
  organize          — Generate CCL file tree from manifest
  update-index      — Update CCL root _index.md with new doc set
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

USER_AGENT = "doc-harvest/1.0 (Claude Code plugin)"


def fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return its text content."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError) as e:
        print(f"Warning: Failed to fetch {url}: {e}", file=sys.stderr)
        return ""


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def url_to_path(url: str, base_path: str) -> str:
    """Convert a URL path to a relative file path under base_path."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if base_path:
        base = base_path.rstrip("/")
        if path.startswith(base):
            path = path[len(base):]
    path = path.strip("/")
    if not path:
        return "index"
    # Remove file extensions
    path = re.sub(r"\.(html?|php|aspx?)$", "", path)
    return path


# ---------------------------------------------------------------------------
# Link extractor (stdlib HTML parser)
# ---------------------------------------------------------------------------

class LinkExtractor(HTMLParser):
    """Extract <a href> and <title> from HTML."""

    def __init__(self, base_url: str, path_prefix: str):
        super().__init__()
        self.base_url = base_url
        self.path_prefix = path_prefix
        self.links: list[dict] = []
        self.title = ""
        self._in_title = False
        self._seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href:
                self._add_link(href)

    def handle_data(self, data: str):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._in_title = False

    def _add_link(self, href: str):
        # Resolve relative URLs
        full = urljoin(self.base_url, href)
        parsed = urlparse(full)
        # Same domain only
        base_parsed = urlparse(self.base_url)
        if parsed.netloc != base_parsed.netloc:
            return
        # Must be under path prefix
        if not parsed.path.startswith(self.path_prefix):
            return
        # Strip fragments and query
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        clean = clean.rstrip("/")
        if clean not in self._seen:
            self._seen.add(clean)
            self.links.append({"url": clean, "path": parsed.path})


class TitleExtractor(HTMLParser):
    """Extract just the <title> from HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


# ---------------------------------------------------------------------------
# Subcommand: discover
# ---------------------------------------------------------------------------

def cmd_discover(args):
    """Find all pages under a URL prefix."""
    url = args.url.rstrip("/")
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    path_prefix = parsed.path.rstrip("/") or "/"

    pages = []
    source = "unknown"

    # --- Try sitemap.xml variants ---
    sitemap_urls = [
        f"{domain}/sitemap.xml",
        f"{domain}/sitemap_index.xml",
    ]

    # Check robots.txt for Sitemap directives
    robots = fetch_url(f"{domain}/robots.txt")
    if robots:
        for line in robots.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                sm_url = line.split(":", 1)[1].strip()
                if sm_url not in sitemap_urls:
                    sitemap_urls.insert(0, sm_url)

    for sm_url in sitemap_urls:
        sm_content = fetch_url(sm_url)
        if not sm_content:
            continue

        try:
            root = ET.fromstring(sm_content)
        except ET.ParseError:
            continue

        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Handle sitemap index (points to other sitemaps)
        sitemaps_to_parse = []
        for sm in root.findall(f".//{ns}sitemap"):
            loc = sm.find(f"{ns}loc")
            if loc is not None and loc.text:
                sitemaps_to_parse.append(loc.text.strip())

        if sitemaps_to_parse:
            # Fetch each sub-sitemap
            for sub_url in sitemaps_to_parse:
                sub_content = fetch_url(sub_url)
                if sub_content:
                    try:
                        sub_root = ET.fromstring(sub_content)
                        for url_elem in sub_root.findall(f".//{ns}url"):
                            loc = url_elem.find(f"{ns}loc")
                            if loc is not None and loc.text:
                                page_url = loc.text.strip().rstrip("/")
                                page_parsed = urlparse(page_url)
                                if page_parsed.path.startswith(path_prefix):
                                    pages.append({
                                        "url": page_url,
                                        "path": page_parsed.path
                                    })
                    except ET.ParseError:
                        continue
        else:
            # Direct sitemap with <url> entries
            for url_elem in root.findall(f".//{ns}url"):
                loc = url_elem.find(f"{ns}loc")
                if loc is not None and loc.text:
                    page_url = loc.text.strip().rstrip("/")
                    page_parsed = urlparse(page_url)
                    if page_parsed.path.startswith(path_prefix):
                        pages.append({
                            "url": page_url,
                            "path": page_parsed.path
                        })

        if pages:
            source = "sitemap"
            break

    # --- Fallback: crawl links from the page ---
    if not pages:
        source = "crawl"
        html = fetch_url(url)
        if html:
            extractor = LinkExtractor(url, path_prefix)
            extractor.feed(html)
            pages = extractor.links

            # Crawl 1 level deep
            first_level = list(pages)
            for page in first_level:
                sub_html = fetch_url(page["url"])
                if sub_html:
                    sub_extractor = LinkExtractor(url, path_prefix)
                    sub_extractor.feed(sub_html)
                    existing_urls = {p["url"] for p in pages}
                    for link in sub_extractor.links:
                        if link["url"] not in existing_urls:
                            pages.append(link)
                            existing_urls.add(link["url"])

    # Deduplicate and sort
    seen = set()
    unique_pages = []
    for p in pages:
        if p["url"] not in seen:
            seen.add(p["url"])
            rel_path = url_to_path(p["url"], path_prefix)
            depth = rel_path.count("/") if rel_path else 0
            unique_pages.append({
                "url": p["url"],
                "path": rel_path,
                "title": "",  # Titles populated during scraping
                "depth": depth,
            })
    unique_pages.sort(key=lambda x: x["path"])

    # Suggest a slug
    slug_parts = []
    if parsed.netloc:
        parts = parsed.netloc.split(".")
        # Use second-level domain (e.g., "tailscale" from "docs.tailscale.com")
        for part in parts:
            if part not in ("www", "docs", "developer", "com", "org", "io", "dev", "net"):
                slug_parts.append(part)
                break
    if path_prefix and path_prefix != "/":
        trail = path_prefix.strip("/").split("/")[-1]
        slug_parts.append(slugify(trail))
    slug = "-".join(slug_parts) if slug_parts else slugify(parsed.netloc)

    result = {
        "base_url": url,
        "domain": parsed.netloc,
        "path_prefix": path_prefix,
        "slug": slug,
        "source": source,
        "page_count": len(unique_pages),
        "pages": unique_pages,
    }

    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Subcommand: clean
# ---------------------------------------------------------------------------

# Block patterns that need DOTALL (match across lines)
BLOCK_STRIP_PATTERNS = [
    # Navigation heading blocks (match from heading to next heading or EOF)
    r"(?m)^#{1,3}\s*(Navigation|Menu|Nav|Breadcrumb|Table of Contents|TOC|Site Map)\s*$.*?(?=^#{1,3}\s|\Z)",
    # Footer boilerplate (from HR to end)
    r"(?m)^---+\s*$\s*(?:Copyright|©|\(c\)|All rights reserved|Terms|Privacy|Legal).*?(?=\Z)",
]

# Line patterns — NO DOTALL (. must not cross newlines)
LINE_STRIP_PATTERNS = [
    # Skip to content links
    r"(?m)^\[Skip to .*?\]\(.*?\)\s*$",
    # Cookie consent banners
    r"(?m)^[^\n]*(?:cookie|consent|privacy\s+(?:policy|notice))[^\n]*accept[^\n]*$",
    # "Was this page helpful" blocks
    r"(?m)^[^\n]*(?:Was this (?:page|article) helpful|Give feedback|Rate this)[^\n]*$",
    # Edit on GitHub links
    r"(?m)^\s*\[?\s*Edit (?:this page )?on GitHub\s*\]?\s*(?:\(.*?\))?\s*$",
    # Share buttons
    r"(?m)^[^\n]*(?:Share (?:this|on)|Tweet this|Share on Facebook|Share on LinkedIn)[^\n]*$",
    # Newsletter signup
    r"(?m)^[^\n]*(?:Subscribe to|Newsletter|Sign up for)[^\n]*(?:email|updates)[^\n]*$",
]

BLOCK_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in BLOCK_STRIP_PATTERNS]
LINE_COMPILED = [re.compile(p, re.IGNORECASE) for p in LINE_STRIP_PATTERNS]


def cmd_clean(args):
    """Clean raw markdown from stdin, write to stdout."""
    content = sys.stdin.read()

    # Strip boilerplate patterns (block patterns first, then line patterns)
    for pattern in BLOCK_COMPILED:
        content = pattern.sub("", content)
    for pattern in LINE_COMPILED:
        content = pattern.sub("", content)

    # Normalize heading levels: find the first heading and make it ##
    lines = content.split("\n")
    first_heading_level = 0
    for line in lines:
        m = re.match(r"^(#{1,6})\s", line)
        if m:
            first_heading_level = len(m.group(1))
            break

    if first_heading_level == 1:
        # Shift all headings down by 1 (# -> ##, ## -> ###, etc.)
        adjusted = []
        for line in lines:
            m = re.match(r"^(#{1,6})(\s.*)", line)
            if m:
                adjusted.append(f"#{m.group(1)}{m.group(2)}")
            else:
                adjusted.append(line)
        content = "\n".join(adjusted)
    elif first_heading_level == 0:
        # No headings found, leave as-is
        content = "\n".join(lines)

    # Absolutize relative image URLs if base_url provided
    if args.base_url:
        base = args.base_url.rstrip("/")
        # ![alt](relative/path) -> ![alt](https://domain/relative/path)
        def fix_img(m):
            alt = m.group(1)
            src = m.group(2)
            if not src.startswith(("http://", "https://", "data:", "//")):
                src = base + "/" + src.lstrip("/")
            elif src.startswith("/"):
                p = urlparse(base)
                src = p.scheme + "://" + p.netloc + src
            return "!" + "[" + alt + "](" + src + ")"

        content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", fix_img, content)

    # Remove excessive blank lines (3+ -> 2)
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Trim leading/trailing whitespace
    content = content.strip()

    print(content)


# ---------------------------------------------------------------------------
# Subcommand: organize
# ---------------------------------------------------------------------------

def cmd_organize(args):
    """Generate CCL file tree plan from a manifest JSON."""
    with open(args.manifest) as f:
        manifest = json.load(f)

    pages = manifest.get("pages", [])
    slug = args.slug or manifest.get("slug", "docs")
    today = date.today().isoformat()

    ccl_root = Path(args.ccl_root).expanduser() if args.ccl_root else None
    doc_root = f"contexts/technical/{slug}"

    # Build directory structure from page paths
    sections: dict[str, list[dict]] = {}
    for page in pages:
        path = page.get("path", "index")
        parts = path.split("/")
        if len(parts) > 1:
            section = parts[0]
        else:
            section = ""  # Root-level page
        sections.setdefault(section, []).append(page)

    # Plan the file tree
    plan = {"slug": slug, "doc_root": doc_root, "files": []}

    # Root _index.md
    section_table = []
    for section_name, section_pages in sorted(sections.items()):
        display = section_name.replace("-", " ").title() if section_name else "Overview"
        section_table.append(f"| {display} | {len(section_pages)} | Pages under /{section_name}/ |")

    root_index = {
        "path": f"{doc_root}/_index.md",
        "type": "root_index",
        "frontmatter": {
            "name": manifest.get("name", slug.replace("-", " ").title()),
            "domain": "technical",
            "source_url": manifest.get("base_url", ""),
            "harvested": today,
            "page_count": len(pages),
            "triggers": [slug.replace("-", " "), manifest.get("domain", "")],
            "related_contexts": [],
            "last_updated": today,
        },
        "section_table": section_table,
    }
    plan["files"].append(root_index)

    # Section _index.md files and individual pages
    for section_name, section_pages in sorted(sections.items()):
        if section_name:
            section_dir = f"{doc_root}/{section_name}"
            page_table = []
            for p in sorted(section_pages, key=lambda x: x["path"]):
                filename = p["path"].split("/")[-1] if "/" in p["path"] else p["path"]
                title = p.get("title", filename.replace("-", " ").title())
                page_table.append(f"| [{title}]({filename}.md) | {p.get('url', '')} |")

            section_index = {
                "path": f"{section_dir}/_index.md",
                "type": "section_index",
                "section": section_name,
                "page_table": page_table,
            }
            plan["files"].append(section_index)

        for p in section_pages:
            path = p.get("path", "index")
            filename = path.split("/")[-1] if "/" in path else path
            if section_name:
                file_path = f"{doc_root}/{section_name}/{filename}.md"
                parent = f"{section_name}/_index.md"
            else:
                file_path = f"{doc_root}/{filename}.md"
                parent = "_index.md"

            title = p.get("title", filename.replace("-", " ").title())
            page_file = {
                "path": file_path,
                "type": "page",
                "frontmatter": {
                    "name": title,
                    "source_url": p.get("url", ""),
                    "parent": parent,
                    "last_updated": today,
                },
            }
            plan["files"].append(page_file)

    if args.write and ccl_root:
        # Write the directory structure and placeholder files
        for f in plan["files"]:
            full_path = ccl_root / f["path"]
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if f["type"] == "root_index":
                fm = f["frontmatter"]
                triggers_yaml = "\n".join(f'  - "{t}"' for t in fm["triggers"] if t)
                content = f"""---
name: {fm['name']}
domain: {fm['domain']}
source_url: {fm['source_url']}
harvested: {fm['harvested']}
page_count: {fm['page_count']}
triggers:
{triggers_yaml}
related_contexts: []
last_updated: {fm['last_updated']}
---

# {fm['name']}

Documentation harvested from [{fm['source_url']}]({fm['source_url']}) on {fm['harvested']}.

## Sections

| Section | Pages | Description |
|---------|-------|-------------|
{chr(10).join(f["section_table"])}

## Source

This documentation was harvested by the doc-harvest plugin. To update, run:
```
/harvest-docs {fm['source_url']}
```
"""
                full_path.write_text(content)

            elif f["type"] == "section_index":
                section_display = f["section"].replace("-", " ").title()
                content = f"""---
name: {section_display}
parent: _index.md
last_updated: {today}
---

# {section_display}

| Page | Source |
|------|--------|
{chr(10).join(f["page_table"])}
"""
                full_path.write_text(content)

            elif f["type"] == "page":
                fm = f["frontmatter"]
                content = f"""---
name: {fm['name']}
source_url: {fm['source_url']}
parent: {fm['parent']}
last_updated: {fm['last_updated']}
---

<!-- Content will be written by the harvest command -->
"""
                full_path.write_text(content)

        print(json.dumps({"status": "written", "file_count": len(plan["files"]), "root": str(ccl_root / doc_root)}, indent=2))
    else:
        print(json.dumps(plan, indent=2))


# ---------------------------------------------------------------------------
# Subcommand: update-index
# ---------------------------------------------------------------------------

def cmd_update_index(args):
    """Update CCL root _index.md with a new doc set entry."""
    ccl_root = Path(args.ccl_root).expanduser()
    index_path = ccl_root / "_index.md"

    if not index_path.exists():
        print(f"Error: CCL index not found at {index_path}", file=sys.stderr)
        sys.exit(1)

    content = index_path.read_text()
    slug = args.slug
    name = args.name
    today = date.today().isoformat()
    ccl_path = f"contexts/technical/{slug}/_index.md"
    trigger_desc = f"Working with {name.lower()}, {slug.replace('-', ' ')} references"

    # Add to Quick Reference table
    new_row = f"| {name} | contexts/technical/{slug}/_index.md | {trigger_desc} |"
    # Find the table and append before the next section
    table_pattern = r"(\| Task Type \| Context File \| When to Load \|\n\|[-|]+\|[-|]+\|[-|]+\|)"
    match = re.search(table_pattern, content)
    if match:
        # Find the last row of the table
        table_end = match.end()
        remaining = content[table_end:]
        # Find where table rows end (next blank line or heading)
        row_pattern = re.compile(r"^\|.*\|$", re.MULTILINE)
        last_row_end = table_end
        for m in row_pattern.finditer(remaining):
            last_row_end = table_end + m.end()

        content = content[:last_row_end] + "\n" + new_row + content[last_row_end:]

    # Update statistics line
    stats_match = re.search(r"- Total contexts: (\d+)", content)
    if stats_match:
        old_count = int(stats_match.group(1))
        content = content.replace(
            f"- Total contexts: {old_count}",
            f"- Total contexts: {old_count + 1}"
        )

    # Update last_updated in statistics
    content = re.sub(
        r"(- Last updated: )\d{4}-\d{2}-\d{2}",
        f"\\g<1>{today}",
        content
    )

    index_path.write_text(content)
    print(json.dumps({"status": "updated", "index": str(index_path), "added": name}))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="harvest",
        description="Documentation harvesting toolkit for Claude Context Library",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # discover
    p_discover = subs.add_parser("discover", help="Find all pages under a URL prefix")
    p_discover.add_argument("url", help="Root URL of the documentation site")

    # clean
    p_clean = subs.add_parser("clean", help="Clean raw markdown (stdin → stdout)")
    p_clean.add_argument("--base-url", default="", help="Base URL for absolutizing relative images")

    # organize
    p_organize = subs.add_parser("organize", help="Generate CCL file tree from manifest")
    p_organize.add_argument("--slug", required=True, help="URL slug for the doc set")
    p_organize.add_argument("--manifest", required=True, help="Path to discovery manifest JSON")
    p_organize.add_argument("--write", action="store_true", help="Write files to disk")
    p_organize.add_argument("--ccl-root", help="CCL root directory (required with --write)")

    # update-index
    p_update = subs.add_parser("update-index", help="Update CCL root _index.md")
    p_update.add_argument("--ccl-root", required=True, help="CCL root directory")
    p_update.add_argument("--slug", required=True, help="Doc set slug")
    p_update.add_argument("--name", required=True, help="Doc set display name")

    args = parser.parse_args()

    if args.command == "discover":
        cmd_discover(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "organize":
        cmd_organize(args)
    elif args.command == "update-index":
        cmd_update_index(args)


if __name__ == "__main__":
    main()
