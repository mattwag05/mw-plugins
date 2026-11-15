# Skill evals

A core skill joins the core only when its evals pass on the floor model: Qwen3.8-27B for judgment skills, Qwen3.6 for mechanical ones. Rerun the evals after you edit a skill or change models.

## Layout

```
<skill>/evals/<case>/
  task.md      the prompt, written the way a user would ask
  workspace/   optional starting files, copied fresh for each run
  check        executable; runs in the workspace after the agent; exit 0 = pass
```

The `check` script gets two environment variables: `EVAL_TRANSCRIPT` (the agent's output) and `EVAL_WORKSPACE`. Its last output line becomes the reason printed in the report.

## Run

```bash
python3 scripts/eval_skill.py <skill-dir> --runs 3
```

By default the runner calls `pi -p` and loads only the skill under test, with no context files, extensions, or MCP. `--model` picks the model, `--case` picks a single case, and `--agent-cmd` swaps in another agent. A case passes only when every run passes. Small models vary from run to run, so use `--runs 3` before a skill joins the core.

## Writing good cases

- Check the step that only the skill would cause. A model with no skill loaded must fail the check. Prove this once with a control run (see `tests/eval_skill/no_skill_agent.sh`).
- Include at least one case that must fail, to prove the check can tell good output from bad.
- Checks must be deterministic: compare files, exit codes, or exact strings. Never ask a model to grade the result.
- Put deterministic steps in commands. In the first fixture run, the 27B model reversed `lantern` by hand and got it wrong. With `rev` named in the skill, it passed 3 of 3.
