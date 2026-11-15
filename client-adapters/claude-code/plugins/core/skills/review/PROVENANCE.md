# Provenance

- mattpocock/skills @ 5863806, skills/engineering/code-review/SKILL.md, MIT: two review axes (Spec: does it do what was asked; Standards: repo conventions) and a short list of concrete code smells.
- t3dotgg/tstack @ 11e37a7, sol-loop skill, MIT: bounded review rounds (3, or 5 for security and concurrency), a findings ledger, "budget end is not approval", "do not agree just to end the loop".
- poteto/plugins pstack @ 74dd229, interrogate skill, MIT: sorting findings into buckets (act on, consider, noted, dismissed with reason).
- kunchenguid/kun @ d87b129, no license: ideas only, no text copied: the reviewer gets the original intent and works apart from the author; tests are checked against intent because agent-written tests can copy the agent's misunderstanding.

Adapted for small models: no parallel subagents or cross-model reviewers (a single agent re-reads intent and diff from files instead of memory); the ledger is a fixed six-column table; smell list cut to a few concrete checks; no repo-specific vocabulary or PR tooling.
