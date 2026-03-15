# Bun Integration Patterns for JXA

Advanced TypeScript and Bun runtime patterns for macOS automation with JXA.

## Overview

Bun provides excellent performance and developer experience for building TypeScript applications that automate macOS. This guide covers patterns for integrating JXA automation into Bun-based projects.

## Core Pattern: runJXA Wrapper

The foundation of type-safe JXA integration:

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

**Key features:**
- Generic type parameter `<T>` for type safety
- Uses Bun.spawn for efficient process execution
- Automatic JSON parsing
- Error handling with clear messages
- Handles empty output gracefully

## Type Safety

### Defining Return Types

Always specify expected return types for type safety:

```typescript
interface Email {
  id: string
  subject: string
  sender: string
  date: string
  read: boolean
}

const script = `
  const Mail = Application('Mail')
  const messages = Mail.inbox().messages()
  const recent = messages.slice(0, 10).map(msg => ({
    id: msg.messageId(),
    subject: msg.subject(),
    sender: msg.sender(),
    date: msg.dateReceived().toISOString(),
    read: msg.readStatus()
  }))
  return JSON.stringify(recent)
`

const emails = await runJXA<Email[]>(script)
// emails is typed as Email[]
```

### Union Types for Error Handling

Handle both success and error cases with union types:

```typescript
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: string }

async function safeRunJXA<T>(script: string): Promise<Result<T>> {
  try {
    const data = await runJXA<T>(script)
    return { success: true, data }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// Usage
const result = await safeRunJXA<number>(script)
if (result.success) {
  console.log('Count:', result.data)
} else {
  console.error('Error:', result.error)
}
```

## Application Client Pattern

Wrap app-specific operations in classes for better organization:

```typescript
export class MailClient {
  private async runScript<T>(script: string): Promise<T> {
    return runJXA<T>(script)
  }

  async isRunning(): Promise<boolean> {
    const script = `
      const System = Application('System Events')
      return System.processes.byName('Mail').exists()
    `
    return this.runScript<boolean>(script)
  }

  async getUnreadCount(): Promise<number> {
    const script = `
      const Mail = Application('Mail')
      return Mail.inbox().unreadCount()
    `
    return this.runScript<number>(script)
  }

  async getRecentMessages(limit: number = 10): Promise<Email[]> {
    const script = `
      const Mail = Application('Mail')
      const messages = Mail.inbox().messages()
      const recent = messages.slice(0, ${limit}).map(msg => ({
        subject: msg.subject(),
        sender: msg.sender(),
        date: msg.dateReceived().toISOString()
      }))
      return JSON.stringify(recent)
    `
    return this.runScript<Email[]>(script)
  }

  async createDraft(to: string, subject: string, body: string): Promise<void> {
    const escapedSubject = this.escapeString(subject)
    const escapedBody = this.escapeString(body)

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
    await this.runScript<string>(script)
  }

  private escapeString(str: string): string {
    return str
      .replace(/\\/g, '\\\\')
      .replace(/"/g, '\\"')
      .replace(/\n/g, '\\n')
      .replace(/\r/g, '\\r')
  }
}

// Usage
const mail = new MailClient()
const unread = await mail.getUnreadCount()
console.log(`Unread: ${unread}`)
```

## Performance Optimization

### Minimize Script Calls

**Bad - Multiple calls:**
```typescript
const count = await runJXA<number>('Application("Mail").inbox().unreadCount()')
const flagged = await runJXA<number>('Application("Mail").inbox().messages().filter(m => m.flaggedStatus()).length')
// Two separate osascript processes
```

**Good - Single call:**
```typescript
interface MailStats {
  unread: number
  flagged: number
}

const script = `
  const Mail = Application('Mail')
  const inbox = Mail.inbox()
  const messages = inbox.messages()

  return JSON.stringify({
    unread: inbox.unreadCount(),
    flagged: messages.filter(m => m.flaggedStatus()).length
  })
`

const stats = await runJXA<MailStats>(script)
// Single osascript process, faster
```

### Batch Processing

Process items in batches to avoid overwhelming osascript:

```typescript
async function processMessagesInBatches(
  messageIds: string[],
  batchSize: number = 50
): Promise<void> {
  for (let i = 0; i < messageIds.length; i += batchSize) {
    const batch = messageIds.slice(i, i + batchSize)

    const script = `
      const Mail = Application('Mail')
      const processedIds = []

      ${batch.map(id => `
        try {
          const msg = Mail.inbox().messages().find(m => m.messageId() === "${id}")
          if (msg) {
            // Process message
            processedIds.push("${id}")
          }
        } catch (e) {}
      `).join('\n')}

      return JSON.stringify(processedIds)
    `

    await runJXA<string[]>(script)
  }
}
```

