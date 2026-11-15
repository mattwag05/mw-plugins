#!/usr/bin/env python3
"""Flag AI tells in prose: em dashes, stock phrases, very long sentences.
Usage: slop_scan.py FILE...   Prints file:line: kind: text. Exit 1 if any found.
Fenced code blocks and inline `code` are skipped."""
import re
import sys

PHRASES = [
    r"\bdelve[sd]?\b", r"\bdelving\b", r"it'?s worth noting", r"it is worth noting",
    r"in today'?s fast-paced", r"ever-evolving", r"\bleverag(?:e|es|ed|ing)\b",
    r"\bseamless(?:ly)?\b", r"\brobust\b", r"\btapestry\b", r"\bpivotal\b",
    r"\butili[sz](?:e|es|ed|ing)\b", r"\bgame-?changer\b", r"great question",
    r"i hope this helps", r"\bin conclusion\b", r"testament to", r"\bunlock the (?:power|potential)\b",
    r"it is important to note", r"it'?s important to note", r"\bcrucial\b",
]
PHRASE_RE = re.compile("|".join(PHRASES), re.I)
MAX_WORDS = 40


def prose_lines(text):
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if not fence:
            yield n, re.sub(r"`[^`]*`", "", line)


def scan(path):
    found = []
    with open(path, encoding="utf-8") as f:
        lines = list(prose_lines(f.read()))
    for n, line in lines:
        if chr(0x2014) in line:
            found.append((n, "em-dash", line.strip()))
        for m in PHRASE_RE.finditer(line):
            found.append((n, "stock-phrase", m.group(0)))
        for s in re.split(r"(?<=[.!?])\s+", line):
            if len(s.split()) > MAX_WORDS:
                found.append((n, "long-sentence", " ".join(s.split()[:12]) + " ..."))
    return found


def main(paths):
    bad = 0
    for p in paths:
        for n, kind, text in scan(p):
            print(f"{p}:{n}: {kind}: {text}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: slop_scan.py FILE...")
    sys.exit(main(sys.argv[1:]))
