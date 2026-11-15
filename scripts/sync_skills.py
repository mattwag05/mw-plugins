#!/usr/bin/env python3
"""Install core skills from a pinned commit and link them into every agent runtime.

  sync_skills.py [--ref REF] [--apply]    plan (default) or apply an install
  sync_skills.py check [--ref REF]        drift check: exit 0 clean, 1 drift

Canonical install: <home>/.agents/skills/<name> (Codex and Pi read this layout).
Runtime links, for each runtime directory that exists on this host:
  <home>/.claude/skills, <home>/.pi/agent/skills, <home>/.hermes/skills,
  <home>/.hermes/profiles/<p>/skills (except "default", which Hermes never reads).
Content comes from `git archive <ref>`, so uncommitted edits are never installed.
Anything replaced is moved to <home>/backups/<timestamp>-core-skill-sync/. A directory
holding nested skills (a category), or a runtime that already has a skill with the same
name, is never touched: it is reported as a conflict (two same-named skills hide each other).
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = "plugins/core/skills"
MANIFEST = ".core-sync.json"
EXCLUDE = {"evals", "__pycache__", ".DS_Store"}
retired = set()  # filled by export_ref from plugins/core/RETIRED at the ref


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True).stdout


def export_ref(ref, dest):
    """Extract plugins/core/skills at ref into dest; return (commit, {name: path})."""
    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    with tarfile.open(fileobj=io.BytesIO(git("archive", commit, SRC)), mode="r:") as tar:
        tar.extractall(dest, filter="data") if sys.version_info >= (3, 12) else tar.extractall(dest)
    root = Path(dest) / SRC
    skills = {p.name: p for p in sorted(root.iterdir()) if (p / "SKILL.md").is_file()}
    try:
        text = git("show", f"{commit}:plugins/core/RETIRED").decode()
    except subprocess.CalledProcessError:
        text = ""
    retired.clear()
    retired.update(l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#"))
    for p in skills.values():
        for junk in [q for q in p.rglob("*") if q.name in EXCLUDE]:
            if not junk.exists():
                continue  # already removed with an excluded parent
            shutil.rmtree(junk) if junk.is_dir() else junk.unlink()
    return commit, skills


def tree_hash(path):
    h = hashlib.sha256()
    for f in sorted(p for p in Path(path).rglob("*") if p.is_file()):
        h.update(str(f.relative_to(path)).encode() + b"\0" + str(os.access(f, os.X_OK)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def runtime_dirs(home):
    dirs = [home / ".claude/skills", home / ".pi/agent/skills", home / ".hermes/skills"]
    profiles = home / ".hermes/profiles"
    if profiles.is_dir():
        dirs += [p / "skills" for p in sorted(profiles.iterdir()) if p.is_dir() and p.name != "default"]
    # A runtime is present if its parent exists; create its skills dir if missing.
    return [d for d in dirs if d.parent.is_dir()]


def plan(home, skills):
    canon = home / ".agents/skills"
    actions = []
    for name, src in skills.items():
        dest = canon / name
        if dest.is_symlink() or not dest.exists():
            actions.append(("install", name, src, dest))
        elif not is_single_skill(dest):
            actions.append(("conflict", name, src, dest))
        elif tree_hash(dest) != tree_hash(src):
            actions.append(("update", name, src, dest))
    for rdir in [canon] + runtime_dirs(home):
        for name in sorted(retired - set(skills)):
            old = rdir / name
            if old.is_symlink() or (old.exists() and is_single_skill(old)):
                actions.append(("retire", name, None, old))
            elif old.exists():
                actions.append(("conflict", name, None, old))
    for rdir in runtime_dirs(home):
        taken = names_in(rdir)
        for name in skills:
            link, target = rdir / name, canon / name
            ours = link.is_symlink() and Path(os.readlink(link)) == target
            if any(d != link for d in taken.get(name, ())):
                # Another skill here already uses this name; two same-named skills hide each other in Hermes.
                actions.append(("unlink" if ours else "conflict", name, target, link))
                continue
            if ours:
                continue
            if link.is_symlink():
                kind = "relink"
            elif not link.exists():
                kind = "link"
            elif is_single_skill(link):
                kind = "replace-dir"
            else:
                kind = "conflict"  # a category or composite skill (for example Hermes research/): never replace
            actions.append((kind, name, target, link))
    return actions


def names_in(rdir):
    """{frontmatter name: [dirs]} for real skills under rdir, not following symlinks (core links are symlinks)."""
    names = {}
    if not rdir.is_dir():
        return names
    for root, dirs, files in os.walk(rdir):
        if "SKILL.md" not in files or Path(root) == rdir:
            continue
        with open(Path(root) / "SKILL.md", errors="ignore") as f:
            head = f.read(2000)
        for line in head.splitlines()[1:]:
            if line.strip() == "---":
                break
            if line.startswith("name:"):
                names.setdefault(line.split(":", 1)[1].strip().strip("\"'"), []).append(Path(root))
    return names


def is_single_skill(path):
    """A plain skill dir: SKILL.md at the top and no nested skills that replacing it would hide."""
    if not (path / "SKILL.md").is_file():
        return False
    return not any(p.name in ("SKILL.md", "DESCRIPTION.md") and p.parent != path for p in path.rglob("*"))


def apply(home, commit, ref, skills, actions):
    backup = home / "backups" / f"{time.strftime('%Y%m%d-%H%M%S')}-core-skill-sync"
    def stash(path):
        if path.is_symlink() or path.exists():
            rel = path.relative_to(home)
            (backup / rel).parent.mkdir(parents=True, exist_ok=True)
            os.rename(path, backup / rel)
    for kind, name, src, dest in actions:
        if kind == "conflict":
            continue
        if kind == "unlink":
            dest.unlink()  # our own symlink; nothing to back up
            continue
        if kind == "retire":
            stash(dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        stash(dest)
        if kind in ("install", "update"):
            shutil.copytree(src, dest, symlinks=False)
        else:
            os.symlink(src, dest)
    canon = home / ".agents/skills"
    manifest = {
        "ref": ref, "commit": commit, "synced_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "skills": {n: tree_hash(canon / n) for n in skills},
        "links": [str(d / n) for d in runtime_dirs(home) for n in skills
                  if (d / n).is_symlink() and Path(os.readlink(d / n)) == canon / n],
        "conflicts": [str(dest) for kind, _, _, dest in actions if kind in ("conflict", "unlink")],
        "retired": sorted(retired),
    }
    (canon / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
    return backup if backup.exists() else None


def check(home, ref):
    canon = home / ".agents/skills"
    try:
        manifest = json.loads((canon / MANIFEST).read_text())
    except (OSError, ValueError):
        print(f"DRIFT no manifest at {canon / MANIFEST}: core skills were never synced here")
        return 1
    problems = []
    for name, want in manifest["skills"].items():
        dest = canon / name
        if not dest.is_dir() or dest.is_symlink():
            problems.append(f"{name}: missing from {canon}")
        elif tree_hash(dest) != want:
            problems.append(f"{name}: edited since sync (installed files differ from the manifest)")
    for link in manifest["links"]:
        link = Path(link)
        if not (link.is_symlink() and Path(os.readlink(link)) == canon / link.name):
            problems.append(f"{link}: not a link to {canon / link.name}")
    with tempfile.TemporaryDirectory() as tmp:
        commit, skills = export_ref(ref, tmp)
        stale = sorted(n for n, p in skills.items() if manifest["skills"].get(n) != tree_hash(p))
    for rdir in [canon] + runtime_dirs(home):
        for name in manifest.get("retired", []):
            old = rdir / name
            if (old.is_symlink() or old.exists()) and str(old) not in manifest.get("conflicts", []):
                problems.append(f"{old}: retired skill is back; rerun sync --apply")
    for c in manifest.get("conflicts", []):
        print(f"NOTE {c}: an existing skill with this name or a category is kept; core skill not linked there")
    if stale:
        problems.append(f"behind {ref} ({commit[:10]}): {', '.join(stale)} differ; run sync --ref {ref} --apply")
    for p in problems:
        print(f"DRIFT {p}")
    if not problems:
        print(f"OK {len(manifest['skills'])} core skills match {manifest['commit'][:10]} and {ref}; links intact")
    return 1 if problems else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", nargs="?", choices=["sync", "check"], default="sync")
    ap.add_argument("--ref", default="HEAD", help="git ref to install from (default HEAD; recorded as a commit)")
    ap.add_argument("--apply", action="store_true", help="make the changes (default: print the plan only)")
    ap.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    home = args.home.resolve()
    if args.command == "check":
        return check(home, args.ref)
    with tempfile.TemporaryDirectory() as tmp:
        commit, skills = export_ref(args.ref, tmp)
        actions = plan(home, skills)
        changes = sum(a[0] != "conflict" for a in actions)
        print(f"core skills at {args.ref} = {commit[:10]}: {len(skills)} skills, {changes} changes, "
              f"{len(actions) - changes} conflicts kept as-is")
        for kind, name, src, dest in actions:
            print(f"  {kind:<11} {dest}" + (f" -> {src}" if kind not in ("install", "update", "retire") else ""))
        if not args.apply:
            print("dry run; rerun with --apply to make these changes")
            return 0
        backup = apply(home, commit, args.ref, skills, actions)
        print(f"applied; backups in {backup}" if backup else "applied; nothing replaced")
    return 0


if __name__ == "__main__":
    sys.exit(main())
