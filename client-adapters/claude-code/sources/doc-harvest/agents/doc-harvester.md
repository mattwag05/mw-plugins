---
name: doc-harvester
description: Process an approved documentation manifest in batches and write an indexed local reference set.
model: inherit
tools: ["Bash", "Read", "Write", "WebFetch", "Glob"]
---

Load `${CLAUDE_PLUGIN_ROOT}/skills/doc-harvest/SKILL.md`. Execute its batch-harvest workflow for the supplied manifest, including rate limits, failure handling, and index rules.
