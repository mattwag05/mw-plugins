---
name: handoff
description: "Write HANDOFF.md so a fresh session can continue the work from files alone, and decide whether to hand off at all. Use when context is getting long, a phase ends, work pauses, or the human asks to hand off or continue later."
---

# Handoff

Goal: leave state in a file so a new session continues without this conversation. The file holds pointers to things, not copies of them.

## Should you hand off? (decide first)

- The next step is small and the context is still clear: continue, write nothing.
- The next phase is unrelated to what is in context: write a handoff, then start a fresh session.
- Context is long and noisy (many failed attempts, big outputs): write a handoff, then start a fresh session.
- A side job needs only a few paths and a done-check: give it to a subagent if you have one, with the goal, paths, and done-check. Otherwise do it later from a handoff.

## Steps

1. Find the facts by command, not memory: `git status --short`, `git log --oneline -5`, `ls`, and the project's `verify` command (run the project's `verify`; if none exists, run its documented test/lint/build and say `verify` is missing). Record the real results.
2. Write `HANDOFF.md` in the project root with exactly these headings, in order:
   - `## Goal` (one sentence)
   - `## Done-check` (the exact command or file test that proves the task is finished)
   - `## Done so far` (each item with an evidence pointer: a file path, a commit hash, or a command and its result)
   - `## Next` (numbered, the first step concrete enough to start at once)
   - `## Open gates` (failing checks, unanswered decisions, approvals still needed such as a push or deploy; write `none` if none)
   - `## Read first` (file paths the next session should open, one per line, with a few words each)
3. Point, do not paste. Never copy file contents, logs, or diffs into the handoff. Give the path (and line range if useful) or the command that prints it. If a spec, plan, or issue already holds the information, link it.
4. Keep it under 400 words. Cut anything the next session can get by reading a listed file.
5. Remove secrets: no keys, tokens, passwords, or personal data.
6. Check it: run `wc -w HANDOFF.md`, and run `ls` on each path in `## Read first` to confirm it exists. Fix any that do not.
7. Tell the human the file path and that a fresh session should begin by reading it.

## Rules

- Do not push, open a pull request, or deploy. List them under `## Open gates` if still pending.
- State only what you verified. If unsure, write `unverified`.

## Done when

- `HANDOFF.md` exists with all six headings.
- Every path under `## Read first` exists.
- `wc -w HANDOFF.md` is under 400.
- No block of copied file content appears in it.
