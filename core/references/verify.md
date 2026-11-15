# The verify convention

Every repo exposes one command an agent runs to check its work: an executable `./verify` at the repo root. Skills and `LOOP.md` call it by that name, and `ship-ready` runs it automatically.

## Rules

- Copy `core/templates/verify` to the repo root, run `chmod +x verify`, and replace the example checks with the repo's real ones: tests, lint, build, generated-file checks, secret scan.
- It runs every check, then reports `PASS`, `FAIL`, or `SKIP` for each one.
- Exit codes:

  | Code | Meaning |
  | --- | --- |
  | 0 | Every check passed. |
  | 1 | A check failed. |
  | 2 | Nothing failed, but a check was skipped because its tool is missing. That is an open gate, not a pass. |
- Keep it fast enough to run after every change, ideally under a minute. Slow suites go in a separate documented command.
- It must be deterministic: no network, no model calls, no prompts.
- Prove each new check once: inject a failure it should catch and confirm `./verify` exits 1.

## When a repo has none

Run the documented test, lint, and build commands, and say `verify` is missing. Adding `./verify` from the template is a good first task in that repo.