### Caching Application State

Cache frequently accessed data to reduce script calls:

```typescript
class CachedMailClient {
  private cache = new Map<string, { data: any; expires: number }>()
  private readonly TTL = 60000  // 1 minute

  async getUnreadCount(): Promise<number> {
    return this.cached('unreadCount', async () => {
      const script = `
        const Mail = Application('Mail')
        return Mail.inbox().unreadCount()
      `
      return runJXA<number>(script)
    })
  }

  private async cached<T>(
    key: string,
    fetcher: () => Promise<T>
  ): Promise<T> {
    const now = Date.now()
    const cached = this.cache.get(key)

    if (cached && cached.expires > now) {
      return cached.data as T
    }

    const data = await fetcher()
    this.cache.set(key, { data, expires: now + this.TTL })
    return data
  }

  clearCache(): void {
    this.cache.clear()
  }
}
```

## Error Handling Patterns

### Retry Logic

```typescript
async function runJXAWithRetry<T>(
  script: string,
  maxRetries: number = 3
): Promise<T> {
  let lastError: Error

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await runJXA<T>(script)
    } catch (error) {
      lastError = error as Error

      // Don't retry permission errors
      if (lastError.message.includes('Not authorized')) {
        throw lastError
      }

      // Wait before retry (exponential backoff)
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 100 * Math.pow(2, attempt)))
      }
    }
  }

  throw new Error(`Failed after ${maxRetries} attempts: ${lastError!.message}`)
}
```

### Application State Checking

```typescript
async function ensureAppRunning(appName: string): Promise<void> {
  const script = `
    const System = Application('System Events')
    if (!System.processes.byName('${appName}').exists()) {
      const app = Application('${appName}')
      app.launch()
      // Wait for app to be ready
      delay(2)
    }
  `
  await runJXA<void>(script)
}

// Usage
await ensureAppRunning('Mail')
const unread = await runJXA<number>('Application("Mail").inbox().unreadCount()')
```

## Testing Patterns

### Mock JXA Execution

```typescript
// mail-client.ts
export interface JXARunner {
  run<T>(script: string): Promise<T>
}

export class RealJXARunner implements JXARunner {
  async run<T>(script: string): Promise<T> {
    return runJXA<T>(script)
  }
}

export class MailClient {
  constructor(private jxa: JXARunner = new RealJXARunner()) {}

  async getUnreadCount(): Promise<number> {
    const script = `
      const Mail = Application('Mail')
      return Mail.inbox().unreadCount()
    `
    return this.jxa.run<number>(script)
  }
}

// mail-client.test.ts
class MockJXARunner implements JXARunner {
  async run<T>(script: string): Promise<T> {
    // Return mock data based on script
    if (script.includes('unreadCount')) {
      return 5 as T
    }
    return [] as T
  }
}

// Test
const mail = new MailClient(new MockJXARunner())
const count = await mail.getUnreadCount()
expect(count).toBe(5)
```

### Integration Tests

```typescript
// integration.test.ts
import { expect, test, describe } from 'bun:test'

describe('Mail Integration', () => {
  test('can access Mail', async () => {
    const script = `
      const Mail = Application('Mail')
      return Mail.version()
    `
    const version = await runJXA<string>(script)
    expect(version).toMatch(/^\d+\.\d+$/)
  })

  test('can get unread count', async () => {
    const script = `
      const Mail = Application('Mail')
      return Mail.inbox().unreadCount()
    `
    const count = await runJXA<number>(script)
    expect(typeof count).toBe('number')
    expect(count).toBeGreaterThanOrEqual(0)
  })
})
```

## Project Structure

Recommended structure for Bun projects with macOS automation:

```
project/
├── src/
│   ├── automation/
│   │   ├── jxa/
│   │   │   ├── runner.ts        # runJXA implementation
│   │   │   ├── mail-client.ts   # Mail automation
│   │   │   ├── calendar-client.ts
│   │   │   └── notes-client.ts
│   │   └── types.ts             # Shared types
│   ├── services/
│   │   └── email-service.ts     # Business logic
│   └── index.ts                 # Entry point
├── tests/
│   ├── integration/
│   │   └── mail.test.ts
│   └── unit/
│       └── mail-client.test.ts
└── package.json
```

