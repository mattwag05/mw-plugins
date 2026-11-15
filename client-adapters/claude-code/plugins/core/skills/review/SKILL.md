---
name: review
description: Review a change from a fresh start against its original intent and write a findings ledger in REVIEW.md. Use when a consequential change is done, before asking to push or merge, or when the user says review.
---

# Review

You review; you do not fix. The author fixes. Read the diff as if you had never seen it.

## Inputs

You need two things: the original intent (the task, spec, or issue as first written, not the author's summary of it) and the diff. Save the intent to `INTENT.md` if it is not a file. Get the diff with `git diff <base>` (or use the diff file you were given). If the intent is missing, stop and ask for it.

## Steps

1. **Start fresh.** If you wrote the change in this session, do not rely on memory: re-read `INTENT.md` and the full diff from the files, and treat your earlier reasoning as untrusted. If you can start a reviewer with no history, give it only the intent and the diff paths.
2. **Spec axis: does it do what was asked?** For each sentence in the intent, find the code that does it and the case at the edges (equal to a limit, empty, zero, negative). Look for missing parts and extra scope.
3. **Tests against intent.** Read each new test. Is its expected value what the intent says, or only what the code happens to return? Passing tests can still be wrong; agent-written tests can copy the author's misunderstanding. Flag any test whose expected value contradicts the intent.
4. **Standards axis: repo conventions.** Read the project's instruction file and nearby code. Flag differences in naming, layout, and error handling. Also check for: duplicated code, a function doing two jobs, an unused parameter, a swallowed error, a hard-coded secret or path.
5. **Write `REVIEW.md`**: a Markdown table with exactly these columns, one row per finding:

   `| id | file:line | axis | bucket | finding | status |`

   - id: R1, R2, ...
   - axis: `spec`, `tests`, or `standards`
   - bucket: `act on` (a bug or intent violation the author must fix), `consider` (worth doing, author decides), `noted` (true but ignorable, such as a style nit), or `dismissed` (a suspicion you checked and ruled out; give the reason in the finding)
   - status: `open` for new rows

   Put each finding under one bucket. A style nit is `noted`, never `act on`. Cite evidence: a line, a failing input, or a command output. No vague findings.
6. **Rounds.** The author fixes every `act on` row and marks it `fixed`. A new round re-reviews only those rows: re-read the changed lines, run the relevant check, then mark each `closed` or `reopened` with a reason. Add new rows only for problems the fixes introduced. Stop after 3 rounds (5 for security or concurrency changes). Do not approve to end the loop. If rows are still open at the limit, say so and hand the decision to the human.

## Done when

- `REVIEW.md` exists with the six columns and one row per finding.
- Every `act on` row names a real `file:line` and says why it breaks the intent.
- Tests were checked against the intent, not only run.
- Each round's result is recorded in the status column; open `act on` rows after the last round are reported to the human as unresolved.

Do not push, merge, or approve a PR without the human naming that action.
