---
name: grill
description: "Settle unclear intent before doing any work, by asking the human numbered questions with recommended answers. Use when the goal or done-check is unclear, the request is ambiguous, or the user says \"grill me\", \"stress-test this plan\", or \"aim higher\" (covers the retired ambition skill)."
---

# Grill

Goal: reach a shared understanding with the human, then record it. Do not start the work.

A **decision** is a choice only the human can make (scope, priority, taste). A **fact** is something the workspace or tools can tell you (file contents, versions, what exists). Facts are your job.

## Steps

1. Read the request. Look in the workspace (README, docs, existing files) for every fact you need. Use `ls`, `cat`, `grep`. Never ask the human a question a file can answer; cite the file instead ("README says X"). Before you offer an option that deletes or replaces something, look at that thing with a tool (`ls`, `cat`) and describe what it holds.
2. List the decisions still open. Keep only those whose earlier decisions are already settled. A question that depends on another open question waits for a later round.
3. Ask one **round**: every question from step 2, numbered, in this format:

   ```
   Q1. <short title>: <the question>
   Recommended: <your answer, worded so that "yes" accepts it>
   ```

   If a structured question tool exists, use it. Otherwise ask in plain text.
4. Stop. Write nothing else and change no files. Wait for the answers.
5. Take the answers. Recompute: which decisions are now settled, which new questions opened. Ask the next round the same way. Repeat until no open decisions remain.
6. Summarize the settled decisions in a short list and ask: "Is this our shared understanding?" Wait for a yes.
7. After the yes, write the decisions to the file the human named, or `decisions.md` if none was named. One line per decision, plus the goal and done-check in the first two lines.
8. Do the work only if the human then asks for it. Otherwise stop after the file is written.

## Rules

- Never act on the plan (no code, no edits other than the decisions file) before the human confirms.
- Do not pad. Five sharp questions beat fifteen vague ones.
- If an answer is "you decide", take your recommendation and mark it `assumed` in the decisions file.

## Aim higher (only when asked)

Use this when the human asks for the ambitious version of a task ("aim higher", "be more ambitious", "how would an expert do this").

1. If you cannot tell what the task is for, ask that one question and stop.
2. Read `references/ambitious-version.md` in this skill's directory.
3. Reply in exactly this shape, one line each:

   ```
   Outcome: <what should be true after this is done>
   Altitude: <upgrade, or "skipped: <reason>">
   Depth: <upgrade, or "skipped: <reason>">
   Range: <upgrade, or "skipped: <reason>">
   Needs: <tools, data, access; mark what you already have>
   Check: <a check that depends on neither you nor the human>
   Which version should I run?
   ```
4. Stop and change no files. A bigger goal never widens approval: the new scope, and any access, deploy, message, or spending it needs, waits for the human's yes.

## Done when

- The transcript shows at least one round of numbered questions, each with a `Recommended:` line.
- No question asks the human for something the workspace already states.
- No source or project file was changed before the human confirmed.
- After confirmation, the decisions file exists with the goal and done-check on top.
- For an aim-higher request: the reply has the `Outcome:` and `Check:` lines, ends with the question, and no file changed.
