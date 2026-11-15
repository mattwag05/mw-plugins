# Provenance

- t3dotgg/tstack @ 11e37a7, skills/full-stop/SKILL.md and skills/full-send/SKILL.md, MIT: the merge gate (proof covers the diff, required checks green, review findings fixed or dismissed with a reason, no unresolved change requests, branch up to date and mergeable) and the rule that the agent stops at ready-to-merge.
- t3dotgg/tstack @ 11e37a7, skills/file-pr/SKILL.md, MIT: short PR body that opens with the problem, then the solution, not an inventory of edits.
- t3dotgg/tstack @ 11e37a7, skills/babysit-pr/SKILL.md, MIT: idea that a script watches CI and the model never writes its own sleep loop (the script itself is not copied; forge polling is out of scope).
- mattpocock/skills @ 5863806, skills/engineering/pr/SKILL.md, MIT: PR body sections for evidence and a one-way or two-way door note.

Adapted for small models: dropped GitHub, bot names, cross-model review and autonomous merge; the agent never pushes or merges. Mechanical checks moved into `scripts/ready_check.sh`; the verdict has a fixed first-line format; steps are numbered with an observable Done-when list.
