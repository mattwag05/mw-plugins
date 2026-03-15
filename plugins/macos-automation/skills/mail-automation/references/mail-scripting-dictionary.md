# Mail.app Scripting Dictionary Reference

Complete API reference for Apple Mail automation via JXA.

## Core Objects

### Application

The Mail application object.

```javascript
const Mail = Application('Mail')
```

**Properties:**
- `version()` - Mail.app version string
- `name()` - Application name ('Mail')
- `running()` - Boolean if app is running
- `includeStandardAdditions` - Enable system event access (set to `true`)

**Methods:**
- `launch()` - Launch Mail if not running
- `activate()` - Bring Mail to foreground
- `quit()` - Quit Mail
- `checkForNewMail()` - Trigger mail check for all accounts

**Collections:**
- `accounts()` - Array of mail accounts
- `mailboxes()` - Array of all mailboxes
- `outgoingMessages()` - Array of draft/outgoing messages
- `messageViewers()` - Array of viewer windows

### Message

Represents an email message.

**Key Properties:**
- `messageId()` - Unique message ID (string)
- `id()` - Internal object ID
- `subject()` - Email subject line
- `sender()` - Sender email (format: "Name <email@domain.com>")
- `replyTo()` - Reply-to address
- `dateReceived()` - Date object when received
- `dateSent()` - Date object when sent
- `content()` - Email body content (HTML or plain text)
- `source()` - Raw email source
- `messageSize()` - Size in bytes
- `readStatus()` - Boolean if read
- `flaggedStatus()` - Boolean if flagged
- `junkMailStatus()` - Boolean if marked as junk
- `wasRepliedTo()` - Boolean if replied to
- `wasForwarded()` - Boolean if forwarded

**Recipient Properties:**
- `toRecipients()` - Array of To recipients
- `ccRecipients()` - Array of CC recipients
- `bccRecipients()` - Array of BCC recipients

**Collections:**
- `headers()` - Array of email headers
- `mailAttachments()` - Array of attachments

**Methods:**
- `delete()` - Move to trash
- `duplicateTo(mailbox)` - Copy to another mailbox
- `forwardOpeningWindow(boolean)` - Forward message
- `redirectOpeningWindow(boolean)` - Redirect message
- `replyOpeningWindow(boolean, replyToAll: boolean)` - Reply to message

**Example:**
```javascript
const Mail = Application('Mail')
const messages = Mail.inbox().messages()
const first = messages[0]

console.log({
  subject: first.subject(),
  sender: first.sender(),
  date: first.dateReceived().toISOString(),
  read: first.readStatus()
})
```

### Mailbox

Represents a mail folder.

**Properties:**
- `name()` - Mailbox name
- `unreadCount()` - Number of unread messages
- `account()` - Parent account object

**Collections:**
- `messages()` - Array of Message objects
- `mailboxes()` - Array of child mailboxes (for nested folders)

**Methods:**
- `delete()` - Delete mailbox

**Common mailboxes:**
```javascript
const Mail = Application('Mail')

// Access common mailboxes
const inbox = Mail.inbox()
const drafts = Mail.draftsMailbox()
const sent = Mail.sentMailbox()
const trash = Mail.trashMailbox()
const junk = Mail.junkMailbox()
```

**Access by name:**
```javascript
// Get mailbox by name
const archive = Mail.mailboxes.byName('Archive')

// Get nested mailbox
const projectMailbox = Mail.mailboxes.byName('Work').mailboxes.byName('Project-A')
```

### Account

Represents an email account.

**Properties:**
- `name()` - Account name
- `enabled()` - Boolean if account is active
- `emailAddresses()` - Array of email addresses for this account
- `fullName()` - User's full name for this account
- `userName()` - Username for account
- `authentication()` - Authentication type (e.g., 'password', 'OAuth')

**Collections:**
- `mailboxes()` - Array of mailboxes for this account

**Example:**
```javascript
const Mail = Application('Mail')
const accounts = Mail.accounts()

accounts.forEach(acc => {
  console.log({
    name: acc.name(),
    email: acc.emailAddresses()[0],
    enabled: acc.enabled()
  })
})
```

### OutgoingMessage

Draft or outgoing email message.

**Properties:**
- `subject()` - Email subject
- `content()` - Email body
- `visible()` - Boolean if draft window is visible
- `sender()` - Sender address

**Collections:**
- `toRecipients()` - Array of To recipients
- `ccRecipients()` - Array of CC recipients
- `bccRecipients()` - Array of BCC recipients

**Methods:**
- `send()` - Send the message
- `delete()` - Delete draft

**Create draft:**
```javascript
const Mail = Application('Mail')

// Create message object
const msg = Mail.OutgoingMessage({
  subject: "Test Subject",
  content: "Test body content",
  visible: true  // Show draft window
})

// Add to outgoing messages
Mail.outgoingMessages.push(msg)

// Add recipients
msg.toRecipients.push(Mail.Recipient({ address: "user@example.com" }))
msg.ccRecipients.push(Mail.Recipient({ address: "cc@example.com" }))

// Optionally send (leave commented to keep as draft)
// msg.send()
```

### Recipient

Email recipient object.

**Properties:**
- `address()` - Email address
- `name()` - Display name

**Create recipient:**
```javascript
const recipient = Mail.Recipient({ address: "user@example.com" })
```

