# GitHub stacked PRs (`gh-stack`)

Everything GitHub-stacked-PR-specific lives in this file. Nothing else in the skill depends on
it. To remove the feature: delete this file and the two pointers to it in `SKILL.md` (§1
detection table, §5 *Stacked PRs — GitHub*). The manual `--base` flow in `SKILL.md` §5 keeps
working untouched.

## Read this first: it's a preview feature

Stacked pull requests entered public preview 2026-07-30
([changelog](https://github.blog/changelog/2026-07-30-stacked-pull-requests-are-now-in-public-preview/)).
Mechanics can still move.

**If any command below doesn't match `gh stack --help`, trust the CLI, not this file** — use
what the CLI reports, and if the shape has changed enough that you're guessing, fall back to
the manual `--base` flow in `SKILL.md` §5. That fallback is always correct; it's what the skill
did before stacks existed. Never block a phase on getting the stack tooling right.

## Availability probe

Run once, at the point you'd cut the first phase branch:

```bash
gh extension list | grep -q 'github/gh-stack' && echo "stacked path" || echo "manual path"
```

If it's missing, say so and hand the user the install line — then **continue on the manual
flow**. Don't auto-install; installing an extension is a change to their tooling, not yours to
make mid-task.

```
gh-stack isn't installed. To use GitHub's native stacked PRs:
    gh extension install github/gh-stack
Proceeding with the manual --base flow for now.
```

Stacks can also be created from github.com, the GitHub mobile app, and Copilot's `gh-stack`
skill. The CLI is what this skill drives, but a user who set the stack up in the web UI is on
the same path — `gh stack` will see it.

## Phase → layer mapping

One phase = one layer. The bottom layer targets `main`; each layer above targets the one below.

This tightens §1's latitude to bundle two tight phases into a single PR. Do that on the manual
path if you like — bundling exists there because each extra PR costs review overhead. In a
stack it doesn't: each layer gets its own stack map showing where it sits, reviewers take them
independently, and you can land several at once. So **on the stacked path, don't bundle.** If
the plan says four phases, ship four layers.

Branch naming is unchanged — `claude/phase-1`, `claude/phase-2`, … The §7 rule still holds:
cut the next phase's branch *before* writing a line of it, so a fixer subagent pushing to the
layer below can't race your WIP.

## What this replaces from `SKILL.md` §5

Two workarounds in the manual flow are dead weight **on this path only** — they stay correct
and necessary for every other host:

- **The "CI doesn't fire on a non-`main` base" retarget + close/reopen dance.** Not needed.
  Branch protections, required status checks, and the merge queue apply per-layer natively, so
  each layer's checks run on its own.
- **The pre-merge "retarget every dependent PR to `main` first" mitigation for the
  `--delete-branch` footgun.** Not needed. Landing a lower layer auto-rebases and retargets the
  layers above it onto the new base.

Do not carry those workarounds into the stacked path — applying the retarget dance to a real
stack flattens it back into a pile of unrelated PRs and you lose the thing you came for.

## Landing the stack

Merging is bottom-up, and merging is *inclusive downward*: landing the topmost layer marked
ready lands it **and every unmerged layer below it** in one operation. You can also land just
the bottom layer, or the bottom two — whatever's actually ready. Everything above rebases and
retargets itself.

Practical consequence: you don't have to babysit merge order. Get the lower layers reviewed,
land as far up the stack as review has reached, and the remainder stays a valid stack.

## Worked example — a 3-phase stack

```bash
# probe once
gh extension list | grep -q 'github/gh-stack' || echo "not installed — manual flow"

# phase 1: bottom layer, targets main
git checkout -b claude/phase-1 main
# ... commit phase 1 ...
git push -u origin claude/phase-1
gh stack create --title "feat(core): extract rate limiter"   # bottom of a new stack

# phase 2: cut the branch BEFORE writing it (§7)
git checkout -b claude/phase-2
# ... commit phase 2 ...
git push -u origin claude/phase-2
gh stack add --title "feat(auth): swap auth onto the new limiter"

# phase 3
git checkout -b claude/phase-3
# ... commit phase 3 ...
git push -u origin claude/phase-3
gh stack add --title "docs(migration): downstream import guide"

# see where things stand
gh stack list

# land: phases 1+2 are reviewed, 3 isn't — merging layer 2 lands 1 and 2 together,
# and phase 3 retargets onto main by itself
gh stack merge claude/phase-2
```

Verify the flag and subcommand names against `gh stack --help` before running these; see the
preview caveat above.

## PR bodies and the stack map

Each layer gets an auto-generated stack map at the top of its PR showing its position. That
map replaces the manual "Standalone base: `main` (#25 will stack on this)" footer and the
hand-written "the follow-up in #25 swaps auth over" cross-links from `SKILL.md` §5's worked
example — the map is generated, always accurate, and doesn't go stale when the stack reorders.

Everything else in §5's PR-body guidance stands unchanged: the setup paragraph, the shape of
the change, considered-and-rejected alternatives, the test plan with deltas. A stack map tells
a reviewer *where* the PR sits. It does not tell them *why* it exists. Still your job.

## CI watching and fixer subagents

Unchanged. Checks run per-layer as normal, so `SKILL.md` §6 applies verbatim: poll with
`ScheduleWakeup`, and when a layer goes red, dispatch a fenced fixer subagent that commits and
pushes to **that layer's branch** and opens no new PR. A push to a layer branch updates that
layer in place; it does not disturb the layers above it.

One addition to the fixer's scope fence on this path: tell it not to run `gh stack` commands.
Its job is the failing layer, not the stack's shape.
