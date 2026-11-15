---
name: skill-authoring
description: Write or edit an agent skill so a small model can follow it, with evals. Use when creating a new SKILL.md, fixing a skill that misbehaves, or reviewing a skill before it ships.
---

# Skill authoring

A skill is a directory with `SKILL.md` (instructions an agent loads) plus optional files. An eval is a small task with a script that checks the result.

## Steps

1. Name the one job. A skill does one thing. If the job needs two, write two skills.
2. Write frontmatter: `name:` (kebab-case, equals the directory name) and `description:` (under 300 characters: what it does, then "Use when ..." triggers). Put the trigger words first. The description sits in the agent's context every turn, so cut every word the body already says.
3. Write the body under 600 words, in this order: short definition of any jargon, numbered steps, `## Done when`. Each step is one action ending in something observable.
4. Write steps as commands, not advice. If a step is mechanical (counting, sorting, reversing, diffing), name the command to run. Small models botch hand-done mechanical work.
5. Say what to do, not what to avoid. A banned behavior drags attention to it. Keep a prohibition only for a hard limit (never push, never deploy) and pair it with the action to take instead.
6. If a step needs another skill, write "read `../<other>/SKILL.md` and follow it". Never rely on the agent remembering a chain.
7. Move long reference (pattern lists, tables) to a sibling file and name it in a step ("read `patterns.md`"). Keep the main file for steps.
8. Refer to the project's `verify` command where checking happens. If none exists, say so and run its test or build command.
9. Use no em dash characters (U+2014). Use commas, colons, or parentheses.
10. Write `PROVENANCE.md`: one line per source `- <repo> @ <commit>, <path>, <license>: <what was taken>`, then `Adapted for small models: <what changed>`. Copy no text from unlicensed sources.
11. Write 2 or 3 eval cases in `evals/<case>/`: `task.md` (the prompt as a user would write it), optional `workspace/` (starting files), and an executable `check` (exit 0 passes; last output line is the reason). Checks compare files, exit codes, or exact strings. Never have a model grade.
12. Prove each check discriminates: in a temp copy of the workspace, build a correct result and run `check` (expect 0), then a plausible wrong result (expect nonzero). Delete the temp copy.
13. At least one case must test behavior that only this skill causes.
14. Run `python3 scripts/lint_skill.py <skill-dir>` (path relative to this skill's directory). Fix each printed failure and rerun until it exits 0.

## Done when

- `python3 scripts/lint_skill.py <skill-dir>` exits 0.
- Every `check` returned 0 on a correct result and nonzero on a wrong one, and you recorded both exit codes.
- Each step in `SKILL.md` ends in something you can observe.
- No step depends on the agent remembering another skill.
