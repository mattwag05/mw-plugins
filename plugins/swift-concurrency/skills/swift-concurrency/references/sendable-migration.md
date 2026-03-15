# Sendable Migration Reference — Swift 6.2

## Diagnosing Sendable Warnings

| Warning Pattern | What It Means | Where to Look |
|---|---|---|
| `Sending 'x' risks causing data races` | A value is leaving its isolation domain without a `sending` annotation | The call site — check whether the callee accepts `sending` |
| `Type 'Foo' does not conform to 'Sendable'` | The type crosses a concurrency boundary but cannot be proven safe | The type definition — look for mutable stored properties |
| `Capture of 'x' with non-sendable type 'T' in a `@Sendable` closure` | A closure escaping to another isolation domain captures a non-Sendable value | The closure body — identify the captured variable |
| `Non-sendable type 'T' returned from actor-isolated ... cannot cross actor boundary` | An actor method returns a non-Sendable value to a different isolation domain | The actor method's return type |
| `Stored property 'x' of 'Sendable'-conforming struct has non-sendable type 'T'` | SE-0418 inference cannot proceed because a property blocks conformance | Each stored property of the struct or class |
| `Main actor-isolated property 'x' can not be referenced from a non-isolated context` | Accessing `@MainActor` state without being on the main actor | The access site — add `await` or annotate the caller |

---

## 6 Sendable Strategies

### Strategy 1: Proper Conformance (Value Types + SE-0418 Inference)

Make the type genuinely Sendable by ensuring all stored properties are Sendable. SE-0418 means structs and enums with all-Sendable stored properties now get implicit conformance in Swift 6 mode — you often just need to remove the block.

```swift
// Swift 6.2: implicit Sendable — no explicit conformance needed
struct AudioMetadata {
    let id: UUID
    let title: String
    let duration: TimeInterval
}

// Explicit conformance when properties are all Sendable but inference is suppressed
struct Config: Sendable {
    var maxRetries: Int
    var timeout: Duration
}
```

### Strategy 2: Move to Actor

If the type has mutable state that must be shared across tasks, make it an actor. The compiler then enforces serialized access automatically.

```swift
// Before: class with racy mutable state
class Cache { var items: [String: Data] = [:] }

// After: actor with safe mutable state
actor Cache {
    private var items: [String: Data] = [:]
    func store(_ data: Data, for key: String) { items[key] = data }
    func retrieve(for key: String) -> Data? { items[key] }
}
```

### Strategy 3: `sending` Parameter (SE-0430)

Use `sending` when a function needs to accept a value and transfer ownership to a different isolation domain. This is a fine-grained alternative to requiring `Sendable` conformance on the type itself.

```swift
func enqueue(_ work: sending () -> Void) async {
    await Task { work() }.value
}

func upload(_ payload: sending RequestPayload) async throws {
    try await networkClient.post(payload)
}
```

### Strategy 4: `@Sendable` Closure

Annotate a closure type with `@Sendable` when it will be called from a different isolation domain. This forces the compiler to check that everything captured by the closure is also Sendable.

```swift
func schedule(after delay: Duration, work: @Sendable @escaping () -> Void) {
    Task {
        try? await Task.sleep(for: delay)
        work()
    }
}
```

### Strategy 5: `nonisolated(unsafe)` with Lock Comment

For a known-safe wrapper around inherently mutable state (e.g., a lock-protected cache), use `nonisolated(unsafe)` and document the synchronization mechanism clearly.

```swift
final class ThreadSafeLogger: Sendable {
    // Protected by NSLock below — safe to treat as Sendable
    nonisolated(unsafe) private var entries: [String] = []
    private let lock = NSLock()

    func log(_ message: String) {
        lock.withLock { entries.append(message) }
    }
}
```

### Strategy 6: `@unchecked Sendable` (Last Resort)

Suppresses all compiler checking. Use only for types where correctness is externally guaranteed and cannot be expressed in the type system. Always include a comment explaining why it is safe.

```swift
// @unchecked Sendable: underlying C library guarantees thread-safe reference counting
final class OpaqueHandle: @unchecked Sendable {
    private let handle: OpaquePointer
    init(_ handle: OpaquePointer) { self.handle = handle }
}
```

---

## SE-0418 Enhanced Sendable Inference

**Types that now get automatic inference (Swift 6 mode):**

- Structs where every stored property is `Sendable`
- Enums where every associated value is `Sendable`
- Tuples where every element is `Sendable`
- Generic types where the generic parameters constrained to `Sendable` cover all stored state

**Types that still need explicit conformance:**

- Classes (reference semantics — compiler cannot guarantee exclusive access)
- Actors (they conform to `Sendable` automatically through the actor mechanism, not SE-0418)
- Structs or enums that contain non-Sendable stored properties — fix the property type first, or apply a strategy above
- `@MainActor`-isolated types (they are `Sendable` but via isolation, not property inference)
- Types crossing module boundaries where the source module was compiled without Swift 6 mode

**Practical rule:** In Swift 6.2, try adding `: Sendable` to a struct and let the compiler tell you which stored properties are the blockers. Fix those properties first before reaching for `@unchecked Sendable`.

---

## Migration Checklist

1. **Enable Swift 6 mode** per target in Xcode: Build Settings → Swift Language Version → Swift 6. Migrate one target at a time, starting with leaf targets (no dependents).

2. **Triage warnings by category** using the diagnostic table above. Group them: missing conformances, closure captures, actor boundary crossings.

3. **Fix leaf types first.** Types used widely throughout the codebase must be resolved before warnings in their callers make sense.

4. **Apply Strategy 1 (proper conformance)** wherever possible. Check if SE-0418 already infers conformance — the warning may disappear just by removing a suppression annotation.

5. **Convert shared mutable state to actors** (Strategy 2). This is usually the highest-value change and resolves entire clusters of warnings at once.

6. **Annotate closure-heavy APIs** with `@Sendable` and `sending` (Strategies 3 and 4). Update all call sites afterward.

7. **Reserve `nonisolated(unsafe)`** (Strategy 5) for wrappers around OS-level primitives or C interop where lock discipline is maintained manually. Add a comment at the declaration.

8. **Reserve `@unchecked Sendable`** (Strategy 6) for third-party types you cannot modify. File an issue with the upstream library.

9. **Run `swift build` with `-strict-concurrency=complete`** (or rely on Swift 6 mode) and confirm zero concurrency warnings before merging.

10. **Review actor boundaries in tests.** `XCTestCase` runs on the main thread; async test methods may require `@MainActor` annotations or explicit `await MainActor.run { }` blocks to avoid warnings in test targets.
