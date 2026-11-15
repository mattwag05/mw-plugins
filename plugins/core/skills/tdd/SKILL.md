---
name: tdd
description: Build new behavior test-first, or refactor safely, one behavior at a time: write a failing test, see it fail, then make it pass. Use when adding a feature, fixing via tests, refactoring, or the user says tdd or red-green.
---

# TDD (test first)

A test is only worth having if you saw it fail first.

## Rules for expected values

Expected values in a test must come from outside your own reasoning: the spec, a worked example in the task, real data, or the bug reproduction. Never compute the expected value with the code under test, and never copy it from your own implementation. If the task gives no example, ask the human for one or say the expected value is unconfirmed.

## New behavior

1. Name the public entry point you will test (a function, command, or endpoint) and what the user can observe through it. Test only there, not at private helpers. If unsure which entry point, ask.
2. List the behaviors in the spec, one line each. Take them one at a time.
3. **Red.** Write one test for the first behavior, with the expected value copied from the spec or example. Run only that test file: `python3 -m unittest <module>` (or the project's single-file test command). Read the failure. It must fail because the behavior is missing (wrong or absent output), not because of a typo, bad import, or syntax error. Fix the test until the failure is for the right reason.
4. **Green.** Write the least code that passes. Do not add behavior no test asks for. Run the same test file; it must pass.
5. Repeat steps 3 and 4 for each behavior. Do not write all tests first.
6. Run the full suite once at the end, through the project's `verify`; if none exists, run its documented test, lint, and build commands and say `verify` is missing.

## Refactoring existing code

1. Do not edit the code yet. Write guardrail tests (tests that pin down what the code does today) for the behavior you will touch. Take inputs from existing callers and real data, and record the current output from running the original code once, as literals in the test.
2. Run them on the unchanged code. They must pass. A guardrail that fails on the original is wrong; fix the test, not the code.
3. Refactor in small steps. Rerun the guardrail tests after each step.
4. Finish with `verify` as in step 6 above.

## Done when

- Each new test failed first, for the right reason, and you saw the output.
- Each test now passes, and the expected values trace to the spec, an example, real data, or recorded original output.
- For a refactor: guardrail tests existed and passed on the original code, and still pass after.
- `verify` (or the stated substitute) was run and its output shown.
- No test file asserts a value that the implementation computed.

Do not commit, push, or deploy without the human naming that action.
