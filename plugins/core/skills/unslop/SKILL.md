---
name: unslop
description: "Make prose read like a careful human wrote it by removing AI tells, and shape replies so the reader can act. Use when writing or editing any prose a person will read: replies, docs, commit messages, emails, READMEs. Covers the retired unslop and i-have-adhd skills."
---

# Unslop

Prose here means sentences meant for a person. Code, commands, file paths, numbers, and quoted evidence are not prose: never change them.

## Steps

1. Write clean the first time. Cleanup afterward fails, so do not draft the bad sentence. While drafting:
   - Use short declarative sentences, one idea each.
   - Say the concrete thing: a name, a number, a command. If a sentence cannot be restated as a fact or an instruction, cut it.
   - Put the frame first and the specific thing last. "The hardest part was Mail." beats "Mail was the hard part."
   - Use plain words ("use", not "leverage" or "utilize") and active voice with a named actor.
   - Never use the em dash character (U+2014). Use a period, comma, colon before a list, or parentheses.
   - Skip openers and closers such as "Great question", "I hope this helps", or a summary that repeats the body.
2. If you are editing an existing file, read `patterns.md` in this skill's directory. It lists the tells to find and the fix for each.
3. Rewrite the prose. Keep every fact, number, name, and clinical or legal claim exactly. Keep fenced code blocks, inline code, and quoted text byte-identical. Match the original tone. Vary sentence length. Have a point of view where the text allows one.
4. Run the scanner on the file: `python3 scripts/slop_scan.py <file>` (path relative to this skill's directory). It prints `file:line: kind: text` for each em dash, stock phrase, and sentence over 40 words, and skips code.
5. Fix every line it prints, then rerun. Repeat until it prints nothing and exits 0.
6. Reread once and ask: what still sounds machine-made? Fix it, then rerun the scanner one last time.

## Replies

A reply is text a person reads to decide what to do next (a chat answer, a status update, a reply draft in a file). Shape it this way:

- The first line is the answer or the next action, such as a command or a file to open. Context comes after.
- Number multi-step work: one action per step, five items at most. Split a longer list into "now" and "later".
- Say where things stand: "Step 3 of 5 done: schema updated."
- Show what now works and how to try it, not a list of edits.
- State an error as cause and fix, without "Uh oh" or "There seems to be".
- Finish the first issue. Offer a second one as a separate question at the end, not as a "by the way" sidebar.
- If anything is still open, end with one next action the reader can do now.
- Give time estimates in concrete units ("about 15 minutes").

Test: a reader who sees only the first and last lines knows what happened and what to do next.

## Done when

- `python3 scripts/slop_scan.py <file>` exits 0 with no output.
- The file contains zero em dash characters.
- Every number, name, command, and code block from the original is still present and unchanged.
- No sentence opens with a stock phrase from `patterns.md`.
- For a reply, the first line is the answer or the next action.
- You did not add facts the original lacked.

## Notes

- A patient-facing or customer-facing text pasted into a chat or email: write plain paragraphs with no headings or bullets. Keep every figure verbatim.
- On a list, card, or summary, lead with the action, then the reason.
- Do not claim the text is clean without a scanner run that exited 0.
