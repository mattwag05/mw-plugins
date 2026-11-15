---
name: debug
description: Fix a bug or regression by first reproducing it with a check that can fail, then fixing the root cause. Use when something is broken, throwing, failing, wrong, or slow, or the user says debug.
---

# Debug

Do not guess a fix. Do not build a theory from reading code until a failing repro exists.

## Steps

1. **Reproduce through real behavior.** Run the actual program, test, or command with the input from the report. Find a command you can run unattended that shows the user's exact symptom. Run it and read the output. It must fail now; a repro that passes on the broken code proves nothing.
2. **If you cannot reproduce it, stop.** Write: `could not reproduce`, what you tried, and what you need (exact input, environment, logs). Make no code change. Let the human choose the next move. Do not guess-fix.
3. **Shrink it.** Remove inputs and steps one at a time, rerunning after each cut, until every remaining piece is needed for the failure.
4. **Save the repro** as a test file or script in the project, before you touch the fix. It must exit nonzero while the bug exists and exit zero once fixed. Run it once more and keep the failing output.
5. **Hypothesize.** Write 3 possible causes, each as: "if X is the cause, then changing Y makes the failure go away." Test them one at a time, one change per test.
6. **Trace if needed.** Prefer a debugger or one targeted print. Start every temporary print with the tag `[DEBUG-` plus four random characters (for example `[DEBUG-a4f2]`), so cleanup is one search.
7. **Fix the root cause.** The wrong code is often a shared helper. Search for every caller: `grep -rn "<function name>" .`. Fix the helper once; do not patch one caller. Do not fix a symptom.
8. **Rerun the same repro.** It must now pass. Paste the before and after output.
9. **Remove temporary output.** Run `grep -rn "\[DEBUG-" .` and delete every match. Also delete any print you added without a tag.
10. **Verify.** Run the project's `verify`; if none exists, run its documented test, lint, and build commands and say `verify` is missing. Then check the other callers from step 7 still behave.

## Done when

- You saw the repro fail before the fix and pass after, with the same command.
- The repro is saved in the project and fails on the original code.
- `grep -rn "\[DEBUG-" .` prints nothing and no stray prints remain.
- The fix is in the shared code, and each caller was checked.
- `verify` (or the stated substitute) was run and its output shown.
- Or: you wrote `could not reproduce`, changed no code, and listed what you need.

Do not commit, push, or deploy without the human naming that action.
