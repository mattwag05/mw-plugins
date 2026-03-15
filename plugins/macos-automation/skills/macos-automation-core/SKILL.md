---
name: macos-automation-core
description: This skill should be used when the user asks to "automate macOS", "use AppleScript", "write JXA", "automate Mac apps", "script Apple applications", "use osascript", "run JavaScript for Automation", or needs guidance on macOS automation fundamentals, TypeScript/Bun integration patterns, or choosing between AppleScript and JXA.
version: 1.0.0
---

# macOS Automation Core

Foundation skill for automating Apple's native macOS applications using AppleScript and JXA (JavaScript for Automation).

## Overview

macOS provides two powerful automation languages for controlling native applications:

1. **JXA (JavaScript for Automation)** - Modern JavaScript syntax with JSON output ⭐ RECOMMENDED
2. **AppleScript** - Traditional AppleScript language with natural-language-like syntax

Both provide full access to application scripting dictionaries, enabling programmatic control of Mail, Calendar, Notes, Reminders, Finder, Safari, and more.

## When to Use

Use this knowledge when:
- Automating native macOS applications (Mail, Calendar, Notes, etc.)
- Building TypeScript/JavaScript tools that integrate with Apple apps
- Replacing manual workflows with scripts
- Creating cross-app automations (e.g., email based on calendar)

## Key Concepts

### JXA vs AppleScript Comparison

| Feature | JXA | AppleScript |
|---------|-----|-------------|
| Syntax | Modern JavaScript | Natural language-like |
| Output format | JSON (easy to parse) | Plain text |
| TypeScript integration | Excellent | Requires parsing |
| Learning curve | Low (if familiar with JS) | Medium |
| Documentation | Community-driven | Extensive Apple docs |
| **Recommendation** | ✅ Preferred | Use when needed |

**When to choose JXA:**
- Building TypeScript/Bun applications (structured JSON output)
- Modern development workflows
- Type-safe integration needed
- JSON output simplifies parsing

**When to choose AppleScript:**
- Legacy scripts exist
- Specific Apple documentation uses AppleScript
- Natural language syntax preferred

### The runJXA Pattern

The recommended pattern for executing JXA from TypeScript:

```typescript
async function runJXA<T>(script: string): Promise<T> {
  const proc = Bun.spawn(['osascript', '-l', 'JavaScript', '-e', script], {
    stdout: 'pipe',
    stderr: 'pipe',
  })

  const output = await new Response(proc.stdout).text()
  const error = await new Response(proc.stderr).text()

  if (error && !error.includes('Warning')) {
    throw new Error(`JXA execution failed: ${error}`)
  }

  if (!output.trim()) {
    return [] as T
  }

  try {
    return JSON.parse(output)
  } catch (e) {
    throw new Error(`Failed to parse JXA output: ${output}`)
  }
}
```

**Key benefits:**
- Type-safe with generic `<T>`
- Automatic JSON parsing
- Error handling with clear messages
- Filters non-critical warnings

### Script Execution Patterns

**Execute JXA from command line:**
```bash
osascript -l JavaScript -e 'Application("Mail").inbox().unreadCount()'
```

**Execute JXA file:**
```bash
osascript -l JavaScript /path/to/script.js
```

**Execute AppleScript:**
```bash
osascript -e 'tell application "Mail" to count of (messages of inbox)'
```

**Execute AppleScript file:**
```bash
osascript /path/to/script.applescript
```

### JXA Script Structure

Basic JXA script pattern:

```javascript
#!/usr/bin/osascript -l JavaScript

function run() {
  const App = Application('Mail')  // Target application
  App.includeStandardAdditions = true  // Enable system events

  // Your automation logic here
  const unreadCount = App.inbox().unreadCount()

  // Return JSON for easy parsing
  return JSON.stringify({ unread: unreadCount })
}
```

**Important conventions:**
- Use `function run()` as entry point
- Enable `includeStandardAdditions` for system access
- Return JSON-serializable data
- Use `JSON.stringify()` for structured output

### Application Objects

Access applications by name:

```javascript
const Mail = Application('Mail')
const Calendar = Application('Calendar')
const Notes = Application('Notes')
const System = Application('System Events')
```

**Check if application is running:**

```javascript
const System = Application('System Events')
const isRunning = System.processes.byName('Mail').exists()
```

### Error Handling

**Common error patterns:**

