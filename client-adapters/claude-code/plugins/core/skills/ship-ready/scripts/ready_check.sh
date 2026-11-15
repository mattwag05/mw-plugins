#!/bin/sh
# Usage: sh ready_check.sh [base-ref]   (run from inside the project repo)
# Checks the local, deterministic ship items. Last line is READY or NOT READY.
# shortcut: local checks only, no forge CI polling; use the forge's own watcher for that.
fails=0
pass() { echo "PASS $1: $2"; }
fail() { echo "FAIL $1: $2"; fails=$((fails + 1)); }

git rev-parse --git-dir >/dev/null 2>&1 || { echo "FAIL repo: not a git repository"; echo "NOT READY"; exit 1; }

# 1. clean tree (SHIP.md is this skill's own output)
dirty=$(git status --porcelain | grep -v ' SHIP.md$')
if [ -n "$dirty" ]; then
  fail tree "uncommitted changes: $(echo "$dirty" | head -5 | tr '\n' ';')"
else
  pass tree "clean"
fi

# 2. verify
log=$(mktemp)
if [ -f ./verify ]; then
  if [ -x ./verify ]; then ./verify >"$log" 2>&1; else sh ./verify >"$log" 2>&1; fi
  rc=$?
elif command -v verify >/dev/null 2>&1; then
  verify >"$log" 2>&1; rc=$?
else
  rc=none
fi
if [ "$rc" = none ]; then
  echo "WARN verify: no verify command found; run the documented checks and list verify as missing (open gate)"
elif [ "$rc" -eq 0 ]; then
  pass verify "exit 0"
else
  fail verify "verify exited $rc; last output: $(tail -3 "$log" | tr '\n' ' ')"
fi
rm -f "$log"

# 3. ahead of and not behind base
base=$1
if [ -z "$base" ]; then
  cur=$(git rev-parse HEAD 2>/dev/null)
  for b in origin/main origin/master main master; do
    if git rev-parse --verify -q "$b" >/dev/null && [ "$(git rev-parse "$b")" != "$cur" ]; then base=$b; break; fi
  done
fi
if [ -z "$base" ]; then
  fail base "no base branch found that differs from HEAD; pass one: sh ready_check.sh <base-ref>"
else
  ahead=$(git rev-list --count "$base..HEAD")
  behind=$(git rev-list --count "HEAD..$base")
  [ "$ahead" -gt 0 ] && pass ahead "$ahead commit(s) ahead of $base" || fail ahead "no commits ahead of $base"
  [ "$behind" -eq 0 ] && pass up-to-date "not behind $base" || fail up-to-date "behind $base by $behind commit(s); update the branch"
fi

# 4. conflict markers
markers=$(git grep -I -n --untracked -E '^(<<<<<<< |>>>>>>> )' -- . ':!SHIP.md' | head -3)
if [ -n "$markers" ]; then fail conflict-markers "found: $(echo "$markers" | tr '\n' ';')"; else pass conflict-markers "none"; fi

# 5. REVIEW.md open items
if [ -f REVIEW.md ]; then
  open=$(grep -iE 'act on' REVIEW.md | grep -viE '\[x\]|dismissed|fixed|done|resolved')
  if [ -n "$open" ]; then fail review "open 'act on' items in REVIEW.md: $(echo "$open" | head -3 | tr '\n' ';')"; else pass review "no open items"; fi
fi

echo
if [ "$fails" -eq 0 ]; then echo "READY"; else echo "NOT READY ($fails problem(s))"; exit 1; fi
