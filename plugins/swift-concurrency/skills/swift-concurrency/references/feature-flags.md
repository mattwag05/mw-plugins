# Swift Upcoming Feature Flags

Swift's upcoming feature flags let you adopt Swift 6 behavior incrementally while staying in Swift 5.x language mode. Each flag gates a single semantic change, so you can migrate one concern at a time before committing to the full Swift 6 language mode.

---

## How to Enable

**Package.swift:**

```swift
targets: [
    .target(
        name: "MyTarget",
        swiftSettings: [
            .enableUpcomingFeature("ExistentialAny"),
            .enableUpcomingFeature("StrictConcurrency"),
        ]
    )
]
```

**Xcode Build Settings:**

Navigate to your target's Build Settings, search for "Upcoming Features", and find **Swift Compiler - Upcoming Features**. Add flag names (without quotes) one per line under "Enable Upcoming Features".

---

## Per-Flag Details

### 1. `ExistentialAny` (SE-0352)

Existential types (protocol-typed values that erase the concrete type) must now be written with an explicit `any` prefix: `any Collection`, `any Error`, `any Sendable`.

**What changes:** Bare protocol names used as types — `func process(_ items: Collection)` — become errors. The compiler can no longer silently box a value into an existential.

**Migration steps:**

1. Build with the flag enabled and collect all errors.
2. Global find-replace is safe here: `(: )([A-Z][A-Za-z]+)` where the matched name is a protocol. Most IDEs and `swift-migrate` tooling handle this mechanically.
3. Pay attention to `some` vs `any`: use `some` for opaque return types (single concrete type, erased from signature) and `any` for true existentials (heterogeneous collections, stored properties that vary at runtime).

**Risk: Low.** Purely syntactic. No runtime behavior changes.

---

### 2. `StrictConcurrency` (SE-0337)

Enables full Swift 6 actor-isolation checking as warnings rather than errors. The compiler audits every crossing of actor boundaries, every `Sendable` requirement, and every data race potential.

**What warnings appear:** Missing `Sendable` conformances on types crossing actor boundaries, calls to non-isolated async functions from isolated contexts, mutable state shared across actors without synchronization.

**Fix strategies:**

- Add `@MainActor` to UI types that are always used on the main thread.
- Mark value types `Sendable` (usually automatic for structs with Sendable stored properties).
- Use `nonisolated` to explicitly opt functions out of actor isolation.
- Wrap legacy non-Sendable types in `@unchecked Sendable` as a last resort, documenting why.

**Risk: High.** This flag surfaces the most warnings of any flag in this list. Enable it last, after the others are clean, so you are not fighting multiple semantic changes simultaneously.

---

### 3. `GlobalActorIsolatedTypesUsability` (SE-0434)

Allows `@MainActor`-isolated types to conform to protocols that have `nonisolated` requirements (such as `Hashable`, `Equatable`, `Codable`, and many others).

**Why this was blocked before:** A `@MainActor` type could not satisfy a `nonisolated` protocol requirement because the compiler could not guarantee the conformance would be called off the main thread safely.

**Example:**

```swift
// Previously a compile error, now allowed:
@MainActor
final class ViewModel: Hashable {
    var id: UUID
    nonisolated func hash(into hasher: inout Hasher) { hasher.combine(id) }
    nonisolated static func == (lhs: ViewModel, rhs: ViewModel) -> Bool { lhs.id == rhs.id }
}
```

**Risk: Low.** Widens what was previously a hard error into valid code.

---

### 4. `DefaultIsolation` (SE-0466)

`@MainActor` isolation becomes the implicit default for all types that do not have explicit isolation declared. Class, struct, enum, and actor declarations without an isolation annotation inherit `@MainActor`.

**What stays non-isolated:** Free functions (module-scope `func` not inside a type), extensions on non-isolated types unless the extension itself is annotated, and any declaration explicitly marked `nonisolated`.

**Opting out:**

```swift
nonisolated func computeHash(_ input: Data) -> String { ... }  // stays off main actor

nonisolated final class BackgroundProcessor { ... }  // entire type is nonisolated
```

**Risk: Medium.** Correct for most UI-heavy targets. Can produce unexpected main-actor requirements in utility types — audit with the compiler before enabling in library code.

---

### 5. `NonisolatedNonsendingByDefault` (SE-0461)

`nonisolated async` functions no longer hop to the global cooperative executor by default. They now inherit and stay on the caller's actor, matching the behavior of synchronous `nonisolated` functions.

**Before this flag:** A `nonisolated async func` would always hop off the caller's actor to the global pool, which was surprising and often unnecessary.

**After this flag:** The function runs on whatever actor the caller is on. To explicitly dispatch to the global executor, annotate with `@concurrent`.

**Migration — grep your codebase:**

```bash
grep -rn "nonisolated.*async" Sources/
```

For each hit, decide: should this truly run on the global executor (`@concurrent`)? Or is staying on the caller's actor correct (no change needed)?

**Risk: Medium.** Behavioral change for existing `nonisolated async` functions that relied on the implicit executor hop.

---

## Recommended Adoption Order

1. **`ExistentialAny`** — mechanical, low risk, cleans up protocol-as-type ambiguity before concurrency work begins.
2. **`GlobalActorIsolatedTypesUsability`** — unlocks conformances you likely already want; no new warnings.
3. **`DefaultIsolation`** — establishes your isolation baseline; surfaces types that need explicit annotation.
4. **`NonisolatedNonsendingByDefault`** — audit `nonisolated async` behavior now that your isolation model is clear.
5. **`StrictConcurrency`** — enable last; by this point most issues are already resolved and remaining warnings are targeted.

---

## Interaction with `swift-tools-version`

Setting `.swift(6)` in `swiftSettings` (or using `swift-tools-version: 6.0` with a `.swift(6)` language mode directive) enables **all** Swift 6 checks at once as hard errors, not warnings. Upcoming feature flags are for **gradual adoption in Swift 5.x mode** — you keep `swift-tools-version: 5.10` (or similar) and add flags one at a time. Once all flags pass cleanly, switching to `.swift(6)` should produce zero new errors.
