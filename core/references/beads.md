# Beads across clones and worktrees

Read this before any `bd sync`, `bd bootstrap`, `bd init`, or first publication of a project's issues. Everyday use (`bd ready`, `--claim`, `close`, `create`) does not need it.

Before operating, check two things: the installed version's `--help`, and the project's current rollout record. Stable Beads 1.3.1 embeds Dolt 2.2.0, and a standalone Dolt on PATH handles Git-protocol transport. Qualifying a newer transport CLI does not qualify a SQL server, and it does not authorize a live migration.

## Where the data lives

- Issue data lives in `refs/dolt/data` on the project's canonical Git origin, separate from code commits.
- Keep one canonical Dolt `main` branch for a project's issues. Switching code branches does not switch the issue branch.
- Worktrees share the main checkout's embedded database, found through Git common-directory discovery.
- Independent clones and machines are independent replicas.
- Check `bd where`. Never initialize another tracker in a worktree.

## Settings for Git-backed collaboration

- Keep `dolt.auto-push`, `export.auto`, and `export.git-add` false.
- Private native backups stay separate from collaboration. They keep recovery history and working state.
- A JSONL export holds only the current exported records. It cannot recover missing native history.
- The global Git secret hook does not scan database values inside the Dolt data ref.

## New clone of an adopted tracker

1. Run `git ls-remote origin refs/dolt/data`. If the ref is absent, stop.
2. Run `bd bootstrap --non-interactive`.
3. Verify `bd where`, the project identity, the native remote URL, and the recorded expected issue IDs and count. Without this check, bootstrap can quietly create an empty tracker, so a successful exit alone proves nothing.
4. Keep existing Git hooks. `bd init` and some configuration setters create Git commits, so review the index before using them.

## Before first publication

1. Verify:
   - project identity and the canonical source;
   - exact issue IDs and count;
   - current restore evidence;
   - origin visibility;
   - how downstream mirrors handle refs.
2. Review the complete issue history, including deleted text and non-issue tables.
3. Do not publish private operational, medical, personal, or credential data to a wider audience. A public code origin does not make existing private issues public.
4. Missing origins, export-only sources, archived projects, and conflicting identities each need a project-specific decision.

## Publishing protocol

Until a project has an agreed protocol that coordinates every machine and agent, keep its remote rollout on hold. The manual procedure works like this:

1. One publisher holds the turn for one project at a time, and every other publisher acknowledges it.
2. Hold the turn through pull, edits or merge review, sync, remote verification, and handoff.
3. Run `bd sync` before selecting and claiming work, and again after updates.
4. Release the turn only after a sync you have verified.
5. If sync fails, keep the turn, preserve local state, and resolve the failure before anyone else publishes.

A local `flock` does not enforce this across machines. Do not claim an offline clone is current.

## Conflicts

- Two independent claims are not a distributed atomic claim.
- Concurrent changes to scalar fields may settle by timestamp, with a warning. These can halt sync:
  - equal timestamps;
  - contested notes or metadata;
  - a delete on one side and a modify on the other.
- When sync halts, inspect both versions before choosing a resolution.
- An unqualified `bd vc merge origin/main` rolled back its conflict in the stable embedded pilot, leaving `bd conflicts resolve` no live row to act on.
- `--strategy ours` and `--strategy theirs` do work, but each picks a side for every conflict and can discard an intended edit:
  - Never use either as an automatic retry.
  - Back up and review the affected rows first.
