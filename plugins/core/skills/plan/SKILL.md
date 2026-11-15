---
name: plan
description: Turn a goal into a plan sized to the work: a short PLAN.md for one session, or a SPEC.md plus ordered, independently checkable issues for multi-session work. Use when starting work bigger than a small fix, or when asked to plan, spec, or break down a task.
---

# Plan

Goal: write the smallest planning artifact that lets work proceed in checkable pieces. The plan is written down, then you stop for approval. Do not start building.

A **slice** is one piece of work that ends in something you can check by running a command or reading a file, and that can be checked on its own. A **done-check** is that command or file test.

## Steps

1. Read the request and the files it touches (`ls`, `cat`, `grep`). State the goal in one sentence and the done-check for the whole task. Only if you cannot state the goal itself, read `../grill/SKILL.md` and follow it first. Open choices (stack, schema, naming) do not block the plan: write each as `assumed: <choice>` in the plan, then list them when you ask for approval.
2. Size the work. One session means a single sitting with fewer than about 6 steps. Anything larger is multi-session.
3. One session: write `PLAN.md` with these headings, in order:
   - `## Goal`
   - `## Files to touch`
   - `## Done-check` (an exact command and its expected result)
   - `## Steps` (numbered, each small and ordered)
   Create no other planning files. Go to step 7.
4. Multi-session: write `SPEC.md` with these headings:
   - `## Problem`
   - `## Decisions` (settled choices, one line each)
   - `## Out of scope`
   - `## Acceptance checks` (commands or file tests for the whole task)
5. Split the work into slices. Rules:
   - Each slice cuts through every layer it needs (data, logic, interface, test) so it works end to end, instead of finishing one layer for the whole task.
   - Each slice has its own done-check. If you cannot say how to check it, merge it into a neighbor or split it differently.
   - Put preparation (refactoring that makes later slices easy) first.
   - Order slices so each lists the slices it is blocked by. No cycles.
6. Record each slice as an issue:
   - If a `.beads/` directory exists, run `bd create "<title>" -d "<goal>. Done-check: <check>"` and note blockers with `bd dep add <blocked-id> <blocker-id>`.
   - Otherwise write `issues/NN-<slug>.md` (NN = 01, 02, ...) containing:
     ```
     # <title>
     Goal: <one sentence>
     Done-check: <exact command or file test>
     Blocked-by: <issue numbers, or none>
     ```
7. Show the plan path and the slice order. Ask for approval. Do not build until the human says to.

## Rules

- No speculative slices. Each one serves the stated goal.
- Wide mechanical changes (a rename across many files): add the new form beside the old, move callers in batches, remove the old form last, each as its own slice.
- Never push, open a pull request, or deploy as part of a plan unless the human names that action.

## Done when

- One-session work: `PLAN.md` exists with the four headings and no `SPEC.md` or `issues/` exists.
- Multi-session work: `SPEC.md` has the four headings, and there are at least two issues, each with a done-check and a blocked-by line (or `bd` issues with the same content).
- The human was asked to approve before any build step.
