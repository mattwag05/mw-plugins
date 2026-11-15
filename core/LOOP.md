# The loop

Use these five steps for every task: code, homelab changes, research, writing. A small task runs them in a few lines. Never skip a step silently; write `skip: <reason>`.

## 1. Frame

1. State the goal in one sentence.
2. State the done-check: the observable result that proves the task is finished. Examples: a command's output, a passing test, a file at a path.
3. If you cannot write the done-check, the intent is unclear. Use `grill` before doing anything else.
4. Pick one playbook and read only that skill:
   - new behavior: `tdd`
   - bug: `debug`
   - homelab or live-system change: `ops-change`
   - question that needs sources: `research`
   - prose for people: `unslop`
5. Size the work:
   - Small (one sitting, obvious change): no planning artifact.
   - One session: a short plan file listing the goal, the files, and the done-check.
   - More than one session: `plan`, which produces a spec and tracked issues.

## 2. Ground

1. Read what the change touches before you edit it: callers, tests, config, and the docs that own the behavior.
2. For a bug, reproduce it through the real behavior first. The reproduction must be able to fail, and you must see it fail.
3. For a live system, find the record that owns it (registry, runbook) and take the source-specific backup before changing state.
4. Facts come from tools, not memory. "Unknown" is an acceptable answer. A guess is not.

## 3. Do

1. Make the smallest complete change. Reuse what already exists. Add no options or abstractions nobody asked for.
2. Follow the playbook's numbered steps in order.
3. Record unrelated findings as issues (in `bd` if `.beads/` exists) and continue the task.

## 4. Verify

1. Run `./verify` at the repo root (see `references/verify.md`), or the playbook's done-check, and paste the output. The output is evidence. Your summary is not.
2. "Inconclusive" is not a pass. A missing or failing check is an open gate: say so plainly.
3. Expected values in tests come from outside your own reasoning: a spec, real data, or the reproduction.
4. For a consequential change, use `review`. The reviewer starts fresh and gets the original goal and the diff.

## 5. Close

1. Use `closeout`. Update the docs that own the changed behavior, close or file issues, and commit the reviewed paths locally.
2. Ask: what went wrong that a check could have caught? Propose that check or skill edit. Do not apply it unasked.
3. Push, PR, merge, deploy, and live-config changes wait for explicit approval. `ship-ready` defines when to ask.
4. Hand off four things: what changed, which checks ran and their results, open gates, and the next step.

## When context runs short

- A fresh context beats a long one. Before clearing, write state to a file (`handoff`).
- Pass file paths, not pasted content.
- A subagent starts fresh. Give it the goal, the paths, and the done-check. Check its artifacts, not its summary.
