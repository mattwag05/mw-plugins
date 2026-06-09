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

## agent (envelope v1)

Compact JSON wrapped in a **versioned envelope**. The previous raw payload now lives under
`data` — parse `.data`, not the top level.

```bash
pippin calendar today --format agent
# Success:
# {"v":1,"status":"ok","duration_ms":138,"data":[{"id":"a1b2c3d4...","calendarTitle":"Work","title":"Team Standup","startDate":"2026-03-10T10:00:00-05:00","isAllDay":false}]}
# Error:
# {"v":1,"status":"error","duration_ms":44,"error":{"code":"access_denied","message":"Calendar access denied. -> Open System Settings > Privacy & Security > Calendars...","remediation":{...}}}
```

Envelope fields:
- `v` — schema version (currently `1`). Bumps on any breaking change.
- `status` — `ok` or `error`. **Branch on this first.**
- `duration_ms` — wall-clock time for the call.
- `data` — the payload (same shape the old bare output had). Present on success.
- `error` — `{code, message, remediation?}` on failure. `code` is stable + snake_case
  (e.g. `access_denied`, `not_found`, `timeout`) and mirrors the process exit code.
- `warnings` — optional array of non-fatal advisories (e.g. partial-results / soft-timeout
  notices). Data is still valid but may be incomplete.

Use when: an agent is the consumer. Saves tokens vs. pretty-printed JSON, and gives a
machine-stable success/error contract.

**Exceptions / notes:**
- `notes show --format agent`: `data` carries `plainText` instead of the HTML `body` to
  avoid large payloads. Fields: `id, title, plainText, folder, modificationDate`.
- Action results (create/edit/delete/complete/send/move/mark): `data` is the compact
  `{success, action, details}` object — still inside the envelope.
- Project further with `--fields a,b,c` to trim `data` to just those keys.

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