### Header

Email header object.

**Properties:**
- `name()` - Header name (e.g., "From", "To", "Subject")
- `content()` - Header value

**Example:**
```javascript
const Mail = Application('Mail')
const message = Mail.inbox().messages()[0]
const headers = message.headers()

headers.forEach(header => {
  console.log(`${header.name()}: ${header.content()}`)
})
```

### Attachment

Email attachment object.

**Properties:**
- `name()` - Filename
- `mimeType()` - MIME type
- `fileSize()` - Size in bytes
- `downloaded()` - Boolean if downloaded

**Example:**
```javascript
const Mail = Application('Mail')
const message = Mail.inbox().messages()[0]
const attachments = message.mailAttachments()

attachments.forEach(att => {
  console.log({
    name: att.name(),
    type: att.mimeType(),
    size: att.fileSize()
  })
})
```

## Common Patterns

### Query Messages

```javascript
const Mail = Application('Mail')
const inbox = Mail.inbox()
const messages = inbox.messages()

// Get recent unread messages
const unread = messages.filter(msg => !msg.readStatus())

// Get messages from last 24 hours
const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000)
const recent = messages.filter(msg => msg.dateReceived() > cutoff)

// Get messages from specific sender
const fromSender = messages.filter(msg =>
  msg.sender().includes('example.com')
)
```

### Compose and Send

```javascript
const Mail = Application('Mail')

// Create message
const msg = Mail.OutgoingMessage({
  subject: "Meeting Notes",
  content: "Here are the notes from today's meeting...",
  visible: false  // Don't show window
})

Mail.outgoingMessages.push(msg)

// Add recipients
msg.toRecipients.push(Mail.Recipient({ address: "team@example.com" }))

// Send immediately
msg.send()
```

### Forward Message

```javascript
const Mail = Application('Mail')
const original = Mail.inbox().messages()[0]

// Forward (opens compose window)
const forwarded = original.forwardOpeningWindow(true)
```

### Reply to Message

```javascript
const Mail = Application('Mail')
const original = Mail.inbox().messages()[0]

// Reply (opens compose window)
const reply = original.replyOpeningWindow(true, false)  // reply, not reply-all

// Reply all
const replyAll = original.replyOpeningWindow(true, true)
```

### Mark as Read/Unread

```javascript
const Mail = Application('Mail')
const message = Mail.inbox().messages()[0]

// Mark as read
message.readStatus = true

// Mark as unread
message.readStatus = false
```

### Flag/Unflag Messages

```javascript
const Mail = Application('Mail')
const message = Mail.inbox().messages()[0]

// Flag message
message.flaggedStatus = true

// Unflag message
message.flaggedStatus = false
```

### Move Messages

```javascript
const Mail = Application('Mail')
const message = Mail.inbox().messages()[0]
const archive = Mail.mailboxes.byName('Archive')

// Move to archive
message.mailbox = archive
```

### Delete Messages

```javascript
const Mail = Application('Mail')
const message = Mail.inbox().messages()[0]

// Delete (move to trash)
message.delete()
```

## Performance Tips

### Minimize Property Access

```javascript
// Good - access each property once
const messages = Mail.inbox().messages()
for (const msg of messages) {
  const subject = msg.subject()
  const sender = msg.sender()
  console.log(subject, sender)
}

// Avoid - getting all properties is slow
const props = msg.properties()  // Don't do this
```

### Batch Operations

```javascript
// Process in chunks
const messages = Mail.inbox().messages()
const chunkSize = 50

for (let i = 0; i < messages.length; i += chunkSize) {
  const chunk = messages.slice(i, i + chunkSize)
  // Process chunk
}
```

### Cache Results

```javascript
// Cache frequently accessed data
const inbox = Mail.inbox()
const messageCount = inbox.messages().length  // Cache this

// Don't repeatedly query
for (let i = 0; i < 10; i++) {
  const count = Mail.inbox().messages().length  // Inefficient
}
```

## Error Handling

### Common Errors

**Application not running:**
```javascript
try {
  const Mail = Application('Mail')
  const count = Mail.inbox().unreadCount()
} catch (error) {
  if (error.message.includes("isn't running")) {
    // Launch Mail or notify user
  }
}
```

**Mailbox not found:**
```javascript
try {
  const mailbox = Mail.mailboxes.byName('NonExistent')
} catch (error) {
  // Handle missing mailbox
}
```

**Index out of range:**
```javascript
const messages = Mail.inbox().messages()
if (messages.length > 0) {
  const first = messages[0]  // Safe
}
```

## Limitations

### Cannot Do:
- Access messages while Mail.app is not running
- Direct SMTP/IMAP access (bypassing Mail.app)
- Modify Mail preferences programmatically
- Access encrypted messages without user interaction
- Bypass authentication for protected accounts

### Workarounds:
- Ensure Mail.app is running before automation
- Use IMAP/SMTP libraries for server-direct access
- Let users configure preferences manually
- Use macOS Keychain for stored credentials

## Additional Information

To explore the complete scripting dictionary:
1. Open **Script Editor.app**
2. File → Open Dictionary...
3. Select **Mail.app**
4. Browse the complete object model

Or via command line:
```bash
osascript -l JavaScript -e 'Application("Mail").properties()'
```
