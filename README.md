# mw-plugins

Matthew Wagner's personal marketplace of **skills, plugins, and extensions** for AI coding agents.

It started as a Claude Code plugin marketplace, but it isn't Claude-only anymore — it's the shared home for agent capabilities across the homelab: Claude Code, Hermes/Talia, Gus, and whatever comes next. Some entries are full Claude Code plugins (commands, agents, MCP servers); others are plain skills or reference bundles that any agent can load.

## Using it as a Claude Code marketplace

```
/plugin marketplace add mattwag05/mw-plugins
/plugin install <plugin-name>@mw-plugins
```

## Layout

```
.claude-plugin/marketplace.json   # registry of every plugin
plugins/<name>/
├── .claude-plugin/plugin.json     # plugin manifest
├── skills/<skill>/SKILL.md        # one or more skills
├── commands/  agents/  scripts/   # optional, per plugin
└── README.md
```

Each top-level entry under `plugins/` is self-contained — Claude Code reads the manifest, but the `skills/` payload is portable to any agent that understands the [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) format.

## What's inside

A mix of homelab integrations (pippin, talia-connector, remote-tasks, obsidian-homelab), platform automation (macos-automation, xcode-mcp, swift-concurrency, testflight-triage), and reusable engineering workflows (autonomous-execution, phased-shipping, doc-harvest, calendar-organizer, internet-skill-finder, openclaw-cli). See `.claude-plugin/marketplace.json` for the full list with descriptions.
