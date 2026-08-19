---
name: swift-audit
description: Audit Swift code for concurrency correctness
argument-hint: [file-or-directory-path]
allowed-tools: Read, Glob, Grep, Bash
---

Load `${CLAUDE_PLUGIN_ROOT}/skills/swift-concurrency-review/SKILL.md` and audit `$ARGUMENTS`, or the current project when no path is supplied.
