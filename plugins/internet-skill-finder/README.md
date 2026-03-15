# Internet Skill Finder

Search and discover Agent Skills from 7 verified GitHub repositories, including the official Anthropic skills repo and top community collections.

## Features

- **Keyword search** across 1,000+ indexed skills
- **Offline cache** for instant results without network access
- **Live GitHub fetching** via `gh` CLI or `GITHUB_TOKEN`
- **Deep-dive** into any skill to read its full SKILL.md
- **Auto-triggered** when you ask about finding or discovering skills

## Installation

Install as a Claude Code plugin:

```bash
claude plugins install /path/to/internet-skill-finder
```

Or test locally:

```bash
claude --plugin-dir ~/.claude/plugins/internet-skill-finder
```

## Usage

### Auto-triggered (Skill)

Just ask naturally:
- "Is there a skill for PDF manipulation?"
- "Find me a skill for React testing"
- "What skills exist for scientific research?"

### Slash command

Use `/find-skill` for an interactive search experience.

### Direct script usage

```bash
# Search by keyword
python3 scripts/fetch_skills.py --search "docker deployment"

# List all skills
python3 scripts/fetch_skills.py --list

# Deep-dive into a skill
python3 scripts/fetch_skills.py --deep-dive "anthropics/skills" "pdf"

# Real-time GitHub fetch
python3 scripts/fetch_skills.py --search "testing" --online

# Update offline cache
python3 scripts/fetch_skills.py --refresh-cache

# Check API rate limits
python3 scripts/fetch_skills.py --rate-limit

# JSON output
python3 scripts/fetch_skills.py --search "react" --json
```

## Monitored Repositories

| Repository | Stars | Skills | Type |
|-----------|-------|--------|------|
| anthropics/skills | 81k+ | 16 | Official Anthropic |
| obra/superpowers | 68k+ | 14 | Dev methodology |
| ComposioHQ/awesome-claude-skills | 39k+ | 860+ | Hybrid (skills + automation) |
| vercel-labs/agent-skills | 21k+ | 5 | React/Next.js |
| K-Dense-AI/claude-scientific-skills | 11k+ | 150+ | Scientific research |
| travisvn/awesome-claude-skills | 8k+ | 10+ | Curated links |
| BehiSecc/awesome-claude-skills | 6k+ | 13+ | Curated links |

## Data Access Priority

1. **gh CLI** (15,000 req/hr) — auto-detected, always preferred
2. **Offline cache** (unlimited) — default fallback
3. **GITHUB_TOKEN** env var (5,000 req/hr) — with `--online` flag

## Requirements

- Python 3.8+
- Optional: `gh` CLI (for best GitHub API access)
- Optional: `GITHUB_TOKEN` env var (for online fetching without gh)
