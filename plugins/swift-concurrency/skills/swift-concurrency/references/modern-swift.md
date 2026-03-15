# Modern Swift 6.2 Features

Beyond the concurrency model, Swift 6.2 introduces several language features that improve expressiveness, performance, and correctness. These are independent of actors and `async`/`await` but frequently appear alongside them in modern Swift code.

---

## Typed Throws (SE-0413)

Functions can now declare the exact error type they throw:

```swift
func parse(_ input: String) throws(ParseError) -> AST { ... }
```

The caller receives a `ParseError` directly — no casting from `any Error` required.

**When to use vs untyped throws:**

Use typed throws when your function has a closed, well-defined error domain: parsers, decoders, validators, and library code with stable public APIs. Prefer untyped `throws` when errors can propagate from multiple sources with different types, or when you do not want to lock your API to a specific error type across versions.

**Typed throws is contagious upward:** If a function calls a `throws(ParseError)` function and wants to rethrow, its own signature must also declare `throws(ParseError)` (or a supertype). Mixing typed-throw callees in a single function that rethrows means you need a common error type or fall back to untyped `throws`.

**Good fit:** Library code with limited error domains — network response parsing, configuration file loading, structured data decoding.

---

## InlineArray (SE-0450)

Fixed-size, stack-allocated arrays with a compile-time-known element count:

```swift
var rgb: InlineArray<3, UInt8> = [255, 128, 0]
```

The size is part of the type. The compiler allocates storage on the stack, avoiding a heap allocation entirely.

**Use when:** You know the count at compile time and care about allocation performance — pixel buffers, small coordinate tuples, fixed-length protocol fields, ring buffer slots.

**Limits:** No dynamic resizing. Size must be a literal integer, not a variable. `InlineArray` does not conform to `Collection` the same way `Array` does — check available APIs before assuming equivalence.

**Not a replacement for `Array`:** For any variable-length or heap-managed data, `Array` remains correct. `InlineArray` is a targeted performance tool.

---

## `weak let` (SE-0481)

Stored properties can now be declared `weak let`, and closures can capture weakly with `[weak let self]`:

```swift
class DataSource {
    weak let delegate: (any Delegate)?
}

someObject.onEvent = { [weak let self] in
    self?.handleEvent()
}
```

**What this eliminates:** The previous pattern required `weak var` for stored properties and `[weak self]` in closures followed by `guard let self = self else { return }` or optional chaining. `weak let` signals that the reference is intentionally weak and will not be reassigned after initialization, without requiring it to be a `var`.

**Practical effect:** Cleaner capture lists, fewer intermediate `guard let` rebindings, and clearer intent at the declaration site.

---

## Task Naming

Long-running tasks can be given human-readable names:

```swift
Task(name: "fetch-user-profile") {
    await userService.fetchProfile(for: userID)
}
```

**Where names appear:** Instruments' Task State lane, Swift concurrency stack traces in crash logs, and the Swift runtime debug output (`SWIFT_DEBUG_CONCURRENCY=1`).

**Practice:** Always name tasks that represent meaningful, identifiable units of work. Use kebab-case names that describe the operation, not the implementation (`"sync-health-records"`, not `"task1"`). Anonymous tasks are fine for trivial fire-and-forget operations.

---

## Swift Testing Enhancements

Swift Testing (the `Testing` module, not XCTest) adds several capabilities in 6.2:

**Typed throw assertions:**

```swift
#expect(throws: ParseError.invalidInput) {
    try parse("???")
}
```

Replaces `XCTAssertThrowsError` with type-checked, expression-based syntax.

**Timeouts:**

```swift
@Test(.timeLimit(.minutes(1)))
func fetchRemoteConfig() async throws { ... }
```

The test runner fails the test if it exceeds the limit, eliminating hung test suites.

**Parameterized tests:**

```swift
@Test(arguments: ["en", "fr", "ja"])
func localizationRoundtrip(locale: String) throws { ... }
```

Each argument value runs as a separate test case with its own pass/fail result. Replaces loops inside a single test body, giving per-case failure visibility.

**Replacing XCTest patterns:** `#expect` replaces `XCTAssert*`, `#require` replaces `XCTUnwrap`, and `withKnownIssue` replaces `XCTExpectFailure`. New code should prefer Swift Testing; XCTest coexists for legacy tests.

---

## Non-Copyable Types (`~Copyable`)

Structs and enums can opt out of the default copy-on-assign behavior:

```swift
struct FileHandle: ~Copyable {
    private let fd: Int32

    consuming func close() {
        Darwin.close(fd)
    }

    deinit {
        Darwin.close(fd)  // called exactly once, deterministically
    }
}
```

**Ownership semantics:** The compiler enforces that a `~Copyable` value is either consumed (moved) or borrowed at each use site. There is no implicit copy. This is ownership tracking without ARC reference counting.

**Method modifiers:**

- `consuming` — the method takes ownership; the value cannot be used after the call.
- `borrowing` — the method reads without taking ownership; the caller retains the value.
- `mutating` — same as today; modifies in place.

**`deinit` is deterministic:** Unlike class `deinit` (which waits for ARC to reach zero), a `~Copyable` struct's `deinit` runs at the exact scope exit where the value is consumed. This makes it suitable for resources that must be released in a predictable order — file descriptors, locks, GPU command buffers.

**When to reach for `~Copyable`:** Wrapping OS resources (file handles, sockets, memory-mapped regions), implementing lock types, or any abstraction where accidental copying would be a semantic error rather than a performance concern.
