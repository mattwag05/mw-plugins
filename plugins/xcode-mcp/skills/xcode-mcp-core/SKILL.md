---
name: xcode-mcp-core
description: This skill should be used when the user asks to "use xcode", "open in xcode", "do something in xcode", "use the xcode mcp", or whenever working in a directory containing .xcodeproj, .xcworkspace, or Package.swift files and an Xcode-specific action is needed. Also activates when user asks generally "what can the Xcode MCP do?" or "how do I use xcode from Claude?".
version: 1.0.0
---

# Xcode MCP Core

The Xcode MCP bridge (`xcrun mcpbridge`) connects Claude Code to a running Xcode instance via the Model Context Protocol. It exposes a **single natural-language tool** — request any Xcode action by describing it in plain English, and Xcode performs it.

## Prerequisites

Before using any Xcode MCP request:

1. **Xcode must be open** with the target project or workspace loaded
2. **External agent access must be enabled:** Xcode → Settings → Intelligence → Model Context Protocol → "Allow external agents to use Xcode tools": ON
3. The Xcode MCP is configured as a project-scoped server at `/Users/matthewwagner` — it is available in any Claude Code session started in or under that directory
4. The MCP bridge was added via: `claude mcp add --transport stdio xcode -- xcrun mcpbridge`

### Intelligence Settings Overview

Xcode's Intelligence settings (Xcode → Settings → Intelligence) organize coding tools into three sections:

- **Agents** — Claude Agent, Codex (install via "Get" button, sign in with account or API key)
- **Model Context Protocol** — "Allow external agents to use Xcode tools" toggle (this is what Claude Code uses)
- **Chat** — ChatGPT in Xcode, Claude Sonnet & Opus, custom providers (Internet Hosted or Locally Hosted supporting Chat Completions API at `/v1/models` and `/v1/chat/completions`)

**Agent permissions:** Click the Permissions row under Agents to manage Allowed Commands (CLI tools) and Allowed Tools (MCP tools) that all agents can use.

**Claude Agent config:** `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig` — set default model, add MCP servers, create skills for the in-Xcode Claude Agent.

**MDM restriction:** Set `CodingAssistantAllowExternalIntegrations` to `false` in an MDM profile to disable the coding assistant on managed devices.

## Using the Xcode MCP Tool

The tool accepts a plain English description of the desired action. Structure requests as imperative commands directed at Xcode:

```
"Build the [scheme name] scheme for [platform]"
"Run all unit tests in the [target] test target"
"Add the [capability name] capability to the main app target"
"Search Apple documentation for [topic]"
"Fix the build error in [file]"
```

**Key behaviors:**
- Xcode receives the request and performs the action in its live session
- Build output, test results, and error diagnostics come back as the tool response
- Xcode's project history/rollback feature tracks all changes made via MCP

## Capabilities Catalog

| Category | What Xcode MCP Can Do |
|----------|----------------------|
| **Build** | Build schemes, clean build folder, run on simulator/device, resolve build errors |
| **Test** | Run test suites, individual test methods, test plans; report pass/fail/coverage |
| **Project Structure** | Add files/groups to project, create new targets, manage build phases |
| **Entitlements & Capabilities** | Add entitlements, enable capabilities (Push, iCloud, HealthKit, etc.) |
| **SPM** | Add, update, or remove Swift Package Manager dependencies |
| **Documentation** | Generate DocC comments for symbols, build documentation catalog |
| **Apple Docs** | Search Apple developer documentation by topic, API, or framework |
| **Code** | Generate/modify code in open files, apply proposed changes |
| **Diagnostics** | Read compiler errors/warnings with precise file+line context |
| **Playgrounds** | Generate playground macros for code exploration |

## Decision Tree: MCP vs. Direct Tools

Use this to choose the right approach:

