# Housekeeping, records, and memory

Read this when closeout includes cleanup, consolidation, memory updates, or unfinished Git work. It keeps the rules of the retired `session-closeout` and `project-housekeeping` skills. Nothing here allows a push, deploy, restart, or config change.

## Scope

1. Work on one bounded target: the project or repository at hand. If you were started at a home or workspace root with no clear project, ask which one.
2. Inventory before changing anything. For each repository: `git worktree list`, `git status --short`, `git diff --cached --stat`, `git log --oneline @{u}..HEAD`. Note which changes are this session's and which are someone else's.
3. A read-only audit or plan mode allows recommendations only. List proposed changes and uncertain items, and stop.

## Records and memory

- Correct a stale fact only from current evidence (code, a command, a live read-only check).
- Put the fact in the record that already owns it. Merge verified duplicates into that record, keep any unique content, and fix incoming links and indexes. Keep pointer-only instruction files as pointers.
- Keep operative rules short. Put incident detail in a reference file and link it.
- Follow each memory system's own write rules. If you lack permission to write memory, propose the note and ask. Never store credentials, patient data, or session transcripts. A private memory does not belong in a public repo.
- Do not invent a lesson on a run where nothing was learned.

## Cleanup

- Age, a `.bak` suffix, an AI-looking name, or being git-ignored does not prove a file is disposable. Check its contents, who reads it, and whether it can be rebuilt.
- Remove a proven-disposable file recoverably: `/usr/bin/trash` or a named quarantine folder outside the repo. For a tracked file, first confirm its contents exist in a reachable commit. Report the original path and the recovery path.
- Ask before touching backups, unique data, ignored secrets, active worktrees, runtime state, or files with unclear owners. Never prune backup stores, volumes, service identities, or databases. Never run `git clean`, a broad recursive delete, or a cache prune.
- Report reclaimed space only after a real deletion, measured with `du`. Moving files to quarantine reclaims nothing.
- Do not rewrite working code for looks.

## Unfinished Git work

- Commit only work you understand and that is finished, in coherent groups. Do not adopt or finish someone else's changes.
- Keep the human's staged selection. If one file mixes your change with another's, ask.
- Never reset, stash, discard, rebase, amend, or rewrite history just to get a clean status.
- Outgoing commits older than this session are the human's call: list them (`git log --oneline @{u}..HEAD`) and say a push would carry them.

## Report

End with: records updated, items removed and their recovery paths, space reclaimed, checks run, commit hashes, work left uncommitted or unpushed, local-only memory notes (listed apart from published records), and items still needing a decision.
