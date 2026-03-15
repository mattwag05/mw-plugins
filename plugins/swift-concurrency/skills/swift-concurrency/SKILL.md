---
description: >
  Activate when writing or reviewing Swift code containing async, await, actor,
  Sendable, @Sendable, Task, @MainActor, @concurrent, nonisolated, DispatchQueue,
  DispatchGroup, withCheckedContinuation, withTaskGroup, AsyncSequence, or when
  the user asks about Swift concurrency, strict concurrency checking, data races,
  actor isolation, Swift 6 migration, or approachable concurrency.
---

# Swift 6.2 Concurrency Patterns

This skill ensures every Swift concurrency pattern you generate is correct under
Swift 6.2 strict concurrency. Read it before writing or reviewing any async/actor code.

---

## Swift 6.2 Approachable Concurrency Model

Swift 6.2 introduced "approachable concurrency" — a deliberate three-phase model
designed so developers adopt only the complexity they need.

**Phase A — Single-threaded default (SE-0466)**
When you compile with `-Xswiftc -default-isolation MainActor` (or enable the
`DefaultIsolation` feature flag), every type without explicit isolation is implicitly
`@MainActor`. This eliminates the majority of Sendable warnings immediately.
Use this phase for UI-heavy apps and command-line tools where parallelism is rare.

**Phase B — Async/await**
Add `async`/`await` for sequential concurrency without crossing isolation boundaries.
`async` functions on the main actor stay on the main actor. Use `Task { }` to launch
async work from sync context; the task inherits the caller's actor isolation.

**Phase C — @concurrent for explicit parallelism (SE-0461)**
Only reach for `@concurrent` when you genuinely need background execution. This
attribute moves a function to the global executor regardless of the caller's isolation.
Use it for CPU-bound work (image processing, JSON parsing of large payloads,
Process/pipe runners) that must not block the main actor.

**Decision rule:** Start at Phase A. Add `@concurrent` only for specific functions
confirmed to be slow. Avoid `Task.detached` — it loses actor isolation context and
structured concurrency lifetime guarantees.

---

## The @concurrent Attribute (SE-0461)

**Breaking change in Swift 6.2:** `nonisolated async` functions now run on the
*caller's* actor by default, not on the global executor. This prevents accidental
main-actor blocking in prior Swift versions — but it also means code written before
6.2 may now block the caller unexpectedly.

**Before Swift 6.2 (legacy — DO NOT generate):**
```swift
nonisolated func processPayload(_ data: Data) async -> Result { ... }
// Ran on global executor — safe but implicit
```

**Swift 6.2 correct:**
```swift
@concurrent func processPayload(_ data: Data) async -> Result { ... }
// Explicit: runs on global executor regardless of caller's isolation
```

**When to use `@concurrent`:**
- CPU-bound work (image decode, crypto, JSON parse >100 KB)
- `Process` + `Pipe` runners (always block until subprocess exits)
- Networking continuation wrappers
- Any function measured to exceed ~5 ms on the main actor

**When NOT to use `@concurrent`:**
- Simple async functions that just chain other awaits
- Functions that update UI or access main-actor state
- Short async operations (database reads via WAL, small JSON)

---

## Sendable Enforcement Hierarchy

Apply in order — stop at the first strategy that fits. Lower numbers are always preferred.

1. **Proper `Sendable` conformance** — value types (`struct`, `enum`) with all-Sendable
   stored properties get it for free under SE-0418. Add `extension Foo: Sendable {}` to
   make it explicit and document intent.

2. **Move to an `actor`** — mutable reference types that are accessed from multiple
   isolation domains belong in actors. Let the compiler enforce thread safety.

3. **`sending` parameter/return annotation (SE-0430)** — when you need to transfer
   ownership of a non-Sendable value across isolation boundaries exactly once.
   `func enqueue(_ work: sending Work)` — the caller cannot use `work` after the call.

4. **`@Sendable` closure** — for closure parameters that cross boundaries.
   `func onComplete(_ handler: @Sendable () -> Void)`.

5. **`nonisolated(unsafe)`** — only for values protected by an external lock/atomic
   not visible to the compiler. Add a comment naming the lock. Never use without one.

6. **`@unchecked Sendable`** — last resort, only for third-party types you cannot modify
   (e.g. wrapping legacy ObjC types with known-safe threading). Document why in a comment.
   **Never generate this for your own types without a lock protecting all mutation.**

---

## Feature Flags Quick Reference

Enable in `Package.swift` via `.enableUpcomingFeature("FlagName")` inside `swiftSettings`.
Xcode: Build Settings → Swift Compiler - Upcoming Features.

| Flag | SE | One-line effect | Risk |
|---|---|---|---|
| `ExistentialAny` | SE-0352 | Requires `any Protocol` syntax for existentials | Low — mechanical rename |
| `StrictConcurrency` | SE-0337 | Full actor isolation checking (Swift 6 level) | High — expect many warnings |
| `GlobalActorIsolatedTypesUsability` | SE-0434 | Eases restrictions on global-actor-isolated types in generic code | Low |
| `DefaultIsolation` | SE-0466 | Makes `@MainActor` the default for all types (approachable concurrency Phase A) | Medium — changes semantics |
| `NonisolatedNonsendingByDefault` | SE-0461 | `nonisolated async` stays on caller's actor; use `@concurrent` for global executor | Medium — changes execution context |

