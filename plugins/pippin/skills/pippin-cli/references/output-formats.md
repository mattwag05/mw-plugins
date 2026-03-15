# Pippin Output Formats

All pippin commands that produce data support `--format <mode>`.

---

## text (default)

Human-readable tables and detail cards. Designed for terminal display.

```bash
pippin calendar today
# Output:
# ID         START              CALENDAR          TITLE
# ─────────  ─────────────────  ────────────────  ──────────────────────────────────
# a1b2c3d4   10:00 Mar 10       Work              Team Standup
```

Use when: you want to read output as a human.

---

## json

Pretty-printed JSON with sorted keys. All fields included.

```bash
pippin calendar today --format json
# Output:
# [
#   {
#     "calendarId": "...",
#     "calendarTitle": "Work",
#     "endDate": "2026-03-10T10:30:00-05:00",
#     "id": "a1b2c3d4...",
#     "isAllDay": false,
#     "startDate": "2026-03-10T10:00:00-05:00",
#     "title": "Team Standup"
#   }
# ]
```

Use when: you want all fields, human-inspectable, piped to `jq`.

---

## agent

Compact JSON — no whitespace, no newlines, no sorted keys. Same fields as `json`.

```bash
pippin calendar today --format agent
# Output:
# [{"id":"a1b2c3d4...","calendarId":"...","calendarTitle":"Work","title":"Team Standup","startDate":"2026-03-10T10:00:00-05:00","endDate":"2026-03-10T10:30:00-05:00","isAllDay":false,"status":"none"}]
```

Use when: Claude Code is the consumer. Saves tokens vs. pretty-printed JSON.

**Exceptions:**
- `notes show --format agent`: Returns `plainText` instead of the HTML `body` field to avoid large HTML payloads. Fields: `id, title, plainText, folder, modificationDate`.
- Action results (create/edit/delete/complete/send/move/mark): Same as `json` — action results are already compact.

---

## When to Use Each Format

| Scenario | Format |
|----------|--------|
| User reading terminal output | `text` |
| Piping to `jq` for inspection | `json` |
| Claude Code processing result | `agent` |
| Checking if action succeeded | `agent` or `json` |
| Reading a full note with HTML | `json` (includes body) |
| Reading a note body as text | `agent` (plainText only) |

---

## Notes-Specific Behavior

`pippin notes show` returns different fields in agent mode:

| Field | json | agent |
|-------|------|-------|
| id | yes | yes |
| title | yes | yes |
| body (HTML) | yes | NO |
| plainText | yes | yes |
| folder | yes | yes |
| folderId | yes | no |
| account | yes | no |
| creationDate | yes | no |
| modificationDate | yes | yes |

This prevents large HTML content from consuming tokens unnecessarily.