```typescript
try {
  const result = await runJXA<T>(script)
  return result
} catch (error) {
  if (error instanceof Error && error.message.includes("isn't running")) {
    throw new Error('Application is not running. Please open it first.')
  }
  if (error.message.includes('permission')) {
    throw new Error('Automation permission denied. Check System Settings.')
  }
  throw error
}
```

**Common errors:**
- `"Application isn't running"` - Target app needs to be launched
- `"Not authorized"` / `"permission denied"` - Automation permissions not granted
- `"Can't get..."` - Property doesn't exist or wrong object type
- JSON parse errors - Script didn't return valid JSON

## Quick Reference

### Common Operations

| Task | JXA Pattern |
|------|-------------|
| Get application | `Application('AppName')` |
| Check if running | `Application('System Events').processes.byName('App').exists()` |
| Get property | `obj.propertyName()` |
| Call method | `obj.methodName(arg)` |
| Create object | `App.ObjectType({ prop: value })` |
| Get collection | `App.objects()` (returns array) |
| Filter collection | `objects.filter(predicate)` |
| Access by name | `objects.byName('name')` |

### Script Execution

| Command | Purpose |
|---------|---------|
| `osascript -l JavaScript -e 'code'` | Execute inline JXA |
| `osascript -l JavaScript script.js` | Execute JXA file |
| `osascript -e 'code'` | Execute inline AppleScript |
| `osascript script.applescript` | Execute AppleScript file |

### TypeScript Integration

| Pattern | Use Case |
|---------|----------|
| `runJXA<T>(script)` | Type-safe execution with JSON parsing |
| `Bun.spawn(['osascript', ...])` | Execute scripts with Bun runtime |
| `JSON.stringify(result)` | Return structured data from JXA |
| Generic types | Ensure type safety in wrappers |

## Permission Requirements

macOS requires explicit permission for apps to control other apps.

**Grant permissions:**
1. Open **System Settings**
2. Navigate to **Privacy & Security** → **Automation**
3. Find your terminal app (Terminal, iTerm, or Claude Code)
4. Enable checkboxes for apps you want to automate (Mail, Calendar, etc.)

**Check permissions programmatically:**

```javascript
// This will trigger permission dialog if not granted
const Mail = Application('Mail')
const inbox = Mail.inbox()  // Triggers permission prompt
```

**Permission denied error:**
```
Error: Not authorized to send Apple events to Mail.
```

**Solution:** Grant automation permission in System Settings.

For detailed troubleshooting, see `references/permissions-guide.md`.

## Advanced Patterns

### Escaping Strings

When embedding user data in scripts, escape special characters:

```typescript
function escapeJXA(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
}

const subject = escapeJXA(userInput)
const script = `App.create({ subject: "${subject}" })`
```

### Script Files vs Inline

**Use inline scripts** (via `-e`) for:
- Simple queries (< 10 lines)
- Dynamic content with variables
- Quick testing

**Use script files** for:
- Complex logic (> 20 lines)
- Reusable operations
- Version control
- Sharing between projects

### Debugging

**Enable verbose output:**
```bash
osascript -l JavaScript -s s script.js  # Print statements
```

**Print to console:**
```javascript
console.log('Debug:', variable)  // Shows in stderr
```

**Test accessibility:**
```bash
# Test if app is accessible
osascript -l JavaScript -e 'Application("Mail").version()'
```

## Performance Considerations

**DO: Access only needed properties**
```javascript
// Good - specific properties
const msg = messages[0]
const subject = msg.subject()
const sender = msg.sender()
```

**DON'T: Access all properties**
```javascript
// Slow - gets everything
const allProps = msg.properties()
```

**Batch operations efficiently:**
- Process in chunks for large datasets
- Avoid repeated app queries in loops
- Cache results when possible

## Additional Resources

- **applescript-vs-jxa.md** - Detailed syntax comparison with examples
- **permissions-guide.md** - Troubleshooting automation permissions
- **bun-integration.md** - Advanced TypeScript/Bun patterns

## Examples

- **run-jxa-wrapper.ts** - Complete TypeScript wrapper implementation
- **run-applescript.ts** - AppleScript execution variant

## Next Steps

Load app-specific skills for detailed automation patterns:
- **mail-automation** - Automate Apple Mail
- **calendar-automation** - Automate Calendar.app
- **notes-automation** - Automate Notes.app
- **reminders-automation** - Automate Reminders (Swift CLI pattern)
