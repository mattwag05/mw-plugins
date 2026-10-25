#!/usr/bin/env python3
"""
doc-harvest: Apple developer docs via Apple's JSON content API (stdlib only).

developer.apple.com renders client-side, but every page is also served as
structured JSON at /tutorials/data/<path>.json. That is faster and cleaner than a
browser render (about 1s/page vs 30s+, no site chrome) and its topicSections give a
complete page tree, which the rendered nav does not.

Subcommands:
  crawl <root-url> --out manifest.json
      Walk topicSections from the root and list every page.
  stage --manifest manifest.json --out DIR [--existing CCL_DOC_DIR] [--workers 4]
      Fetch every page and write full-text Markdown into DIR, mirroring the layout of
      an existing doc set (matched by source_url) and placing new pages from the
      page's `hierarchy`. Hub pages that already have an _index.md are skipped.
      Then run `harvest.py diff` / `install` to review and apply.

Example:
  apple_json.py crawl https://developer.apple.com/design/human-interface-guidelines -o m.json
  apple_json.py stage -m m.json -o /tmp/stage --existing "$CCL/30-Technology/apple-hig"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE = "https://developer.apple.com"
UA = "Mozilla/5.0 (doc-harvest)"


def get_json(path: str) -> dict:
    last: Exception | None = None
    for _ in range(3):
        try:
            req = Request(f"{BASE}/tutorials/data{path}.json", headers={"User-Agent": UA})
            with urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # network/HTTP: retry, then raise the last one
            last = e
            time.sleep(2)
    raise RuntimeError(f"fetch failed for {path}: {last}")


def _root_path(url: str) -> str:
    return urlparse(url).path.rstrip("/").lower()


def child_paths(doc: dict, root: str) -> list[str]:
    """topicSections identifiers -> site paths under `root` (lowercased)."""
    out = []
    for sec in doc.get("topicSections", []):
        for ident in sec.get("identifiers", []):
            m = re.match(r"doc://[^/]+/(?:design|documentation)/([^/]+)/(.+)", ident, re.I)
            if m:
                out.append(f"{root.rsplit('/', 1)[0]}/{m.group(1).lower()}/{m.group(2).lower()}")
    return out


def crawl(root_url: str) -> dict:
    root = _root_path(root_url)
    seen: dict[str, str | None] = {}
    todo = [root]
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        try:
            doc = get_json(p)
        except RuntimeError as e:
            print(f"warning: {e}", file=sys.stderr)
            seen[p] = None
            continue
        seen[p] = doc.get("metadata", {}).get("title", "")
        todo += [c for c in child_paths(doc, root) if c not in seen]
        time.sleep(0.2)
    pages = sorted(p for p in seen if p != root)
    return {"root": root, "base_url": BASE + root, "pages": pages,
            "titles": seen, "errors": [p for p, t in seen.items() if t is None]}


# ---------------------------------------------------------------------------
# JSON -> Markdown
# ---------------------------------------------------------------------------

def inline(nodes, refs) -> str:
    out = ""
    for n in nodes or []:
        t = n.get("type")
        if t == "text":
            out += n["text"]
        elif t == "strong":
            out += "**" + inline(n["inlineContent"], refs).strip() + "**"
        elif t in ("emphasis", "newTerm"):
            out += "*" + inline(n["inlineContent"], refs).strip() + "*"
        elif t == "codeVoice":
            out += "`" + n["code"] + "`"
        elif t == "reference":
            r = refs.get(n["identifier"], {})
            title = inline(n.get("overridingTitleInlineContent"), refs) or r.get("title", "")
            url = r.get("url", "")
            out += f"[{title}]({BASE + url if url.startswith('/') else url})" if url else title
        elif t == "link":
            out += f"[{n.get('title') or n['destination']}]({n['destination']})"
        elif "inlineContent" in n:
            out += inline(n["inlineContent"], refs)
    return out


def blocks(nodes, refs) -> list[str]:
    out: list[str] = []
    for n in nodes or []:
        t = n.get("type")
        if t == "paragraph":
            out.append(inline(n["inlineContent"], refs).strip())
        elif t == "heading":
            out.append("#" * min(n["level"] + 1, 6) + " " + n["text"])
        elif t in ("unorderedList", "orderedList"):
            items = []
            for i, it in enumerate(n["items"], 1):
                b = blocks(it["content"], refs)
                mark = "- " if t == "unorderedList" else f"{i}. "
                items.append(mark + "\n  ".join(" ".join(b).split("\n")))
            out.append("\n".join(items))
        elif t == "table":
            rows = ["| " + " | ".join(" ".join(blocks(c, refs)).replace("\n", " ").replace("|", "\\|")
                                      for c in r) + " |" for r in n["rows"]]
            if rows:
                rows.insert(1, "|" + " --- |" * len(n["rows"][0]))
                out.append("\n".join(rows))
        elif t == "aside":
            label = (n.get("name") or n.get("style") or "note").title()
            out.append(f"> **{label}** " + " ".join(blocks(n["content"], refs)).replace("\n", " "))
        elif t == "codeListing":
            out.append("```\n" + "\n".join(n["code"]) + "\n```")
        elif t == "row":
            for c in n["columns"]:
                out += blocks(c["content"], refs)
        elif t == "small":
            out.append(inline(n["inlineContent"], refs))
        elif t in ("image", "video", "links"):
            continue  # media: not useful as text context
        elif "content" in n:
            out += blocks(n["content"], refs)
    return out


def to_markdown(doc: dict) -> str:
    refs = doc.get("references", {})
    md = []
    abstract = inline(doc.get("abstract"), refs).strip()
    if abstract:
        md.append(abstract)
    for sec in doc.get("primaryContentSections", []):
        md += blocks(sec.get("content", []), refs)
    return "\n\n".join(x for x in md if x.strip())


# ---------------------------------------------------------------------------
# stage
# ---------------------------------------------------------------------------

def existing_by_url(doc_dir: Path) -> dict[str, str]:
    """source_url -> path relative to doc_dir, for every page already stored."""
    found: dict[str, str] = {}
    for f in doc_dir.rglob("*.md"):
        m = re.search(r"^source_url: (\S+)", f.read_text(encoding="utf-8")[:800], re.M)
        if m:
            found[m.group(1).rstrip("/")] = str(f.relative_to(doc_dir))
    return found


def destination(path: str, doc: dict, old: dict[str, str], root: str) -> str:
    url = BASE + path
    if url in old:
        return old[url]
    # New page: place by hierarchy (everything after the doc-set root), e.g.
    # components/menus-and-actions/<slug>.md
    chain = [h.rsplit("/", 1)[1].lower() for h in doc["hierarchy"]["paths"][0]
             if h.lower().rsplit("/", 1)[0].startswith(("doc://com.apple.hig/design/human-interface-guidelines",))]
    chain = [c for c in chain if c != root.rsplit("/", 1)[1]]
    return "/".join(chain + [path.rsplit("/", 1)[1]]) + ".md"


def stage(manifest: dict, out: Path, existing: Path | None, workers: int, mode: str = "full") -> dict:
    root = manifest["root"]
    old = existing_by_url(existing) if existing and existing.exists() else {}
    today = date.today().isoformat()
    report = {"pages": 0, "hubs": 0, "new": []}

    def fetch(p):
        return p, get_json(p)

    with ThreadPoolExecutor(workers) as ex:
        for p, doc in ex.map(fetch, manifest["pages"]):
            slug = p.rsplit("/", 1)[1]
            rel = destination(p, doc, old, root)
            # A hub already stored as <...>/<slug>/_index.md (or the root itself) keeps its curated text.
            if doc.get("topicSections") and (rel.endswith("_index.md") or
                                              (existing and any(existing.glob(f"**/{slug}/_index.md")))):
                report["hubs"] += 1
                continue  # hub with an existing _index.md: leave its curated text alone
            title = doc["metadata"]["title"]
            parent = str(Path(rel).parent)
            parent = "" if parent == "." else parent + "/"
            fm = (f"---\nname: {title} - Apple HIG\nsource_url: {BASE + p}\n"
                  f"parent: {existing.name if existing else 'apple-hig'}/{parent}_index.md\n"
                  f"harvest_mode: {mode}\nlast_updated: {today}\n---\n\n# {title}\n\n")
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(fm + to_markdown(doc) + "\n", encoding="utf-8")
            report["pages"] += 1
            if BASE + p not in old:
                report["new"].append(rel)
    return report


def main():
    ap = argparse.ArgumentParser(prog="apple_json", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crawl")
    c.add_argument("url")
    c.add_argument("-o", "--out", required=True)
    s = sub.add_parser("stage")
    s.add_argument("-m", "--manifest", required=True)
    s.add_argument("-o", "--out", required=True)
    s.add_argument("--existing", help="existing doc-set dir to match pages against")
    s.add_argument("--workers", type=int, default=4)
    s.add_argument("--mode", choices=["full", "summary"], default="full")
    a = ap.parse_args()
    if a.cmd == "crawl":
        m = crawl(a.url)
        Path(a.out).write_text(json.dumps(m, indent=1))
        print(f"{len(m['pages'])} pages, {len(m['errors'])} errors -> {a.out}")
        sys.exit(1 if m["errors"] else 0)
    manifest = json.loads(Path(a.manifest).read_text())
    rep = stage(manifest, Path(a.out), Path(a.existing) if a.existing else None, a.workers, a.mode)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
