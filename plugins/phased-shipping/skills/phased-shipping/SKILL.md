---
name: phased-shipping
description: Ship a multi-phase engineering plan as a sequence of stacked PRs, using beads for task tracking and background subagents to fix red CI without blocking the main thread. Use this skill ANY TIME the user says things like "ship the next phase", "continue until everything is green", "take this plan and do it across several PRs", "implement phases 1 through N", "keep going until all the PRs land", "work through this roadmap", "if any PRs hit CI issues send subagents to fix them so you can remain focused", or any phrasing that implies a long-running multi-PR engineering task that needs to flow from plan to landed PRs without babysitting. Trigger even when the user doesn't explicitly say "skill" — if the task spans multiple logical commits, multiple PRs, or has explicit phase structure, this is the workflow.
---

# Phased Shipping

You're about to run a multi-hour engineering task that doesn't fit in one PR. The goal is to land it as a clean sequence of reviewable PRs, each with green CI, while never blocking on synchronous work that could run in the background. This skill is the playbook.

The core insight is that the chat is a **coordination thread**, not an execution thread. Long-running subprocesses (CI, subagent investigations, scheduled polls) happen in the background. You keep writing the next phase while they work. When something lands red, you dispatch a surgical fixer subagent with explicit scope fences and continue.

## The seven stages

1. **Plan** — enumerate phases, sequence by dependency, confirm scope
2. **File** — create a beads issue for each logical commit *before* writing code
3. **Implement** — claim, build, test, lint, close (one bead at a time)
4. **Review** — run `/simplify` on the branch, triage findings, fix must-fixes
5. **Ship** — commit per bead, push, open PR with structured body
6. **Watch** — poll CI with `ScheduleWakeup`; dispatch fencer subagents if red
7. **Continue** — move to the next phase while prior CI finishes

Stages 6 and 7 run in parallel. That's the whole point.

**Known landmine you will hit:** if you open a PR stacked on another branch (base ≠ main), your project's CI probably won't run because workflows typically trigger only on PRs targeting main. See §5 *Stacked PRs* for the retarget-then-reopen fix — read it before opening the second PR, not after.

---

## 1. Plan

Before any code: get the shape of the work clear in the chat. Skim the plan the user handed you (PR description, roadmap, design doc, prior handoff) and produce a **phase list** — each phase is a single, mergeable PR.

For each phase, list:

- **What ships** in one sentence
- **Why** it's a separate PR (not bundled)
- **Depends on** which prior phase's branch this stacks on, if any (git base, not just conceptual dependency)
- **Beads** to file for it (one per intended commit)

**Verify each phase's premise against the actual code before you build it — not just at plan time, but as you reach the phase.** Plans (and the research behind them) are often subtly wrong: a feature the plan says to "add" may already exist (just not in the mode that matters), the named bottleneck may live somewhere the proposed fix can't reach, or the cited project may not even be the one you're working on. When exploration contradicts the plan, **re-scope the phase to the real gap and file a follow-up bead for the deferred remainder** rather than building to the stale plan or silently expanding scope. A phase that ships the genuinely-missing 20% plus a clear bead for the rest beats one that rebuilds the existing 80%. Note the re-scope in the chat and the PR body so the divergence from the plan is legible.

### Reconciling a handoff

If the user handed you a handoff note ("Phase A done, phases B and C ready"):

- **Run `git log --oneline main..HEAD` first**, plus `gh pr list --state=merged --limit 10` if checking merged upstream work. Trust commits, not notes — notes can be stale after further merges.
- **Don't retroactively file beads** for already-merged phases. Beads track *commitments*, not history. If the merged PR closed a bead, it's already closed; if no bead existed, don't invent one.
- **Do check `bd memories` and `bd list --status=open`** — look for prior-session memos that capture architectural decisions you shouldn't re-litigate, and for follow-up beads from earlier phases (bugs, tech debt, edge cases) that belong in an upcoming phase rather than being re-filed.
- **If merged upstream changes conflict with your uncommitted working tree**, rebase/resolve before starting new phases — don't build on an inconsistent base.

