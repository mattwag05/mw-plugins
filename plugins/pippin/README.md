# Pippin

Use [Pippin](https://github.com/mattwag05/pippin) for Apple mail, calendar, reminders, contacts, notes, memos, messages, audio, browser work, and diagnostics.

`mcp.json` starts `pippin mcp-server` for clients that support Agent Plugins v1. The generated Claude Code adapter exposes the same server through `.mcp.json`.

## Skills

- `pippin-cli` documents MCP use, command-line fallback, response envelopes, permissions, and command syntax.
- `pippin-release` contains the release procedure for the Pippin repository and Homebrew tap.

## Requirements

- Pippin installed on `PATH`.
- macOS privacy permissions appropriate to the requested data.
- Mail.app open for mail commands.

Run `pippin doctor` to inspect dependencies and permission state.
