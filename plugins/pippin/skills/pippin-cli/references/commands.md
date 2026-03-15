# Pippin CLI — Command Reference

Binary: `/opt/homebrew/bin/pippin` (v0.11.0)

---

## mail

Interact with Apple Mail via JXA automation. **Mail.app must be open.**

```bash
pippin mail accounts
# Lists all configured accounts: name, email

pippin mail mailboxes [--account NAME]
# Lists mailboxes per account with message/unread counts

pippin mail list [--account NAME] [--mailbox INBOX] [--unread] [--limit 20] [--page 1]
# List messages, newest first. Compound ID format: account||mailbox||numericId

pippin mail search <query> [--account NAME] [--mailbox NAME] [--body] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--to EMAIL] [--verbose] [--limit 10] [--page 1]
# Search by subject/sender. --body searches body content (slower).

pippin mail show <id>
pippin mail show --subject <query>
# Show full message details including body, attachments

pippin mail mark <id> --read | --unread [--dry-run]
# Mark message read/unread

pippin mail move <id> --to <mailbox> [--dry-run]
# Move message to another mailbox. Mailbox aliases: Trash, Junk, Sent, Drafts

pippin mail send --to <email> [--to <email>] --subject <subj> --body <text> [--cc <email>] [--bcc <email>] [--from NAME] [--attach <path>] [--dry-run]
# Send email. --to is repeatable.

pippin mail reply <id> --body <text> [--to <email>] [--cc <email>] [--from NAME] [--attach <path>] [--dry-run]
# Reply to a message.

pippin mail forward <id> --to <email> [--body <text>] [--cc <email>] [--dry-run]
# Forward a message.

pippin mail attachments <id> [--save-dir <path>]
# List (and optionally save) attachments from a message.
```

---

## memos

Interact with Voice Memos via GRDB SQLite access (no app required).

```bash
pippin memos list [--since YYYY-MM-DD] [--limit 20]
# List recordings, newest first.

pippin memos info <id>
# Full metadata for a single recording (UUID prefix OK).

pippin memos export <id> | --all --output <dir> [--transcribe] [--format txt|srt|markdown|rtf]
# Copy recording(s) to a directory.

pippin memos transcribe <id> | --all [--output <dir>]
# Transcribe audio to text using parakeet-mlx or SFSpeechRecognizer.

pippin memos delete <id> --force
# Delete memo (DB row + audio file). Irreversible.

pippin memos templates
# List built-in summarization prompt templates.

pippin memos summarize <id> [--template <name>] [--provider ollama|claude] [--model <name>]
# AI-powered memo summarization.
```

---

## calendar

Interact with Apple Calendar via EventKit.

```bash
pippin calendar list [--type local|calDAV|exchange|subscription|birthday]
# List all calendars.

pippin calendar events [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--range today|today+N|week|month] [--calendar ID] [--calendar-name NAME] [--limit 50] [--type TYPE] [--fields title,startDate,...]
# List events. Defaults to today.

pippin calendar today [--fields title,startDate,...]
# Events for today.

pippin calendar remaining [--fields title,startDate,...]
# Events from now until end of today.

pippin calendar upcoming [--fields title,startDate,...]
# Events for the next 7 days.

pippin calendar show <id>
# Full event details by ID or prefix.

pippin calendar create --title <t> --start <YYYY-MM-DD|ISO8601> [--end <date>] [--calendar ID] [--location <l>] [--notes <n>] [--all-day] [--url <u>] [--alert 15m|1h|2d]
# Create a new event.

pippin calendar edit <id> [--title <t>] [--start <date>] [--end <date>] [--location <l>] [--notes <n>] [--alert OFFSET] [--span this|future]
# Edit an event.

pippin calendar delete <id> --force [--span this|future]
# Delete an event. --force required.

pippin calendar search --query <q> [--from <date>] [--to <date>] [--calendar-name NAME] [--limit 50]
# Search events by title, notes, or location.

pippin calendar smart-create <description> [--provider ollama|claude] [--calendar ID] [--dry-run]
# Natural language event creation using AI.

pippin calendar agenda [--days 1-7] [--provider ollama|claude]
# AI-generated briefing of upcoming events.
```

