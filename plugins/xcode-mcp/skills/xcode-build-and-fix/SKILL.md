---
name: xcode-build-and-fix
description: This skill should be used when the user asks to "build the app", "compile the project", "fix build errors", "build failed", "resolve compiler errors", "make it compile", "clean build", or when Swift/SwiftUI compilation errors need to be diagnosed and fixed. Also activates when working on iOS/macOS code after making changes that need to be verified via a build.
version: 1.0.0
---

# Xcode Build and Fix

Use the Xcode MCP to build projects and diagnose compiler errors. Xcode's incremental build system is faster than `xcodebuild` CLI for iterative development, and the MCP bridge returns rich diagnostic output including file paths, line numbers, and error messages.

## Build Request Patterns

### Basic Build

```
"Build the [scheme] scheme"
"Build the [scheme] scheme for iOS Simulator"
"Build the [scheme] scheme for My Mac (Designed for iPad)"
"Build and report any errors or warnings"
```

### Clean Build

```
"Clean the build folder and rebuild the [scheme] scheme"
"Clean derived data for [scheme] then build"
```

### Run on Device/Simulator

```
"Build and run the [scheme] scheme on the iPhone 17 Pro simulator"
"Build and run on the connected device"
```

## Iterative Build-Fix Workflow

Follow this cycle when fixing compilation errors:

1. **Request a build** via Xcode MCP to get current error state
2. **Read the diagnostic output** — note file paths and line numbers
3. **Fix errors** using the Edit tool on the flagged source files
4. **Request another build** to verify fixes and catch cascading errors
5. **Repeat** until build succeeds with zero errors

Example request sequence:
```
Step 1: "Build the MyApp scheme and list all errors with file and line"
Step 3: [Use Edit tool on ContentView.swift:42]
Step 4: "Build the MyApp scheme again"
```

**Important:** Fix errors in dependency order — compiler errors often cascade. Address errors in types/protocols before errors in consuming code.

## Reading Build Diagnostics

The MCP response will contain Xcode's build log. Key fields to parse:

- **Error location:** `path/to/File.swift:line:column: error: message`
- **Warning location:** `path/to/File.swift:line:column: warning: message`
- **Note:** Additional context attached to errors
- **Build succeeded/failed:** Final status line

When multiple errors exist, prioritize:
1. Errors in shared types, protocols, and base classes
2. Errors in files that many others import
3. Errors in leaf files (views, view models) last

## Common Swift/SwiftUI Build Errors

### Type Mismatch / Cannot Convert

```swift
// Error: Cannot convert value of type 'Int' to expected argument type 'String'
// Fix: Add explicit conversion
Text(String(count))  // not Text(count)
```

### Missing Protocol Conformance

```swift
// Error: Type 'MyModel' does not conform to protocol 'Identifiable'
// Fix: Add required property
struct MyModel: Identifiable {
    let id = UUID()
}
```

### Ambiguous Use of Operator

Usually a missing import or conflicting module. Request from Xcode MCP:
```
"Search Apple docs for [the symbol or operator] to find which framework provides it"
```

### SwiftUI `@State` / `@Binding` Misuse

```swift
// Error: Cannot assign to property: 'x' is a get-only property
// Fix: Pass Binding, not the value
MyView(isOn: $isOn)  // not MyView(isOn: isOn)
```

### SourceKit False Positives in SPM Packages

When a project uses local SPM packages with `@_exported import`, SourceKit/IDE analysis will report errors like "No such module 'SomeModule'" or "Cannot find type 'X' in scope" even when the code is valid. These are false positives — SourceKit cannot resolve transitive SPM imports outside Xcode's full build graph. **Never act on SourceKit diagnostics alone; `xcodebuild build` is the only authoritative check.**

### Strict Concurrency (Swift 6)

For Swift 6 concurrency errors, the swift-concurrency plugin's `swift-concurrency` skill provides detailed guidance. Use it alongside this skill when builds fail with actor isolation or Sendable errors.

## When to Use xcodebuild CLI Instead

Prefer `xcodebuild` via Bash when:
- Xcode is not open (CI-like scenarios)
- Need to capture build output to a file
- Running `xcodebuild archive` or `xcodebuild exportArchive`
- Need `-destination` flags for specific device/OS combinations
- Running `xcodebuild test` with `-resultBundlePath` for CI artifacts

```bash
xcodebuild -scheme MyApp -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

**Note:** iOS 26 simulators no longer include `iPhone 16` — use `xcrun simctl list devices` to find available names.


## Build Performance Tips

When builds are slow, request via MCP:
```
"Check the build phases for the main target and identify any slow custom run script phases"
"Enable explicit module builds for the [scheme] scheme"
```

For large projects, prefer incremental builds — avoid clean builds unless diagnosing cache issues.
