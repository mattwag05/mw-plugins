/**
 * Complete TypeScript client for Apple Mail automation
 *
 * Adapted from ai-email-assistant project patterns.
 * Provides type-safe wrapper around Mail.app JXA scripting.
 */

/**
 * Execute JXA script with type safety
 * (Import from macos-automation-core in production)
 */
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

// Type definitions
export interface Email {
  id: string
  subject: string
  sender: string
  to: Array<{ name: string; email: string }>
  date: string
  content: string
  read: boolean
  mailbox: string
}

export interface MailboxInfo {
  name: string
  unreadCount: number
  totalCount: number
}

export interface MailAccount {
  name: string
  email: string
  enabled: boolean
}

/**
 * Apple Mail Client
 *
 * Type-safe wrapper around Mail.app JXA automation.
 */
export class MailClient {
  /**
   * Check if Apple Mail is currently running
   */
  async isRunning(): Promise<boolean> {
    const script = `
      function run() {
        const System = Application('System Events')
        return System.processes.byName('Mail').exists()
      }
    `
    try {
      return await runJXA<boolean>(script)
    } catch {
      return false
    }
  }

  /**
   * Get unread message count from inbox
   */
  async getUnreadCount(): Promise<number> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        return Mail.inbox().unreadCount()
      }
    `
    return await runJXA<number>(script)
  }

  /**
   * Get recent messages from inbox
   *
   * @param limit - Number of messages to retrieve (default: 10)
   * @param hoursLookback - Only include messages from last N hours (default: 24)
   * @returns Array of email objects
   */
  async getRecentMessages(
    limit: number = 10,
    hoursLookback: number = 24
  ): Promise<Email[]> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        Mail.includeStandardAdditions = true

        const cutoffDate = new Date(Date.now() - ${hoursLookback} * 60 * 60 * 1000)
        const messages = Mail.inbox().messages()
        const filtered = []

        for (let i = 0; i < messages.length && filtered.length < ${limit}; i++) {
          const msg = messages[i]
          const msgDate = msg.dateReceived()

          if (msgDate < cutoffDate) continue

          try {
            const msgId = msg.messageId() || msg.id().toString()
            const from = msg.sender()
            const fromMatch = from.match(/(.*?)\\s*<(.+?)>/) || [null, from, from]
            const fromName = fromMatch[1]?.trim() || fromMatch[2]
            const fromEmail = fromMatch[2] || from

            const toAddresses = msg.toRecipients()
            const toList = []
            for (let j = 0; j < toAddresses.length; j++) {
              const toAddr = toAddresses[j].address()
              const toMatch = toAddr.match(/(.*?)\\s*<(.+?)>/) || [null, toAddr, toAddr]
              toList.push({
                name: toMatch[1]?.trim() || toMatch[2],
                email: toMatch[2] || toAddr
              })
            }

            let content = msg.content()
            if (content && content.length > 5000) {
              content = content.substring(0, 5000) + '...'
            }

            filtered.push({
              id: msgId,
              subject: msg.subject() || '(No subject)',
              sender: from,
              to: toList,
              date: msgDate.toISOString(),
              content: content || '',
              read: msg.readStatus(),
              mailbox: 'INBOX'
            })
          } catch (msgError) {
            // Skip messages that cause errors
            continue
          }
        }

        return JSON.stringify(filtered)
      }
    `

    try {
      return await runJXA<Email[]>(script)
    } catch (error) {
      if (error instanceof Error && error.message.includes("isn't running")) {
        throw new Error('Apple Mail is not running. Please open Mail.app first.')
      }
      throw error
    }
  }

  /**
   * Get unread messages only
   *
   * @param limit - Number of messages to retrieve
   * @returns Array of unread email objects
   */
  async getUnreadMessages(limit: number = 20): Promise<Email[]> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        const allMessages = Mail.inbox().messages()
        const unreadMessages = allMessages.filter(msg => !msg.readStatus())
        const limited = unreadMessages.slice(0, ${limit})

        return JSON.stringify(
          limited.map(msg => ({
            id: msg.messageId() || msg.id().toString(),
            subject: msg.subject() || '(No subject)',
            sender: msg.sender(),
            to: [],
            date: msg.dateReceived().toISOString(),
            content: msg.content() || '',
            read: false,
            mailbox: 'INBOX'
          }))
        )
      }
    `

    return await runJXA<Email[]>(script)
  }

  /**
   * Search messages by sender
   *
   * @param senderEmail - Email address to search for
   * @param limit - Max results to return
   * @returns Matching emails
   */
  async searchBySender(senderEmail: string, limit: number = 20): Promise<Email[]> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        const messages = Mail.inbox().messages()
        const matching = messages.filter(msg =>
          msg.sender().toLowerCase().includes("${senderEmail.toLowerCase()}")
        )

        return JSON.stringify(
          matching.slice(0, ${limit}).map(msg => ({
            id: msg.messageId() || msg.id().toString(),
            subject: msg.subject() || '(No subject)',
            sender: msg.sender(),
            to: [],
            date: msg.dateReceived().toISOString(),
            content: '',
            read: msg.readStatus(),
            mailbox: 'INBOX'
          }))
        )
      }
    `

    return await runJXA<Email[]>(script)
  }

  /**
   * Create a draft message in Mail.app
   *
   * @param to - Recipient email address
   * @param subject - Email subject
   * @param body - Email body content
   */
  async createDraft(to: string, subject: string, body: string): Promise<void> {
    // Escape strings for JXA
    const escapedSubject = subject.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')
    const escapedBody = body.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')

    const script = `
      function run() {
        const Mail = Application('Mail')
        Mail.includeStandardAdditions = true

        const outgoingMsg = Mail.OutgoingMessage({
          subject: "${escapedSubject}",
          content: "${escapedBody}",
          visible: true
        })

        Mail.outgoingMessages.push(outgoingMsg)
        outgoingMsg.toRecipients.push(
          Mail.Recipient({ address: "${to}" })
        )

        return "Draft created"
      }
    `

    await runJXA<string>(script)
  }

  /**
   * Get information about all mailboxes
   */
  async getMailboxes(): Promise<MailboxInfo[]> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        const mailboxes = Mail.mailboxes()

        return JSON.stringify(
          mailboxes.map(mb => ({
            name: mb.name(),
            unreadCount: mb.unreadCount(),
            totalCount: mb.messages().length
          }))
        )
      }
    `

    return await runJXA<MailboxInfo[]>(script)
  }

  /**
   * Get all configured email accounts
   */
  async getAccounts(): Promise<MailAccount[]> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        const accounts = Mail.accounts()

        return JSON.stringify(
          accounts.map(acc => ({
            name: acc.name(),
            email: acc.emailAddresses()[0] || '',
            enabled: acc.enabled()
          }))
        )
      }
    `

    return await runJXA<MailAccount[]>(script)
  }

  /**
   * Get Mail.app version
   */
  async getVersion(): Promise<string> {
    const script = `
      function run() {
        const Mail = Application('Mail')
        return Mail.version()
      }
    `
    return await runJXA<string>(script)
  }
}

