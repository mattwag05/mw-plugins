# Pippin output

Every command and every error writes one compact JSON envelope (v4). There is no other
format: `--format agent` is an accepted no-op, and `--format text|json` are usage errors.
`--help`, `init` and `mail watch` (NDJSON) are the exceptions.

```bash
pippin calendar today
# Success:
# {"v":4,"status":"ok","duration_ms":138,"data":[{"id":"a1b2c3d4...","calendarTitle":"Work","title":"Team Standup","startDate":"2026-03-10T10:00:00-05:00","isAllDay":false}]}
# Error:
# {"v":4,"status":"error","duration_ms":44,"error":{"code":"access_denied","message":"Calendar access denied.","next_step":{"retryable":false,"human_action":"Open System Settings > Privacy & Security > Calendars..."},"remediation":{...}}}
```

Envelope fields:
- `v`: schema version (currently `4`). Bumps on any breaking change.
- `status`: `ok` or `error`. **Branch on this first.**
- `duration_ms`: wall-clock time for the call.
- `data`: the payload. Present on success, and the same type with or without pagination.
- `partial`: `true` when the answer is incomplete. Omitted on complete results.
- `warnings`: optional non-fatal advisories.
- `next_cursor`: token for the next page. Omitted on the last page.
- `error`: `{code, message, next_step, remediation?}` on failure. `code` is stable and
  snake_case. `next_step` holds `retryable`, `retry_after_seconds?`, `next_call?`
  (`{tool, args, argv}`) and `human_action?`.

Notes:
- List and search rows default to essential fields. `--fields a,b,c` picks keys,
  `--fields all` returns whole rows, and a field no row has adds a warning.
- `notes show`: `data` carries `plainText` instead of the HTML `body`. Fields: `id, title,
  plainText, folder, modifiedAt`.
- Action results (create/edit/delete/complete/send/move/mark): `data` is the compact
  `{success, action, details}` object.
