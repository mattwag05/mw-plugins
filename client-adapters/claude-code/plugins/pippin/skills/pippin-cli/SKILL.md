---
name: pippin-cli
description: Use Pippin through MCP or its command-line interface for Apple mail, calendar, reminders, contacts, notes, memos, messages, audio, browser work, permissions, and diagnostics.
metadata:
  version: "1.4.0"
---

# Pippin CLI skill

`pippin` is a macOS CLI that automates Apple's native apps (Mail, Calendar, Reminders,
Notes, Contacts, Voice Memos, Messages) plus audio and browser. It is built for agents:
every command speaks a stable, versioned JSON envelope under `--format agent`.

**Current state:** stable **v0.33.0** (`pippin --version` to confirm), exposing **45 MCP
tools** (mail, calendar, reminders, contacts, notes, memos, messages, status, doctor,
agent-info, …). The pippin MCP server is attached for both the **[agent-runtime]/[agent] gateway**
(stdio, pointed at `~/.local/bin/pippin mcp-server`) and **Claude Cowork** (via the
`pippin@mw-plugins` plugin's generated MCP configuration). Any agent *without* the MCP attached falls back
to the CLI: see "How to call pippin" below.

## Trigger phrases

Use this skill when the user asks to:
- Check mail / read email / search inbox / send mail
- Check calendar / list events / what's on my schedule / create an event
- Read reminders / create a reminder / complete a task
- Search notes / create a note / read a note
- List or search contacts
- Transcribe audio / voice memos / list recordings
- Browse the web / open a URL / take a screenshot
- Use pippin / Apple app automation

## How to call pippin

Two equivalent surfaces: both produce the same agent JSON, because the MCP server is a
thin wrapper that shells out to the CLI. Everything in this skill (commands, envelope,
gotchas) applies identically to both.

1. **MCP tools** (`mail_list`, `calendar_today`, `reminders_create`, `status`, …) when a
   pippin MCP server is attached. **Prefer these when available**: no shell quoting, and
   the host has already resolved the binary path and TCC identity for you.
2. **CLI fallback**: when no pippin MCP server is attached ([agent-runtime]/[agent] and Claude Cowork
   have it; a bare Claude Code session, a scheduled task, or any other agent may not), or
   when an MCP tool errors and you want to retry/diagnose at the shell, call the CLI
   directly. **Invoke the stable path explicitly:**

   ```bash
   ~/.local/bin/pippin <area> <verb> … --format agent
   ```

   `~/.local/bin/pippin` is the TCC-granted binary (see Permissions below): agents and
   scheduled tasks should always use this path, **not** the brew symlink
   `/opt/homebrew/bin/pippin`, whose grant is lost on every `brew upgrade`. Bare `pippin`
   on PATH resolves to the stable copy too, but spelling out the absolute path removes any
   doubt about which binary (and which grant) you're invoking.

## Use these habits every time (efficiency)

These are the difference between fast, cheap calls and slow, token-heavy ones:

1. **Always pass `--format agent`** when you (not a human) consume the output. Compact
   JSON in a versioned envelope. Never parse `text` output.
2. **Project with `--fields`** to return only the keys you need: universal on every
   structured command, including `mail list/search/activity`, `calendar events/search/
   today`, `reminders list/search`, `notes list/search`, `contacts list/search`.
   `pippin mail list --limit 20 --fields id,subject,from --format agent` is far cheaper
   than the full payload.
3. **Bound the work**: pass `--limit` and the narrowest filters you can (`--account`,
   `--mailbox`, `--folder`, `--after/--before`, `--range`). Broad/unbounded queries are
   what hit soft timeouts.
4. **Prefer narrow commands over the firehose.** `pippin status` gathers every subsystem;
   if you only need mail, call `pippin mail list`. Narrow calls are faster and never
   partial.
5. **Run independent reads in parallel** (e.g. mail + calendar + reminders for a briefing),
   then process together.

## Output: the agent envelope (v1)

Every `--format agent` response is wrapped in a versioned envelope. **Parse `.data`, not
the top level.**

Success:
```json
{"v":1,"status":"ok","duration_ms":142,"data":<payload>,"warnings":["…"]?}
```
Error:
```json
{"v":1,"status":"error","duration_ms":51,"error":{"code":"access_denied","message":"…","remediation":{…}}}
```

- The previous raw payload now lives under `data` unchanged: `jq '.data | length'`,
  `jq '.data[].id'`, etc.
- `warnings` (optional) carries non-fatal advisories such as partial-results notices.
- **Always branch on `status`** before reading `data`. On error, read `error.code`
  (stable, snake_case) and `error.remediation` for the fix.

### Partial results (soft timeout)

Long scans (mail, notes, full `status`) are bounded by a soft wall-clock cap. When a call
runs out of budget it returns **what it has so far** plus `status:"ok"` with a `warnings`
entry (and, for `status`, a top-level `timedOut:true` in `data`). Treat partial results as
incomplete, not empty: re-run with a narrower filter / smaller `--limit` for the rest.

### Exit codes

The process exit code mirrors `error.code`, so shells/agents can branch without parsing:
`0` ok · `2` usage · `3` not-found · `4` auth/permission/config · `5` tool/bridge ·
`7` timeout/rate-limit.

## Permissions & TCC: read this before automating from an agent

Apple privacy permissions (TCC) are the #1 cause of "it works in my terminal but not from
the agent" failures.

**The grant keys on Pippin's identity and binary path, not on the launcher.** As of
**v0.31.0** pippin re-execs itself "disclaimed" so it is its own macOS TCC *responsible
process*. macOS therefore keys Reminders/Calendar/Contacts/Automation/Full-Disk consent on
pippin's signed identity at its binary path, **regardless of which app launched it**
(Terminal, Codex, a background MCP gateway, launchd). Grant pippin once and it works under
every launcher.

Two consequences that bite agents:

- **Grants are per binary PATH (bare CLI, not a `.app`).** `/opt/homebrew/bin/pippin`
  resolves to a *versioned* `Cellar/<ver>/…` path, so a brew grant is **lost on every
  `brew upgrade`**. The durable, granted home is the **stable** `~/.local/bin/pippin`
  (a copied real file at a fixed path; the grant survives rebuilds). **Agents and
  scheduled tasks should invoke `~/.local/bin/pippin` explicitly**, never the brew symlink.
- **The prompt only appears in an interactive session.** `pippin permissions` (or
  `pippin init`) triggers every promptable permission in one pass, but only from a real
  TTY. Under MCP, `--format agent/json`, or a non-TTY pipe it **refuses to prompt** (an
  unanswerable dialog would just hang) and prints a read-only report instead, and EventKit
  commands fast-fail with `access_denied` rather than blocking.

**So the one-time setup for durable agent access:** run `pippin permissions` against
`~/.local/bin/pippin` **once in a Terminal** and approve the prompts. After that, that path
works from any launcher. (`make install` refreshes the binary at the same path without
losing the grant.)

- **Check state any time** without prompting: `pippin permissions --status --format agent`
  or `pippin doctor`: each integration reports `granted` / `not_determined` /
  `manual_required` + whether it's promptable.
- **Voice Memos and Messages need Full Disk Access**, which has *no* prompt: grant it
  manually in System Settings ▸ Privacy & Security ▸ Full Disk Access to the pippin binary,
  then relaunch.

When a structured call fails with `error.code == "access_denied"`, surface
`error.remediation` to the user verbatim: it names the exact System Settings pane and the
launcher to enable.

## Quick reference

```bash
# Mail (Mail.app must be running)
pippin mail accounts --format agent
pippin mail list [--account NAME] [--mailbox INBOX] [--unread] [--limit 20] [--fields id,subject,from] --format agent
pippin mail search <query> [--account NAME] [--after YYYY-MM-DD] [--body] [--limit 10] [--fields id,subject] --format agent
pippin mail activity [--since YYYY-MM-DD] [--fields id,from] --format agent
pippin mail show <id> --format agent              # id is account||mailbox||numericId
pippin mail send --to <email> --subject <s> --body <t>
pippin mail mark <id> --read|--unread
pippin mail move <id> --to <mailbox>              # Trash, Junk, Sent, Drafts
pippin mail apply-rules [--account NAME] [--live] # bulk move/mark by rule; PREVIEWS unless --live

# Calendar
pippin calendar today|remaining|upcoming [--fields id,title,startDate] --format agent
pippin calendar events [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--range today|week|month] --format agent
pippin calendar search --query <q> [--fields id,title] --format agent
pippin calendar create --title <t> --start <date> [--end <date>] [--notes <n>] [--alert 15m]
pippin calendar show <id> --format agent

# Reminders   (note: title is POSITIONAL; --list takes an EventKit ID from `reminders lists`)
pippin reminders list [--completed] [--priority high|medium|low] [--fields id,title,dueDate] --format agent
pippin reminders create <title> [--due YYYY-MM-DD] [--priority high|medium|low] [--notes <n>]
pippin reminders complete <id>
pippin reminders search <query> --format agent

# Notes
pippin notes list [--folder NAME] [--limit 50] [--fields id,title] --format agent
pippin notes show <id> --format agent             # agent mode returns plainText, not HTML body
pippin notes search <query> --format agent
pippin notes create <title> [--body <text>] [--folder NAME]
pippin notes edit <id> [--body <text>] [--append]

# Contacts   (--fields here selects which CN keys are *fetched* — server-side)
pippin contacts list [--group NAME] [--fields id,fullName,emails] --format agent
pippin contacts search <query> --format agent
pippin contacts show <id> --format agent

# Voice Memos / Messages (require Full Disk Access)
pippin memos list [--since YYYY-MM-DD] [--limit 20] --format agent
pippin memos transcribe <id>

# Audio / Browser (gated behind PIPPIN_EXPERIMENTAL=1)
pippin audio speak <text> [--voice af_heart] [--output-file path.wav]
pippin browser open <url> --format agent ; pippin browser snapshot --format agent

# System / diagnostics
pippin status --format agent                       # whole-system dashboard (broad — may be partial)
pippin permissions [--status] [--format agent]     # grant (interactive) or report TCC state
pippin doctor                                      # permissions + dependency health
pippin agent-info --format agent                   # capability/feature probe
pippin --version
```

## Critical gotchas

1. **Mail.app must be open** for any `pippin mail` command: `open -a Mail && sleep 4`.
2. **Locked screen blocks all GUI automation** (pippin, osascript, screencapture). Check
   idle: `ioreg -n IOHIDSystem | grep HIDIdleTime` (÷ 1e9 for seconds).
3. **Compound mail IDs** use `account||mailbox||numericId`. Always pass the full ID to
   `show`/`mark`/`move`.
4. **Reminders/Calendar flag footguns**: `reminders create`'s title is *positional*;
   `reminders --list` / `calendar create --calendar` take EventKit **IDs** (from
   `reminders lists` / `calendar list`), not names. Filter calendar events by name with
   `--calendar-name`.
5. **Permissions**: see the TCC section above: most "denied from the agent" issues are the
   launcher/responsible-process mismatch, not a pippin bug.
6. **Audio/browser are experimental**: hidden unless `PIPPIN_EXPERIMENTAL=1`; require
   mlx-audio / node respectively (`pippin doctor` checks).

## References

- Full command syntax: `references/commands.md`
- Output envelope & formats: `references/output-formats.md`
- Multi-step workflow patterns: `references/agent-patterns.md`
