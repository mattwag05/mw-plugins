---
name: xcode-build-fix
description: Build an Xcode project, fix compiler errors, and repeat until the build passes or a defined blocker is reached.
model: sonnet
tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
---

Load `${CLAUDE_PLUGIN_ROOT}/skills/xcode-build-and-fix/SKILL.md` and run its iterative build-fix workflow.
