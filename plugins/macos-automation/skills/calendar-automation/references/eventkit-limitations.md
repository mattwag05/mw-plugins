# Calendar EventKit Limitations

## What JXA Can Do ✅

- Read events and calendars
- Create basic events
- Update event properties
- Search events
- Filter by date/title
- Access event details

## What Requires EventKit ❌

- Complex recurrence patterns
- Alarm configuration
- Attendee management (full)
- Calendar sharing settings
- Time zone handling (advanced)

## Recommendation

For 95% of automation tasks, JXA is sufficient. Use Swift CLI with EventKit only if you need the advanced features listed above.

## EventKit Example (Swift)

```swift
import EventKit

let store = EKEventStore()
let granted = try await store.requestFullAccessToEvents()
let calendars = store.calendars(for: .event)
// Full EventKit API available
```
