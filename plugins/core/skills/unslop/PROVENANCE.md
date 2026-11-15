- poteto/plugins pstack @ 74dd229, skills/unslop/SKILL.md, MIT: the pattern catalogue and the add-voice guidance (condensed into patterns.md).
- poteto/plugins pstack @ 74dd229, skills/poteto-mode/SKILL.md ("Writing the reply"), MIT: the write-it-clean-the-first-time rule, the em dash ban, the colon rule.
- mw-plugins archive/plugins/unslop/skills/unslop/SKILL.md v0.4.0: frame-first rule, plain-speech rules, patient-facing paragraph rule, action-first rule.
- mw-plugins archive/plugins/i-have-adhd/skills/i-have-adhd/SKILL.md v0.3.0, MIT: the reply-shape rules (next action first, numbered steps capped at five, restated state, visible finished work, cause-and-fix errors, no sidebars, one closing action, concrete estimates, the first-and-last-line test), folded into the "Replies" section. Its session-long mode toggle was dropped: the rules now apply to every reply.
- mw-plugins archive/plugins/unslop (second pass, 2026-11-15): name-dropping, false ranges, cutoff disclaimers, en-dash substitutes, extra vocabulary, idioms, announcing openers, empty hedges, and voice notes, appended to patterns.md.
Adapted for small models: cut from 1,233 words to under 600 by moving the pattern list to patterns.md; added slop_scan.py so detection of em dashes, stock phrases, and long sentences is a command, not a judgment; added an explicit loop of run, fix, rerun until clean; added a rule to leave code and quotes untouched.

Eval `reply-shape` checks the Replies rules: first line is the next action, steps numbered in order, commands kept, chat filler gone.
