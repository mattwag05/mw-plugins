/**
 * TypeScript wrapper for executing JXA (JavaScript for Automation) scripts
 *
 * This pattern provides type-safe JXA execution with automatic JSON parsing,
 * error handling, and integration with Bun runtime.
 *
 * Adapted from ai-email-assistant project patterns.
 */

/**
 * Execute a JXA (JavaScript for Automation) script and return parsed result
 *
 * @template T - Expected return type (will be JSON-parsed from script output)
 * @param script - JXA script to execute (should return JSON-serializable data)
 * @returns Parsed result of type T
 * @throws Error if execution fails or output cannot be parsed
 *
 * @example
 * ```typescript
 * // Get unread count from Mail
 * const script = `
 *   const Mail = Application('Mail')
 *   return Mail.inbox().unreadCount()
 * `
 * const count = await runJXA<number>(script)
 * console.log(`Unread: ${count}`)
 * ```
 *
 * @example
 * ```typescript
 * // Get structured data
 * interface Email {
 *   subject: string
 *   sender: string
 *   date: string
 * }
 *
 * const script = `
 *   const Mail = Application('Mail')
 *   const messages = Mail.inbox().messages()
 *   const recent = messages.slice(0, 5).map(msg => ({
 *     subject: msg.subject(),
 *     sender: msg.sender(),
 *     date: msg.dateReceived().toString()
 *   }))
 *   return JSON.stringify(recent)
 * `
 * const emails = await runJXA<Email[]>(script)
 * ```
 */
export async function runJXA<T>(script: string): Promise<T> {
  // Spawn osascript with JXA language flag
  const proc = Bun.spawn(['osascript', '-l', 'JavaScript', '-e', script], {
    stdout: 'pipe',
    stderr: 'pipe',
  })

  // Read stdout and stderr
  const output = await new Response(proc.stdout).text()
  const error = await new Response(proc.stderr).text()

  // Check for errors (ignore harmless warnings)
  if (error && !error.includes('Warning')) {
    throw new Error(`JXA execution failed: ${error}`)
  }

  // Handle empty output
  if (!output.trim()) {
    return [] as T  // Return empty array for empty results
  }

  // Parse JSON output
  try {
    return JSON.parse(output)
  } catch (e) {
    throw new Error(`Failed to parse JXA output: ${output}`)
  }
}

/**
 * Check if a macOS application is currently running
 *
 * @param appName - Application name (e.g., 'Mail', 'Calendar', 'Notes')
 * @returns true if application is running, false otherwise
 *
 * @example
 * ```typescript
 * if (await isAppRunning('Mail')) {
 *   console.log('Mail is running')
 * } else {
 *   console.log('Please open Mail.app first')
 * }
 * ```
 */
export async function isAppRunning(appName: string): Promise<boolean> {
  const script = `
    function run() {
      const System = Application('System Events')
      return System.processes.byName('${appName}').exists()
    }
  `

  try {
    return await runJXA<boolean>(script)
  } catch {
    return false
  }
}

/**
 * Get the version of a macOS application
 *
 * @param appName - Application name
 * @returns Version string (e.g., "16.0")
 *
 * @example
 * ```typescript
 * const version = await getAppVersion('Mail')
 * console.log(`Mail version: ${version}`)
 * ```
 */
export async function getAppVersion(appName: string): Promise<string> {
  const script = `
    function run() {
      const App = Application('${appName}')
      return App.version()
    }
  `

  return await runJXA<string>(script)
}

// Example usage
if (import.meta.main) {
  // Test basic JXA execution
  console.log('Testing JXA wrapper...\n')

  // Test 1: Simple script
  const testScript = `
    function run() {
      return JSON.stringify({ test: 'success', timestamp: new Date().toISOString() })
    }
  `
  const result = await runJXA<{ test: string; timestamp: string }>(testScript)
  console.log('Test 1 - Basic execution:', result)

  // Test 2: Check if Mail is running
  const mailRunning = await isAppRunning('Mail')
  console.log('Test 2 - Mail running:', mailRunning)

  if (mailRunning) {
    // Test 3: Get Mail version
    const mailVersion = await getAppVersion('Mail')
    console.log('Test 3 - Mail version:', mailVersion)

    // Test 4: Get unread count
    const unreadScript = `
      function run() {
        const Mail = Application('Mail')
        return Mail.inbox().unreadCount()
      }
    `
    const unread = await runJXA<number>(unreadScript)
    console.log('Test 4 - Unread count:', unread)
  } else {
    console.log('Mail is not running - skipping Mail tests')
  }

  console.log('\nAll tests completed!')
}
