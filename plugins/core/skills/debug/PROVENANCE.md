# Provenance

- mattpocock/skills @ 5863806, skills/engineering/diagnosing-bugs/SKILL.md, MIT: build a feedback loop that can fail before any hypothesis; minimize the repro; ranked falsifiable hypotheses; tagged `[DEBUG-xxxx]` logs removed by one grep; stop and say so when no loop can be built.
- poteto/plugins pstack @ 74dd229, pstack/.../playbooks/bug-fix, MIT: save the failing repro before the fix; fix the root cause in shared code and grep all callers.
- kunchenguid/kun @ d87b129, no license: idea only, no text copied: if the bug cannot be reproduced, say so and let the human choose, never guess-fix.
- t3dotgg/tstack @ 11e37a7, MIT: reproduce failure, fix, rerun the same repro (prove step).

Adapted for small models: one numbered list instead of six phases; the redaction, HITL script, and perf branches dropped; concrete grep commands named; hypotheses fixed at 3; an explicit stop-and-report path for unreproducible bugs; no references to glossaries or subagents.
