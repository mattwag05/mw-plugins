---
name: organize-calendar
description: Extract, clean, and organize a calendar schedule from a file or text into structured events with markdown table and ICS output
argument-hint: <file path or paste schedule text>
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
---

# Organize Calendar

Process a schedule from the provided source and output structured calendar data.

## Instructions

1. **Determine the input source from $ARGUMENTS:**
   - If a file path is given, read that file
   - If text is pasted, parse it directly
   - If no arguments, ask the user what schedule they want to organize

2. **Load the calendar-organizer skill knowledge** — follow the parsing rules, time interpretation, and output format guidance from the calendar-organizer skill.

3. **Set up the Python environment** if processing Excel/CSV or generating ICS:
   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup_venv.sh
   ```

4. **Parse the schedule data:**
   - For .xlsx/.csv: use `${CLAUDE_PLUGIN_ROOT}/scripts/parse_excel.py`
   - For images: use vision to read the content
   - For text/ICS: parse directly
   - Apply time interpretation rules from the skill

5. **Show a preview** of the parsed events as a markdown table. Highlight any assumptions made about times or event details. Ask the user to confirm before generating the ICS file.

6. **Generate outputs** after user confirmation:
   - Final markdown table (sorted chronologically)
   - ICS file using `${CLAUDE_PLUGIN_ROOT}/scripts/generate_ics.py`
   - Summary statistics (event count, date range)

7. **Offer next steps:**
   - Open the ICS file to import into Apple Calendar
   - Export to CSV
   - Detect scheduling conflicts
   - Adjust any times
