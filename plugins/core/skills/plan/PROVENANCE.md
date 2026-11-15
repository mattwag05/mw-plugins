# Provenance

- mattpocock/skills @ 5863806, skills/engineering/to-spec/SKILL.md, MIT: the spec as a separate artifact from the tickets; problem, decisions, out-of-scope structure.
- mattpocock/skills @ 5863806, skills/engineering/to-tickets/SKILL.md, MIT: vertical slices that are each verifiable on their own, prefactoring first, explicit blocking edges, expand-then-migrate-then-remove for wide refactors.
- poteto/plugins pstack @ 74dd229, principle sequence-verifiable-units, MIT: order work as units that each end in a check.
- mw-plugins archive/plugins/phased-shipping/skills (existing, same repo): per-unit issue tracking with bd before implementation.
- mw-plugins core/LOOP.md step 1.5 sizing: no artifact for small work, a plan file for one session, spec plus issues beyond that.

- mw-plugins archive/plugins/phased-shipping/skills/phased-shipping/SKILL.md (second pass, 2026-11-15): check each phase's premise against the code at plan time and when the phase starts, plan only the real gap; one PR per slice with its stack base noted. PR mechanics went to `../ship-ready/references/stacked-prs.md`.
- Hermes `plan` skill (Theo profile, software-development/plan v2.0.0, MIT, adapted by Hermes from obra/superpowers): each step names the exact file and the command that checks it. Its `.hermes/plans/` path, full-code-in-plan, and subagent execution handoff were dropped.

Adapted for small models: dropped the term "tracer bullet" in favor of "slice" with a plain definition; fixed exact headings and file names so a script can check them; added a one-session versus multi-session branch with exact commands for `bd`; removed the interactive quiz (approval is one question at the end); removed tracker and label setup.

Eval `stale-premise` checks the premise rule: the request asks for a flag that already exists, and the plan must record it with `exists:` and plan only the missing flag.
