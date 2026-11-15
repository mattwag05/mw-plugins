---
name: ship-ready
description: Decide whether a change is ready to ask the human to push or merge, and prepare the ask (SHIP.md with verdict, checklist, PR body). Use before asking to push, open a PR, or merge.
---

# Ship ready

You never push, open a PR, or merge. You decide whether the change is ready, write the ask, and wait for the human to approve a named action.

## Steps

1. Find this skill's folder (where you read this file). From the project root run:
   `sh <skill-folder>/scripts/ready_check.sh [base-branch]`
   It checks: clean tree, `verify` exit code, branch ahead of and not behind base, no conflict markers, no open "act on" items in `REVIEW.md`. Do not redo these by hand.
2. Check what the script cannot:
   - The proof covers the diff: run `git diff <base>...HEAD --stat` and make sure the `verify` output (or the documented checks) exercised the changed behavior. If `verify` is missing, say so; that is an open gate.
   - Review findings (bot, human, `REVIEW.md`) are each fixed, or dismissed with a written reason.
   - No unresolved change requests.
   - CI: forge polling is out of scope here. If the forge has its own watcher or status command, use it. Never write your own sleep loop. If you cannot read CI state, list it as unchecked.
3. Write `SHIP.md` in the project root. Line 1 is exactly `Verdict: READY` or `Verdict: NOT READY`. Then:
   - `## Checklist`: each script line, plus your step 2 results, as PASS, FAIL, or UNCHECKED with a reason.
   - If NOT READY: `## Blocking` listing every FAIL, naming the failing check (for example "verify exited 1"), and the next fix. Stop there.
   - If READY: `## PR body` with `### Problem`, `### Change`, `### Proof`.
4. PR body rules: Problem is one or two plain sentences on what was wrong or missing, from the user's request, not an inventory of edits. Change says in a few lines what you did and why. Proof pastes the `verify` command and its final output lines. Add a `Door: one-way` or `two-way` line (can it be undone after merge?). Use a title that says why the change matters.
5. Reply with the verdict and the one action you want approved, naming it, for example "Approve: push branch X to remote Y, then open a PR". Wait.

## Done when

- `SHIP.md` exists, line 1 is `Verdict: READY` or `Verdict: NOT READY`, and it matches the script's last line plus your step 2 findings.
- A NOT READY verdict names each failing check.
- A READY verdict has a PR body with Problem, Change, and Proof sections.
- No push, PR, or merge command was run, and no remote was added.
