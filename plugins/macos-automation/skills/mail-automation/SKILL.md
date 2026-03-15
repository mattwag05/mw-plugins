---
name: mail-automation
description: This skill should be used when the user asks to "automate Apple Mail", "read emails programmatically", "create email drafts", "check unread count", "send email from Mail app", "access mailboxes", "search inbox", "filter messages", or mentions Mail.app automation, email scripting, or macOS email workflows.
version: 1.0.0
---

# Apple Mail Automation

Automate Apple Mail using JXA (JavaScript for Automation) for reading, composing, searching, and managing email programmatically.

## Overview

Apple Mail provides a complete scripting dictionary accessible via JXA, enabling full programmatic control of email operations. Use this skill to build email automation, daily briefings, email triage systems, and integration with other applications.

## Prerequisites

- **Mail.app** configured with at least one email account
- **Automation permissions** granted in System Settings → Privacy & Security → Automation
- **Mail.app running** (most operations require the app to be open)
- **macos-automation-core** loaded for `runJXA<T>()` pattern

## Core Capabilities

| Category | Operations | JXA Support |
|----------|------------|-------------|
| Reading | Access inbox/mailboxes, read properties, check status | ✅ Full |
| Composing | Create drafts, set recipients, add content | ✅ Full |
| Sending | Send messages programmatically | ✅ Full |
| Searching | Filter by date, status, sender, subject | ✅ Full |
| Accounts | List accounts, access properties | ✅ Full |
| Attachments | Read attachment metadata, access files | ✅ Full |

## Quick Reference

### Common Operations

| Task | JXA Pattern |
|------|-------------|
| Get unread count | `Mail.inbox().unreadCount()` |
| Get all messages | `Mail.inbox().messages()` |
| Filter unread | `messages.filter(m => !m.readStatus())` |
| Get subject | `message.subject()` |
| Get sender | `message.sender()` |
| Get date | `message.dateReceived()` |
| Get content | `message.content()` |
| Create draft | `Mail.OutgoingMessage({...})` |
| Add recipient | `msg.toRecipients.push(...)` |
| Send message | `msg.send()` |

### Mailbox Access

```javascript
const Mail = Application('Mail')

// Access inbox
const inbox = Mail.inbox()

// Access mailbox by name
const mailbox = Mail.mailboxes.byName('Archive')

// List all mailboxes
const allMailboxes = Mail.mailboxes()
```

## TypeScript Integration

Recommended pattern using type-safe wrapper:

```typescript
import { runJXA } from './jxa-runner'

interface Email {
  id: string
  subject: string
  sender: string
  date: string
  content: string
  read: boolean
}

async function getRecentEmails(limit: number = 10): Promise<Email[]> {
  const script = `
    const Mail = Application('Mail')
    const messages = Mail.inbox().messages()

    return JSON.stringify(
      messages.slice(0, ${limit}).map(msg => ({
        id: msg.messageId() || msg.id().toString(),
        subject: msg.subject() || '(No subject)',
        sender: msg.sender(),
        date: msg.dateReceived().toISOString(),
        content: msg.content() || '',
        read: msg.readStatus()
      }))
    )
  `

  return await runJXA<Email[]>(script)
}
```

## Common Patterns

### Pattern 1: Check Unread Count

```typescript
async function getUnreadCount(): Promise<number> {
  const script = `
    const Mail = Application('Mail')
    return Mail.inbox().unreadCount()
  `
  return await runJXA<number>(script)
}
```

### Pattern 2: Read Recent Messages

```typescript
interface MessageSummary {
  subject: string
  sender: string
  date: string
  read: boolean
}

async function getRecentMessages(limit: number = 10): Promise<MessageSummary[]> {
  const script = `
    const Mail = Application('Mail')
    const messages = Mail.inbox().messages()

    return JSON.stringify(
      messages.slice(0, ${limit}).map(msg => ({
        subject: msg.subject(),
        sender: msg.sender(),
        date: msg.dateReceived().toISOString(),
        read: msg.readStatus()
      }))
    )
  `
  return await runJXA<MessageSummary[]>(script)
}
```

### Pattern 3: Filter by Criteria

```typescript
async function getUnreadMessages(limit: number = 10): Promise<Email[]> {
  const script = `
    const Mail = Application('Mail')
    const allMessages = Mail.inbox().messages()
    const unreadMessages = allMessages.filter(msg => !msg.readStatus())

    return JSON.stringify(
      unreadMessages.slice(0, ${limit}).map(msg => ({
        id: msg.messageId(),
        subject: msg.subject(),
        sender: msg.sender(),
        date: msg.dateReceived().toISOString()
      }))
    )
  `
  return await runJXA<Email[]>(script)
}
```

### Pattern 4: Filter by Date Range

```typescript
async function getRecentEmailsFromHours(hours: number = 24): Promise<Email[]> {
  const script = `
    const Mail = Application('Mail')
    const cutoffDate = new Date(Date.now() - ${hours} * 60 * 60 * 1000)
    const messages = Mail.inbox().messages()

    return JSON.stringify(
      messages
        .filter(msg => msg.dateReceived() > cutoffDate)
        .map(msg => ({
          subject: msg.subject(),
          sender: msg.sender(),
          date: msg.dateReceived().toISOString()
        }))
    )
  `
  return await runJXA<Email[]>(script)
}
```

