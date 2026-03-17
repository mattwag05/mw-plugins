# Time Interpretation Rules

Complete reference for interpreting times from schedule data.

## Default Times

| Condition | Start | End |
|-----------|-------|-----|
| No time specified | 8:00 AM | 5:00 PM |
| Conference (no time given) | 8:00 AM | 12:00 PM |
| All-day event | 8:00 AM | 5:00 PM |

## Suffix Patterns

| Pattern | Start | End | Example |
|---------|-------|-----|---------|
| "AM" suffix | 8:00 AM | 12:30 PM | "Clinic AM" |
| "PM" suffix | 1:30 PM | 5:00 PM | "Rounds PM" |
| "- AM" suffix | 8:00 AM | 12:00 PM | "Surgery - AM" |
| "- PM" suffix | 1:30 PM | 5:00 PM | "Surgery - PM" |

## Explicit Time Ranges

Parse time ranges directly when present:

| Format | Interpretation |
|--------|---------------|
| "8-9" or "8:00-9:00" | 8:00 AM - 9:00 AM |
| "8a-12p" | 8:00 AM - 12:00 PM |
| "1:00 PM - 3:30 PM" | 1:00 PM - 3:30 PM |
| "0800-1700" | 8:00 AM - 5:00 PM (military) |

When a range like "8-9" is ambiguous (AM/PM), default to AM unless context suggests otherwise.

## Positional Rules (Block/Scanned Calendars)

For calendars with visual sections (dotted lines, morning/afternoon headers):

| Position | Start | End |
|----------|-------|-----|
| Above dotted line / top section | 8:00 AM | 12:00 PM |
| Below dotted line / bottom section | 1:30 PM | 5:00 PM |
| Split entry (appears in both) | Create two events: AM + PM |

If a single event text spans both sections, create two separate events:
1. Morning session: 8:00 AM - 12:00 PM
2. Afternoon session: 1:30 PM - 5:00 PM

## Contextual Keywords

| Keyword | Interpretation |
|---------|---------------|
| "morning" | 8:00 AM - 12:00 PM |
| "afternoon" | 1:30 PM - 5:00 PM |
| "evening" | 5:00 PM - 9:00 PM |
| "lunch" | 12:00 PM - 1:00 PM |
| "half day" | 8:00 AM - 12:00 PM |

## Priority Order

When multiple rules conflict, apply in this order:
1. Explicit time ranges (always win)
2. AM/PM suffixes
3. Contextual keywords
4. Positional rules (block calendars)
5. Event-type defaults (conference, etc.)
6. Global default (8:00 AM - 5:00 PM)
