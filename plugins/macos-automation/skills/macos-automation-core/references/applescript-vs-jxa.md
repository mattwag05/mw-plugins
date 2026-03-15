# AppleScript vs JXA: Complete Comparison

Detailed comparison of AppleScript and JXA (JavaScript for Automation) for macOS automation.

## Overview

Both AppleScript and JXA provide access to the same application scripting dictionaries and capabilities. The choice is primarily about syntax preference and integration requirements.

## Syntax Comparison

### Accessing Applications

**AppleScript:**
```applescript
tell application "Mail"
    -- commands here
end tell
```

**JXA:**
```javascript
const Mail = Application('Mail')
// commands here
```

### Getting Properties

**AppleScript:**
```applescript
tell application "Mail"
    set messageCount to count of messages of inbox
    set firstSubject to subject of first message of inbox
end tell
```

**JXA:**
```javascript
const Mail = Application('Mail')
const messageCount = Mail.inbox().messages().length
const firstSubject = Mail.inbox().messages()[0].subject()
```

### Creating Objects

**AppleScript:**
```applescript
tell application "Mail"
    set newMessage to make new outgoing message with properties {subject:"Test", content:"Body"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"user@example.com"}
    end tell
end tell
```

**JXA:**
```javascript
const Mail = Application('Mail')
const msg = Mail.OutgoingMessage({
    subject: "Test",
    content: "Body"
})
Mail.outgoingMessages.push(msg)
msg.toRecipients.push(Mail.Recipient({ address: "user@example.com" }))
```

### Loops and Iteration

**AppleScript:**
```applescript
tell application "Mail"
    set unreadMessages to (messages of inbox whose read status is false)
    repeat with msg in unreadMessages
        set msgSubject to subject of msg
        -- process message
    end repeat
end tell
```

**JXA:**
```javascript
const Mail = Application('Mail')
const allMessages = Mail.inbox().messages()
const unreadMessages = allMessages.filter(msg => !msg.readStatus())

for (const msg of unreadMessages) {
    const subject = msg.subject()
    // process message
}
```

### Conditionals

**AppleScript:**
```applescript
tell application "Mail"
    if (unread count of inbox) > 0 then
        display dialog "You have unread mail"
    else
        display dialog "No unread mail"
    end if
end tell
```

**JXA:**
```javascript
const Mail = Application('Mail')
if (Mail.inbox().unreadCount() > 0) {
    // You have unread mail
} else {
    // No unread mail
}
```

### Lists and Arrays

**AppleScript:**
```applescript
tell application "Mail"
    set messageList to {}
    repeat with msg in messages of inbox
        set end of messageList to subject of msg
    end repeat
    return messageList
end tell
```

**JXA:**
```javascript
const Mail = Application('Mail')
const messages = Mail.inbox().messages()
const subjects = messages.map(msg => msg.subject())
return subjects
```

## Output Formats

### AppleScript Output

AppleScript returns plain text that requires parsing:

```applescript
tell application "Mail"
    return {subject of first message of inbox, sender of first message of inbox}
end tell
-- Output: {"Important Message", "sender@example.com"}
```

Parsing required:
```typescript
const output = await runAppleScript(script)
// Output: '{"Important Message", "sender@example.com"}'
// Requires custom parsing of AppleScript list format
```

### JXA Output

JXA can return JSON-serialized data:

```javascript
function run() {
    const Mail = Application('Mail')
    const msg = Mail.inbox().messages()[0]
    return JSON.stringify({
        subject: msg.subject(),
        sender: msg.sender()
    })
}
// Output: {"subject":"Important Message","sender":"sender@example.com"}
```

Direct JSON parsing:
```typescript
const output = await runJXA<{subject: string, sender: string}>(script)
// output is already parsed as { subject: "Important Message", sender: "sender@example.com" }
```

## Error Handling

### AppleScript

```applescript
try
    tell application "Mail"
        set msgCount to count of messages of inbox
    end tell
on error errMsg
    return "Error: " & errMsg
end try
```

### JXA

```javascript
try {
    const Mail = Application('Mail')
    const msgCount = Mail.inbox().messages().length
} catch (error) {
    return JSON.stringify({ error: error.message })
}
```

## Advanced Features

### System Events

**AppleScript:**
```applescript
tell application "System Events"
    set isRunning to exists process "Mail"
end tell
```

**JXA:**
```javascript
const System = Application('System Events')
const isRunning = System.processes.byName('Mail').exists()
```

### File Operations

**AppleScript:**
```applescript
set filePath to POSIX file "/path/to/file.txt"
set fileContents to read filePath
```

