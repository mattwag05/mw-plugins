# Pippin Agent Workflow Patterns

Common multi-step workflows for Claude Code as the pippin consumer.

---

## Morning Briefing

Gather mail, calendar, and reminders in parallel for a daily summary.

```bash
# Ensure Mail.app is open first
open -a Mail && sleep 4

# Parallel gather (run all three, then process)
pippin mail list --unread --limit 10 --format agent
pippin calendar remaining --format agent
pippin reminders list --format agent
```

Process results: summarize unread mail count, list today's remaining events, list open reminders.

---

## Inbox Triage

Search for specific emails, read them, then act.

```bash
# Step 1: Search
pippin mail search "meeting request" --after 2026-03-08 --format agent

# Step 2: Read a specific message (use full compound ID from step 1)
pippin mail show "iCloud||INBOX||12345" --format agent

# Step 3: Act
pippin mail mark "iCloud||INBOX||12345" --read --format agent
pippin mail move "iCloud||INBOX||12345" --to Trash --format agent
```

---

## Note-Taking Workflow

Create a note, then verify it was created.

```bash
# Step 1: Create
pippin notes create "Meeting Notes Mar 10" --body "Discussed Q1 goals." --folder "Work" --format agent

# Step 2: Search to confirm (note IDs are returned in action result details)
pippin notes search "Meeting Notes Mar 10" --format agent

# Step 3: Append more content
pippin notes edit <id-from-step-2> --body "Action items: ..." --append --format agent
```

---

## Reminder Management

List, complete, and create reminders.

```bash
# Step 1: List open reminders
pippin reminders list --format agent

# Step 2: Complete one
pippin reminders complete <id> --format agent

# Step 3: Create a new one with a due date
pippin reminders create "Follow up with Alice" --due 2026-03-15 --priority high --format agent
```

---

## Calendar Planning

Check free time, create an event, verify it appears.

```bash
# Step 1: Check what's on the schedule
pippin calendar upcoming --format agent

# Step 2: Create an event
pippin calendar create \
  --title "1:1 with Bob" \
  --start "2026-03-12T14:00:00" \
  --end "2026-03-12T15:00:00" \
  --alert 15m \
  --format agent

# Step 3: Search for it to get the ID
pippin calendar search --query "1:1 with Bob" --format agent
```

---

## Browser Research Workflow

Open a page, snapshot it, interact with elements.

```bash
# Step 1: Open URL
pippin browser open "https://example.com" --format agent

# Step 2: Snapshot — get interactive elements with @ref IDs
pippin browser snapshot --format agent

# Step 3: Click a link or fill a form
pippin browser click "@ref3"
pippin browser fill "@ref7" "search query"

# Step 4: Snapshot again to see result
pippin browser snapshot --format agent

# Step 5: Fetch raw content (no browser needed for simple pages)
pippin browser fetch "https://example.com/api/data"
```

---

## Contact Lookup

Find a contact and get their email for sending mail.

```bash
# Step 1: Search contacts
pippin contacts search "Alice Smith" --format agent

# Step 2: Get full details
pippin contacts show <identifier> --format agent

# Step 3: Use email in mail send
pippin mail send \
  --to "alice@example.com" \
  --subject "Following up" \
  --body "Hi Alice, ..." \
  --format agent
```

---

## Error Handling Pattern (envelope v1)

Every `--format agent` response is an envelope: `{"v":1,"status":"ok|error","duration_ms":N,
"data":…}` or `{…,"status":"error","error":{"code","message","remediation"}}`. Branch on
`status`; the action payload (`{success, action, details}`) lives under `data` on success.

The process **exit code** already mirrors the error (`0` ok, `3` not-found, `4`
auth/permission, `5` bridge, `7` timeout), so the cheapest check is the exit code:

```bash
if pippin reminders complete <id> --format agent >/tmp/out.json; then
  echo "ok: $(jq -c '.data' /tmp/out.json)"
else
  code=$?                                  # 4 = permission, 3 = not-found, ...
  jq -r '.error | "\(.code): \(.message)"' /tmp/out.json
  jq -r '.error.remediation // empty' /tmp/out.json   # show the fix to the user
fi
```

Parsing the envelope directly:

```bash
result=$(pippin reminders complete <id> --format agent)
status=$(echo "$result" | jq -r '.status')
if [ "$status" = "ok" ]; then
  echo "Completed: $(echo "$result" | jq -c '.data')"
else
  # access_denied here is almost always the launcher/TCC mismatch — see SKILL.md.
  echo "Failed [$(echo "$result" | jq -r '.error.code')]: $(echo "$result" | jq -r '.error.message')"
fi
```

Common `error.code` values: `access_denied` (TCC — surface `.error.remediation`),
`not_found`, `timeout`, `usage`. A `status:"ok"` with a `warnings` entry means partial
results — re-run narrower for the rest.
