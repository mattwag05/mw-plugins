# xcode-mcp

Teach Claude Code to effectively use the Xcode MCP bridge (`xcrun mcpbridge`) for building, testing, diagnosing errors, and managing Xcode projects — all via natural-language requests.

## Overview

The Xcode MCP bridge is a single natural-language tool: describe what you want Xcode to do, and Xcode does it. This plugin gives Claude the knowledge to use it effectively — knowing when to reach for the MCP vs. direct file editing, how to phrase requests, and how to run autonomous build-fix loops.

## Skills

| Skill | Triggers On |
|-------|------------|
| `xcode-mcp-core` | Xcode project directories, general Xcode MCP questions |
| `xcode-build-and-fix` | Build requests, compile errors, "fix build errors" |
| `xcode-project-management` | Add files/targets/entitlements, SPM dependencies |
| `xcode-testing` | Run tests, test coverage, XCTest, test plans |
| `xcode-docs-and-search` | DocC generation, Apple documentation search |

## Agents

| Agent | Purpose |
|-------|---------|
| `xcode-build-fix` | Autonomous build → diagnose → fix → rebuild loop |

## Prerequisites

1. **Xcode must be open** with your project loaded
2. **Enable external agent access:** Xcode → Settings → Intelligence → Model Context Protocol → "Allow external agents to use Xcode tools": ON
3. **MCP configured** (already done if you're reading this):
   ```
   claude mcp add --transport stdio xcode -- xcrun mcpbridge
   ```
4. **Claude Agent config (optional):** Customize the in-Xcode Claude Agent at `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig`

## Works Best With

- **swift-concurrency plugin** — handles Swift 6 concurrency errors that `xcode-build-fix` agent surfaces
