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
| `apple-container` | Run Linux containers with Apple's `container` CLI and migrate Docker workflows. |
| `autonomous-execution` | Finish verifiable work with available tools before asking the user to intervene. |
| `calendar-organizer` | Extract schedules and produce structured events and ICS files. |
| `doc-harvest` | Harvest documentation sites and navigate indexed local references. |
| `i-have-adhd` | Shape responses for an ADHD reader with direct, bounded next actions. |
| `internet-skill-finder` | Search verified GitHub repositories for Agent Skills. |
| `macos-automation` | Automate Mail, Calendar, Notes, and Reminders on macOS. |
| `phased-shipping` | Ship multi-phase engineering work as stacked pull requests. |
| `pippin` | Use Pippin through MCP or its command-line interface. |
| `swift-concurrency` | Write, review, and migrate Swift concurrency code. |
| `testflight-triage` | Review TestFlight data and track actionable work. |
| `unslop` | Remove common AI writing patterns and restore a natural voice. |
| `xcode-mcp` | Build, test, fix, and manage Xcode projects through MCP. |

Versions and adapter source paths are recorded in `.claude-plugin/marketplace.json`.

## Attribution

`unslop` is copied from Lauren Tan's [poteto/plugins](https://github.com/poteto/plugins/blob/main/pstack/skills/unslop/SKILL.md) repository under the MIT License. Its [bundled license](plugins/unslop/LICENSE) retains the upstream copyright notice. The upstream `SKILL.md` is preserved byte-for-byte.

`i-have-adhd` is adapted from Ayoub Ghriss's [i-have-adhd](https://github.com/ayghri/i-have-adhd) repository under the MIT License. Its [bundled license](plugins/i-have-adhd/LICENSE) retains the upstream copyright notice.
