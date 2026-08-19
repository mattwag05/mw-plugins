# mw-plugins

Personal Claude Code plugin marketplace — **skills, plugins, and extensions** for AI coding agents.

Entries are packaged as Claude Code plugins (commands, agents, MCP servers), but their `skills/` payloads use the portable [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) format, so any skills-aware agent can load them too.

## From Claude Code

```
/plugin marketplace add mattwag05/mw-plugins
/plugin install <plugin-name>@mw-plugins
```

## Layout

```
.claude-plugin/marketplace.json   # the Claude Code index (lists the plugins/ entries)
plugins/<name>/
├── .claude-plugin/plugin.json
├── skills/<skill>/SKILL.md
└── commands/  agents/  scripts/   # optional, per plugin
```

## What's inside

| Plugin | Description |
| --- | --- |
| `apple-container` | Run Linux containers with Apple's `container` CLI on Apple silicon; migrate Docker/Compose workflows |
| `autonomous-execution` | Complete tasks autonomously — execute, verify, diagnose, and fix rather than asking the user to check things |
| `calendar-organizer` | Extract, clean, and organize calendar schedules from messy sources into structured calendar data |
| `doc-harvest` | Scrape documentation websites into structured context-library entries with progressive disclosure navigation |
| `internet-skill-finder` | Search and recommend Agent Skills from verified GitHub repositories |
| `macos-automation` | Automate Apple's native macOS apps (Mail, Calendar, Notes, Reminders) with AppleScript, JXA, and Swift |
| `phased-shipping` | Ship a multi-phase engineering plan as a sequence of stacked PRs |
| `pippin` | Bundles the pippin MCP server (mail, calendar, reminders, contacts, notes, memos, messages) plus CLI skills |
| `swift-concurrency` | Swift 6 concurrency patterns, proactive code review, and migration planning |
| `testflight-triage` | Scrape App Store Connect TestFlight feedback via Chrome automation and triage into issues |
| `unslop` | Edit writing to remove common AI patterns and add a more natural human voice |
| `xcode-mcp` | Drive the Xcode MCP bridge for building, testing, fixing, and managing Xcode projects |

See `.claude-plugin/marketplace.json` for versions and full descriptions.

## Attribution

`unslop` is copied from Lauren Tan's [poteto/plugins](https://github.com/poteto/plugins/blob/main/pstack/skills/unslop/SKILL.md) repository and is used under the MIT License. The bundled [license](plugins/unslop/LICENSE) retains the upstream copyright notice.
