/**
 * TypeScript wrapper for Reminders Swift CLI
 */

export interface Reminder {
  title: string
  list: string
  priority: number
  completed: boolean
  dueDate?: string
  notes?: string
}

export class RemindersClient {
  private cliPath: string

  constructor(cliPath: string) {
    this.cliPath = cliPath
  }

  async getReminders(): Promise<Reminder[]> {
    const proc = Bun.spawn([this.cliPath], {
      stdout: 'pipe',
      stderr: 'pipe',
    })

    const output = await new Response(proc.stdout).text()
    const error = await new Response(proc.stderr).text()

    if (error) {
      throw new Error(`Reminders CLI error: ${error}`)
    }

    if (!output.trim()) {
      return []
    }

    try {
      return JSON.parse(output)
    } catch (e) {
      throw new Error(`Failed to parse reminders output: ${output}`)
    }
  }

  async getTodayReminders(): Promise<Reminder[]> {
    const allReminders = await this.getReminders()
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    return allReminders.filter(reminder => {
      if (!reminder.dueDate) return false
      const dueDate = new Date(reminder.dueDate)
      return dueDate >= today && dueDate < tomorrow
    })
  }

  async getOverdueReminders(): Promise<Reminder[]> {
    const allReminders = await this.getReminders()
    const now = new Date()

    return allReminders.filter(reminder => {
      if (!reminder.dueDate) return false
      return new Date(reminder.dueDate) < now
    })
  }
}

// Example usage
if (import.meta.main) {
  // Update path to your built CLI
  const cliPath = './reminders-cli/.build/release/reminders-cli'
  const client = new RemindersClient(cliPath)

  console.log('Fetching reminders...\n')
  const reminders = await client.getReminders()
  console.log(`Total reminders: ${reminders.length}\n`)

  const today = await client.getTodayReminders()
  console.log(`Due today: ${today.length}`)
  today.forEach(r => console.log(`  - ${r.title}`))

  const overdue = await client.getOverdueReminders()
  console.log(`\nOverdue: ${overdue.length}`)
  overdue.forEach(r => console.log(`  - ${r.title}`))
}
