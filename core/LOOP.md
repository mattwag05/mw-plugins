# The loop

Use these five steps for every task. Never skip a step silently; write `skip: <reason>`.

## 1. Frame

1. State the goal in one sentence.
2. State the done-check: the observable result that proves the task is finished.
3. If you cannot write the done-check, intent is unclear: use `grill` first.
4. Pick one playbook. Before your first edit, read its file, `~/.agents/skills/<name>/SKILL.md`, and follow it:
   - new behavior: `tdd`
   - bug: `debug`
   - homelab or live-system change: `ops-change`
   - question that needs sources: `research`
   - prose for people: `unslop`
5. Size the work:
   - Small (one sitting, obvious change): no planning artifact.
   - One session: a short plan file (goal, files, done-check).
   - More than one session: `plan`, which produces a spec and tracked issues.

## 2. Ground

1. Read what the change touches before you edit it: callers, tests, config, owning docs.
2. For a bug, reproduce it through the real behavior first. The reproduction must be able to fail, and you must see it fail.
3. For a live system, find the record that owns it (registry, runbook) and take the source-specific backup before changing state.
4. Facts come from tools, not memory. Say "unknown" rather than guess.

## 3. Do

1. Make the smallest complete change, reusing what exists. Add nothing nobody asked for.
2. Follow the playbook's numbered steps in order.
3. Record unrelated findings as issues (in `bd` if `.beads/` exists) and continue the task.
4. After 3 distinct approaches fail, stop. Rewording or rerunning a call is not a new approach. Report what each try showed and ask one specific question.

## 4. Verify

1. Run `./verify` at the repo root, or the playbook's done-check, and paste the output. The output is evidence. Your summary is not.
2. "Inconclusive" is not a pass. A missing or failing check is an open gate: say so plainly. Show each new check failing once before you trust it.
3. Judge success by a check that does not depend on you: a spec, real data, the reproduction, or another system's output. Expected values in tests come from there.
4. For a consequential change, use `review`. The reviewer starts fresh and gets the original goal and the diff.

## 5. Close

1. Use `closeout`. Update the docs that own the changed behavior, close or file issues, and commit the reviewed paths locally.
2. Ask: what went wrong that a check could have caught? Propose it; do not apply it unasked.
3. Push, PR, merge, deploy, and live-config changes wait for explicit approval. `ship-ready` defines when to ask.
4. Hand off: what changed, checks run with results, open gates, next step.

## When context runs short

- A fresh context beats a long one. Before clearing, write state to a file (`handoff`).
- Pass file paths, not pasted content.
- A subagent starts fresh. Give it the goal, paths, and done-check. Check its artifacts, not its summary.