### Pattern 5: Create Draft Email

```typescript
async function createDraft(
  to: string,
  subject: string,
  body: string
): Promise<void> {
  // Escape special characters
  const escapedSubject = subject.replace(/"/g, '\\"').replace(/\n/g, '\\n')
  const escapedBody = body.replace(/"/g, '\\"').replace(/\n/g, '\\n')

  const script = `
    const Mail = Application('Mail')

    const msg = Mail.OutgoingMessage({
      subject: "${escapedSubject}",
      content: "${escapedBody}",
      visible: true
    })

    Mail.outgoingMessages.push(msg)
    msg.toRecipients.push(Mail.Recipient({ address: "${to}" }))

    return "Draft created"
  `

  await runJXA<string>(script)
}
```

### Pattern 6: Search by Sender

```typescript
async function getEmailsFromSender(senderEmail: string): Promise<Email[]> {
  const script = `
    const Mail = Application('Mail')
    const messages = Mail.inbox().messages()

    return JSON.stringify(
      messages
        .filter(msg => msg.sender().includes("${senderEmail}"))
        .slice(0, 20)
        .map(msg => ({
          subject: msg.subject(),
          sender: msg.sender(),
          date: msg.dateReceived().toISOString()
        }))
    )
  `
  return await runJXA<Email[]>(script)
}
```

## Error Handling

### Common Errors

**"Application isn't running":**
```typescript
try {
  const count = await getUnreadCount()
} catch (error) {
  if (error.message.includes("isn't running")) {
    throw new Error('Apple Mail is not running. Please open Mail.app first.')
  }
  throw error
}
```

**Permission denied:**
```
Error: Not authorized to send Apple events to Mail.
```

**Solution:** Grant automation permission:
1. System Settings → Privacy & Security → Automation
2. Enable checkbox for Mail under your terminal app

**Mailbox not found:**
```typescript
// Check if mailbox exists first
const script = `
  const Mail = Application('Mail')
  const mailboxNames = Mail.mailboxes().map(m => m.name())
  return JSON.stringify(mailboxNames)
`
const mailboxes = await runJXA<string[]>(script)
if (!mailboxes.includes('Archive')) {
  throw new Error('Mailbox "Archive" not found')
}
```

## Performance Considerations

### DO: Minimize Property Access

```javascript
// Good - access only needed properties
const messages = Mail.inbox().messages()
for (const msg of messages) {
  const subject = msg.subject()
  const sender = msg.sender()
}
```

### DON'T: Access All Properties

```javascript
// Slow - gets everything
const messages = Mail.inbox().messages()
for (const msg of messages) {
  const props = msg.properties()  // Avoid this
}
```

### Batch Operations

```typescript
// Process large message sets in batches
async function processMessagesInBatches(batchSize: number = 50) {
  // Get total count first
  const countScript = `
    const Mail = Application('Mail')
    return Mail.inbox().messages().length
  `
  const total = await runJXA<number>(countScript)

  // Process in batches
  for (let offset = 0; offset < total; offset += batchSize) {
    const script = `
      const Mail = Application('Mail')
      const messages = Mail.inbox().messages()
      return JSON.stringify(
        messages.slice(${offset}, ${offset + batchSize}).map(msg => ({
          subject: msg.subject(),
          sender: msg.sender()
        }))
      )
    `
    const batch = await runJXA<MessageSummary[]>(script)
    // Process batch
  }
}
```

## Limitations

### Cannot Do:

- ❌ Access Mail without Mail.app running
- ❌ Bypass Mail.app (requires Mail.app installed and configured)
- ❌ Direct IMAP/POP3 access (use mail client libraries instead)
- ❌ Modify Mail.app preferences programmatically (very limited support)
- ❌ Access mail while account is not configured

### Workarounds:

**For direct IMAP/POP3:** Use libraries like `imapflow` or `nodemailer` for server access without Mail.app

**For mail without Mail.app:** Consider IMAP/SMTP libraries instead of JXA

**For advanced filtering:** Mail Rules in Mail.app or server-side filters

## Application Client Pattern

Full TypeScript client implementation (see `examples/mail-client.ts`):

```typescript
export class MailClient {
  async getUnreadCount(): Promise<number> { /* ... */ }
  async getRecentMessages(limit: number): Promise<Email[]> { /* ... */ }
  async createDraft(to: string, subject: string, body: string): Promise<void> { /* ... */ }
  async isMailRunning(): Promise<boolean> { /* ... */ }
}

// Usage
const mail = new MailClient()
if (await mail.isMailRunning()) {
  const unread = await mail.getUnreadCount()
  console.log(`Unread: ${unread}`)
}
```

## Additional Resources

- **mail-scripting-dictionary.md** - Complete Mail.app scripting API reference
- **imap-vs-native.md** - When to use IMAP libraries vs JXA

## Examples

- **mail-client.ts** - Full TypeScript Mail client implementation
- **read-inbox.jxa** - Standalone inbox reading script
- **create-draft.jxa** - Draft creation script
- **search-messages.jxa** - Message search patterns

## Next Steps

Combine with other automation skills:
- **calendar-automation** - Create emails based on calendar events
- **notes-automation** - Email notes to yourself
- **reminders-automation** - Email reminders summary
