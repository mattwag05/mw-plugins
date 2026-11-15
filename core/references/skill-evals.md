# Skill evals

A core skill joins the core only when its evals pass on Qwen3.8-27B, the floor model for every skill. Rerun the evals after you edit a skill or change models.

## Layout

```
<skill>/evals/<case>/
  task.md      the prompt, written the way a user would ask
  workspace/   optional starting files, copied fresh for each run
  setup        optional executable; prepares state (such as git history) in the workspace before the agent
  check        executable; runs in the workspace after the agent; exit 0 = pass
```

The `check` script gets two environment variables: `EVAL_TRANSCRIPT` (the agent's output) and `EVAL_WORKSPACE`. Its last output line becomes the reason printed in the report.

## Run

```bash
python3 scripts/eval_skill.py <skill-dir> --runs 3
```

By default the runner calls `pi -p` and loads only the skill under test, with no context files, extensions, or MCP. It also tells the model which `SKILL.md` to read, because the 27B model often skips a skill that only its description advertises. That is why `LOOP.md` names the skill to read. `--no-hint` drops that line, to test routing on its own. The runner also loads the anti-loop no-progress guard, as production Pi does. Without it, the 27B model once repeated a single tool call more than 150 times until the run timed out. `--no-guard` turns it off. `--model` picks the model, `--case` picks a single case, and `--agent-cmd` swaps in another agent. A case passes only when every run passes. Small models vary from run to run, so use `--runs 3` before a skill joins the core.

## Writing good cases

- Check the step that only the skill would cause. A model with no skill loaded must fail the check. Prove this once with a control run (see `tests/eval_skill/no_skill_agent.sh`).
- Include at least one case that must fail, to prove the check can tell good output from bad.
- Checks must be deterministic: compare files, exit codes, or exact strings. Never ask a model to grade the result.
- Put deterministic steps in commands. In the first fixture run, the 27B model reversed `lantern` by hand and got it wrong. With `rev` named in the skill, it passed 3 of 3.
