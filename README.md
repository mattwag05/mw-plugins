# mw-plugins

Matthew Wagner's personal marketplace of **skills, plugins, and extensions** for AI coding agents.

It started as a Claude Code plugin marketplace, but it isn't Claude-only anymore — it's the shared home for agent capabilities across the homelab: Claude Code, [agent-runtime]/[agent], [agent], and whatever comes next. Some entries are full Claude Code plugins (commands, agents, MCP servers); others are plain skills or reference bundles that any agent can load.

## Using it as a Claude Code marketplace

```
/plugin marketplace add mattwag05/mw-plugins
/plugin install <plugin-name>@mw-plugins
```

## Layout

The repo holds two kinds of artifact:

```
.claude-plugin/marketplace.json   # registry — lists the Claude Code plugins ONLY
plugins/<name>/                    # (1) Claude Code plugins — registered above
├── .claude-plugin/plugin.json     #     plugin manifest
├── skills/<skill>/SKILL.md        #     one or more skills
├── commands/  agents/  scripts/   #     optional, per plugin
└── README.md
agent-runtime-skills/<name>/SKILL.md      # (2) [agent-runtime] skills — NOT in the marketplace manifest
agent-runtime-providers/<name>/           # (2) [agent-runtime] memory providers — NOT in the manifest (future)
```

**(1) Claude Code plugins** live under `plugins/` and are registered in
`.claude-plugin/marketplace.json`. Each entry is self-contained — Claude Code
reads the manifest, and the `skills/` payload is portable to any agent that
understands the [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
format.

**(2) [agent-runtime] artifacts** live under `agent-runtime-skills/` (and, in future,
`agent-runtime-providers/`). These are **not** Claude Code plugins and are **not** listed
in `marketplace.json` — Claude Code never loads them. The [agent-runtime] agent ([agent])
consumes them directly: skills via `skills.external_dirs` in `~/.agent-runtime/config.yaml`,
memory providers via `$HERMES_HOME/plugins/`. They live here so all of Matt's
agent capabilities share one versioned home.

## What's inside

A mix of homelab integrations (pippin, [agent]-connector, remote-tasks, obsidian-homelab), platform automation (macos-automation, xcode-mcp, swift-concurrency, testflight-triage), and reusable engineering workflows (autonomous-execution, phased-shipping, doc-harvest, calendar-organizer, internet-skill-finder, agent-cli-cli). See `.claude-plugin/marketplace.json` for the full list with descriptions.
