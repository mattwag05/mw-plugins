---
name: calendar-organizer
description: |
  Extracts, cleans, and organizes calendar schedules from messy sources (Excel files, CSV, images, text, ICS files) into structured calendar data. Use this skill when the user uploads a calendar or schedule file (.xlsx, .csv, .ics, .png, .jpg), shares an image of a calendar or schedule, asks to "organize my schedule", "clean up this calendar", or "extract events from this", requests calendar extraction from any source, wants to convert schedule data to different formats, or needs to add schedule data to their calendar app.
tools: Read, Bash, Write, Glob, Grep
version: 1.0.0
---

# Calendar Organizer

Process schedule data from any source into clean, structured calendar output.

## Workflow

### 1. Identify Input and Set Up Environment

Determine the input type (Excel, CSV, image, text, ICS) and ensure Python dependencies are available:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup_venv.sh
```

This creates a venv at `${CLAUDE_PLUGIN_ROOT}/.venv/` with required packages (openpyxl, ics, python-dateutil, pytz) on first run, and is instant on subsequent runs.

### 2. Extract Raw Data

**For Excel/CSV files** — use the parse_excel.py utility:

```bash
${CLAUDE_PLUGIN_ROOT}/.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/parse_excel.py "/path/to/file.xlsx"
```

This outputs JSON with all cell data, sheet names, and structure. Analyze the output to identify event rows, date columns, and time patterns.

**For images** — read the image directly using the Read tool. Claude's vision capabilities can extract text from calendar images. Look for:
- Grid/table structures indicating days and time slots
- Positional cues (above/below dotted lines, morning vs afternoon sections)
- Handwritten or typed event names

**For text/email** — read the text directly and parse event information using the time interpretation rules below.

**For ICS files** — read directly. The format is plaintext with VEVENT blocks.

### 3. Parse Events Using Time Interpretation Rules

Apply these rules to every extracted event. See `${CLAUDE_PLUGIN_ROOT}/skills/calendar-organizer/references/time-interpretation-rules.md` for the complete ruleset.

**Key defaults:**
- No time specified: 8:00 AM - 5:00 PM
- Conference: 8:00 AM - 12:00 PM
- "AM" suffix: 8:00 AM - 12:00 PM
- "PM" suffix: 1:30 PM - 5:00 PM
- "All day": 8:00 AM - 5:00 PM

**Positional rules (block/scanned calendars):**
- Above dotted line or in top section: morning (8:00 AM - 12:00 PM)
- Below dotted line or in bottom section: afternoon (12:00 PM - 5:00 PM)

**On-call rules:** See `${CLAUDE_PLUGIN_ROOT}/skills/calendar-organizer/references/on-call-rules.md`

### 4. Validate Data

For every parsed event, check:
- Date is valid (no Feb 30, etc.)
- Day-of-week matches the date
- Start time is before end time (unless overnight)
- No duplicate events on same date/time
- Flag ambiguous entries in Notes column

### 5. Generate Outputs

**Always produce these three outputs:**

#### Markdown Table

Present a chronologically sorted table:

```
| Date | Day | Event Title | Start Time | End Time | Location | Notes |
|------|-----|-------------|------------|----------|----------|-------|
```

#### ICS File

Generate using the generate_ics.py utility:

```bash
echo '<events_json>' | ${CLAUDE_PLUGIN_ROOT}/.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/generate_ics.py --timezone "America/New_York" --output "/path/to/output.ics"
```

Pass events as a JSON array on stdin. Each event object:
```json
{
  "title": "Event Name",
  "date": "2026-03-15",
  "start_time": "08:00",
  "end_time": "17:00",
  "location": "",
  "notes": ""
}
```

#### Summary Statistics

Report:
- Total event count
- Date range (first date - last date)
- Event type breakdown (if categories are apparent)

### 6. Offer Next Steps

After presenting results, offer:
- Import ICS to Apple Calendar, Google Calendar, or Outlook
- Export as CSV for spreadsheet use
- Detect scheduling conflicts
- Adjust any interpreted times

## Important Notes

- Always show a preview of parsed events and highlight assumptions before generating final output
- When uncertain about a time or event, flag it in the Notes column rather than guessing
- For Apple Calendar import on macOS, the user can simply open the .ics file
- Default timezone is America/New_York unless the user specifies otherwise
