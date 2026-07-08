# Swift 6.3 & 6.4 Changes

What changed after Swift 6.2 (the "approachable concurrency" baseline). Use this to
keep generated code current. As of mid-2026, **6.3.3 is stable** and **6.4 (WWDC 2026)
is the newest** — verify 6.4 details against the official release notes once published,
since the swift.org 6.4 release post was not yet available at harvest time.

Grounding: apple/swift-migration-guide, swift.org/blog/swift-6.3-released, and
developer coverage (avanderlee.com) for the 6.4 concurrency proposals.

---

## Swift 6.3 (2026-03-24) — mostly non-concurrency

6.3 focused on interop, tooling, and platforms rather than the concurrency model:

- **C interoperability** — `@c` attribute to expose Swift functions/enums to C.
- **Module selectors** — `ModuleA::symbol` syntax to disambiguate APIs imported from
  multiple modules.
- **Performance control** — `@specialize`, `@inline(always)`, `@export(implementation)`.
- **Android SDK** — official Swift SDK for Android.
- **Swift Testing** — warning issues, test cancellation, image attachments.
- **`weak let` (SE-0481)** — the one concurrency-relevant change; see below.

Nothing in 6.3 changes how you write actors/`Sendable`/`async` from 6.2.

---

## Swift 6.4 (WWDC 2026) — concurrency ergonomics

### Async `defer` (SE-0493)
`defer` bodies in an `async` function may now contain `await`. Asynchronous cleanup
runs like synchronous deferred cleanup always has — before the function returns.

```swift
func importArticles() async throws {
    let importer = try await Importer.open()
    defer { await importer.close() }   // previously a compile error
    try await importer.run()           // close() runs even if this throws
}
```
Prefer this over a manual `do { … } catch { await cleanup(); throw error }`.

### Task cancellation shields (SE-0504)
`withTaskCancellationShield { }` temporarily prevents code from *observing*
cancellation, so rollback/cleanup that must complete isn't interrupted. Inside the
shield, `Task.isCancelled` returns `false` and cancellation-aware APIs don't throw.

```swift
func persist() async throws {
    try await write(tempFile)
    await withTaskCancellationShield {
        await moveIntoPlace(tempFile)   // must finish atomically
    }
}
```
**Use sparingly.** A shield is for the narrow "interrupting this corrupts state" case.
Do not wrap ordinary work to dodge cancellation — that breaks structured concurrency's
cooperative-cancellation contract.

### Discardable-Task warning + typed throws (SE-0520)
Creating a throwing `Task` without handling its error or storing the handle now emits
a warning — the error was silently dropped before.

```swift
Task { try await importArticles() }          // ⚠️ warning: thrown error ignored

Task {                                        // Fix A: handle inside
    do { try await importArticles() } catch { report(error) }
}
let handle = Task { try await importArticles() }   // Fix B: keep + await later
// ...
try await handle.value
```
Tasks can also pin an exact failure type:
```swift
let task: Task<String, URLError> = Task { throw URLError(.badURL) }
```

### Async `Result` (SE-0530)
Capture an async throwing operation into a `Result` value:
```swift
let result: Result<[Article], any Error> = await Result {
    try await importArticles()
}
```

### `~Sendable` — explicit non-Sendable (SE-0518)
Document *intentional* non-conformance and suppress automatic `Sendable` inference.
Communicates design intent and prevents accidental cross-isolation use.
```swift
enum ExecutionResult: ~Sendable {
    case success
    case failure(NonSendableError)
}
```
Contrast with the Sendable *hierarchy* (SKILL.md): those strategies make a type
Sendable; `~Sendable` is the deliberate opposite.

### `weak let` (SE-0481, shipped in 6.3)
Immutable weak references — no `var` required. Because the reference can't be
reassigned, a class that only needed `@unchecked Sendable` for a `weak var`
delegate can switch to `weak let` and earn *proper* compiler-checked `Sendable`.
```swift
final class Preview: Sendable {
    weak let delegate: PreviewDelegate?   // was: weak var + @unchecked Sendable
}
```

---

## Migration checklist (6.2 → 6.4)

1. Replace manual async-cleanup `do/catch` with `defer { await … }` (SE-0493).
2. Audit throwing `Task { }` sites — the compiler now warns; handle or store each.
3. Introduce `withTaskCancellationShield` only around must-complete cleanup.
4. Swap `weak var` + `@unchecked Sendable` for `weak let` + real `Sendable`.
5. Mark deliberately non-Sendable types `~Sendable` instead of leaving inference implicit.
6. Consider typed-throws `Task<Success, Failure>` where the error type is known.
