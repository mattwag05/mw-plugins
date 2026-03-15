/**
 * TypeScript wrapper for executing AppleScript
 *
 * Use this when working with AppleScript instead of JXA, or when existing
 * AppleScript documentation is being adapted.
 *
 * Note: JXA is recommended for new projects due to JSON output support.
 * Use AppleScript when:
 * - Adapting existing AppleScript code
 * - Following Apple documentation that uses AppleScript
 * - Working with scripts that are easier in AppleScript syntax
 */

/**
 * Execute an AppleScript and return the output as a string
 *
 * @param script - AppleScript code to execute
 * @returns Script output as string (requires manual parsing)
 * @throws Error if execution fails
 *
 * @example
 * ```typescript
 * const script = `
 *   tell application "Mail"
 *     return count of (messages of inbox whose read status is false)
 *   end tell
 * `
 * const output = await runAppleScript(script)
 * const unread = parseInt(output.trim())
 * console.log(`Unread: ${unread}`)
 * ```
 */
export async function runAppleScript(script: string): Promise<string> {
  const proc = Bun.spawn(['osascript', '-e', script], {
    stdout: 'pipe',
    stderr: 'pipe',
  })

  const output = await new Response(proc.stdout).text()
  const error = await new Response(proc.stderr).text()

  if (error && !error.includes('Warning')) {
    throw new Error(`AppleScript execution failed: ${error}`)
  }

  return output.trim()
}

/**
 * Execute an AppleScript file
 *
 * @param filePath - Path to .applescript file
 * @returns Script output as string
 *
 * @example
 * ```typescript
 * const output = await runAppleScriptFile('/path/to/script.applescript')
 * console.log(output)
 * ```
 */
export async function runAppleScriptFile(filePath: string): Promise<string> {
  const proc = Bun.spawn(['osascript', filePath], {
    stdout: 'pipe',
    stderr: 'pipe',
  })

  const output = await new Response(proc.stdout).text()
  const error = await new Response(proc.stderr).text()

  if (error && !error.includes('Warning')) {
    throw new Error(`AppleScript file execution failed: ${error}`)
  }

  return output.trim()
}

/**
 * Check if Mail is running using AppleScript
 *
 * @returns true if Mail is running
 */
async function isMailRunning(): Promise<boolean> {
  const script = `
    tell application "System Events"
      return exists process "Mail"
    end tell
  `

  try {
    const result = await runAppleScript(script)
    return result === 'true'
  } catch {
    return false
  }
}

/**
 * Get unread count from Mail using AppleScript
 *
 * @returns Number of unread messages
 */
async function getUnreadCount(): Promise<number> {
  const script = `
    tell application "Mail"
      set inboxRef to inbox
      return unread count of inboxRef
    end tell
  `

  const output = await runAppleScript(script)
  return parseInt(output)
}

/**
 * Get list of mailbox names using AppleScript
 *
 * @returns Array of mailbox names
 */
async function getMailboxes(): Promise<string[]> {
  const script = `
    tell application "Mail"
      set mailboxNames to name of mailboxes
      set AppleScript's text item delimiters to "|"
      return mailboxNames as string
    end tell
  `

  const output = await runAppleScript(script)
  return output.split('|').filter(name => name.trim())
}

// Example usage
if (import.meta.main) {
  console.log('Testing AppleScript wrapper...\n')

  // Test 1: Basic AppleScript
  const testScript = `
    set currentDate to current date
    return currentDate as string
  `
  const dateResult = await runAppleScript(testScript)
  console.log('Test 1 - Current date:', dateResult)

  // Test 2: Check if Mail is running
  const mailRunning = await isMailRunning()
  console.log('Test 2 - Mail running:', mailRunning)

  if (mailRunning) {
    // Test 3: Get unread count
    try {
      const unread = await getUnreadCount()
      console.log('Test 3 - Unread count:', unread)
    } catch (error) {
      console.log('Test 3 failed:', error instanceof Error ? error.message : error)
    }

    // Test 4: Get mailboxes
    try {
      const mailboxes = await getMailboxes()
      console.log('Test 4 - Mailboxes:', mailboxes.slice(0, 5))
    } catch (error) {
      console.log('Test 4 failed:', error instanceof Error ? error.message : error)
    }
  } else {
    console.log('Mail is not running - skipping Mail tests')
  }

  console.log('\nAll tests completed!')
}

/**
 * Comparison Notes: AppleScript vs JXA
 *
 * AppleScript advantages:
 * - Natural language-like syntax
 * - Extensive Apple documentation
 * - Better for adapting existing scripts
 *
 * JXA advantages:
 * - Modern JavaScript syntax
 * - JSON output (no parsing needed)
 * - Better TypeScript integration
 * - Familiar to JS developers
 *
 * Recommendation: Use JXA (run-jxa-wrapper.ts) for new projects.
 * Use AppleScript when adapting existing scripts or following
 * AppleScript-specific documentation.
 */
