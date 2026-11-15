# mw-plugins

Portable Agent Plugins with generated Claude Code compatibility packages.

Each package under `plugins/` follows [Agent Plugins v1.0.0](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md). Skills follow the [Agent Skills specification](https://agentskills.io/specification). The files under `client-adapters/claude-code/plugins/` are generated because current Claude Code releases still require legacy manifests.

## Install with Claude code

```text
/plugin marketplace add mattwag05/mw-plugins
/plugin install <plugin-name>@mw-plugins
```

## Repository layout

```text
plugins/<name>/
├── plugin.json
├── mcp.json                     # optional
└── skills/<skill>/SKILL.md

client-adapters/claude-code/
├── sources/<name>/              # authored Claude-only wrappers
├── plugins/<name>/              # generated compatibility packages
└── config.json

.claude-plugin/marketplace.json  # client distribution metadata
scripts/build_claude_adapters.py
```

Regenerate compatibility packages after changing a portable plugin:

```bash
python3 scripts/build_claude_adapters.py
python3 scripts/build_claude_adapters.py --check
```

## Plugins

| Plugin | Purpose |
| --- | --- |
| `core` | The 12 core skills for the shared agent loop (`core/LOOP.md`), sized and evaluated for small local models. |
| `anti-loop` | Stop agents from rerunning or rewording tool calls whose output they already have; includes an enforcing Pi extension. |
| `apple-container` | Run Linux containers with Apple's `container` CLI and migrate Docker workflows. |
| `calendar-organizer` | Extract schedules and produce structured events and ICS files. |
| `doc-harvest` | Harvest documentation sites and navigate indexed local references. |
| `macos-automation` | Automate Mail, Calendar, Notes, and Reminders on macOS. |
| `pippin` | Use Pippin through MCP or its command-line interface. |
| `swift-concurrency` | Write, review, and migrate Swift concurrency code. |
| `testflight-triage` | Review TestFlight data and track actionable work. |
| `xcode-mcp` | Build, test, fix, and manage Xcode projects through MCP. |

Retired plugins (ambition, autonomous-execution, i-have-adhd, internet-skill-finder, phased-shipping, project-housekeeping, session-closeout, unslop) live in `archive/plugins/`; see `archive/README.md`.

Versions and adapter source paths are recorded in `.claude-plugin/marketplace.json`.

## Attribution

`core` adapts material from mattpocock/skills, poteto/plugins (pstack) and t3dotgg/tstack under the MIT License; notices are in [plugins/core/THIRD_PARTY_NOTICES.md](plugins/core/THIRD_PARTY_NOTICES.md), and each skill's `PROVENANCE.md` names its sources. Archived plugins keep their own license files under `archive/plugins/`.
