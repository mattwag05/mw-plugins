# Calendar organizer

Extract schedule data from Excel, CSV, ICS, images, or text. The skill applies explicit time rules, previews ambiguous events, and can write an RFC 5545 ICS file.

## Components

| Path | Purpose |
| --- | --- |
| `plugin.json` | Agent Plugins v1 manifest. |
| `skills/calendar-organizer/SKILL.md` | Parsing, review, and output workflow. |
| `skills/calendar-organizer/scripts/parse_excel.py` | Excel and CSV parser. |
| `skills/calendar-organizer/scripts/generate_ics.py` | ICS generator. |
| `skills/calendar-organizer/scripts/setup_venv.sh` | Local Python environment setup. |

Claude Code users can also run `/organize-calendar`; that command is generated as a thin adapter for the same skill.
