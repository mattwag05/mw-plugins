# Swift CLI Pattern for macOS Automation

## When to Use

Use Swift CLIs when:
- JXA/AppleScript support is insufficient (e.g., Reminders)
- Need access to native frameworks (EventKit, etc.)
- Performance-critical operations
- Complex native API access required

## Basic Structure

```swift
import Foundation
import EventKit // or other frameworks

@main
struct MyCLI {
    static func main() async {
        // 1. Request permissions
        // 2. Access native APIs
        // 3. Output JSON to stdout
    }
}
```

## Building

```bash
swift build -c release
.build/release/my-cli
```

## TypeScript Integration

```typescript
async function runSwiftCLI<T>(cliPath: string): Promise<T> {
  const proc = Bun.spawn([cliPath], {
    stdout: 'pipe',
    stderr: 'pipe'
  })
  const output = await new Response(proc.stdout).text()
  return JSON.parse(output)
}
```

## Best Practices

- Always output JSON for easy parsing
- Handle permissions gracefully
- Provide clear error messages
- Use async/await for EventKit
- Include error handling in TypeScript wrapper
