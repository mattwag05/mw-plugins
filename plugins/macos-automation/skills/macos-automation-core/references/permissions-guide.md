# macOS Automation Permissions Guide

Comprehensive guide to understanding and troubleshooting automation permissions on macOS.

## Overview

macOS requires explicit user permission for applications to control other applications through AppleScript or JXA. This security feature prevents malicious scripts from accessing sensitive data or performing unwanted actions.

## Permission System

### Automation Privacy Controls

Starting with macOS Mojave (10.14), Apple introduced strict privacy controls for automation:

**Location:** System Settings → Privacy & Security → Automation

This panel shows:
- Which apps want to control other apps
- Checkboxes to grant/revoke permissions per app pair

Example:
```
Terminal
  ☑ Mail
  ☑ Calendar
  ☐ Notes
```

This means Terminal can control Mail and Calendar, but not Notes.

## Common Error Messages

### "Not authorized to send Apple events"

**Full error:**
```
Error: Not authorized to send Apple events to Mail.
```

**Meaning:** Your terminal/app doesn't have permission to control the target app.

**Solution:**
1. Open System Settings
2. Go to Privacy & Security → Automation
3. Find your terminal app (Terminal, iTerm, Claude Code, etc.)
4. Enable the checkbox for the target app (Mail, Calendar, etc.)

### "Application isn't running"

**Full error:**
```
Error: Application("Mail") isn't running
```

**Meaning:** The target application needs to be launched before automation can access it.

**Solution:**
```typescript
// Check if running first
const System = Application('System Events')
if (!System.processes.byName('Mail').exists()) {
    throw new Error('Please open Mail.app first')
}
```

Or launch it:
```javascript
const Mail = Application('Mail')
Mail.launch()  // Launches Mail if not running
```

### "Can't get object"

**Full error:**
```
Error: Can't get object.
```

**Meaning:** Trying to access an object that doesn't exist or you don't have permission for.

**Common causes:**
- Mailbox doesn't exist
- Message index out of range
- Application not fully initialized

**Solution:** Add existence checks:
```javascript
const Mail = Application('Mail')
const messages = Mail.inbox().messages()
if (messages.length > 0) {
    const first = messages[0]
    // Safe to access
}
```

## Permission Flow

### Initial Access Attempt

When your script first tries to control an app:

1. **macOS shows permission dialog:**
   ```
   "Terminal" would like to control "Mail".
   This will allow Terminal to control Mail and access
   its documents and data.

   [Don't Allow]  [OK]
   ```

2. **If you click OK:** Permission granted, script proceeds
3. **If you click Don't Allow:** Permission denied, script fails

### Persistent Permissions

Once granted, permissions persist until:
- Manually revoked in System Settings
- App is reinstalled
- System reset

## Granting Permissions

### Method 1: Automatic (Recommended)

Run your automation script - macOS will prompt automatically:

```bash
osascript -l JavaScript -e 'Application("Mail").inbox().unreadCount()'
```

If not authorized, you'll see the permission dialog.

### Method 2: Manual Configuration

1. Open **System Settings**
2. Click **Privacy & Security**
3. Scroll down and click **Automation**
4. Find your terminal/app in the list
5. Enable checkboxes for apps you want to control

### Method 3: System Events Approach

Some operations use System Events as intermediary:

```javascript
// This may trigger a different permission request
const System = Application('System Events')
System.processes.byName('Mail').exists()
```

## Special Cases

### Full Disk Access

Some operations may require **Full Disk Access** in addition to automation permissions:

**Location:** System Settings → Privacy & Security → Full Disk Access

**When needed:**
- Accessing certain user directories
- Reading specific Mail.app database files
- Some Finder operations

**Grant access:**
1. Navigate to Full Disk Access settings
2. Click the **+** button
3. Add your terminal app
4. Restart terminal

### Reminders and Calendar (EventKit)

Reminders and Calendar use **additional permissions**:

**Reminders access:**
- System Settings → Privacy & Security → Reminders
- Must grant separately from automation

**Calendar access:**
- System Settings → Privacy & Security → Calendars
- Must grant separately from automation

**In Swift CLI:**
```swift
let eventStore = EKEventStore()
let granted = try await eventStore.requestFullAccessToReminders()
if !granted {
    print("Reminders access denied")
}
```

### Accessibility Permission

Some advanced operations require **Accessibility** permission:

**Location:** System Settings → Privacy & Security → Accessibility

**When needed:**
- UI scripting (clicking buttons, reading window contents)
- Keystroke simulation
- Advanced Finder operations

**Not typically needed for basic app scripting.**

## Troubleshooting

