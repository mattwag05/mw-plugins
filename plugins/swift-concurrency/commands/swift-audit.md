---
description: Audit Swift code for concurrency correctness. Analyzes the specified file or directory (or all .swift files in the current project) for data races, actor isolation violations, GCD anti-patterns, and Sendable gaps. Reports issues by severity with actionable fixes.
argument-hint: [file-or-directory-path]
allowed-tools: Read, Glob, Grep, Bash
---

# Swift Concurrency Audit

You are performing a Swift concurrency audit. Argument: `$ARGUMENTS`

## Step 1: Determine Scope

If `$ARGUMENTS` is empty:
- Glob `**/*.swift` in the current directory
- Exclude `.build/`, `.worktrees/`, `DerivedData/`, `.swiftpm/`

If `$ARGUMENTS` is a `.swift` file:
- Audit that single file

If `$ARGUMENTS` is a directory:
- Glob `*.swift` and `**/*.swift` within it
- Exclude build directories

Report: "Auditing N files for concurrency correctness."

## Step 2: Classify Files by Concurrency Signal Type

For each file, grep for these signals and categorize:

| Signal | Category |
|--------|----------|
| `DispatchQueue`, `DispatchGroup`, `DispatchSemaphore` | GCD — needs migration |
| `Process.*waitUntilExit\|Pipe()` | Blocking I/O — needs `@concurrent` |
| `actor `, `@MainActor`, `@concurrent` | Actor-isolated — check reentrancy |
| `Task {`, `Task.detached` | Unstructured tasks — check hygiene |
| `@unchecked Sendable`, `nonisolated(unsafe)` | Escape hatches — verify justification |
| `Sendable` without conformance | Potential gaps |

Files with no concurrency signals: mark as "no concurrency — skip".

## Step 3: Deep Review (6 categories)

Apply these 6 review categories to every file with signals:

### 1. Sendable Gaps [HIGH/MED]
- Reference types crossing actor/Task boundaries without Sendable conformance
- Value types with non-Sendable stored properties in async context
- `@unchecked Sendable` without a comment naming the protecting lock

### 2. Actor Isolation Correctness [HIGH]
- Actor-isolated state accessed without `await` from outside
- `nonisolated` methods that read/write `self` properties (actor state)
- `@MainActor` methods called from non-MainActor context without `await`

### 3. Reentrancy Hazards [MED/HIGH]
- `guard balance >= amount` → `await logSomething()` → `balance -= amount` (stale state)
- Any check-then-act pattern with an `await` between the check and the mutation

### 4. GCD in Async Context [MED/HIGH]
- `DispatchQueue.main.async` inside `async` function → redundant, use `@MainActor` directly
- `DispatchSemaphore.wait()` in async context → deadlock risk
- `waitUntilExit()` on cooperative thread without `@concurrent` → actor starvation
- `DispatchGroup.enter/leave` in code that should use `withTaskGroup`

### 5. Missing @MainActor [MED]
- `@Observable` or `ObservableObject` classes mutating `@Published` from background tasks
- Delegate methods touching UIKit/AppKit without isolation guarantee

### 6. Task Hygiene [LOW/MED]
- `Task.detached` without stored handle (leak risk)
- Long tasks without `Task(name:)`
- Missing `try Task.checkCancellation()` in looping tasks

## Step 4: Structured Report

Output:

```
## Swift Concurrency Audit Report
Scope: [files/directories audited]
Files with concurrency signals: N / Total
```

Then a table:

```
| File | GCD | Blocking | Actors | Tasks | Escape Hatches |
|------|-----|----------|--------|-------|----------------|
| ...  | N   | N        | N      | N     | N              |
```

Then each issue:

```
[SEVERITY] Category: path/file.swift:Line
  Problem: description
  Fix: correction
```

Then top 3 recommendations (highest leverage changes).

Then verdict:
- `CONCURRENCY-SAFE` — zero issues found
- `ISSUES FOUND: N critical, M high, P medium, Q low`

## Swift 6.2 Behavioral Notes

Apply these rules while reviewing:
- `nonisolated async func` in Swift 6.2 (NonisolatedNonsendingByDefault) stays on caller's actor — if it does blocking work, it needs `@concurrent`
- SE-0418: structs/enums with all-Sendable stored properties are Sendable automatically — don't report these as gaps
- `Task { }` inherits actor isolation from the enclosing scope; `Task.detached { }` does not — flag detached tasks that access actor state
- `@concurrent` is the correct replacement for `DispatchQueue.global().async` wrapping an async function
