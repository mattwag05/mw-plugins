---
name: reminders-automation
description: This skill should be used when the user asks to "automate Reminders", "read reminders programmatically", "create reminders", "check due tasks", "access reminder lists", "mark reminders complete", or mentions Reminders.app automation. Note that full functionality requires Swift CLI with EventKit since AppleScript/JXA access to Reminders is severely limited.
version: 1.0.0
---

# Reminders.app Automation

Automate Reminders.app using Swift CLI with EventKit (JXA support is too limited for practical use).

## Overview

**Important:** Unlike other macOS apps, Reminders.app requires Swift with EventKit for full automation. AppleScript/JXA can only read list names - not actual reminders or their properties.

## Why Swift CLI?

| Feature | JXA Support | EventKit (Swift) Support |
|---------|-------------|--------------------------|
| List reminder lists | ✅ Yes | ✅ Yes |
| Read reminders | ❌ No | ✅ Yes |
| Create reminders | ❌ No | ✅ Yes |
| Update reminders | ❌ No | ✅ Yes |
| Mark complete | ❌ No | ✅ Yes |
| Due dates | ❌ No | ✅ Yes |
| Priorities | ❌ No | ✅ Yes |

**Recommendation:** Use Swift CLI for Reminders automation.

## Prerequisites

- **Swift** compiler (included with Xcode Command Line Tools)
- **EventKit permission** granted
- **macos-automation-core** for TypeScript integration

## Swift CLI Pattern

### Create Swift Package

```bash
mkdir reminders-cli
cd reminders-cli
swift package init --type executable
```

### Package.swift

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "reminders-cli",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(name: "reminders-cli")
    ]
)
```

### Sources/main.swift

```swift
import EventKit
import Foundation

@main
struct RemindersCLI {
    static func main() async {
        let store = EKEventStore()

        do {
            let granted = try await store.requestFullAccessToReminders()
            guard granted else {
                print("{\"error\": \"Permission denied\"}")
                return
            }
        } catch {
            print("{\"error\": \"\\(error.localizedDescription)\"}")
            return
        }

        let calendars = store.calendars(for: .reminder)
        let predicate = store.predicateForIncompleteReminders(
            withDueDateStarting: nil,
            ending: nil,
            calendars: calendars
        )

        let reminders = await withCheckedContinuation { continuation in
            store.fetchReminders(matching: predicate) { reminders in
                continuation.resume(returning: reminders)
            }
        }

        guard let reminders = reminders else {
            print("[]")
            return
        }

        let output = reminders.map { reminder in
            [
                "title": reminder.title ?? "",
                "list": reminder.calendar.title,
                "priority": reminder.priority,
                "completed": reminder.isCompleted
            ]
        }

        if let data = try? JSONSerialization.data(withJSONObject: output),
           let json = String(data: data, encoding: .utf8) {
            print(json)
        }
    }
}
```

### Build and Run

```bash
swift build -c release
.build/release/reminders-cli
```

## TypeScript Integration

```typescript
interface Reminder {
  title: string
  list: string
  priority: number
  completed: boolean
}

async function getReminders(): Promise<Reminder[]> {
  const proc = Bun.spawn(
    ['/path/to/reminders-cli/.build/release/reminders-cli'],
    { stdout: 'pipe', stderr: 'pipe' }
  )

  const output = await new Response(proc.stdout).text()
  const error = await new Response(proc.stderr).text()

  if (error) throw new Error(error)
  return JSON.parse(output)
}
```

## Common Patterns

### Today's Reminders

```swift
let today = Calendar.current.startOfDay(for: Date())
let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: today)!

let predicate = store.predicateForIncompleteReminders(
    withDueDateStarting: nil,
    ending: tomorrow,
    calendars: calendars
)
```

### Create Reminder

```swift
let reminder = EKReminder(eventStore: store)
reminder.title = "New Task"
reminder.calendar = store.defaultCalendarForNewReminders()
reminder.dueDateComponents = Calendar.current.dateComponents([.year, .month, .day], from: dueDate)

try store.save(reminder, commit: true)
```

## Permissions

Grant permission in System Settings → Privacy & Security → Reminders.

First run will prompt for permission:
```
"reminders-cli" would like to access your reminders.
[Don't Allow] [OK]
```

## What JXA Cannot Do

JXA is severely limited with Reminders:

```javascript
// This only gets list names, not reminders
const Reminders = Application('Reminders')
const lists = Reminders.lists().map(l => l.name())
// Cannot access actual reminder items!
```

## Additional Resources

- **eventkit-requirements.md** - Why EventKit is required
- **swift-cli-pattern.md** - Building Swift CLIs for automation

## Examples

- **reminders-cli/** - Complete Swift CLI implementation
- **reminders-wrapper.ts** - TypeScript integration

## Recommendation

Always use Swift CLI with EventKit for Reminders automation. JXA is insufficient for practical use.
