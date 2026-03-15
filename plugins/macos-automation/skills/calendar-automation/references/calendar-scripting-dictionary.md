# Calendar.app Scripting Dictionary

## Core Objects

### Calendar
**Properties:**
- `name()` - Calendar name
- `color()` - Calendar color
- `description()` - Calendar description

**Collections:**
- `events()` - Array of events in calendar

### Event
**Properties:**
- `summary()` - Event title
- `startDate()` - Start date/time (Date object)
- `endDate()` - End date/time (Date object)
- `location()` - Location string
- `description()` - Event notes
- `allDayEvent()` - Boolean if all-day
- `calendar()` - Parent calendar object

**Create event:**
```javascript
const Calendar = Application('Calendar')
const cal = Calendar.calendars.byName('Work')
const event = Calendar.Event({
  summary: "Meeting",
  startDate: new Date("2026-01-21T14:00:00"),
  endDate: new Date("2026-01-21T15:00:00"),
  location: "Conference Room"
})
cal.events.push(event)
```

## Common Patterns

**List calendars:**
```javascript
const Calendar = Application('Calendar')
Calendar.calendars().map(c => c.name())
```

**Get events in date range:**
```javascript
const events = calendar.events().filter(e => {
  const start = e.startDate()
  return start >= startDate && start < endDate
})
```

**Filter by title:**
```javascript
const meetings = calendar.events().filter(e =>
  e.summary().includes('Meeting')
)
```