Tell the user the plan in 5-10 lines and confirm before proceeding. Example:

> Plan: (1) browser fetch retry + pagination extensions (one PR, 2 commits). (2) Phase B jobs subsystem (same PR, 2 commits). (3) Phase C `pippin do` as a separate PR stacked on #5. Going (1)→(2)→(3).

Confirming up front prevents you from silently accumulating scope mid-flow.

---

## 2. File beads before coding

For every logical commit you intend to make, file a beads issue *first*:

```bash
bd create --title "..." --description "..." --type=task|bug|feature --priority=2
bd update <id> --claim
```

The bead is your commitment device — if the work grows beyond what the bead describes, that's a signal to split it, not to silently expand scope.

**One bead = one commit = one coherent chunk.** If a phase has 3 commits, it has 3 beads.

Close beads as you finish, not in a batch:

```bash
bd close <id> --reason "Shipped: <one-line summary>"
```

Proactive filing: if you discover follow-up work mid-flow (e.g. "this retry pattern should extend to browser fetch too"), file a new bead immediately. You decide later whether it belongs in this phase or a future one. Persistence you don't need beats lost context.

---

## 3. Implement

Standard loop, nothing surprising:

- Write code
- Add tests (unit + integration where practical)
- `swift build` / `make build` / equivalent — must be clean
- Run the test suite — must be 0 failures
- Lint the touched files (not the whole tree; faster feedback)
- `bd close <id>`

**Do not push yet.** Keep committing locally until the phase is complete. Push once per phase (or once for multiple tight-related phases), not per commit.

A phase-level PR typically closes multiple beads (one per commit). That's expected — `Closes A, B, C` in the PR body is normal.

---

## 4. Pre-push review

Before pushing, run `/simplify` on the branch's diff against `main`. `/simplify` spawns three parallel review agents (reuse, quality, efficiency) and returns findings in categories.

**Right-size the review to the diff.** `/simplify`'s multi-agent fan-out earns its cost on diffs that span subsystems (output infra + several commands + models + MCP, say). For a *tiny, self-contained* phase — one new pure-function file plus trivial wiring and tests — the fan-out burns tokens and latency without adding signal; do a focused inline review instead and state the call ("diff is small + self-contained → inline review"). Reserve the full fan-out for genuinely multi-subsystem phases and for any change touching load-bearing code. Across a 4-phase stack you'll typically inline-review the small phases and fan out on the big ones.

**Triage the findings**:

- **Must-fix**: correctness issues (races, memory leaks, wrong state). Fix before push.
- **Should-fix**: quality wins with obvious one-liner fixes (stringly-typed flags, error swallowing). Fix if cheap.
- **Skip**: stylistic preferences, polish that'd widen the diff materially, items the reviewer flagged low-confidence.

Commit the review fixes as a single `fix(<area>): simplify pass — ...` commit so they're traceable in the PR history.

Don't argue with review findings. Either fix them or skip them explicitly. Arguing in the chat wastes context — the next reviewer might agree.

---

## 5. Ship

> **Frame of reference:** every commit is a beat, every PR is a chapter, and the sequence of PRs on a project is a story arc. A reviewer six months later skimming `git log` or the PR list should be able to follow *why things evolved this way*, not just *what changed*. Write accordingly.

### Commit messages

Subject line uses conventional-commit style: `feat(area): ...`, `fix(area): ...`, `chore(area): ...`. Reference the beads issue in the subject or body (e.g. `(pippin-tss)`).

Body explains **why** and highlights non-obvious design decisions — the beat this commit contributes to the chapter. One paragraph per distinct change. If you find yourself describing *what the diff shows*, stop; the diff is already visible. Instead say why the change was worth making, what it unblocks, what you considered and rejected.

Always co-author with Claude:

```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Pass via HEREDOC to preserve formatting.

### Pre-push gate

If the project has a pre-push hook that requires `/simplify` to have run, the flag `touch /tmp/.claude-simplify-approved` is your way through. Set it in a **separate** Bash call from the push — hooks match the command string and will block `touch ... && git push`.

### PR body — write a chapter, not a changelog

**A PR body is a chapter in the project's story, not a dump of the diff.** The diff is already on the "Files" tab. Your job is to tell a human reviewer — one who wasn't in the session — what changed, *why*, and what it means for the rest of the codebase. Imagine someone six months from now running `git blame` and landing on this PR. What do they need?

Structure the body as three moves:

1. **The setup** — a short paragraph (not a bullet list) framing the problem this PR solves and why now. If this PR is part of a larger plan, say so explicitly and link the prior PR. Reference handoff context or earlier decisions so a newcomer can find the thread.

2. **The shape of the change** — explain the architecture or approach. *Why* this design, not just *what* was built. Surface the non-obvious trade-offs: what you considered and rejected, what follow-up work this creates, what breaking changes or deprecations are now ticking. When you reference a file, use markdown links (`` [`path/to/file.ext`](path/to/file.ext) ``) so GitHub renders them clickable. Break into small subsections per subsystem if the PR spans several.

3. **Verification** — a concrete test plan. Not "I ran the tests", but what specifically would convince a skeptical reviewer:

   - Build/lint/type-check status
   - Test counts: `X passed / Y total (was Z before this branch, so +N)` — the delta matters
   - Any E2E or integration scenario walked through
   - CI gates still pending (checkbox unchecked) so it's clear what's left

End with `Closes <bead-id>[, ...]`, a link to prior PRs in the stack, and the Claude Code footer.

**Good narrative signals:**

- Use **why** language — "we needed X because Y", "the previous shape broke down when Z", "this unlocks W"
- Call out the **decision points** — "considered running this inline but forking keeps stdin clean"
- Surface **landmines future-you will hit** — "note: the pre-push hook matches command strings, so `touch && push` in one shell call won't work"
- Use a paragraph when a bullet list would lose the through-line

**Bad changelog signals (avoid):**

- Pure bulleted diff summary (`Added X. Added Y. Modified Z.`) — the diff shows that
- Narrating your own tool use (`I read file A, then edited file B`)
- Restating commit messages verbatim — readers see them already in the "Commits" tab
- Exhaustive test plans that say nothing ("all tests pass") — say which tests, how many, what increments

#### Worked example

Here's what a good PR body looks like for a real phase (rate-limiter extracted into its own module — imagine a 3-commit PR that closes 3 beads). Note the headers are tuned to the story; don't copy them verbatim for unrelated PRs.

```markdown
## Summary

Extracts the rate-limiter out of `auth/middleware.py` into a standalone
`rate_limiter/` module. This is prep work — no consumers are wired up in this PR,
so behavior on `main` is unchanged. The follow-up in #25 swaps auth over to the
new module; #26 ships the migration guide for downstream services that used to
import the limiter from its old home. Splitting extraction from consumer-swap
keeps `main` green at every step and makes the swap PR a small, reviewable diff
instead of a 600-line refactor.

## Why a standalone module — and why now

The limiter grew three different call sites since the RBAC middleware extraction
landed in #22, and each was re-implementing "tier-aware burst" logic
inconsistently. Pulling the types, the storage backend, and the CLI entrypoint
into one place gives us one definition of "what a quota is" and one place to
test it.

**Core types** ([`rate_limiter/types.py`](rate_limiter/types.py)): `Quota`,
`Window`, `Decision`. `Decision` is an enum-plus-reason rather than a bool so
downstream logging gets structured data without a second round-trip. Considered
a dataclass with `allowed: bool` and a free-form string; rejected because every
call site would end up writing the same switch statement on the reason string.

**Storage backend** ([`rate_limiter/storage/`](rate_limiter/storage/)):
protocol + in-memory implementation + Redis implementation behind the same
interface. Redis uses a Lua script for atomic check-and-increment — the naive
`INCR`/`EXPIRE` pair has a race that bit us in the old middleware (see
`test_concurrent_burst_no_double_charge`). Considered `aiolimiter`; rejected
because it doesn't expose the decision reason and we'd have had to fork it.

