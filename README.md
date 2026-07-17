# mw-plugins

Matthew Wagner's personal marketplace of **skills, plugins, and extensions** for AI coding agents.

It started as a Claude Code plugin marketplace, but it isn't Claude-only anymore — it's the shared home for agent capabilities across the homelab: Claude Code, [agent-runtime]/[agent], [agent], and whatever comes next. Some entries are full Claude Code plugins (commands, agents, MCP servers); others are plain skills or reference bundles that any agent can load.

## From Claude Code

Claude Code is one consumer among several — it reads the `marketplace.json` index:

```
/plugin marketplace add mattwag05/mw-plugins
/plugin install <plugin-name>@mw-plugins
```

## Layout

mw-plugins is consumer-agnostic: several agents load from it, and each has its own
discovery path. Nothing here is Claude-only by nature — `marketplace.json` is just
the Claude Code index, not the repo's boundary.

```
.claude-plugin/marketplace.json   # the Claude Code index (lists the plugins/ entries)
plugins/<name>/                    # packaged as Claude Code plugins; skills/ payload is portable
├── .claude-plugin/plugin.json
├── skills/<skill>/SKILL.md
└── commands/  agents/  scripts/   # optional, per plugin
agent-runtime-skills/<name>/SKILL.md      # [agent-runtime] ([agent]) skills — loaded via skills.external_dirs
agent-runtime-providers/<name>/           # [agent-runtime] memory providers (future) — symlinked into $HERMES_HOME/plugins/
```

- **`plugins/`** — packaged as Claude Code plugins and indexed in `marketplace.json`.
  Their `skills/` payloads use the portable
  [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) format, so
  [agent-runtime], [agent], or any skills-aware agent can load them too.
- **`agent-runtime-skills/`** — skills for the [agent-runtime] agent ([agent]), loaded via
  `skills.external_dirs` in `~/.agent-runtime/config.yaml`. Not in the marketplace manifest.
- **`agent-runtime-providers/`** — [agent-runtime] memory providers (future), symlinked into
  `$HERMES_HOME/plugins/`. Not in the manifest.

The directory a capability lives in reflects how it's **packaged and discovered**,
not which agent it "belongs" to. A portable skill under `plugins/` is fair game for
every agent; the `agent-runtime-*` trees are only for capabilities that use [agent-runtime]-specific
wiring (config keys, the `MemoryProvider` ABC) with no Claude Code equivalent.

## What's inside

A mix of homelab integrations (pippin, [agent]-connector, remote-tasks, obsidian-homelab), platform automation (macos-automation, xcode-mcp, swift-concurrency, testflight-triage), and reusable engineering workflows (autonomous-execution, phased-shipping, doc-harvest, calendar-organizer, internet-skill-finder, agent-cli-cli). See `.claude-plugin/marketplace.json` for the full list with descriptions.
