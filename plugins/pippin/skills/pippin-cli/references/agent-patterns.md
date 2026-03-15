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

## Error Handling Pattern

All action results return `{success: bool, action: string, details: {}}`. Check `success` before proceeding:

```bash
result=$(pippin reminders complete <id> --format agent)
# result: {"success":true,"action":"complete","details":{"id":"..."}}

# In a shell script:
if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d['success'] else 1)"; then
  echo "Completed successfully"
else
  echo "Failed: $result"
fi
```
