#!/usr/bin/env python3
"""
doc-harvest: URL discovery, content cleaning, and CCL organization.

Stdlib-only (no pip dependencies). Subcommands:
  discover <url>    — Find all pages under a URL prefix
                      (--html <file>: parse a Scrapling-rendered HTML file for
                       links instead of urllib — for JS/SPA sites whose nav and
                       sitemap don't work with a static fetch)
  clean             — Clean raw markdown (stdin -> stdout)
  organize          — Generate CCL file tree from manifest
  update-index      — Update CCL root _index.md with new doc set
  find              — Locate an existing doc set in the library by slug or source URL
  diff              — Compare a staged re-harvest against the stored doc set
  install           — Back up the stored doc set, then apply a staged re-harvest
  validate          — Check a doc-set dir for nav boilerplate, empty pages, bad links
  registry          — Rebuild doc-navigator's known-docs.md from the library

The library root comes from --ccl-root or $DOC_HARVEST_CCL (see ccl_root()).

Content fetching is done by scrapling-fetch.sh (Scrapling in Apple Container), NOT this
script — it renders JS, bypasses anti-bot, and emits --ai-targeted main-content
Markdown. `clean` is now a light post-pass (headings/images/whitespace), not the
primary boilerplate stripper.
"""

from __future__ import annotations  # allow PEP 604 (X | None) annotations on Python 3.9

import argparse
import json
import os
import re
import shutil
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

    # --- JS/SPA path: parse a pre-rendered HTML file (from scrapling fetch) ---
    # Static sitemap + urllib crawl fail on SPA sites whose nav is JS-rendered.
    # The workflow renders the landing page with Scrapling, then re-runs discover
    # with --html pointing at that file. We extract links from the real DOM and
    # skip the sitemap/urllib paths entirely.
    if getattr(args, "html", None):
        html = Path(args.html).read_text(errors="replace")
        extractor = LinkExtractor(url, path_prefix)
        extractor.feed(html)
        pages = extractor.links
        source = "rendered-html"
        if not pages:
            print(
                f"Warning: --html {args.html} yielded 0 links under {path_prefix} — "
                "falling back to sitemap/static crawl (the rendered HTML may be a "
                "thin SPA shell or the wrong page).",
                file=sys.stderr,
            )

    # --- Try sitemap.xml variants ---
    sitemap_urls = [
        f"{domain}/sitemap.xml",
        f"{domain}/sitemap_index.xml",
    ]

    # Check robots.txt for Sitemap directives (skip if --html already found links)
    robots = "" if pages else fetch_url(f"{domain}/robots.txt")
    if robots:
        for line in robots.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                sm_url = line.split(":", 1)[1].strip()
                if sm_url not in sitemap_urls:
                    sitemap_urls.insert(0, sm_url)

    for sm_url in (sitemap_urls if not pages else []):
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

# ponytail: Scrapling's --ai-targeted does DOM-level main-content extraction
# upstream of this step, so nav/footer/share/newsletter boilerplate is already
# gone. We keep only a few cheap line-level insurance patterns for the stray
# bits that occasionally survive (or for content fetched without --ai-targeted).
LINE_STRIP_PATTERNS = [
    # Skip-to-content links
    r"(?m)^\[Skip to .*?\]\(.*?\)\s*$",
    # Cookie / consent banners
    r"(?m)^[^\n]*(?:cookie|consent|privacy\s+(?:policy|notice))[^\n]*accept[^\n]*$",
    # "Was this page helpful" feedback widgets
    r"(?m)^[^\n]*(?:Was this (?:page|article) helpful|Give feedback|Rate this)[^\n]*$",
]

LINE_COMPILED = [re.compile(p, re.IGNORECASE) for p in LINE_STRIP_PATTERNS]
# Block-level boilerplate stripping (nav/footer) is now Scrapling's --ai-targeted
# job upstream, so cmd_clean no longer runs a block-pattern pass.


def cmd_clean(args):
    """Clean raw markdown from stdin, write to stdout."""
    content = sys.stdin.read()

    # Browser-rendered pages can still carry site chrome ahead of the content: drop
    # everything before the first H1 when asked.
    if args.from_h1:
        m = re.search(r"^# .+$", content, re.M)
        if m:
            content = content[m.start():]

    # Strip the few line-level boilerplate patterns that survive --ai-targeted
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
# Library lookup, re-harvest diff/install, validation, registry
# ---------------------------------------------------------------------------

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def frontmatter(path: Path) -> dict:
    """Minimal `key: value` frontmatter reader (enough for our own pages)."""
    m = FM_RE.match(path.read_text(encoding="utf-8", errors="replace")[:2000] + "\n")
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        if v and not k.startswith((" ", "-")):
            out[k.strip()] = v.strip()
    return out


