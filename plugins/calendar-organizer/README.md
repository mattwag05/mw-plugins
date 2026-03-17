# calendar-organizer

Claude Code plugin for extracting, cleaning, and organizing calendar schedules from messy sources.

## Features

- Parse Excel (.xlsx), CSV, images, text, and ICS files
- Intelligent time interpretation (AM/PM, positional, on-call patterns)
- Markdown table output for review
- ICS file generation for calendar import
- Summary statistics

## Installation

```bash
claude --plugin-dir ~/Projects/calendar-organizer
```

Or add to your Claude Code settings.

## Usage

### Automatic
Upload or reference a schedule file — the skill triggers automatically when Claude detects schedule-like content.

### Command
```
/organize-calendar /path/to/schedule.xlsx
```

## Prerequisites

- Python 3.12+ (installed via Homebrew)
- Dependencies auto-install on first use via venv

## Components

| Component | Description |
|-----------|-------------|
| `skills/calendar-organizer/` | Core parsing knowledge and workflow |
| `commands/organize-calendar.md` | `/organize-calendar` slash command |
| `scripts/parse_excel.py` | Excel/CSV parser (outputs JSON) |
| `scripts/generate_ics.py` | ICS calendar file generator |
| `scripts/setup_venv.sh` | Virtual environment setup |

## Output Formats

1. **Markdown table** — Date, Day, Event Title, Start/End Time, Location, Notes
2. **ICS file** — RFC 5545 compliant, importable to Apple Calendar / Google / Outlook
3. **Summary** — Event count, date range, type breakdown

## Time Interpretation

See `skills/calendar-organizer/references/time-interpretation-rules.md` for the full ruleset including defaults, suffix patterns, positional rules, and priority order.

## On-Call Rules

See `skills/calendar-organizer/references/on-call-rules.md` for day-specific on-call timing rules.
