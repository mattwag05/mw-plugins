# Provenance

- mattpocock/skills @ 5863806, skills/productivity/grilling/SKILL.md, MIT: the round structure (ask every question whose prerequisites are settled), numbered questions with recommended answers worded so "yes" accepts, facts are the agent's job and decisions the human's, stop and wait, do not act until shared understanding is confirmed.
- mattpocock/skills @ 5863806, skills/engineering/grill-with-docs, MIT: look up facts in the project's own docs before asking.

- mw-plugins archive/plugins/ambition/skills/ambition/SKILL.md v0.1.0 (a paraphrase of Felix Rieseberg, "How to be more ambitious: A tutorial for humans with models", 13 October 2026): the outcome question, the altitude, depth, and range axes, the outside-judge rule, and "ambition changes scope, never authorization". Condensed into `references/ambitious-version.md` and the "Aim higher" section; the notes for the human were dropped.

Adapted for small models: removed "design tree", "frontier" and the sub-agent dispatch (no subagents here; facts are looked up directly); added the explicit question format, a decisions file at the end, an `assumed` rule, and a no-edits-before-confirmation check.

The "Aim higher" section uses a fixed reply shape (`Outcome:` through `Check:` lines, then one question) so eval `aim-higher` can check it with string matches and a workspace diff.
