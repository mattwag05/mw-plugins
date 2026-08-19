# Why Reminders requires EventKit

## The problem

Apple's Reminders.app scripting support via AppleScript/JXA is extremely limited:

**JXA can only:**
- Yes List reminder list names
- No Access actual reminder items
- No Read reminder properties
- No Create or update reminders

**Example of JXA limitation:**
```javascript
const Reminders = Application('Reminders')
const lists = Reminders.lists() // Works
const reminders = lists[0].reminders() // Does not exist!
```

## The solution: EventKit

EventKit is Apple's framework for Calendar and Reminders access. It provides full CRUD operations for reminders.

**EventKit provides:**
- Yes Full reminder access
- Yes Create/update/delete
- Yes Due dates and priorities
- Yes Notes and completion status
- Yes All reminder properties

## Swift CLI pattern

Since EventKit is a Swift/Objective-C framework, we use a Swift CLI tool that outputs JSON, then call it from TypeScript:

```
TypeScript → Swift CLI → EventKit → Reminders.app
```

## Implementation

1. Build Swift CLI with EventKit
2. Output JSON from Swift
3. Parse JSON in TypeScript
4. Type-safe Reminder objects

See `examples/reminders-cli/` for complete implementation.