**CLI wiring** ([`rate_limiter/cli.py`](rate_limiter/cli.py)): `ratelimit
inspect <key>` and `ratelimit reset <key>` for ops. Gated behind
`PIPPIN_ADMIN=1` until the UX is fully stable. A deprecation shim in
`auth/middleware.py` re-exports the old names with a `DeprecationWarning` so
#25 doesn't have to be a synchronized flag-day — downstream importers get a
one-release warning.

## Trade-offs and follow-ups

- In-memory backend isn't shared across workers. Fine for dev; production must
  use Redis. Documented in the module README rather than enforced in code —
  enforcing would require reading worker-count at import time, which is the
  wrong layer.
- Deprecation shim stays until 0.6. Filed `pippin-rxx` to delete it then.
- No metrics yet — `Decision` carries the reason but nothing emits it. Deferred
  to #25 where it'll wire into the existing auth metrics pipeline rather than
  standing up a parallel one.

## Test plan

- [x] Build clean (Python 3.13)
- [x] Tests: 1073 passed / 1073 total (was 1049 on `main`, so +24 — 18 unit
  for types/storage, 6 integration covering the Redis Lua path including
  `test_concurrent_burst_no_double_charge`)
- [x] Lint clean on touched files
- [x] Manual: `ratelimit inspect test-key` + `ratelimit reset test-key`
  against local Redis
- [ ] Verify CI green on `ubuntu-latest` + `macos-14`

Closes pippin-rl1, pippin-rl2, pippin-rl3.

