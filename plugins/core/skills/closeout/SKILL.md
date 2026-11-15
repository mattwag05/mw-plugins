---
name: closeout
description: "Close a work session cleanly: update owning docs, file issues, commit only reviewed paths locally, propose checks for mistakes, and hand off. Use at the end of every session or finished batch of changes. Covers the retired session-closeout and project-housekeeping."
---

# Closeout

Leave the work and its records consistent. Never push, and never touch a remote. For a read-only request or plan mode, write the proposed updates and stop: no edits, no commit. If asked to clean up, consolidate, update memory, or reconcile unfinished work, also read `references/housekeeping.md` and follow it.

## Steps

1. Scope. Run `git status --short` and `git diff --stat`. List the files this session changed on purpose. Any other modified or untracked file (scratch notes, someone else's work) is not yours: leave it alone, do not delete it, do not commit it. If the task names a file not to commit, that file stays out.
2. Verify. Run the project's `verify`; if none exists, run its documented test, lint or build and say `verify` is missing. Keep the output. A failure is an open gate: do not call the work complete, and do not commit it as finished.
3. Docs. For each behavior you changed, find the doc that owns it: `grep -rl "<command or name>" --include='*.md' .`. Edit that doc so it matches the new behavior. Do not create a new doc when one exists. If none owns it, write `skip: no doc owns it` in the handoff.
4. Issues. If `.beads/` exists: `bd close <id>` for finished work, `bd create` for out-of-scope findings. Otherwise use the tracker the project names. If there is none, list the leftovers under Open gates.
5. Stage only reviewed paths, one by one: `git add -- <path> ...`. Never `git add -A`, `git add .`, or `git commit -a`. Then run `git diff --cached --stat` and confirm it lists only your paths.
6. Secret check on what is staged:
   `git diff --cached | grep -nEi '(api[_-]?key|secret|token|passw(or)?d)[[:space:]]*[=:]|BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}'`
   Any hit: unstage it and report it. In a public repo, also keep private infrastructure and personal details out. Never use `--no-verify`.
7. Commit locally: `git commit -m "<what changed and why>"`. Do not push, add a remote, or open a PR. Make no empty commit when nothing changed. Pushing waits for a human approval that names it (see `../ship-ready/SKILL.md`).
8. Retro. Ask: what went wrong this session that a check could have caught? Read the errors and retries in this session's log or output. For each one write a proposal: the mistake, the check (a command, lint rule, or `verify` addition), and where it would live. A mistake of judgment becomes a proposed edit to a skill or doc instead. Do not edit any lint, verify, hook, CI, or skill file yourself. If nothing went wrong, write `none`.
9. Handoff. Write `CLOSEOUT.md` in the project root, leave it uncommitted, and paste the same text in your final reply. Headings, exactly:
   - `## What changed`: files and behavior, plus the commit hash.
   - `## Checks run`: each command with its result.
   - `## Open gates`: failing or missing checks, unpushed commits, files left uncommitted on purpose, approvals still needed.
   - `## Next step`: the one next action.
   - `## Proposed checks`: step 8 proposals (not applied).
   Use plain sentences, no em dashes.

## Done when

- `git log -1` shows a new local commit holding the intended files and none of the files you left alone.
- `git remote -v` and the reflog show no push was attempted.
- `CLOSEOUT.md` has all five headings.
- Changed behavior is described in its owning doc, or the handoff says why not.
- No lint, verify, hook, or CI file was changed by the retro.
