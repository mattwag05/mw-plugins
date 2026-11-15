# Workflow bindings

Use the shared agentic development guide at `~/Projects/shared-workflows/docs/AGENTIC-WORKFLOW.md` when available. Contributor-specific server addresses belong in local instructions. Otherwise follow this repository's contribution, verification, and publication rules.

- Default branch: `main`. Fetch and verify its ref before creating a worktree; preserve the current branch and existing worktrees.
- Canonical remote: `origin`, the Forgejo repository (address in local instructions). GitHub `mattwag05/mw-plugins` is a one-way push mirror: never push to it.
- Issue tracker: Forgejo issues on `origin`. Read `docs/agents/issue-tracker.md`.
- Verification: `./verify` (adapters current, marketplace valid, unit tests, core skill lint, no em dashes in core, secret scan; exit 2 means a tool was missing). Regenerate adapters with `python3 scripts/build_claude_adapters.py` only after authored source changes.
- Durable documentation: README.md and the changed plugin's README.md / SKILL.md

Load the relevant Matt Pocock skill for the task. Apply `unslop` to authored prose and use `session-closeout` to finish. Preserve existing secret checks. Missing tools or unavailable verification are open gates, not successful checks.

Background coding remains opt-in. These bindings alone do not enable it or authorize pushes, PR changes, merges, or deployments. Follow the current user's publication authority. Historical specs under directories named for older skills retain their design evidence; they do not select the current workflow.