**JXA:**
```javascript
const app = Application.currentApplication()
app.includeStandardAdditions = true
const contents = app.read(Path('/path/to/file.txt'))
```

### Dialogs and User Interaction

**AppleScript:**
```applescript
display dialog "Enter your name:" default answer ""
set userName to text returned of result
```

**JXA:**
```javascript
const app = Application.currentApplication()
app.includeStandardAdditions = true
const response = app.displayDialog('Enter your name:', { defaultAnswer: '' })
const userName = response.textReturned
```

## Performance Comparison

Both languages have similar performance characteristics since they use the same underlying Apple Event system.

| Operation | AppleScript | JXA | Notes |
|-----------|-------------|-----|-------|
| Launch script | ~50ms | ~50ms | Initial overhead same |
| Get inbox count | <100ms | <100ms | Same underlying API |
| Read 100 messages | ~2-3s | ~2-3s | Same performance |
| Create draft | <100ms | <100ms | No difference |

Performance tips apply to both:
- Access only needed properties
- Avoid getting all properties
- Process in batches for large datasets
- Cache results when possible

## Documentation and Resources

### AppleScript

**Strengths:**
- Extensive Apple documentation
- Many books and tutorials
- Large community with decades of examples
- Every app's scripting dictionary well-documented

**Resources:**
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [AppleScript Language Guide](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
- Script Editor's built-in dictionary browser

### JXA

**Strengths:**
- Modern JavaScript syntax
- Better for developers familiar with JS
- JSON output patterns

**Weaknesses:**
- Limited Apple documentation
- Smaller community
- Apple has reduced focus on JXA development

**Resources:**
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook/wiki)
- [Scripting from the Command Line](https://developer.apple.com/library/archive/technotes/tn2065/_index.html)
- Community-driven examples on GitHub

## Migration Guide

### Converting AppleScript to JXA

**AppleScript:**
```applescript
tell application "Mail"
    set unreadList to (messages of inbox whose read status is false)
    repeat with msg in unreadList
        set msgInfo to {subject:subject of msg, sender:sender of msg}
    end repeat
end tell
```

**JXA equivalent:**
```javascript
const Mail = Application('Mail')
const allMessages = Mail.inbox().messages()
const unreadList = allMessages.filter(msg => !msg.readStatus())

for (const msg of unreadList) {
    const msgInfo = {
        subject: msg.subject(),
        sender: msg.sender()
    }
}
```

**Key conversions:**
- `tell application "X"` → `const X = Application('X')`
- `property of object` → `object.property()`
- `repeat with x in list` → `for (const x of list)`
- `whose` clause → `.filter()` method
- `count of collection` → `collection.length`
- AppleScript lists → JavaScript arrays

## Recommendations

### Use JXA When:

✅ Building TypeScript/Bun applications
✅ Need JSON output for parsing
✅ Familiar with JavaScript
✅ Want type-safe integration
✅ Creating new automations from scratch

### Use AppleScript When:

✅ Adapting existing AppleScript code
✅ Following Apple documentation examples
✅ Prefer natural language syntax
✅ Working with AppleScript-only resources
✅ Need extensive documentation

### Hybrid Approach:

For some projects, you may use both:
- JXA for data retrieval (JSON output)
- AppleScript for complex logic found in documentation

Example:
```typescript
// Use JXA for data (JSON output)
const data = await runJXA<DataType>(jxaScript)

// Use AppleScript for documented workflows
await runAppleScript(documentedAppleScript)
```

## Troubleshooting

### Common Issues

**Issue: JXA object method not working**
```javascript
// Wrong - missing parentheses
const count = Mail.inbox().unreadCount  // Returns function, not value

// Correct
const count = Mail.inbox().unreadCount()  // Calls method, returns value
```

**Issue: AppleScript list parsing**
```typescript
// AppleScript returns: {"item1", "item2", "item3"}
// Not valid JSON - requires custom parsing
const items = output.match(/"([^"]+)"/g).map(s => s.slice(1, -1))
```

**Issue: Property access patterns differ**
```applescript
-- AppleScript
subject of message

// JXA
message.subject()  // Method call, not property
```

## Conclusion

**Default recommendation: Use JXA** for new macOS automation projects, especially when:
- Building TypeScript applications
- Need structured data output
- Familiar with JavaScript syntax

**Use AppleScript when necessary** for:
- Adapting documented workflows
- Working with AppleScript-specific resources

Both are equally capable - the choice is about syntax preference and integration needs.
