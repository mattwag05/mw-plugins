# Pippin CLI Skill

## Trigger Phrases

Use this skill when the user asks to:
- Check mail / read email / search inbox
- Check calendar / list events / what's on my schedule
- Read reminders / create a reminder / complete a task
- Search notes / create a note / read a note
- List contacts / search contacts
- Browse the web / open a URL / take a screenshot
- Transcribe audio / voice memos / list recordings
- Use pippin / Apple app automation

## Quick Reference

```bash
# Mail
pippin mail accounts
pippin mail list [--mailbox INBOX] [--unread] [--limit 20] [--format agent]
pippin mail search <query> [--account NAME] [--after YYYY-MM-DD] [--limit 10] [--format agent]
pippin mail show <id> [--format agent]
pippin mail send --to <email> --subject <subj> --body <text>
pippin mail mark <id> --read | --unread
pippin mail move <id> --to <mailbox>

# Calendar
pippin calendar today [--format agent]
pippin calendar remaining [--format agent]
pippin calendar upcoming [--format agent]
pippin calendar events [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--range today|week|month] [--format agent]
pippin calendar show <id> [--format agent]
pippin calendar create --title <t> --start <date> [--end <date>] [--notes <n>]
pippin calendar search --query <q> [--format agent]

# Reminders
pippin reminders list [--completed] [--priority high|medium|low] [--format agent]
pippin reminders show <id> [--format agent]
pippin reminders create <title> [--due YYYY-MM-DD] [--priority high|medium|low]
pippin reminders complete <id>
pippin reminders search <query> [--format agent]

# Notes
pippin notes list [--folder NAME] [--limit 50] [--format agent]
pippin notes show <id> [--format agent]
pippin notes search <query> [--format agent]
pippin notes create <title> [--body <text>] [--folder NAME]
pippin notes edit <id> [--body <text>] [--append]

# Contacts
pippin contacts list [--group NAME] [--format agent]
pippin contacts search <query> [--format agent]
pippin contacts show <id> [--format agent]

# Voice Memos
pippin memos list [--since YYYY-MM-DD] [--limit 20] [--format agent]
pippin memos transcribe <id>

# Audio (mlx-audio)
pippin audio speak <text> [--voice af_heart] [--output-file path.wav]
pippin audio transcribe <file> [--format text|srt|json]

# Browser
pippin browser open <url> [--format agent]
pippin browser snapshot [--format agent]
pippin browser click <ref>
pippin browser fill <ref> <value>
pippin browser fetch <url>

# Diagnostics
pippin doctor
pippin --version
```

## Output Formats

- `--format text` (default): Human-readable tables and cards
- `--format json`: Pretty-printed JSON with all fields
- `--format agent`: Compact JSON (no whitespace) — use this when Claude is the consumer

**Always use `--format agent` when programmatically processing output.**

## Critical Gotchas

1. **Mail.app must be open**: All `pippin mail` commands fail/timeout otherwise.
   ```bash
   open -a Mail && sleep 4
   ```

2. **Locked screen blocks all GUI automation**: pippin, osascript, screencapture all fail when the Mac is locked. Check idle time:
   ```bash
   ioreg -n IOHIDSystem | grep HIDIdleTime  # divide by 1e9 for seconds
   ```

3. **Mail accounts**: `iCloud`, `Exchange`, `Yahoo!`, `Google`, `mattwag0766@gmail.com` — verify with `pippin mail accounts` if any call fails.

4. **Compound message IDs**: Mail IDs are `account||mailbox||numericId` — always pass the full ID to `show`, `mark`, `move`.

5. **Notes/Calendar/Reminders**: Require TCC permissions. `pippin doctor` checks all permissions.

6. **mlx-audio not installed by default**: `pippin audio` commands fail if mlx-audio is absent. Check with `pippin doctor`.

## References

- Full command syntax: `references/commands.md`
- Output format details: `references/output-formats.md`
- Multi-step workflow patterns: `references/agent-patterns.md`