Standalone base: `main` (#25 will stack on this).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Notice what this body is doing: the headers tell a story (*why this shape*, *trade-offs and follow-ups*) rather than mechanically listing `## Summary` and `## Changes`. Each subsystem paragraph names the files with inline markdown links, surfaces at least one considered-and-rejected alternative, and points forward to the next PR in the stack. The test plan reports deltas and names specific tests, not just counts. For your own PR, keep this skeleton in mind but rewrite headers and paragraphs so they fit the actual story you're telling.

### If `/simplify` finds a must-fix *after* you've pushed

A second review pass sometimes surfaces something you missed. Options in order of preference:

1. **CI still running, PR not reviewed yet** — fix on the same branch, push a new commit (`fix(<area>): simplify re-pass — <...>`). Normal case.
2. **PR already approved / partial review done** — push a follow-up commit and mention the change in a PR comment so reviewers can see what moved.
3. **PR merged** — the must-fix becomes a new bead and a new PR. Don't force-push to public history.

Default to (1) unless you have a specific reason not to.

### Stacked PRs

If phase N depends on phase N-1 that's already in an open PR:

```bash
git checkout -b claude/phase-n
# ... commit phase N on this branch ...
gh pr create --base claude/phase-n-1-branch --title "..." --body "..."
```

Using `--base` means the PR's diff on GitHub shows only phase N's files, not the stacked history. Once phase N-1 merges, GitHub auto-rebases phase N's base onto `main` and CI re-runs.

**Known gotcha**: if the project's CI workflow only triggers on PRs targeting `main` (check `.github/workflows/*.yml` for `pull_request: branches: [main]`), the stacked PR will show no CI runs. Fix: retarget the base to `main` with `gh pr edit <N> --base main`, then close+reopen the PR to trigger the `pull_request` event. The diff will include the stacked commits, but they've already been reviewed in the base PR.

### Merging the stack (the `--delete-branch` footgun)

When you merge a stack bottom-up, **`gh pr merge <N> --delete-branch` will silently CLOSE — not retarget — the next PR up the stack**, if that PR's base is the branch you just deleted and GitHub hasn't retargeted it yet. Auto-retarget races branch deletion and loses. I closed a mid-stack PR this way; recovering it (recreate the deleted base ref → `gh pr reopen` → `gh pr edit --base main` → merge) is fiddly because **you can't reopen a PR whose base branch no longer exists, and you can't change the base of a closed PR** — chicken-and-egg.

Two ways to avoid it entirely:

1. **Retarget every dependent PR to `main` *before* you start merging.** `main` never gets deleted, so deleting an intermediate branch can't close anything. Walk the stack top-down with `gh pr edit <N> --base main` first, then merge bottom-up. This is the simplest and most robust — do this.
2. Or merge bottom-up but **don't** pass `--delete-branch`; delete the branches manually only after the whole stack has landed.

After each merge, verify the next PR's state before proceeding — `gh pr view <N> --json state,baseRefName`. `state: CLOSED` (not `MERGED`) on a PR you didn't merge means you hit this; recover before continuing:

```bash
# recreate the deleted base ref so the PR can reopen, then point it at main
git push origin origin/main:refs/heads/<deleted-base-branch>
gh pr reopen <N>
gh pr edit <N> --base main
# decouple any PR still based on a branch you're about to delete FIRST:
gh pr edit <N+1> --base main
gh pr merge <N> --merge --delete-branch   # safe now that N+1 is off this branch
```

Prefer `--merge` over `--rebase` when landing a stack: `--merge` preserves commit SHAs, so each higher branch's already-merged ancestors keep matching `main` (a `--rebase` lands rewrites SHAs and the next branch then re-applies "duplicate" ancestor commits).

---

## 6. Watch — and use subagents

**First, confirm where the real gate lives.** Some repos *disable* their GitHub build/test workflow and gate locally instead (e.g. pippin runs `make ci` natively / in a VM; `ci.yml` is off). There, `gh pr checks` shows only the still-active jobs (CodeQL, secret/unicode scans) — green there does **not** mean the build passed. The build/test gate is the local command you ran before pushing, so run it every push and treat it as authoritative; don't wait on or trust remote checks that aren't actually running your tests. Check `.github/workflows/` (and whether workflows are `disabled`) once at the start so you know which signal matters. When the gate is local, §6's "watch CI" reduces to "I already gated locally" — there may be nothing to poll.

After push, CI runs for ~5–10 minutes. Don't idle. **Use `ScheduleWakeup`** to poll in the background.

Pick a delay that respects the prompt cache TTL: stay under 270s if CI might finish soon, or jump straight to 1200s+ (20 min) if you know the build is slow. Avoid the 300–900s range — you pay a cache miss without amortizing it.

```
ScheduleWakeup(
  delaySeconds: 240,            // under cache TTL; CI finishing soon
  prompt: "<<autonomous-loop-dynamic>>",
  reason: "CI on PR #N due in ~3 min — verify green, dispatch fixer if red"
)
```

Or for longer waits:

```
ScheduleWakeup(
  delaySeconds: 1500,           // 25 min; pay one cache miss, then coast
  prompt: "<<autonomous-loop-dynamic>>",
  reason: "macOS Swift build is slow — check back when it should definitely be done"
)
```

When the wakeup fires, check status:

```bash
gh pr checks <N>                # summary
gh run list --branch <B> --limit 5
gh run view <run-id> --log-failed | head -200
```

### If CI is red — dispatch a fixer subagent

This is the most important technique in this skill. **Do not investigate CI failures yourself** — you have other phases to build.

The fixer pattern applies equally to:

- **CI that just went red on a PR you pushed** this session — standard case.
- **A PR already open and red when you walked in** (handoff or parallel work) — same template, different scope fence. Fence off the phase directories *you* plan to touch this session so the fixer doesn't stumble into your planned work.

Dispatch a subagent with:

1. **The exact failure URL** and what the failing job is named
2. **Branch + worktree path** so it can reproduce locally
3. **Scope fences** — list files the agent must **not** touch (usually: the in-progress phase you haven't pushed yet)
4. **A stopping condition** — "commit + push to the existing branch, do NOT open a new PR"
5. **Explicit permission or denial on `/simplify`** — if you've already run it this session and the flag is set, tell the subagent so it doesn't loop
6. **A word cap** on the report ("under 200 words") to preserve your context

Template:

```
PR #<N> on <repo> is failing CI on "<job name>". URL: <failing-run-url>

Working dir: <worktree absolute path>
Branch: <branch> (currently checked out). Main: <main-branch>.

What's on the branch: <3-5 bullets of commits>

**Your task:**
1. `gh run view <run-id> --log-failed | head -200` to see the actual failure.
2. Diagnose + fix. Commit with `fix(ci): <one-line>`.
3. `git push origin <branch>`. Do NOT open a new PR.
4. Do NOT touch: <list of untouchable files — usually the next phase's dir>.
5. `/simplify` has already run this session; the flag at `/tmp/.claude-simplify-approved` is set. Don't re-run it.
6. If you can't fix it in <time budget>, report back with what you learned.

Report under 200 words.

Run in background.
```

Launch with `run_in_background: true`. You'll get an auto-notification when it finishes. **Do not poll for it.** Keep working on the next phase.

### Bounded-effort fixers (fix-or-punt)

Sometimes the user explicitly says "if this can't be fixed quickly, just route around it." That's a different contract from "fix it." Make the escape hatch explicit in the subagent prompt:

```
Hard budget: 15 minutes on the investigation. If you can't land a confident
fix in that window, STOP and:
1. Skip the failing test(s) with @skipOnCI (or the project equivalent) +
   a `TODO(bead:<new-id>)` comment.
2. `bd create` a follow-up bead tracking re-enablement, referencing the
   test name and last-known failure URL.
3. Commit as `chore(ci): skip flaky <X> — tracked in <bead-id>`.
4. Push. Report back which path you took (fix vs. skip).
```

The skip-with-bead path keeps the project's CI green so downstream work unblocks while still leaving a clear re-enablement thread. Only use this pattern when the user has authorized it — don't silently skip tests on your own judgment.

### The fencer pattern, why it works

The reason to fence the subagent (step 3 above) is that you probably have **uncommitted work** on the same branch (the next phase you're actively writing). If the subagent commits + pushes, and you'd also accumulated changes, you can end up fighting for the same branch tip. By telling the subagent "do not touch `pippin/Planner/` or `DoCommand.swift`", you're making the fence explicit — it'll leave your working tree alone.

A well-fenced subagent will:
- Either commit its fix and push cleanly, leaving your working tree untouched
- Or `git reset` off any accidental stage of your uncommitted files

Either way, your work-in-progress survives. When you come back, your working tree still has the next phase ready to commit.

---

## 7. Continue while waiting

Having dispatched the CI fixer, **keep writing**. But first:

### Branch off before writing phase N+1

As soon as you've pushed phase N, create the branch for phase N+1 *before* you write another line of code:

```bash
git checkout -b claude/phase-n+1
```

This is non-negotiable. Your WIP for phase N+1 must not live on phase N's branch. The fixer subagent may push commits to phase N's branch while you work, and if your WIP is sitting on that branch you'll end up resolving a merge race over the same HEAD. Separate branches = no race.

Then:

- Finish the next phase's code
- Write its tests, lint, close its beads
- Commit locally on the new branch

When the fixer notifies you it's done:

- `git fetch && git status` — confirm your branch is now synced with origin
- If the fixer pushed, your local HEAD is behind; `git pull --rebase` or just observe that HEAD matches origin
- Proceed to push your next phase

### Stacked-branch handoff

A clean pattern when the fixer has pushed commits to branch A and you have work-in-progress commits for phase N+1:

```bash
git checkout -b claude/phase-n+1            # branch off current A's tip
git add <phase N+1 files>                   # (they're still in the working tree)
git commit -m "feat(...): phase N+1"
git push -u origin claude/phase-n+1
gh pr create --base <previous-branch-or-main> ...
```

The commit lands on a fresh branch, cleanly stacked on the fixer's latest commit.

---

## Appendix: the parallel-review skill

`/simplify` is a separate skill that spawns three review agents (reuse, quality, efficiency) in parallel. If you find yourself writing a manual "let me review this diff" pass, **use the skill instead** — parallel agents finish in 1-2 minutes and catch more.

## Appendix: things this skill assumes

- Project uses **beads** for task tracking (`bd` in PATH, `.beads/` in repo)
- Git hosted on GitHub with `gh` CLI authenticated
- PRs use branch-based workflow (not trunk-based)
- CI configured to run on `pull_request` events
- The user has a pre-push `/simplify` gate or is OK with running `/simplify` voluntarily

If any of those are missing, adapt — e.g., skip the beads filing step if the project doesn't use beads; skip the pre-push gate dance if there's no hook.
