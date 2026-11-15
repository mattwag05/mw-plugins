---
name: unslop
description: Make prose read like a careful human wrote it by removing AI tells. Use when writing or editing any prose a person will read: replies, docs, commit messages, emails, READMEs.
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

## Done when

- `python3 scripts/slop_scan.py <file>` exits 0 with no output.
- The file contains zero em dash characters.
- Every number, name, command, and code block from the original is still present and unchanged.
- No sentence opens with a stock phrase from `patterns.md`.
- You did not add facts the original lacked.

## Notes

- A patient-facing or customer-facing text pasted into a chat or email: write plain paragraphs with no headings or bullets. Keep every figure verbatim.
- On a list, card, or summary, lead with the action, then the reason.
- Do not claim the text is clean without a scanner run that exited 0.
