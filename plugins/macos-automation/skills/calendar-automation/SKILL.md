---
name: calendar-automation
description: This skill should be used when the user asks to "automate Calendar", "read calendar events", "create calendar events", "check today's schedule", "find meetings", "add appointments", "access calendars programmatically", or mentions Calendar.app automation, event scripting, or macOS calendar workflows.
version: 1.0.0
---

# Calendar.app Automation

Automate Calendar.app using JXA for reading, creating, and managing calendar events programmatically.

## Overview

Calendar.app provides scripting support for event management via JXA. Use this skill to build schedule automation, daily briefings, meeting summaries, and calendar-based workflows.

## Prerequisites

- **Calendar.app** configured with at least one calendar
- **Automation permissions** granted in System Settings
- **Calendar.app running** for most operations
- **macos-automation-core** loaded for `runJXA<T>()` pattern

## Core Capabilities

| Category | Operations | JXA Support |
|----------|------------|-------------|
| Reading | Access calendars, read events, check properties | ✅ Full |
| Creating | Create events, set times, add attendees | ✅ Full |
| Updating | Modify events, change times, update details | ✅ Full |
| Searching | Filter by date, calendar, title | ✅ Full |
| Calendars | List calendars, access properties | ✅ Full |

## Quick Reference

| Task | JXA Pattern |
|------|-------------|
| Get all calendars | `Calendar.calendars()` |
| Get calendar by name | `Calendar.calendars.byName('Work')` |
| Get all events | `calendar.events()` |
| Filter by date | `events.filter(e => e.startDate() > date)` |
| Get event title | `event.summary()` |
| Get start time | `event.startDate()` |
| Get end time | `event.endDate()` |
| Get location | `event.location()` |
| Create event | `Calendar.Event({...})` |

## TypeScript Integration

```typescript
interface CalendarEvent {
  summary: string
  startDate: string
  endDate: string
  location?: string
  calendar: string
}

async function getTodayEvents(): Promise<CalendarEvent[]> {
  const script = `
    const Calendar = Application('Calendar')
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    const allEvents = Calendar.calendars()
      .flatMap(cal => cal.events())
      .filter(event => {
        const start = event.startDate()
        return start >= today && start < tomorrow
      })

    return JSON.stringify(
      allEvents.map(event => ({
        summary: event.summary(),
        startDate: event.startDate().toISOString(),
        endDate: event.endDate().toISOString(),
        location: event.location() || '',
        calendar: event.calendar().name()
      }))
    )
  `
  return await runJXA<CalendarEvent[]>(script)
}
```

## Common Patterns

### Get Today's Events

```typescript
async function getTodaysSchedule(): Promise<CalendarEvent[]> {
  const script = `
    const Calendar = Application('Calendar')
    const calendars = Calendar.calendars()

    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    const todayEvents = []
    for (const cal of calendars) {
      const events = cal.events()
      for (const event of events) {
        const start = event.startDate()
        if (start >= today && start < tomorrow) {
          todayEvents.push({
            summary: event.summary(),
            startDate: start.toISOString(),
            endDate: event.endDate().toISOString(),
            location: event.location() || '',
            calendar: cal.name()
          })
        }
      }
    }

    return JSON.stringify(todayEvents.sort((a, b) =>
      new Date(a.startDate) - new Date(b.startDate)
    ))
  `
  return await runJXA<CalendarEvent[]>(script)
}
```

### Create Event

```typescript
async function createEvent(
  summary: string,
  startDate: Date,
  endDate: Date,
  calendarName: string = 'Calendar'
): Promise<void> {
  const script = `
    const Calendar = Application('Calendar')
    const cal = Calendar.calendars.byName('${calendarName}')

    const event = Calendar.Event({
      summary: "${summary}",
      startDate: new Date("${startDate.toISOString()}"),
      endDate: new Date("${endDate.toISOString()}")
    })

    cal.events.push(event)
    return "Event created"
  `
  await runJXA<string>(script)
}
```

### Search Events

```typescript
async function findMeetings(searchTerm: string): Promise<CalendarEvent[]> {
  const script = `
    const Calendar = Application('Calendar')
    const allEvents = Calendar.calendars()
      .flatMap(cal => cal.events())
      .filter(event =>
        event.summary().toLowerCase().includes("${searchTerm.toLowerCase()}")
      )

    return JSON.stringify(
      allEvents.slice(0, 20).map(event => ({
        summary: event.summary(),
        startDate: event.startDate().toISOString(),
        endDate: event.endDate().toISOString(),
        calendar: event.calendar().name()
      }))
    )
  `
  return await runJXA<CalendarEvent[]>(script)
}
```

## Error Handling

Common errors and solutions:

**"Calendar not found":**
```typescript
// List available calendars first
const script = `
  const Calendar = Application('Calendar')
  return JSON.stringify(Calendar.calendars().map(c => c.name()))
`
const calendarNames = await runJXA<string[]>(script)
```

**Permission denied:**
Grant calendar access in System Settings → Privacy & Security → Calendars

## Limitations

### EventKit Restrictions

Some operations require EventKit (Swift CLI) instead of JXA:
- ❌ Complex recurrence rules
- ❌ Alarms with sound
- ❌ Some attendee operations

For most use cases, JXA is sufficient. See `references/eventkit-limitations.md` for details.

## Additional Resources

- **calendar-scripting-dictionary.md** - Complete API reference
- **eventkit-limitations.md** - What requires EventKit

## Examples

- **calendar-client.ts** - Full TypeScript client
- **list-events.jxa** - List today's events
- **create-event.jxa** - Create new event
- **search-events.jxa** - Search by title
