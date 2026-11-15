---
name: session-closeout
description: Update project documentation, related homelab references, and permitted memories from verified session learnings, then validate and commit completed work and prepare approved pushes. Use when closing out a session or after a completed batch of codebase changes before handoff.
---

# Session closeout

Leave completed work and its records consistent. Follow the session's changes, not every repository or service you can reach. This skill supports explicit and contextual invocation. It is not a post-edit hook and does not authorize background runs.

Before making changes, locate and read the installed `unslop` skill, which may appear as `unslop:unslop`. If it is unavailable, inspect and report only. Ask for access before editing, removing files, writing memory, committing, or pushing.

## Establish scope

- Read applicable project instructions and follow their pointers to canonical machine, homelab, Git, and memory guidance. Discover locations from the environment rather than assuming a particular layout or forge.
- Review the session's decisions, actual diffs, test results, and unresolved issues. Distinguish executed verification from plans, hypotheses, and another agent's claims.
- Identify each affected repository and documentation or memory owner. Inspect its branch, worktree, index, untracked files, and upstream state before editing. Record which changes belong to this session and preserve older or concurrent work.
- Follow related homelab references where the changes affect them. If a relevant host or record is unavailable, report the gap. Do not expand into a whole-system audit, deployment, service restart, or configuration change.
- An explicit read-only request or plan mode takes precedence. In that case, propose the updates without writing, committing, or pushing.

## Update the records

- Check current code or live read-only evidence before correcting drift-prone facts. Record verified behavior, durable lessons, changed commands, and remaining limitations in the existing authoritative records.
- Keep operative rules concise. Put incident details in references and repair their indexes or links. Preserve pointer-only instruction files instead of copying canonical documents into them.
- Update only records that need a change. Avoid fresh summary files when an existing runbook, reference, or issue already owns the information. Do not manufacture a lesson or create an empty commit on a no-op run.
- Follow each memory system's own write policy. Where generated memory is read-only, use its supported update-note mechanism. Contextual selection alone does not grant explicit memory-write permission. If permission is missing, propose the update and ask before writing it. Never store credentials, patient data, or private session transcripts.
- Keep private operational details out of public repositories. A useful private memory does not automatically belong in the project's documentation or Git history.

## Validate and commit

1. Apply unslop to changed prose, comments, memory notes, and commit messages. Preserve meaning, source attribution, exact commands, and machine-readable content. Do not rewrite functional code or quoted evidence for style.
2. Run relevant project checks and review changed documentation links. Report failures and verification limits. Do not commit or publish a failing batch as complete, bypass hooks, or start unrelated repairs just to get a clean result.
3. Re-read worktree and index changes before staging. Stage only reviewed paths or hunks owned by this closeout. Check new paths for ignore rules and scan the proposed commit for secrets, private information, and unintended files. Do not use blanket staging or force-add ignored material.
4. Create coherent commits in each owning repository. Preserve unrelated staged changes in the index and exclude them from the commit. If changes share a file or concurrent edits prevent safe isolation, ask rather than capturing or discarding someone else's work. Do not initialize a repository solely to publish local memory or documents.

## Push and hand off

- Refresh relevant remote state with read-only inspection or fetch when allowed. Verify the canonical push remote, branch, mirror rules, and complete outgoing commit range, including commits from before this session. Do not assume `origin`, `main`, or GitHub is the right destination.
- Unknown older outgoing commits block handling or publishing those commits, not an independent, validated local commit. Leave their disposition unresolved and explain that a branch push would include them.
- Request approval for the named repository, remote, branch, and outgoing work unless the user has already authorized that exact push. Skill selection, a local commit, or approval for another repository is not push permission. If there is no upstream or the branch has diverged, explain the choice and ask before reconciliation or publishing.
- Never force-push, change pull-request state, or deploy as part of closeout. Stop and report a rejected push rather than broadening permissions or rewriting history to retry.
- After an approved push, compare the destination ref with the intended commit. If verification is unavailable, say the push is unverified. Report results separately for each repository, including partial success.
- Finish with updated locations, validation results, commit IDs, confirmed push status, uncommitted or unpushed work left behind, and approvals or evidence still needed. Mention local-only memory updates separately from published records.
