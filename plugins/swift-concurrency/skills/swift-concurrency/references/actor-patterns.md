# Actor Patterns Reference — Swift 6.2

## Actor Fundamentals

Every actor defines an **isolation domain** — a serial execution context that the compiler enforces. Code inside the actor runs with exclusive access to the actor's mutable state. Code outside must cross the boundary, which requires `await`.

**What is automatic:**
- `self`-method calls from within the actor body are synchronous (no `await`)
- Conformance to `Sendable` is granted automatically by the actor mechanism
- The compiler rejects cross-boundary access that does not use `await`

**What requires explicit annotation:**
- Properties or methods that are safe to call from outside without `await` must be marked `nonisolated`
- Actor-to-actor calls always require `await`, even between two actor instances of the same type

```swift
actor AudioSession {
    private var isRecording = false

    func start() { isRecording = true }          // synchronous inside

    nonisolated var description: String {        // safe to call without await
        "AudioSession"
    }
}

let session = AudioSession()
await session.start()                           // await required from outside
print(session.description)                      // no await — nonisolated
```

---

## Reentrancy Deep Dive

Actors are reentrant: when a method suspends at an `await`, other callers can run on the actor before the first method resumes. This is by design (prevents deadlock), but creates a **check-then-act hazard**.

```
Time ──────────────────────────────────────────────────────►

Caller A:  enter loadTrack()
           check: cache miss ─── await fetchFromDisk() ───────────── resume ── store in cache ── return
                                          │
Caller B:                         enters loadTrack()
                                  check: cache miss ─── await fetchFromDisk() ─── resume ── DOUBLE STORE
```

Caller B sees a cache miss because Caller A had not yet stored the result when B ran. Both fetch from disk.

**The fix: re-validate state after every `await`.**

```swift
actor TrackLoader {
    private var cache: [String: AudioTrack] = [:]
    private var inFlight: [String: Task<AudioTrack, Error>] = [:]

    func load(id: String) async throws -> AudioTrack {
        if let cached = cache[id] { return cached }        // 1. check cache

        if let existing = inFlight[id] {                   // 2. reuse in-flight task
            return try await existing.value
        }

        let task = Task { try await AudioTrack.fetch(id: id) }
        inFlight[id] = task
        let track = try await task.value                   // 3. suspend here
        cache[id] = track                                  // 4. re-validate unnecessary: task dedup handles it
        inFlight.removeValue(forKey: id)
        return track
    }
}
```

---

## Global Actors

A **global actor** is a singleton actor that provides a named isolation domain shared across the codebase. `@MainActor` is the canonical example: it serializes execution on the main thread.

**Defining a custom global actor:**

```swift
@globalActor
actor RenderActor {
    static let shared = RenderActor()
}

@RenderActor
func drawFrame(_ frame: VideoFrame) { /* ... */ }

@RenderActor
class RenderPipeline {
    var currentFrame: VideoFrame?   // protected by RenderActor
}
```

**When custom global actors make sense:**
- A subsystem (audio engine, render pipeline, database layer) needs its own serial queue semantics without coupling every caller to a specific actor instance
- You want `@RenderActor` annotations to be as natural as `@MainActor`
- Third-party callbacks arrive on an unknown thread and you want to funnel them into a known context

---

## @concurrent Attribute (SE-0461)

`@concurrent` marks a function or closure as running on the Swift cooperative thread pool — explicitly not inheriting the caller's isolation context.

**Behavioral change from Swift 6.1:** In Swift 6.1, `nonisolated async` functions could inherit the caller's actor context in some cases. SE-0461 makes the break explicit and opt-in.

```swift
// Runs on cooperative pool, never on caller's actor
@concurrent
func processInBackground(_ data: Data) async -> ProcessedResult {
    // CPU-intensive work, safe to run off the main actor
    return heavyTransform(data)
}
```

**Decision checklist:**
- Is this function CPU-intensive and safe to parallelize? Use `@concurrent`.
- Does it need to read/write actor state? Do not use `@concurrent` — keep actor isolation.
- Is it a nonisolated utility used by many actors? `@concurrent` makes the intent explicit and prevents accidental isolation inheritance.

---

## Isolated Conformances (SE-0470)

Protocol conformances can now be scoped to a specific actor's isolation domain. The conformance is only usable from within that actor.

```swift
protocol Renderable {
    func render()
}

@MainActor
class ViewController: Renderable {
    // This conformance is @MainActor-isolated
    // Callers must be on MainActor to use ViewController as Renderable
    func render() { view.setNeedsDisplay() }
}
```

This eliminates the previous workaround of marking the protocol method `@MainActor` globally, which infected every conforming type.

---

## Default MainActor Isolation (SE-0466)

The compiler flag `-default-isolation MainActor` (or the module-level `@MainActor` annotation) makes every declaration in the target implicitly `@MainActor` unless otherwise annotated.

**What `nonisolated` means in this world:** It explicitly opts a declaration out of the default `@MainActor` isolation, moving it to the cooperative thread pool (for async functions) or making it synchronously callable from any context (for sync functions and properties).

```swift
// With -default-isolation MainActor:
class ViewModel {
    var title: String = ""          // implicitly @MainActor

    nonisolated func hash() -> Int { // explicitly not @MainActor
        title.hashValue              // ERROR: cannot access @MainActor property here
    }

    nonisolated func staticID() -> String { "vm-\(UUID())" }  // fine — no actor state
}
```

**When to apply:** Large UIKit/SwiftUI app targets where nearly all code runs on the main actor. Enable per-target in Xcode via "Swift Compiler — Other Flags". Do not apply to library targets shared across threading contexts.

---

## Task.immediate (SE-0472)

`Task.immediate` starts executing synchronously on the caller's current executor until it hits its first suspension point, then continues asynchronously.

This differs from `Task { }`, which always hops to the cooperative thread pool before starting — creating an observable delay.

```swift
// Task { } — schedules asynchronously, control returns to caller immediately
Task { await updateUI() }  // updateUI() may not start before next runloop turn

// Task.immediate — starts now, on the caller's executor
Task.immediate { await updateUI() }  // updateUI() runs synchronously until first await
```

**Use case:** Replacing `DispatchQueue.main.async { }` in `@MainActor` code when you need the work to begin in the current runloop turn — for example, starting an animation immediately or updating state before the next layout pass.

---

## Isolated deinit (SE-0371)

Actors can declare `isolated deinit`, which runs on the actor's own executor (not the thread that released the last reference). This makes it safe to access actor-isolated state during deinitialization.

```swift
actor ResourceManager {
    var openHandles: [FileHandle] = []

    isolated deinit {
        // Runs on ResourceManager's executor — safe to access openHandles
        for handle in openHandles {
            try? handle.close()
        }
        openHandles.removeAll()
    }
}
```

**Without `isolated deinit`:** The default actor `deinit` is `nonisolated` and cannot safely access `openHandles` — doing so produces a compiler error in Swift 6 mode.

**Constraint:** `isolated deinit` cannot contain `await` expressions. If async cleanup is needed, store a cleanup task or use a `withTaskGroup` pattern triggered before the actor is released.