def ccl_root(arg: str | None) -> Path:
    """--ccl-root, else $DOC_HARVEST_CCL, else the first Obsidian vault named
    'Context Library' / 'Claude Context Library'. Never guess a path that is missing."""
    cand = arg or os.environ.get("DOC_HARVEST_CCL")
    if not cand:
        docs = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents"
        for name in ("Context Library", "Claude Context Library"):
            if (docs / name).is_dir():
                cand = str(docs / name)
                break
    if not cand or not Path(cand).expanduser().is_dir():
        print("Error: library root not found; pass --ccl-root or set DOC_HARVEST_CCL", file=sys.stderr)
        sys.exit(1)
    return Path(cand).expanduser()


def doc_sets(root: Path):
    """Yield (dir, frontmatter) for each doc-set root: an _index.md with source_url + harvested."""
    for idx in root.rglob("_index.md"):
        if len(idx.relative_to(root).parts) > 4:
            continue
        fm = frontmatter(idx)
        if "source_url" in fm and "harvested" in fm:
            yield idx.parent, fm


def cmd_find(args):
    root = ccl_root(args.ccl_root)
    needle = args.query.lower().rstrip("/")
    hits = [(d, fm) for d, fm in doc_sets(root)
            if d.name.lower() == needle or needle in fm["source_url"].lower()]
    for d, fm in hits:
        print(json.dumps({"dir": str(d), "slug": d.name, "source_url": fm["source_url"],
                          "harvested": fm["harvested"], "page_count": fm.get("page_count")}))
    sys.exit(0 if hits else 1)


def _pages(d: Path) -> dict[str, str]:
    """source_url -> relative path for every page under d."""
    return {fm["source_url"].rstrip("/"): str(f.relative_to(d))
            for f in d.rglob("*.md") if (fm := frontmatter(f)).get("source_url")}


def cmd_diff(args):
    old, new = _pages(Path(args.existing)), _pages(Path(args.staged))
    added = sorted(set(new) - set(old))
    # Hubs (_index.md) are curated and never re-staged, so they are not "removed".
    missing = sorted(u for u in set(old) - set(new) if not old[u].endswith("_index.md"))
    # Renamed: a missing old URL and an added URL that share a title.
    title = lambda d, u, r: frontmatter(d / r).get("name", "")
    old_t = {title(Path(args.existing), u, r): u for u, r in old.items() if u in missing}
    renamed = [(old_t[title(Path(args.staged), u, new[u])], u) for u in added
               if title(Path(args.staged), u, new[u]) in old_t]
    ren_old = {a for a, _ in renamed}
    ren_new = {b for _, b in renamed}
    rep = {"updated": len(set(old) & set(new)),
           "added": [u for u in added if u not in ren_new],
           "removed": [u for u in missing if u not in ren_old],
           "renamed": [{"from": a, "to": b} for a, b in renamed]}
    print(json.dumps(rep, indent=1))


def cmd_install(args):
    """Back up the stored set, copy staged pages over it, refresh root index metadata,
    and list added pages in their section _index.md."""
    existing, staged = Path(args.existing), Path(args.staged)
    today = date.today().isoformat()
    backup = Path(args.backup) if args.backup else existing.parent.parent / f".doc-harvest-backups/{existing.name}-{today}"
    if backup.exists():
        print(f"Error: backup {backup} already exists", file=sys.stderr)
        sys.exit(1)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(existing, backup)
    old = _pages(existing)
    added = []
    for f in sorted(staged.rglob("*.md")):
        rel = f.relative_to(staged)
        url = frontmatter(f).get("source_url", "").rstrip("/")
        target = existing / old[url] if url in old else existing / rel   # renamed pages keep their path
        target.parent.mkdir(parents=True, exist_ok=True)
        if url not in old:
            added.append((target, frontmatter(f).get("name", rel.stem).replace(f" - {args.suffix}", "")))
        shutil.copyfile(f, target)
    for target, name in added:   # list new pages in their section index
        idx = target.parent / "_index.md"
        if idx.exists() and f"({target.name})" not in idx.read_text() and f"**{name}**" not in idx.read_text():
            with idx.open("a") as fh:
                fh.write(f"- [{name}]({target.name})\n")
    # touch dates on untouched hub indexes and refresh the root metadata
    root_idx = existing / "_index.md"
    pages = len(_pages(existing))
    for idx in existing.rglob("_index.md"):
        t = idx.read_text()
        t = re.sub(r"^last_updated: .*$", f"last_updated: {today}", t, flags=re.M)
        if idx == root_idx:
            t = re.sub(r"^harvested: .*$", f"harvested: {today}", t, flags=re.M)
            t = re.sub(r"^page_count: .*$", f"page_count: {pages}", t, flags=re.M)
        idx.write_text(t)
    print(json.dumps({"backup": str(backup), "pages": pages, "added": [str(t.relative_to(existing)) for t, _ in added]}))