### Permission Dialog Not Appearing

**Problem:** Running script but no permission dialog shows.

**Causes:**
- Permission already denied (check System Settings)
- Script has syntax error (never reaches app access)
- Using wrong application name

**Solutions:**
```bash
# Verify app name
osascript -l JavaScript -e 'Application("Mail").name()'

# Check for syntax errors
osascript -l JavaScript -e 'console.log("test")'

# Check System Settings → Automation for denied permissions
```

### Permission Granted But Still Failing

**Problem:** Checkbox is enabled in System Settings but script fails.

**Solutions:**

1. **Restart terminal:**
   ```bash
   # Close and reopen terminal application
   ```

2. **Check app is running:**
   ```bash
   osascript -l JavaScript -e 'Application("System Events").processes.byName("Mail").exists()'
   ```

3. **Verify app name:**
   ```bash
   # Get correct app name
   osascript -l JavaScript -e 'Application("Mail").name()'
   ```

4. **Reset permissions (last resort):**
   ```bash
   # Remove terminal from Automation list in System Settings
   # Re-run script to trigger new permission request
   ```

### Different Terminal Apps

Each terminal application needs its own permissions:

| Terminal App | Appears in Settings As |
|--------------|------------------------|
| Terminal.app | Terminal |
| iTerm2 | iTerm |
| VSCode terminal | Code |
| Bun (direct) | bun |

If you switch terminal apps, you need to grant permissions again.

### Claude Code Specific

When running scripts through Claude Code:

1. Claude Code appears as "Claude" in Automation settings
2. Grant Claude permission to control target apps
3. May need to restart Claude Code after granting

## Best Practices

### Graceful Permission Handling

```typescript
async function safeMailAccess() {
    try {
        const Mail = Application('Mail')
        const count = Mail.inbox().unreadCount()
        return count
    } catch (error) {
        if (error.message.includes('Not authorized')) {
            throw new Error(
                'Permission denied. Please grant automation access:\n' +
                'System Settings → Privacy & Security → Automation → [Your Terminal] → Mail'
            )
        }
        if (error.message.includes("isn't running")) {
            throw new Error('Please open Mail.app first')
        }
        throw error
    }
}
```

### Check Before Running

```typescript
async function checkMailPermissions(): Promise<boolean> {
    try {
        const Mail = Application('Mail')
        Mail.inbox()  // This will fail if no permission
        return true
    } catch {
        return false
    }
}

// Usage
if (!await checkMailPermissions()) {
    console.log('Please grant Mail automation permission')
    return
}
```

### User Instructions

When distributing scripts, include permission instructions:

```markdown
## Setup

1. Open System Settings
2. Navigate to Privacy & Security → Automation
3. Find your terminal app in the list
4. Enable checkboxes for:
   - Mail
   - Calendar
   - Notes
5. Restart your terminal
6. Run the script again
```

## Security Considerations

### Why Permissions Matter

Automation access allows scripts to:
- Read all email content and metadata
- Send emails on your behalf
- Access calendar events
- Read and write notes
- Access file system (with Full Disk Access)

**Only grant to trusted applications and scripts.**

### Revoking Access

To remove automation permissions:

1. System Settings → Privacy & Security → Automation
2. Find the app
3. Uncheck boxes for apps you want to revoke
4. Or remove the app entirely from the list

### Sandboxed Apps

Some App Store apps are sandboxed and **cannot** use automation:
- Cannot be controlled via AppleScript/JXA
- Cannot control other apps
- Sandboxing restrictions prevent automation

**Solution:** Use non-sandboxed versions or alternatives.

## Testing Permissions

### Quick Test Script

```bash
#!/bin/bash
# Test automation permissions

echo "Testing Mail automation..."
osascript -l JavaScript -e 'Application("Mail").version()' 2>&1

echo "Testing Calendar automation..."
osascript -l JavaScript -e 'Application("Calendar").version()' 2>&1

echo "Testing Notes automation..."
osascript -l JavaScript -e 'Application("Notes").version()' 2>&1
```

**Expected output (if permitted):**
```
Testing Mail automation...
16.0

Testing Calendar automation...
16.0

Testing Notes automation...
14.0
```

**Error output (if denied):**
```
Error: Not authorized to send Apple events to Mail.
```

## Summary

**Key points:**
- macOS requires explicit permission for app-to-app control
- Grant permissions in System Settings → Privacy & Security → Automation
- Different terminal apps need separate permissions
- Permission dialogs appear on first access attempt
- Check for "Not authorized" errors and guide users to settings
- Test permissions before running complex automation

**Default recommendation:** Include permission checks and clear error messages in all automation scripts.