## Bun-Specific Features

### Using Bun.file() for Script Files

```typescript
// Store complex scripts in files
async function runJXAFile(filepath: string): Promise<any> {
  const file = Bun.file(filepath)
  const script = await file.text()
  return runJXA(script)
}

// Usage
const result = await runJXAFile('./scripts/mail/get-inbox.jxa')
```

### Environment Variables

```typescript
// .env
MAIL_LOOKBACK_HOURS=24
OLLAMA_URL=http://localhost:11434

// Bun loads .env automatically
const hoursLookback = parseInt(Bun.env.MAIL_LOOKBACK_HOURS || '24')

const script = `
  const Mail = Application('Mail')
  const cutoff = new Date(Date.now() - ${hoursLookback} * 3600000)
  // Use cutoff in query
`
```

### Bun.spawn Advantages

```typescript
// Bun.spawn is faster than child_process
const proc = Bun.spawn(['osascript', '-l', 'JavaScript', '-e', script], {
  stdout: 'pipe',
  stderr: 'pipe',
  // Optional: Set working directory, env vars, etc.
})

// Efficient streaming
const output = await new Response(proc.stdout).text()
```

## Advanced Patterns

### Parallel Execution

```typescript
async function getMailStats() {
  // Run multiple independent queries in parallel
  const [unread, flagged, recent] = await Promise.all([
    runJXA<number>('Application("Mail").inbox().unreadCount()'),
    runJXA<number>('Application("Mail").inbox().messages().filter(m => m.flaggedStatus()).length'),
    runJXA<Email[]>(`
      const Mail = Application('Mail')
      const messages = Mail.inbox().messages()
      return JSON.stringify(messages.slice(0, 10).map(m => ({
        subject: m.subject(),
        sender: m.sender()
      })))
    `)
  ])

  return { unread, flagged, recent }
}
```

### Script Composition

```typescript
function createMailQuery(options: {
  mailbox?: string
  limit?: number
  unreadOnly?: boolean
}) {
  const mailbox = options.mailbox || 'inbox'
  const limit = options.limit || 10
  const filter = options.unreadOnly ? '.filter(m => !m.readStatus())' : ''

  return `
    const Mail = Application('Mail')
    const messages = Mail.${mailbox}().messages()${filter}
    return JSON.stringify(messages.slice(0, ${limit}).map(m => ({
      subject: m.subject(),
      sender: m.sender(),
      date: m.dateReceived().toISOString()
    })))
  `
}

// Usage
const unreadInbox = await runJXA<Email[]>(
  createMailQuery({ unreadOnly: true })
)
```

### Event-Driven Automation

```typescript
import { EventEmitter } from 'events'

class MailWatcher extends EventEmitter {
  private interval: Timer | null = null
  private lastCount = 0

  start(pollInterval: number = 5000): void {
    this.interval = setInterval(async () => {
      const count = await runJXA<number>(
        'Application("Mail").inbox().unreadCount()'
      )

      if (count !== this.lastCount) {
        this.emit('change', count, this.lastCount)
        this.lastCount = count
      }
    }, pollInterval)
  }

  stop(): void {
    if (this.interval) {
      clearInterval(this.interval)
      this.interval = null
    }
  }
}

// Usage
const watcher = new MailWatcher()
watcher.on('change', (newCount, oldCount) => {
  console.log(`Unread count changed: ${oldCount} → ${newCount}`)
})
watcher.start()
```

## Best Practices Summary

1. **Use generic types** for type safety with runJXA
2. **Minimize script calls** by batching operations
3. **Cache frequently accessed data** to reduce overhead
4. **Handle errors gracefully** with clear messages
5. **Escape user input** when embedding in scripts
6. **Check app state** before running scripts
7. **Structure code** with client classes for organization
8. **Test with mocks** for unit tests
9. **Use Bun features** for better performance
10. **Document expected types** for all JXA operations

## Performance Benchmarks

Typical operation times with Bun:

| Operation | Time | Notes |
|-----------|------|-------|
| Script launch | ~50ms | Initial osascript overhead |
| Get unread count | ~100ms | Simple query |
| Read 10 messages | ~200ms | Light data processing |
| Read 100 messages | ~2-3s | Heavy processing |
| Create draft | ~150ms | Single operation |

Optimization can reduce these times by 20-40% through batching and caching.
