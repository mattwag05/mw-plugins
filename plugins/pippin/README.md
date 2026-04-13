# pippin

Claude Code plugin for [pippin](https://github.com/mattwag05/pippin), a macOS CLI toolkit for Apple app automation (Mail, Calendar, Reminders, Contacts, Notes, Voice Memos, Audio, Browser).

## What it provides

### MCP server (new in 1.1.0)

Bundles `pippin mcp-server` so Claude Code calls pippin directly as MCP tools instead of shelling out. Installing this plugin auto-connects the following tool surface once enabled:

| Area | Tools |
|---|---|
| Mail | `mail_accounts`, `mail_mailboxes`, `mail_list`, `mail_show`, `mail_search` |
| Calendar | `calendar_list`, `calendar_events`, `calendar_today`, `calendar_remaining`, `calendar_upcoming`, `calendar_search`, `calendar_create` |
| Reminders | `reminders_lists`, `reminders_list`, `reminders_show`, `reminders_search`, `reminders_create`, `reminders_complete` |
| Contacts | `contacts_search`, `contacts_show` |
| Notes | `notes_list`, `notes_search`, `notes_show`, `notes_folders` |
| System | `status`, `doctor` |

Destructive commands (`mail send/reply/forward`, `delete`) are intentionally not exposed — use the CLI directly when needed.

After installing the plugin, run `/mcp` in Claude Code to confirm the pippin server is connected. The tool surface is full documented in pippin's own `docs/mcp-server.md`.

### `pippin-cli` skill

Triggers when the user asks about mail, calendar, reminders, notes, contacts, voice memos, audio, or browser automation. Covers:

- Complete command reference across all 8 command groups
- Output format guide (text / json / agent)
- Multi-step workflow patterns for common automation tasks

Useful when you want Claude to drive pippin from the shell (`pippin mail send ...`) rather than through MCP tools.

## Requirements

- **pippin ≥ 0.17.0** installed and on `$PATH`
  - Homebrew: `brew tap mattwag05/tap && brew install pippin`
  - From source: `git clone https://forgejo.example-tailnet.ts.net/matthewwagner/pippin && cd pippin && make install`
- macOS 15+ with appropriate TCC permissions (run `pippin doctor` to audit)
- Mail.app open for mail commands
- `mlx-audio` installed for audio commands: `pipx install mlx-audio`

## Configuration notes

The bundled `.mcp.json` uses the bare command `pippin` so it resolves through `$PATH`. Claude Code launches MCP servers with a login shell's PATH by default, so Homebrew (`/opt/homebrew/bin`) is found automatically. If you installed to `~/.local/bin` via `make install` and that directory isn't on your login PATH, either add it or override `.mcp.json` with an absolute path.

## Source

- Plugin: `https://forgejo.example-tailnet.ts.net/matthewwagner/claude-plugins/src/branch/main/plugins/pippin`
- pippin itself: `https://forgejo.example-tailnet.ts.net/matthewwagner/pippin`
