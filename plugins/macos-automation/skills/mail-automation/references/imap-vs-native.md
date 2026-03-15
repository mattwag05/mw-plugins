# IMAP vs Native Mail Automation

When to use IMAP/SMTP libraries vs JXA for Apple Mail automation.

## Decision Matrix

| Use Case | Recommended Approach | Reason |
|----------|---------------------|---------|
| Mail.app configured, interactive workflows | JXA ✅ | Direct access, drafts visible |
| Server-only, no Mail.app | IMAP/SMTP ✅ | No Mail.app needed |
| Headless automation (servers) | IMAP/SMTP ✅ | No GUI required |
| Draft creation with user review | JXA ✅ | Shows in Mail.app |
| Bulk processing (100+ messages) | IMAP ✅ | More efficient |
| Multiple mailboxes/folders | Both work | JXA easier if Mail configured |
| Gmail-specific features (labels) | IMAP ✅ | Direct API access |
| Exchange/Outlook features | IMAP/EWS ✅ | Better protocol support |

## JXA (Native Mail Automation)

### Advantages

✅ **No configuration** - Uses existing Mail.app setup
✅ **User-friendly** - Drafts appear in Mail.app UI
✅ **Account agnostic** - Works with any account Mail supports
✅ **Rich features** - Flags, rules, mailboxes all accessible
✅ **Simple code** - No protocol knowledge required

### Disadvantages

❌ **Requires Mail.app** - Must be installed and running
❌ **macOS only** - Not portable to other platforms
❌ **UI dependencies** - Can be affected by Mail.app state
❌ **Performance** - Slower for bulk operations
❌ **Limited filtering** - Basic filtering only

### Best For:

- Personal automation on macOS
- Integration with other macOS apps (Calendar, Notes)
- Creating drafts for manual review
- Simple inbox monitoring
- Leveraging existing Mail.app configuration

### Example:

```typescript
// No IMAP config needed - uses Mail.app
const mail = new MailClient()
const unread = await mail.getUnreadCount()
const messages = await mail.getRecentMessages(10)
```

## IMAP/SMTP Libraries

### Advantages

✅ **Platform independent** - Works on any OS
✅ **No GUI needed** - Headless automation
✅ **Direct server access** - Faster bulk operations
✅ **Advanced filtering** - Server-side search
✅ **More control** - Lower-level protocol access
✅ **Gmail labels, etc** - Provider-specific features

### Disadvantages

❌ **Manual configuration** - Requires server details, credentials
❌ **Protocol complexity** - Need to understand IMAP/SMTP
❌ **App-specific passwords** - Gmail/Outlook require special setup
❌ **No UI integration** - Drafts don't appear in Mail.app
❌ **Account-specific** - Each account needs separate config

### Best For:

- Server-based automation
- High-volume processing
- Gmail label management
- Cross-platform applications
- Advanced search/filtering
- Webhook/API integration

### Example:

```typescript
import { ImapFlow } from 'imapflow'

const client = new ImapFlow({
  host: 'imap.gmail.com',
  port: 993,
  secure: true,
  auth: {
    user: 'user@gmail.com',
    pass: 'app-specific-password'
  }
})

await client.connect()
const messages = await client.fetch('1:10', { envelope: true })
```

## Hybrid Approach

Combine both for best results:

```typescript
export class EmailService {
  private jxa: MailClient
  private imap: ImapFlow | null

  constructor() {
    this.jxa = new MailClient()
    // Initialize IMAP only if needed
  }

  async getRecentMessages(): Promise<Email[]> {
    // Try JXA first (simpler, uses existing config)
    if (await this.jxa.isRunning()) {
      return this.jxa.getRecentMessages()
    }

    // Fallback to IMAP if Mail.app not available
    if (this.imap) {
      return this.fetchViaIMAP()
    }

    throw new Error('No email access method available')
  }

  async createDraft(to: string, subject: string, body: string): Promise<void> {
    // Always use JXA for drafts (shows in Mail.app)
    await this.jxa.createDraft(to, subject, body)
  }

  async bulkProcess(handler: (msg: Email) => void): Promise<void> {
    // Use IMAP for bulk operations (more efficient)
    if (this.imap) {
      return this.bulkProcessViaIMAP(handler)
    }

    // Fallback to JXA
    return this.bulkProcessViaJXA(handler)
  }
}
```

## Provider-Specific Considerations

### Gmail

**IMAP advantages:**
- Direct label access
- Advanced search syntax
- Better quota management

**JXA works if:**
- Mail.app configured with Gmail
- Mailboxes mapped to labels
- Standard operations only

