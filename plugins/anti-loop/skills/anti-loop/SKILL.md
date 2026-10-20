---
name: anti-loop
description: >-
  Use while iterating with tools: rerunning a measurement, benchmark, test or command to
  "double-check", rewording a call after it returned the same output, retrying after a tool
  error, or continuing after a guard blocked a call. Use when the user asks "what happened?",
  "are you stuck?" or says "you're looping". Also use when setting up an agent on a small or
  local model, where repeated identical calls are the most common failure.
metadata:
  version: "0.3.0"
---

# Anti-loop

A result you already have will not change if you run the call again or reword it. Rerunning is not investigation. It spends time and context and hides the real next step: deciding what the result means.

## Rules

1. **Say what each result showed.** After every batch of tool results, write one line: what you learned and what you will do next. If you cannot write that line, you are about to loop.
2. **Never rerun a call whose output you already have.** Collapsing whitespace, swapping quotes, `python -c` for a heredoc, `echo` for `printf`, adding a comment: all of these are the same call. The same output from a reworded call is the same evidence, not new evidence.
3. **Measure once, then act.** When a measurement answers the question, act on it: change the code, run a *different* check, or report. Repeat a measurement only after a change that could move it, and say which change.
4. **Three identical errors means stop.** Read the error (a missing argument, wrong format, wrong path), change approach, and tell the user what happened.
5. **A block is information.** When a guard or the user blocks a call, do not retry it or a reworded version. Explain in text what you were trying to learn, what the output already shows, and what you would do instead.
6. **Questions get answers.** When the user asks "what happened?" or "are you stuck?", answer in text before calling any tool.

Progress means a file changed or a result you have not seen before. Ten tool calls without either means you should stop gathering evidence: state your hypothesis in one sentence, then act on it or report the blocker.

## What a loop looks like

```text
python3 -c "...benchmark..."      -> real work: 0.001s
python3 -c "... import sys ..."   -> real work: 0.001s   (reworded, same result)
python3 - <<'EOF' ... EOF         -> real work: 0.001s   (reworded again)
```

The first result already said the code is fast and the delay is elsewhere. The next step was to look at the deliberate `sleep` calls, not to measure again.

## Enforcing it in Pi

Prose rules reduce loops but cannot prevent them. `assets/pi/no-progress-guard.ts` is an extension for the [Pi coding agent](https://github.com/earendil-works/pi) that enforces the rules above:

| Trigger | Action |
| --- | --- |
| An exact call (whitespace-normalized) already returned the same output twice | Block the third run and quote the output it already returned |
| The same output (20+ characters) seen 3 times from any calls | Annotate the result: rewording will not change it; the 4th stops the run |
| One command rerun only to view other parts of its output (`\| sed -n`, `head`, `tail`, `grep`, `wc`) | Annotate at 3 runs (save it to a file once), block after 6, stop on retry |
| 5 edits in a row that leave a check's output unchanged | Annotate at 3 (read the failing assertion first), stop at 5 |
| A command that deletes or overwrites paths outside the working directory | Annotate the 2nd run, block the 3rd (scratch paths are exempt) |
| An edit, write or bash command that changes nothing in the files it targets or names | Annotate it; a scripted write that changed nothing is called out (its pattern probably missed) |
| A file that loses over 30% of its size (and 2 KB) in one call | Annotate: check the edit did not delete code |
| 10, 20 and 30 calls with no file change and no new evidence | Steer, steer again, stop |
| 6 assistant turns with tool calls and no prose | Ask for a status line; if ignored once, block up to 2 silent calls, then let one through |
| A stop | Pause tools and request a text-only explanation that says what is still unverified |
| A question from the user after a stop | Answer with tools off, with the repeated outputs in context |

Files are compared before and after each call, so a bash command that changes a project file it names counts as an edit, the same as `edit` or `write`. Output comparison ignores process ids, timestamps and memory addresses, so reruns of the same failing check compare equal. A file-changing call resets the repeat counts. State lasts for the session, so a follow-up message does not re-arm reruns. The guard keeps only in-memory hashes and short excerpts. File changes made through `bash` do not count as progress.

Install:

```bash
mkdir -p ~/.pi/agent/extensions
cp assets/pi/no-progress-guard.ts ~/.pi/agent/extensions/
```

Then `/reload` in an open Pi session, or start a new one. Run the tests with `node --test assets/pi/test/`. They replay three real 2026-10-19 Qwen sessions: one reworded a benchmark until it was aborted three times without an explanation; one paged one program run through 45 `sed` windows, made 11 edits that never changed a failing test, and deleted files in the home directory 40 times; one patched a Three.js game through about 20 `node -e` scripts, one of which silently deleted 300 lines.

Tested on Pi 1.3.0, 0.80.6 and 0.73.1. Pi 1.x delivers the explanation request as a separate turn. Older releases ignore `turn_end` entries and `terminate`, so the request also travels in the tool result, a third call while paused aborts the run, and `agent_end` restores tools.

For small local models, also cut the prompt: skills, prompt templates and MCP or memory tool sets each add schema and instructions the model must read on every request. Loading only the tools a task needs (for example `pi --no-skills --no-prompt-templates --no-extensions -e <guard>`) cut one 27B setup from 8,189 to 2,575 first-request tokens.
