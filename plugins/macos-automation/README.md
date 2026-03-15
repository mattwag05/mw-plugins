# macos-automation

Teach Claude how to automate Apple's native macOS apps (Mail, Calendar, Notes, Reminders) using AppleScript and JXA (JavaScript for Automation).

## Overview

This plugin provides comprehensive knowledge skills that give Claude expertise in macOS automation. When you describe an automation intent (e.g., "check my unread emails", "create a calendar event"), Claude automatically understands the patterns and builds working solutions.

## Components

### Skills

1. **macos-automation-core** - Foundation skill covering:
   - JXA vs AppleScript comparison
   - TypeScript/Bun integration patterns
   - Permission requirements
   - Error handling

2. **mail-automation** - Apple Mail automation:
   - Reading inbox and mailboxes
   - Creating drafts and sending
   - Searching and filtering messages
   - Managing accounts

3. **calendar-automation** - Calendar.app automation:
   - Reading events and calendars
   - Creating and modifying events
   - Searching by date/title
   - EventKit limitations

4. **notes-automation** - Notes.app automation:
   - Reading and searching notes
   - Creating notes
   - Accessing folders
   - Known limitations

5. **reminders-automation** - Reminders.app automation:
   - Swift CLI pattern (EventKit required)
   - Why JXA is insufficient
   - Building and using Swift CLIs
   - TypeScript integration

### Agent

- **automation-builder** - Proactive agent that triggers when you describe automation intent. Analyzes requirements, loads relevant skills, and builds working automations using JXA or Swift CLI patterns.

## Usage

The plugin activates automatically when you mention macOS automation tasks:

```
"I need to check my unread emails and summarize them"
→ mail-automation skill loads, creates JXA solution

"Can you show my calendar for today?"
→ calendar-automation skill loads, builds Calendar.app query

"Help me create a daily briefing with reminders and calendar"
→ automation-builder agent activates, combines multiple patterns
```

## Prerequisites

- **macOS** (Monterey or later recommended)
- **Bun** runtime (for TypeScript examples)
- **System Permissions** - Grant automation access in System Settings → Privacy & Security → Automation

## Key Patterns

### JXA Preferred Over AppleScript

This plugin teaches JXA (JavaScript for Automation) as the primary automation language because:
- JSON output (easy to parse)
- Modern JavaScript syntax
- Better TypeScript integration
- Same capabilities as AppleScript

### TypeScript Wrapper Pattern

All skills teach the `runJXA<T>()` wrapper pattern for type-safe automation:

```typescript
async function runJXA<T>(script: string): Promise<T> {
  const proc = Bun.spawn(['osascript', '-l', 'JavaScript', '-e', script], {
    stdout: 'pipe',
    stderr: 'pipe',
  })
  // Parse JSON output
}
```

### Swift CLI for Reminders

Reminders.app requires EventKit for full functionality (AppleScript/JXA support is too limited). The reminders-automation skill teaches how to build Swift CLIs that integrate with TypeScript.

## Examples

Each skill includes working code examples in `examples/` directories:
- TypeScript wrappers for each app
- Standalone JXA scripts
- Swift CLI for Reminders
- Integration patterns

## Testing

Test the plugin with automation queries:

```bash
# Check JXA access
osascript -l JavaScript -e 'Application("Mail").inbox().unreadCount()'

# Verify plugin loaded
cc --plugin-dir ~/.claude/plugins/macos-automation
# Then ask: "How do I automate Apple Mail?"
```

## Troubleshooting

**"Application isn't running" errors:**
- Ensure the target app (Mail, Calendar, Notes) is running

**Permission denied:**
- Check System Settings → Privacy & Security → Automation
- Grant Terminal/Claude Code access to control the app

**Reminders not working:**
- Grant Reminders access in Privacy & Security
- Use Swift CLI pattern (JXA is insufficient)

## Development

This plugin follows Claude Code plugin-dev best practices:
- Progressive disclosure (lean SKILL.md → detailed references/)
- Third-person skill descriptions with trigger phrases
- Working examples in all skills
- TypeScript-first integration patterns

## License

MIT
