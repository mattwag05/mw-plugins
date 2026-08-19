# Swift CLI pattern for macOS automation

## When to use

Use Swift CLIs when:
- JXA/AppleScript support is insufficient (e.g., Reminders)
- Need access to native frameworks (EventKit, etc.)
- Performance-critical operations
- Complex native API access required

## Basic structure

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

## TypeScript integration

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

## Best practices

- Always output JSON for easy parsing
- Handle permissions gracefully
- Provide clear error messages
- Use async/await for EventKit
- Include error handling in TypeScript wrapper
