# Internet skill finder

Search a cached index of Agent Skills from seven GitHub repositories. The helper can refresh from GitHub through `gh` or `GITHUB_TOKEN`.

Run commands from the skill directory:

```bash
python3 scripts/fetch_skills.py --search "docker deployment"
python3 scripts/fetch_skills.py --list
python3 scripts/fetch_skills.py --deep-dive "anthropics/skills" "pdf"
python3 scripts/fetch_skills.py --refresh-cache
```

The portable workflow is in `skills/internet-skill-finder/SKILL.md`. Claude Code's `/find-skill` command is a generated wrapper for that skill.
