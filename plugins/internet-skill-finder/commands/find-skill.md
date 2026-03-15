---
name: find-skill
description: Search for Agent Skills across 7 verified GitHub repositories
allowed-tools:
  - Bash
  - AskUserQuestion
---

# Find Skill Command

Help the user discover Agent Skills from verified GitHub repositories.

## Instructions

1. Ask the user what kind of skill they are looking for. Ask about:
   - What task or domain they need help with
   - Any specific tools, languages, or frameworks involved

2. Once the user describes their need, search for matching skills:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_skills.py" --search "relevant keywords"
```

3. Present the results clearly, formatting each match as:

```
### [Skill Name]
**Source**: [owner/repo] | Stars: [count]
**Description**: [description]
**Tags**: [tags]
**URL**: [github_url]
```

4. If the user wants more details about a specific skill, run a deep-dive:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_skills.py" --deep-dive "owner/repo" "skill-name"
```

5. If no results match, suggest:
   - Broader or alternative search terms
   - Listing all available skills: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_skills.py" --list`
   - Creating a custom skill for their use case

## Tips

- Use multiple search terms for better results (e.g., `"react testing"` instead of just `"react"`)
- The `--online` flag fetches real-time data from GitHub if cached results seem outdated
- Results are ranked by relevance: exact name matches score highest, followed by tag matches, then description matches
