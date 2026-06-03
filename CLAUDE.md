# mw-plugins — agent instructions

Personal marketplace of **skills, plugins, and extensions** for AI coding agents (Claude Code, Hermes/Talia, Gus). Not Claude-only — `skills/` payloads are portable to any agent that reads the Agent Skills format.

GitHub: `mattwag05/mw-plugins` (renamed from `claude-plugins` 2026-06-03; old URLs still redirect). `origin` is SSH.

## Repo layout

```
.claude-plugin/marketplace.json   # registry — EVERY plugin must be listed here
plugins/<name>/
├── .claude-plugin/plugin.json     # plugin manifest (name, version, description, author)
└── skills/<skill>/SKILL.md        # the skill(s); commands/ agents/ scripts/ optional
```

Convention: **one skill per plugin** (see `autonomous-execution`, `phased-shipping`). A plugin folder is self-contained.

## Adding a plugin/skill

1. `mkdir -p plugins/<name>/.claude-plugin plugins/<name>/skills/<name>`
2. Write `plugins/<name>/.claude-plugin/plugin.json` (copy an existing manifest's shape).
3. Drop the skill at `plugins/<name>/skills/<name>/SKILL.md`.
4. **Register it** — append an entry to the `plugins` array in `.claude-plugin/marketplace.json` (`name`, `source: "./plugins/<name>"`, `description`, `version`). Forgetting this is the #1 way a plugin silently doesn't appear.
5. Validate JSON before committing: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"`.

## Gotchas

- **Two names, keep them in sync:** the local marketplace display name (`marketplace.json` `name`) and the GitHub repo name are independent. They drifted once (manifest said `mw-plugins` while the repo was still `claude-plugins`).
- **Local marketplace config** lives in `~/.claude/plugins/known_marketplaces.json` and `~/.claude/settings.json` (`extraKnownMarketplaces.mw-plugins.source.repo`). If you rename the repo again, update both.
- After pushing, pick up changes with `/plugin marketplace update mw-plugins` then `/reload-plugins`.

## Commit / push

Conventional-commit subjects (`feat(<plugin>): …`). End commit messages with the Claude co-author trailer. This repo has no CI and no beads DB — don't `bd init` it.
