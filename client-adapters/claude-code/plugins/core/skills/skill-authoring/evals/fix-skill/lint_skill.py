#!/usr/bin/env python3
"""Mechanical lint for a skill dir. Usage: lint_skill.py SKILL_DIR...
Prints each failure; exits 1 if any."""
import os
import re
import sys


def yaml_unsafe(fm):
    """Flag frontmatter that strict YAML parsers (Pi uses npm `yaml`) reject, which makes them drop the skill."""
    errs = []
    for line in fm.splitlines():
        m = re.match(r"([A-Za-z_][\w-]*):[ \t]+(\S.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).rstrip()
        if val[0] == '"':
            if len(val) < 2 or not val.endswith('"') or re.search(r'(?<!\\)"', val[1:-1]):
                errs.append(f"frontmatter: {key} has unbalanced or unescaped double quotes")
        elif val[0] == "'":
            if len(val) < 2 or not val.endswith("'") or re.search(r"(?<!')'(?!')", val[1:-1]):
                errs.append(f"frontmatter: {key} has unbalanced single quotes")
        elif val[0] not in "|>[{" and (": " in val or val.endswith(":") or " #" in val):
            errs.append(f"frontmatter: {key} is unquoted but contains ': ', ' #', or a trailing ':' (double-quote it)")
    return errs


def lint(d):
    errs = []
    sk = os.path.join(d, "SKILL.md")
    if not os.path.isfile(sk):
        return ["SKILL.md missing"]
    text = open(sk, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return ["frontmatter missing"]
    fm, body = m.groups()
    errs += yaml_unsafe(fm)
    name = re.search(r"^name:\s*(\S.*)$", fm, re.M)
    desc = re.search(r"^description:\s*(\S.*)$", fm, re.M)
    if not name:
        errs.append("frontmatter: name missing")
    if not desc:
        errs.append("frontmatter: description missing")
    elif len(desc.group(1).strip().strip("'\"")) >= 300:
        errs.append("description is 300 characters or more")
    words = len(body.split())
    if words >= 600:
        errs.append(f"body has {words} words (limit under 600)")
    if not re.search(r"^#{1,6}\s*Done when\b", body, re.M | re.I):
        errs.append("no 'Done when' heading")
    if not re.search(r"^\s*1\.\s", body, re.M):
        errs.append("no numbered steps")
    for root, _, files in os.walk(d):
        if "evals" in os.path.relpath(root, d).split(os.sep):
            continue
        for f in files:
            if f.endswith((".md", ".py", ".sh")):
                p = os.path.join(root, f)
                if chr(0x2014) in open(p, encoding="utf-8", errors="ignore").read():
                    errs.append(f"em dash in {os.path.relpath(p, d)}")
    if not os.path.isfile(os.path.join(d, "PROVENANCE.md")):
        errs.append("PROVENANCE.md missing")
    ev = os.path.join(d, "evals")
    cases = sorted(c for c in os.listdir(ev) if os.path.isdir(os.path.join(ev, c))) if os.path.isdir(ev) else []
    if not 2 <= len(cases) <= 3:
        errs.append(f"{len(cases)} eval cases (need 2 or 3)")
    for c in cases:
        cd = os.path.join(ev, c)
        if not os.path.isfile(os.path.join(cd, "task.md")):
            errs.append(f"evals/{c}: task.md missing")
        chk = os.path.join(cd, "check")
        if not (os.path.isfile(chk) and os.access(chk, os.X_OK)):
            errs.append(f"evals/{c}: check missing or not executable")
    return errs


def main(dirs):
    bad = 0
    for d in dirs:
        errs = lint(d.rstrip("/"))
        for e in errs:
            print(f"{d}: {e}")
        bad += len(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: lint_skill.py SKILL_DIR...")
    sys.exit(main(sys.argv[1:]))
