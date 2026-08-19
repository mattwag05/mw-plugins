# Xcode MCP

Use the Xcode MCP bridge (`xcrun mcpbridge`) to build, test, fix, document, and manage Xcode projects.

## Skills

| Skill | Purpose |
| --- | --- |
| `xcode-mcp-core` | Connect to Xcode and phrase MCP requests. |
| `xcode-build-and-fix` | Run a bounded build, diagnose, edit, and rebuild loop. |
| `xcode-project-management` | Add files, targets, capabilities, and package dependencies. |
| `xcode-testing` | Run and inspect Xcode tests. |
| `xcode-docs-and-search` | Generate DocC and search Apple documentation. |

The generated Claude Code adapter retains `xcode-build-fix` as a client-only agent wrapper for `xcode-build-and-fix`.

Xcode must be open with external agent access enabled under Settings > Intelligence > Model Context Protocol.
