#!/usr/bin/env python3
"""Generate ICS calendar files from structured event JSON.

Usage:
    echo '<json_array>' | python generate_ics.py --timezone "America/New_York" --output "schedule.ics"
    python generate_ics.py --input events.json --timezone "America/New_York" --output "schedule.ics"

Input JSON format (array of events):
[
    {
        "title": "Event Name",
        "date": "2026-03-15",
        "start_time": "08:00",
        "end_time": "17:00",
        "location": "Room 101",
        "notes": "Optional notes",
        "end_date": "2026-03-16"  // optional, for overnight events
    }
]

Generates RFC 5545 compliant ICS output.
"""

import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from dateutil import parser as dateparser


def create_ics(events: list[dict], timezone: str = "America/New_York") -> str:
    """Create an ICS calendar string from event list."""
    tz = pytz.timezone(timezone)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Calendar Organizer//Claude Code Plugin//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-TIMEZONE:{timezone}",
        # VTIMEZONE block
        "BEGIN:VTIMEZONE",
        f"TZID:{timezone}",
        "END:VTIMEZONE",
    ]

    for event in events:
        title = event.get("title", "Untitled Event")
        date_str = event["date"]
        start_time = event.get("start_time", "08:00")
        end_time = event.get("end_time", "17:00")
        location = event.get("location", "")
        notes = event.get("notes", "")
        end_date_str = event.get("end_date", "")

        # Parse date and times
        event_date = dateparser.parse(date_str).date()
        start_dt = datetime.combine(
            event_date,
            dateparser.parse(start_time).time(),
        )
        start_dt = tz.localize(start_dt)

        # Handle overnight events
        if end_date_str:
            end_date = dateparser.parse(end_date_str).date()
        else:
            end_hour = dateparser.parse(end_time).time()
            start_hour = dateparser.parse(start_time).time()
            end_date = event_date + timedelta(days=1) if end_hour < start_hour else event_date

        end_dt = datetime.combine(end_date, dateparser.parse(end_time).time())
        end_dt = tz.localize(end_dt)

        uid = str(uuid.uuid4())
        now = datetime.now(pytz.utc).strftime("%Y%m%dT%H%M%SZ")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
            f"DTSTART;TZID={timezone}:{start_dt.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID={timezone}:{end_dt.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{escape_ics(title)}",
        ])

        if location:
            lines.append(f"LOCATION:{escape_ics(location)}")
        if notes:
            lines.append(f"DESCRIPTION:{escape_ics(notes)}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def escape_ics(text: str) -> str:
    """Escape special characters per RFC 5545."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def main():
    timezone = "America/New_York"
    output_path = None
    input_path = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--timezone" and i + 1 < len(args):
            timezone = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--input" and i + 1 < len(args):
            input_path = args[i + 1]
            i += 2
        else:
            i += 1

    # Read events from file or stdin
    if input_path:
        with open(input_path) as f:
            events = json.load(f)
    else:
        events = json.load(sys.stdin)

    if not isinstance(events, list):
        print("Error: Input must be a JSON array of events", file=sys.stderr)
        sys.exit(1)

    ics_content = create_ics(events, timezone)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ics_content)
        print(f"ICS file written: {output_path}")
        print(f"Events: {len(events)}")
    else:
        print(ics_content)


if __name__ == "__main__":
    main()
