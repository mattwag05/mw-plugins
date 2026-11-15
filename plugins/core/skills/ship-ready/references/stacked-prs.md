# Stacked PRs

Read this when work ships as several PRs that build on each other. It keeps the mechanics from the retired `phased-shipping` skill. Every push, PR, retarget, and merge below needs the human's own words naming it.

## Shape

- One slice is one branch and one PR. Phase N's branch starts from phase N-1's branch.
- Create the branch for the next slice before you write its first line: `git switch -c <next-branch>`. Work for slice N+1 never sits on slice N's branch.
- Commit locally as you go. Push once per slice, after approval.

## Find the review host

Run `git remote get-url --push origin`. That host is where PRs are reviewed. A second remote that mirrors it is a publishing target, not a review host. A leftover `.github/` or `.forgejo/` directory is not a host signal. If it is unclear, ask.

## Open a stacked PR

Open it with its base set to the previous slice's branch (`--base <previous-branch>`), so the diff shows only this slice.

Gotcha: many workflows run only on PRs that target `main` (look for `pull_request: branches: [main]`). A stacked PR then shows no CI. Retarget it to `main` and close and reopen it to trigger CI; the diff then also shows the lower slices' commits.

## Merge a stack

Merging bottom-up with branch deletion can close the next PR instead of retargeting it. Avoid that:

1. Retarget every dependent PR to `main` first, top-down.
2. Merge bottom-up. Prefer a merge commit over rebase-merge: it keeps commit hashes, so higher branches do not replay their lower slices' commits.
3. After each merge, check the next PR's state and base. `CLOSED` on a PR you did not merge means it hit this problem: recreate the deleted base branch, reopen the PR, retarget it to `main`.

Never force-push a branch whose PR has been reviewed or merged. A fix found after merge is a new slice.
