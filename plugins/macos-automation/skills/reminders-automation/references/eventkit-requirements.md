# Why Reminders Requires EventKit

## The Problem

Apple's Reminders.app scripting support via AppleScript/JXA is extremely limited:

**JXA can only:**
- ✅ List reminder list names
- ❌ Access actual reminder items
- ❌ Read reminder properties
- ❌ Create or update reminders

**Example of JXA limitation:**
```javascript
const Reminders = Application('Reminders')
const lists = Reminders.lists() // Works
const reminders = lists[0].reminders() // Does not exist!
```

## The Solution: EventKit

EventKit is Apple's framework for Calendar and Reminders access. It provides full CRUD operations for reminders.

**EventKit provides:**
- ✅ Full reminder access
- ✅ Create/update/delete
- ✅ Due dates and priorities
- ✅ Notes and completion status
- ✅ All reminder properties

## Swift CLI Pattern

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