---

## contacts

Interact with Apple Contacts via CNContactStore.

```bash
pippin contacts list [--group NAME] [--fields id,fullName,emails,...]
# List all contacts.

pippin contacts search <query> [--email] [--fields id,fullName,...]
# Search by name (default) or email (--email flag).

pippin contacts show <identifier>
# Full contact details by ID.

pippin contacts groups
# List contact groups with member count.
```

---

## reminders

Interact with Apple Reminders via EventKit.

```bash
pippin reminders lists
# List all reminder lists.

pippin reminders list [--list ID] [--completed] [--due-before YYYY-MM-DD] [--due-after YYYY-MM-DD] [--priority high|medium|low|none] [--limit 50] [--fields id,title,dueDate,...]
# List reminders. Defaults to incomplete.

pippin reminders show <id>
# Full reminder details by ID or prefix.

pippin reminders create <title> [--list ID] [--due YYYY-MM-DD|ISO8601] [--priority high|medium|low|none] [--notes <n>] [--url <u>]
# Create a reminder.

pippin reminders edit <id> [--title <t>] [--due <date>] [--priority <p>] [--notes <n>] [--list ID]
# Edit a reminder.

pippin reminders complete <id>
# Mark reminder as completed.

pippin reminders delete <id> --force
# Delete a reminder. --force required.

pippin reminders search <query> [--list ID] [--completed] [--limit 50] [--fields id,title,...]
# Search reminders by title and notes.
```

---

## notes

Interact with Apple Notes via JXA automation.

```bash
pippin notes list [--folder NAME] [--limit 50] [--fields id,title,folder,...]
# List notes, newest first.

pippin notes show <id>
# Full note details (id, title, body HTML, plainText, folder, dates).
# In --format agent mode: returns plainText instead of HTML body.

pippin notes search <query> [--folder NAME] [--limit 50] [--fields id,title,...]
# Search by title or body.

pippin notes folders
# List all Notes folders.

pippin notes create <title> [--body <text>] [--folder NAME]
# Create a new note.

pippin notes edit <id> [--title <t>] [--body <text>] [--append]
# Edit a note. --append appends body instead of replacing.

pippin notes delete <id> --force
# Move note to Recently Deleted. --force required.
```

---

## audio

Text-to-speech and speech-to-text via mlx-audio Python subprocess.

```bash
pippin audio speak <text> [--model kokoro] [--voice af_heart] [--output-file path.wav]
# Synthesize speech. Plays via system audio if no --output-file.

pippin audio transcribe <file> [--model parakeet] [--format text|srt|json]
# Transcribe an audio file to text.

pippin audio voices [--model kokoro]
# List available TTS voices.

pippin audio models
# List available STT/TTS models.
```

Note: mlx-audio must be installed: `pip install mlx-audio`

---

## browser

Control a headless WebKit browser via Playwright.

```bash
pippin browser open <url> [--session-dir PATH]
# Open a URL, return page info (url, title, status).

pippin browser snapshot [--session-dir PATH]
# Take an accessibility tree snapshot — returns interactive elements with @ref IDs.

pippin browser screenshot [--file screenshot.png] [--session-dir PATH]
# Save a screenshot.

pippin browser click <ref> [--session-dir PATH]
# Click element by @ref ID from snapshot.

pippin browser fill <ref> <value> [--session-dir PATH]
# Fill an input by @ref ID.

pippin browser scroll <up|down|left|right> [--session-dir PATH]
# Scroll the page.

pippin browser tabs [--session-dir PATH]
# List all open tabs.

pippin browser close [--session-dir PATH]
# Close the browser session.

pippin browser fetch <url>
# HTTP fetch (no browser required) — returns raw content.
```

---

## Other Commands

```bash
pippin doctor
# Check all permissions, dependencies, and required apps.

pippin init
# Guided first-run setup.

pippin completions [--shell zsh|bash|fish]
# Generate shell completions.

pippin --version
# Print current version.
```
