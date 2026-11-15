---
name: project-housekeeping
description: Clean up redundant project artifacts, stale documentation, related homelab references, and permitted memories, and reconcile unfinished Git work. Use for cleanup, consolidation, wasted-space reviews, or uncommitted and unpushed work, not ordinary feature development.
---

# Project housekeeping

Reduce clutter without losing useful work or recovery options. Inspect the active project and related homelab material, not the whole machine by default. Both explicit and contextual invocation are supported. This skill does not schedule work or authorize production maintenance.

Before making changes, locate and read the installed `unslop` skill, which may appear as `unslop:unslop`. If it is unavailable, inspect and report only. Ask for access before editing, removing files, writing memory, committing, or pushing.

## Inventory before changing anything

- Read applicable project instructions and their canonical machine, homelab, Git, backup, and memory references. Resolve exact roots and owners. If the active directory is a broad home or workspace root with no clear project, ask for a bounded target rather than treating everything underneath it as in scope.
- Inspect each relevant repository's worktrees, branch, index, staged and unstaged diffs, untracked files, upstream, and outgoing commits. Distinguish understood, completed work from unrelated, unfinished, or concurrent changes.
- Look within those roots for duplicate reports, obsolete plans, stale documentation, old backups, generated artifacts, and large disposable files. Follow related references only when evidence connects them to the project. Do not read secret contents or scan unrelated personal files merely to classify disk usage.
- Check contents, references and callers, ownership, reproducibility, sizes, and recovery options. A filename that looks AI-generated, an old timestamp, a `.bak` suffix, or Git ignore status is not proof that a file is disposable.
- Summarize proposed low-risk changes and uncertain candidates before acting. A read-only audit request or plan mode permits recommendations only, not cleanup or commits.

## Clean up what is understood

- Correct stale documentation from current evidence. Consolidate verified duplicates into the authoritative record, preserve useful unique content, and fix incoming links, indexes, and memory identifiers. Keep required operational warnings and pointer-only instruction files intact.
- Follow each memory system's write and retention rules. Use supported update notes when generated memory cannot be edited directly. Contextual invocation does not replace explicit memory-write permission. Ask before a restricted memory write; do not delete generated stores or raw session history to save space.
- Remove proven disposable files recoverably. For tracked files, first prove the removed contents exist in reachable committed history; modified or untracked contents need a separate recoverable copy. Use the platform's Trash or a named quarantine outside the repository for those files, and report original and recovery locations.
- Ask before touching uncertain backups, unique data, ignored secrets, active worktrees, runtime state, or files whose owners or consumers are unclear. Do not prune backup stores, production volumes, service identities, or databases. Do not run blanket `git clean`, broad recursive deletion, or cache-prune commands.
- Do not create new permanent inventories or backup copies inside the project unless the task needs them. Moving files into quarantine does not reclaim disk space. Measure reclaimed space only when actual deletion is authorized and performed.
- Do not rewrite working code for aesthetics. Stop short of unrelated refactors, deployments, restarts, and persistent configuration changes. Report inaccessible hosts or records as coverage gaps.

## Reconcile unfinished Git work

- Review every pending change and outgoing commit within scope. Complete record updates and commit clearly understood, already-completed work in coherent groups. Do not silently adopt unrelated changes, finish unknown feature work, or publish old commits just because they are ahead of upstream.
- Unknown older outgoing commits block handling or publishing those commits, not an independent, validated local commit. Leave their disposition unresolved and explain that a branch push would include them.
- Preserve the user's staged selection and uncommitted contents. Stage only reviewed paths or hunks and exclude unrelated staged files from commits. If a file mixes ownership or changes arrive concurrently, ask when safe isolation is uncertain. Never reset, stash, discard, or overwrite work merely to obtain a clean status.
- Inspect canonical remote and upstream rules. Refresh relevant remote state with read-only checks or fetch where allowed. Ask about a missing upstream, divergence, conflicting intent, or unknown outgoing commits. Do not rebase, amend existing commits, merge, or rewrite history as an automatic cleanup step.
- Leave non-Git documents and approved memory notes in their existing storage. Do not initialize repositories or force-add ignored files to make every change pushable.

## Validate, commit, and publish

1. Apply unslop to changed prose, comments, permitted memory notes, and commit messages. Preserve technical meaning, exact commands, source attribution, quoted evidence, and machine-readable content.
2. Run relevant checks and verify consolidation links and recovery copies. Review the exact staged diff for unintended changes, secrets, private information, and ignored paths. Keep private homelab and memory details out of public repositories. Do not bypass hooks or call a failing batch complete.
3. Commit only reviewed, validated changes in each owning repository. Recheck status and commit contents afterward, including preserved staged work. Do not make empty commits for no-op runs.
4. Review the complete outgoing range and obtain approval for each named repository, remote, branch, and outgoing work unless that exact push is already authorized. Invoking the skill is not blanket push permission. Never force-push, change pull-request state, or deploy. Stop on rejection.
5. Verify each approved push against the destination ref. Report partial results or unavailable verification honestly. Summarize updates, removals, recovery locations, actual space reclaimed, validation, commit IDs, push status, remaining dirty or unpushed work, and unresolved candidates.
