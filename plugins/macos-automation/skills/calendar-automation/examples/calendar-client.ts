/**
 * TypeScript client for Calendar.app automation
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
  return output.trim() ? JSON.parse(output) : [] as T
}

export interface CalendarEvent {
  summary: string
  startDate: string
  endDate: string
  location?: string
  calendar: string
}

export class CalendarClient {
  async getTodayEvents(): Promise<CalendarEvent[]> {
    const script = `
      const Calendar = Application('Calendar')
      const today = new Date(); today.setHours(0,0,0,0)
      const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1)

      const events = Calendar.calendars().flatMap(cal =>
        cal.events().filter(e => {
          const start = e.startDate()
          return start >= today && start < tomorrow
        }).map(e => ({
          summary: e.summary(),
          startDate: e.startDate().toISOString(),
          endDate: e.endDate().toISOString(),
          location: e.location() || '',
          calendar: cal.name()
        }))
      )
      return JSON.stringify(events.sort((a,b) => new Date(a.startDate) - new Date(b.startDate)))
    `
    return await runJXA<CalendarEvent[]>(script)
  }

  async createEvent(summary: string, start: Date, end: Date, cal: string = 'Calendar'): Promise<void> {
    const script = `
      const Calendar = Application('Calendar')
      const calendar = Calendar.calendars.byName('${cal}')
      const event = Calendar.Event({
        summary: "${summary}",
        startDate: new Date("${start.toISOString()}"),
        endDate: new Date("${end.toISOString()}")
      })
      calendar.events.push(event)
      return "Event created"
    `
    await runJXA<string>(script)
  }

  async listCalendars(): Promise<string[]> {
    const script = `
      const Calendar = Application('Calendar')
      return JSON.stringify(Calendar.calendars().map(c => c.name()))
    `
    return await runJXA<string[]>(script)
  }
}

if (import.meta.main) {
  const cal = new CalendarClient()
  console.log('Today:', await cal.getTodayEvents())
  console.log('Calendars:', await cal.listCalendars())
}