**Recommended adoption order:**
1. `ExistentialAny` — no concurrency impact, purely syntactic
2. `DefaultIsolation` — largest benefit/noise ratio for single-threaded apps
3. `GlobalActorIsolatedTypesUsability` — unblocks generic code
4. `NonisolatedNonsendingByDefault` — requires auditing all `nonisolated async` functions
5. `StrictConcurrency` — enable last; fix remaining warnings before enabling Swift 6 mode

Do **not** jump straight to `StrictConcurrency`. Fix each flag's warnings before adding the next.

---

## Anti-Patterns — NEVER Generate

**1. Blanket `@unchecked Sendable` on your own mutable types**
```swift
// WRONG — hides real data races
class Cache: @unchecked Sendable { var items: [String: Data] = [:] }
```
Fix: Make `Cache` an `actor`.

**2. `DispatchQueue.main.async` inside an async function**
```swift
// WRONG — defeats structured concurrency, creates a second async hop
func update() async { DispatchQueue.main.async { self.label.text = "done" } }
```
Fix: The function is already on the main actor if annotated `@MainActor`. Just assign directly.

**3. `Task.detached` without explicit cancellation**
```swift
Task.detached { await self.loadData() }  // WRONG — unstructured, leaks on view disappear
```
Fix: Use `.task {}` modifier in SwiftUI, or store and cancel in `deinit`.

**4. Synchronous blocking in a `nonisolated async` context (pre-6.2)**
```swift
nonisolated func run() async { process.waitUntilExit() }  // WRONG in 6.2 — blocks caller's actor
```
Fix: Mark `@concurrent`.

**5. Accessing actor state without `await`**
```swift
actor Counter { var value = 0 }
let c = Counter()
print(c.value)  // WRONG — compile error in Swift 6
```
Fix: `await c.value` (or expose via async computed property).

**6. `nonisolated(unsafe)` without naming the protecting lock**
```swift
nonisolated(unsafe) var cache: [String: Data] = [:]  // WRONG — no lock named
```
Fix: Add a `NSLock` or use `@Mutex`, document it above the declaration.

**7. Mixing GCD + structured concurrency for the same resource**
```swift
DispatchQueue.global().async { self.processItem() }
await withTaskGroup(of: Void.self) { group in ... }
```
Fix: Pick one. Prefer structured concurrency; wrap legacy GCD in `withCheckedContinuation`.

---

## Actor Reentrancy

Actors suspend on `await` and can interleave with other callers. The most common bug:
check-then-act on actor state across an `await`.

**Wrong (stale state after suspension):**
```swift
actor BankAccount {
    var balance: Double = 0
    func withdraw(_ amount: Double) async throws {
        guard balance >= amount else { throw BankError.insufficient }
        await logTransaction(amount)   // ← suspends here
        balance -= amount              // ← stale! another withdraw may have run
    }
}
```

**Correct (re-validate after resume):**
```swift
func withdraw(_ amount: Double) async throws {
    guard balance >= amount else { throw BankError.insufficient }
    await logTransaction(amount)
    guard balance >= amount else { throw BankError.insufficient }  // re-check
    balance -= amount
}
```

**Rule:** Capture actor state to local constants before any `await`. After resuming,
re-read state from the actor; never trust pre-await snapshots.

See `examples/actor-reentrancy.swift` for a complete runnable example.

---

## GCD Migration Decision Tree

| Legacy pattern | Swift 6.2 replacement |
|---|---|
| `DispatchQueue.global().async { }` | `@concurrent func` + `Task { await fn() }` |
| `DispatchQueue.main.async { }` | Direct call in `@MainActor` context |
| `DispatchGroup.enter/leave` | `withTaskGroup(of: T.self) { }` |
| `DispatchSemaphore.wait()` | `async let` or `TaskGroup`; **never** semaphore in async — deadlocks |
| `process.waitUntilExit()` | `withCheckedThrowingContinuation` + `@concurrent` |
| Completion handler `func(Result) -> Void` | `async throws -> Result` |
| `OperationQueue` | `TaskGroup` with `maxConcurrentTasks` |

See `references/gcd-to-async.md` and `examples/process-runner-async.swift` for
full annotated migrations.

---

## SwiftLint Concurrency Rules

Four opt-in SwiftLint rules are relevant to Swift 6.2 concurrency. Enable them in `.swiftlint.yml`:

```yaml
opt_in_rules:
  - async_without_await           # flags async funcs that never await
  - incompatible_concurrency_annotation  # catches @Sendable/@concurrent conflicts
  - unhandled_throwing_task       # requires try on Task bodies that throw
# Enabled by default:
# - redundant_sendable            # removes @unchecked Sendable where not needed
```

Run `swiftlint --fix` after enabling — `redundant_sendable` has an auto-correction.

---

## Cross-References

| Topic | File |
|---|---|
| Sendable strategies + migration checklist | `references/sendable-migration.md` |
| Actor reentrancy, @concurrent deep dive, SE-0470/0466/0472/0371 | `references/actor-patterns.md` |
| SwiftUI @MainActor, .task, @Observable | `references/swiftui-concurrency.md` |
| Full GCD→async translations with code | `references/gcd-to-async.md` |
| Feature flag details and adoption order | `references/feature-flags.md` |
| Typed throws, InlineArray, weak let, modern Swift | `references/modern-swift.md` |
| All 6 Sendable strategies in runnable code | `examples/sendable-conformance.swift` |
| Actor reentrancy: wrong + correct | `examples/actor-reentrancy.swift` |
| MailBridge-style GCD Process runner → async | `examples/process-runner-async.swift` |
| @concurrent vs nonisolated async | `examples/concurrent-attribute.swift` |