```
Need to EDIT a Swift file?
  → Use Edit/Write tools directly (faster, no Xcode required)

Need to BUILD or get compiler diagnostics?
  → Use Xcode MCP ("Build the [scheme] scheme")

Need to ADD a file to the Xcode PROJECT (not just create it)?
  → Use Xcode MCP ("Add [filename] to the Xcode project")
  (Creating the file: Write tool. Registering it with Xcode: MCP)

Need to run TESTS?
  → Use Xcode MCP ("Run tests in [target]")
  (Alternative: xcodebuild test via Bash — slower, no live IDE feedback)

Need to search APPLE DOCUMENTATION?
  → Use Xcode MCP ("Search Apple docs for...")
  (Alternative: WebFetch on developer.apple.com — works when Xcode is closed)

Need to add ENTITLEMENTS or CAPABILITIES?
  → Use Xcode MCP (editing .entitlements XML manually risks Xcode ignoring it)

Need to add an SPM DEPENDENCY?
  → Use Xcode MCP ("Add the Swift package at [URL]")
  (Editing Package.swift directly works for package targets; for app targets use MCP)

Running a non-Xcode CLI task (e.g., swiftformat, fastlane)?
  → Use Bash tool directly
```

## Effective Request Patterns

**Be specific about targets and schemes:**
```
✅ "Build the MyApp scheme for iOS Simulator"
✅ "Run the MyAppTests test target"
❌ "Build the app"  (ambiguous if multiple schemes exist)
```

**Name files and symbols explicitly:**
```
✅ "Add the NetworkService.swift file to the Sources group in the MyApp target"
✅ "Generate DocC documentation for the UserRepository class"
```

**For error fixing, provide context:**
```
✅ "Fix the build errors — the compiler is reporting a type mismatch in ContentView.swift line 42"
```

**For Apple docs, use framework + symbol:**
```
✅ "Search Apple docs for URLSession data task async await"
✅ "Look up the SwiftData @Model macro documentation"
```

## Workflow Integration

The Xcode MCP is most powerful when combined with Claude's direct file tools:

1. **Write code** using Edit/Write tools
2. **Build** via Xcode MCP to get compiler feedback
3. **Fix errors** using Edit tool on the flagged files
4. **Rebuild** via Xcode MCP to confirm clean
5. **Run tests** via Xcode MCP to validate

This hybrid approach — Claude edits files, Xcode compiles and reports — is faster than `xcodebuild` CLI because it uses Xcode's incremental build system and gives richer diagnostics.

## Xcode Coding Assistant

The coding assistant is Xcode's sidebar UI for interacting with agents and chat models (open with Cmd-0). Key features relevant to external agent workflow:

- **Conversation history:** Xcode maintains full transcripts of all agent interactions, including external MCP sessions
- **Rollback:** Click History button → use slider to unwind changes prompt-by-prompt; click Restore to apply
- **Auto-apply toggle:** "Automatically apply code changes" button (lower-right) — when off, chat changes appear as proposals to selectively apply
- **Context references:** Type `@` in message field to reference specific symbols/files; "Upload files" for external files
- **Playgrounds & Previews:** Coding tools popover → "Generate a Playground" for `#Playground` macros rendered in canvas
- **Coding tools popover:** Click the coding intelligence icon in the source editor gutter, or Control-click a symbol and choose Show Coding Tools (Cmd-Opt-0) for Explain, Document, Generate a Playground

When Claude Code acts as an external agent via MCP, Xcode tracks all MCP-initiated changes in the conversation history and supports rollback.

## Limitations

- Xcode must be running and have the project open — the MCP bridge has no fallback
- Only one project can be active at a time in the Xcode session
- Some actions (like major refactors) work better directly in Xcode's editor
- The MCP bridge reflects whatever project is currently open in Xcode's front window

## Additional Skills

More detailed guidance in companion skills:
- **`xcode-build-and-fix`** — Build workflows, error diagnosis, iterative fix cycles
- **`xcode-project-management`** — Files, targets, entitlements, capabilities, SPM
- **`xcode-testing`** — Test suites, test plans, coverage reporting
- **`xcode-docs-and-search`** — DocC generation, Apple documentation search