**Setup for IMAP:**
```typescript
// Enable "Less secure app access" or use App Password
const gmail = new ImapFlow({
  host: 'imap.gmail.com',
  port: 993,
  secure: true,
  auth: {
    user: 'user@gmail.com',
    pass: 'app-specific-password'  // Generate in Google Account settings
  }
})
```

### iCloud Mail

**JXA preferred:**
- Already configured in Mail.app on macOS
- No additional setup needed
- Better integration

**IMAP if needed:**
```typescript
const icloud = new ImapFlow({
  host: 'imap.mail.me.com',
  port: 993,
  secure: true,
  auth: {
    user: 'user@icloud.com',
    pass: 'app-specific-password'
  }
})
```

### Microsoft 365 / Outlook

**IMAP limitations:**
- Some features require EWS (Exchange Web Services)
- Shared mailboxes may not work

**JXA works well:**
- If Outlook for Mac configured
- Standard IMAP operations

**OAuth2 consideration:**
Both JXA and IMAP can use OAuth2 tokens for authentication.

## Performance Comparison

### Small Operations (< 20 messages)

| Operation | JXA | IMAP |
|-----------|-----|------|
| Check unread count | ~100ms | ~200ms |
| Read 10 messages | ~300ms | ~400ms |
| Create draft | ~150ms | N/A* |

*IMAP doesn't show drafts in Mail.app

### Bulk Operations (100+ messages)

| Operation | JXA | IMAP |
|-----------|-----|------|
| Read 100 messages | ~3s | ~1.5s |
| Process 500 messages | ~15s | ~5s |
| Search entire inbox | Slow | Fast (server-side) |

**Conclusion:** IMAP wins for bulk operations, JXA sufficient for small tasks.

## Migration Path

### Starting with JXA:

```typescript
// Phase 1: JXA only (simple, works immediately)
const mail = new MailClient()
const messages = await mail.getRecentMessages()
```

### Adding IMAP Later:

```typescript
// Phase 2: Add IMAP for specific operations
class EmailService {
  // Use JXA for UI operations
  async createDraft() { /* JXA */ }

  // Use IMAP for bulk operations
  async processAllMessages() { /* IMAP */ }
}
```

## Code Examples

### JXA-Only Pattern

```typescript
// Simple, works with existing Mail.app config
import { MailClient } from './mail-client'

const mail = new MailClient()

if (await mail.isRunning()) {
  const unread = await mail.getUnreadCount()
  console.log(`Unread: ${unread}`)

  const messages = await mail.getUnreadMessages(20)
  messages.forEach(msg => {
    console.log(`- ${msg.subject}`)
  })
}
```

### IMAP-Only Pattern

```typescript
// More configuration, but platform-independent
import { ImapFlow } from 'imapflow'

const client = new ImapFlow({
  host: 'imap.gmail.com',
  port: 993,
  secure: true,
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
})

await client.connect()
await client.mailboxOpen('INBOX')

const messages = client.fetch('1:20', {
  envelope: true,
  bodyStructure: true
})

for await (const msg of messages) {
  console.log(`- ${msg.envelope.subject}`)
}

await client.logout()
```

### Hybrid Pattern

```typescript
// Best of both worlds
class EmailAutomation {
  private jxa = new MailClient()
  private imap: ImapFlow | null = null

  async init() {
    // Try JXA first
    if (await this.jxa.isRunning()) {
      console.log('Using JXA (Mail.app)')
      return
    }

    // Setup IMAP as fallback
    if (process.env.IMAP_HOST) {
      this.imap = new ImapFlow({...})
      await this.imap.connect()
      console.log('Using IMAP')
    }
  }

  async getMessages(): Promise<Email[]> {
    if (this.jxa) return this.jxa.getRecentMessages()
    if (this.imap) return this.fetchViaIMAP()
    throw new Error('No email access available')
  }
}
```

## Recommendation

**Start with JXA** if:
- Running on macOS
- Mail.app already configured
- Simple automation needs
- Want immediate results

**Use IMAP** if:
- Need cross-platform support
- Headless/server automation
- Bulk processing required
- Provider-specific features needed

**Use hybrid** for:
- Production applications
- Varying deployment environments
- Flexible requirements
- Best user experience (JXA) with fallback reliability (IMAP)

## Further Reading

- [ImapFlow Documentation](https://imapflow.com/)
- [Nodemailer Documentation](https://nodemailer.com/)
- [Gmail IMAP Settings](https://support.google.com/mail/answer/7126229)
- [iCloud IMAP Settings](https://support.apple.com/en-us/HT202304)
