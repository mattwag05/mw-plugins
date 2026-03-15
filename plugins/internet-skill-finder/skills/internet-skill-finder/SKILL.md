---
name: internet-skill-finder
description: >-
  Search and recommend Agent Skills from 7 verified GitHub repositories.
  Use this skill whenever users ask to find, discover, search for, browse,
  or recommend skills or plugins for specific tasks, domains, or workflows.
  Also trigger when users say things like "is there a skill for...",
  "find me a skill", "what skills exist for...", "I need a plugin for...",
  "are there any skills that...", "search for skills", "browse available
  skills", or any mention of searching skill repositories, importing
  skills, or browsing available agent capabilities. Even if the user just
  describes a task and you suspect a community skill might exist, consider
  using this to check.
version: 1.0.0
---

# Internet Skill Finder

Search 7 verified GitHub repositories for Agent Skills, including the official Anthropic skills repo and top community collections.

## How to Search

Run the fetch script via Bash to search for skills matching the user's query:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_skills.py" --search "keyword"
```

Replace `"keyword"` with terms relevant to what the user is looking for. Use multiple words for broader matches (e.g., `--search "react testing"`).

## Available Commands

| Command | Purpose |
|---------|---------|
| `--search "query"` | Search by keyword (most common) |
| `--list` | List all skills across all repos |
| `--deep-dive "owner/repo" "skill-name"` | Fetch full details for a specific skill |
| `--online` | Force real-time fetch from GitHub |
| `--json` | Output structured JSON |
| `--limit N` | Limit search results (default: 20) |
| `--rate-limit` | Check GitHub API rate limits |
| `--refresh-cache` | Update the offline cache from GitHub |

## Workflow

1. **Search first**: Run `--search` with the user's keywords.
2. **Present results**: Format each match clearly with name, source, stars, description, tags, and GitHub URL.
3. **Deep-dive if interested**: If a result looks promising, run `--deep-dive` to get full details.
4. **Suggest alternatives**: If no matches, suggest broadening the search terms or listing all skills with `--list`.

## Presenting Results

Format each matching skill as:

```
### [Skill Name]
**Source**: [owner/repo] | Stars: [count]
**Description**: [description]
**Tags**: [tags]
**URL**: [github_url]
```

## When No Results Found

- Suggest alternative or broader search terms
- Offer to list all available skills for browsing
- Mention that the user can create a custom skill

## Data Sources

The script automatically selects the best available data source:

1. **gh CLI** (15,000 req/hr) — auto-detected, always preferred
2. **Offline cache** (unlimited) — default fallback, no network needed
3. **GITHUB_TOKEN** (5,000 req/hr) — with `--online` flag

## Monitored Repositories

1. **anthropics/skills** — Official Anthropic skills (81k+ stars)
2. **obra/superpowers** — Dev methodology framework (68k+ stars)
3. **ComposioHQ/awesome-claude-skills** — 800+ automation skills (39k+ stars)
4. **vercel-labs/agent-skills** — React/Next.js skills (21k+ stars)
5. **K-Dense-AI/claude-scientific-skills** — 150+ scientific skills (11k+ stars)
6. **travisvn/awesome-claude-skills** — Curated link directory (8k+ stars)
7. **BehiSecc/awesome-claude-skills** — Curated skill list (6k+ stars)
