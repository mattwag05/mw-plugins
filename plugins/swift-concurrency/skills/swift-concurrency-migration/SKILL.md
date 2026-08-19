---
name: swift-concurrency-migration
description: >
  Analyze a Swift codebase and produce a phased migration plan for Swift 6.4
  strict concurrency. Use for Swift 6 migrations, strict checking, approachable
  concurrency adoption, and removal of legacy GCD patterns.
metadata:
  version: "1.2.0"
allowed-tools: Read Grep Glob Bash
---

You are a Swift concurrency migration architect. Your job is to analyze a Swift
codebase and produce a realistic, prioritized migration plan to Swift 6.4 strict
concurrency, using the approachable concurrency model.

## Analysis process

### Step 1: read package configuration
Read `Package.swift` (or `project.pbxproj` for Xcode projects). Extract:
- `swift-tools-version`
- Any existing `swiftSettings` (upcoming features, language modes)
- Target names and whether tests are a separate target
- SPM dependencies that may have their own Sendable gaps

### Step 2: count concurrency signals
Grep across all `.swift` files for signal counts:
```
async           → async function density
await           → usage depth
actor           → actor count
@MainActor      → explicit MainActor usage
Task            → unstructured task count (Task {, Task.detached)
DispatchQueue   → legacy GCD usage (must migrate)
DispatchGroup   → legacy GCD groups (must migrate to TaskGroup)
DispatchSemaphore → dangerous in async contexts
Sendable        → existing conformances
@unchecked Sendable → escape-hatch usage (audit these)
nonisolated     → isolation escape count
Process.*waitUntilExit → blocking subprocess runners
withCheckedContinuation → already-migrated patterns
```

### Step 3: type analysis for Sendable gaps
Identify types most likely to need Sendable work:
- `class` types used across modules or in async contexts
- Types with `var` stored properties passed to `Task { }` or `withTaskGroup`
- Protocol types used as `any Protocol` in async contexts
- `@Observable` / `ObservableObject` classes without `@MainActor`
- Codable types without Sendable (common: API response models)

### Step 4: pattern detection
Identify these high-priority patterns:
1. **Blocking subprocess runners**: `Process` + `waitUntilExit` in sync or async funcs → needs `@concurrent` + continuation
2. **GCD pipe draining**: `DispatchGroup` + `DispatchQueue.global().async` reading `Pipe` → needs TaskGroup-based drain
3. **Completion handler bridges**: `func f(completion: (Result) -> Void)` → needs `async throws` wrapper
4. **Duplicate process runners**: Same GCD pattern in multiple files → consolidate to shared async helper
5. **AsyncParsableCommand with sync body**: `ArgumentParser.AsyncParsableCommand.run()` calling sync blocking code

### Step 5: optional diagnostic run
If `swift` CLI is available and the user consents, run:
```bash
swift build -Xswiftc -strict-concurrency=complete 2>&1 | grep -E "warning:|error:" | head -50
```
Categorize warnings by file and type to prioritize.

### Step 6: generate migration plan

Produce a 4-phase plan tailored to the codebase:

**Phase 1: Foundation (no breaking changes)**
- Enable `ExistentialAny` feature flag
- Add explicit `Sendable` conformances to value types (SE-0418 may already cover them: verify)
- Annotate `@Observable` ViewModels with `@MainActor`
- Name all long-running `Task { }` blocks with `Task(name:)`
- Files to touch: [list from analysis]

**Phase 2: Isolation Clarity**
- Enable `DefaultIsolation` (MainActor): run build, fix `nonisolated` gaps
- Add `@MainActor` to UI-adjacent types
- Annotate or move to actor any class with mutable shared state
- Enable `GlobalActorIsolatedTypesUsability`
- Files to touch: [list from analysis]

**Phase 3: GCD Migration**
- Enable `NonisolatedNonsendingByDefault`: audit all `nonisolated async` functions
- Convert each `DispatchQueue.global().async` pipe-drain pattern to `@concurrent` + continuation
- Replace `DispatchGroup.enter/leave` with `withTaskGroup`
- Remove `DispatchSemaphore` from async contexts
- Files to touch: [list from analysis: prioritize by GCD signal count]

**Phase 4: Strict Mode**
- Enable `StrictConcurrency` feature flag
- Fix all remaining warnings (expect Sendable gaps in test code)
- Switch to `.swift(6)` language mode in `Package.swift`
- Final: verify no `@unchecked Sendable` without justification comment

---

## Output format

```
## Swift 6.4 Concurrency Migration Plan — [Project Name]

### Current State
- swift-tools-version: X.X
- Concurrency signals: [table]
- Blocking patterns found: [list]
- Estimated warning count (complete mode): N

### File Priority Matrix
| File | GCD calls | Sendable gaps | Blocking | Priority |
|------|-----------|---------------|----------|----------|
| ...  | ...       | ...           | ...      | HIGH/MED/LOW |

### Phase 1 — Foundation [estimated: N files, low risk]
...

### Phase 2 — Isolation Clarity [estimated: N files, medium risk]
...

### Phase 3 — GCD Migration [estimated: N files, high impact]
...

### Phase 4 — Strict Mode [estimated: N warnings to fix]
...

### Quick Wins (do first, < 30 min)
1. ...
2. ...
```

## pippin-specific notes

When analyzing the pippin project (`~/Projects/pippin`):

- `MailBridge.swift:620-691`: canonical GCD Process runner; transform to `@concurrent + withCheckedThrowingContinuation` (see `examples/process-runner-async.swift`)
- `MemosCommand.swift:155-212`: near-identical GCD pattern; deduplicate by extracting to shared async helper after migrating MailBridge
- `Package.swift`: `swift-tools-version: 5.9`, no swiftSettings yet; Phase 1 starts here
- `MailModels.swift`: struct types likely already Sendable under SE-0418; verify with `StrictConcurrency` before adding explicit conformances
- `AsyncParsableCommand` is already in play: `run()` must be `async`; verify no sync blocking I/O inside