// Example usage
if (import.meta.main) {
  const mail = new MailClient()

  console.log('Testing Mail Client...\n')

  // Check if Mail is running
  const running = await mail.isRunning()
  console.log('Mail running:', running)

  if (!running) {
    console.log('\nPlease open Mail.app to test further functionality')
    process.exit(0)
  }

  // Get Mail version
  const version = await mail.getVersion()
  console.log('Mail version:', version)

  // Get unread count
  const unread = await mail.getUnreadCount()
  console.log('Unread count:', unread)

  // Get recent messages
  console.log('\nFetching recent messages...')
  const recent = await mail.getRecentMessages(5, 24)
  console.log(`Found ${recent.length} messages:`)
  recent.forEach(msg => {
    console.log(`  - ${msg.subject} (from ${msg.sender})`)
  })

  // Get mailboxes
  console.log('\nMailboxes:')
  const mailboxes = await mail.getMailboxes()
  mailboxes.slice(0, 5).forEach(mb => {
    console.log(`  - ${mb.name}: ${mb.unreadCount} unread / ${mb.totalCount} total`)
  })

  // Get accounts
  console.log('\nAccounts:')
  const accounts = await mail.getAccounts()
  accounts.forEach(acc => {
    console.log(`  - ${acc.name} (${acc.email}) ${acc.enabled ? '✓' : '✗'}`)
  })

  console.log('\nAll tests completed!')
}