BOILERPLATE = ("Skip Navigation", "Explore Get Started", "Stay Updated", "Cookie Preferences", "Back to top")


def cmd_validate(args):
    d = Path(args.dir)
    problems, per_section, total = [], {}, 0
    for f in sorted(d.rglob("*.md")):
        if f.name == "_index.md":
            continue
        total += 1
        sec = f.relative_to(d).parts[0] if len(f.relative_to(d).parts) > 1 else "root"
        per_section[sec] = per_section.get(sec, 0) + 1
        body = FM_RE.sub("", f.read_text(encoding="utf-8") + "\n", count=1)
        rel = str(f.relative_to(d))
        if len(body.strip()) < args.min_chars:
            problems.append(f"{rel}: body under {args.min_chars} chars")
        if "doc://" in body:
            problems.append(f"{rel}: unresolved doc:// link")
        if any(b in body for b in BOILERPLATE):
            problems.append(f"{rel}: site navigation boilerplate")
        if not frontmatter(f).get("source_url"):
            problems.append(f"{rel}: missing source_url")
    if args.manifest:
        expected = len(json.loads(Path(args.manifest).read_text())["pages"])
        if total > expected:
            problems.append(f"page count {total} exceeds manifest {expected}")
        # Hubs are skipped on re-harvest, so a lower count is only noted.
        print(f"manifest pages: {expected}  files: {total}", file=sys.stderr)
    print(json.dumps({"files": total, "per_section": per_section, "problems": problems}, indent=1))
    sys.exit(1 if problems else 0)


def cmd_registry(args):
    """Rewrite doc-navigator's known-docs.md from the doc sets found in the library."""
    root = ccl_root(args.ccl_root)
    rows = []
    for d, fm in sorted(doc_sets(root), key=lambda x: x[0].name):
        rows.append(f"| {fm.get('name', d.name)} | {d.name} | {d.relative_to(root)}/ | "
                    f"{re.sub(r'^https?://', '', fm['source_url'])} | {fm.get('page_count', '?')} | {fm['harvested']} |")
    out = ("# Known harvested documentation\n\nGenerated by `harvest.py registry` from the library "
           f"at `{root}`. Do not hand-edit.\n\n"
           "| Name | Slug | Library path | Source | Pages | Harvested |\n|------|------|------|------|------|------|\n"
           + "\n".join(rows) + "\n")
    Path(args.out).write_text(out)
    print(json.dumps({"rows": len(rows), "out": args.out}))


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
    p_discover.add_argument(
        "--html",
        help="Path to a Scrapling-rendered HTML file to extract links from "
        "(for JS/SPA sites where sitemap + static crawl find nothing)",
    )

    # clean
    p_clean = subs.add_parser("clean", help="Clean raw markdown (stdin → stdout)")
    p_clean.add_argument("--base-url", default="", help="Base URL for absolutizing relative images")
    p_clean.add_argument("--from-h1", action="store_true",
                         help="Drop everything before the first H1 (site chrome on browser-rendered pages)")

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

    p_find = subs.add_parser("find", help="Locate a stored doc set by slug or source URL fragment")
    p_find.add_argument("query")
    p_find.add_argument("--ccl-root")

    p_diff = subs.add_parser("diff", help="Compare a staged re-harvest against the stored doc set")
    p_diff.add_argument("--existing", required=True)
    p_diff.add_argument("--staged", required=True)

    p_inst = subs.add_parser("install", help="Back up the stored doc set and apply a staged re-harvest")
    p_inst.add_argument("--existing", required=True)
    p_inst.add_argument("--staged", required=True)
    p_inst.add_argument("--backup", help="backup dir (default: <library>/.doc-harvest-backups/<slug>-<date>)")
    p_inst.add_argument("--suffix", default="Apple HIG", help="title suffix stripped when listing new pages")

    p_val = subs.add_parser("validate", help="Check a doc-set dir for boilerplate, empty pages, bad links")
    p_val.add_argument("dir")
    p_val.add_argument("--manifest")
    p_val.add_argument("--min-chars", type=int, default=200)

    p_reg = subs.add_parser("registry", help="Rebuild known-docs.md from the library")
    p_reg.add_argument("--ccl-root")
    p_reg.add_argument("--out", required=True)

    args = parser.parse_args()

    if args.command == "discover":
        cmd_discover(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "organize":
        cmd_organize(args)
    elif args.command == "update-index":
        cmd_update_index(args)
    else:
        {"find": cmd_find, "diff": cmd_diff, "install": cmd_install,
         "validate": cmd_validate, "registry": cmd_registry}[args.command](args)


if __name__ == "__main__":
    main()
