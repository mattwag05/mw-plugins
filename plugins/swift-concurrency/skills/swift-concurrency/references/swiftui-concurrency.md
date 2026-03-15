# SwiftUI Concurrency Reference

## Views Are @MainActor

Every SwiftUI `View` body runs on the main actor. The `View` protocol itself is annotated `@MainActor`, which means the `body` property, all `@State` property accesses, and any synchronous helper methods called from `body` are automatically on the main thread.

What this means in practice:

- You do **not** need `await MainActor.run { }` inside a `View` body or any `@MainActor`-isolated method — you are already there.
- Calling `await MainActor.run { }` inside `body` is redundant and adds overhead.
- Any `async` function you `await` from `body` will suspend and resume on the main actor (unless the callee switches actors internally).

```swift
// Correct — no MainActor.run needed here
struct ContentView: View {
    @State private var title = "Hello"

    var body: some View {
        Text(title)
            .onAppear {
                // Still on main actor — no special annotation needed
                title = "Appeared"
            }
    }
}
```

## .task Modifier: Lifecycle and Cancellation

The `.task { }` modifier creates a `Task` that is tied to the view's lifetime. When the view disappears, SwiftUI automatically cancels the task. This makes it the correct hook for async work that should stop when the user navigates away.

Use `.task` for:

- Network requests that populate view state
- Consuming `AsyncSequence` streams (WebSocket, NotificationCenter async sequences, etc.)
- Any async setup work that should not outlive the view

```swift
struct FeedView: View {
    @State private var items: [FeedItem] = []

    var body: some View {
        List(items) { item in ItemRow(item: item) }
            .task {
                // Cancelled automatically when FeedView disappears
                do {
                    for await item in FeedService.shared.liveStream() {
                        items.append(item)
                    }
                } catch {
                    // Handle cancellation or network error
                }
            }
    }
}
```

The `for await in` loop cooperates with structured cancellation: when SwiftUI cancels the task, the next suspension point in the loop throws `CancellationError` and exits cleanly.

## @Observable Isolation

Types annotated with `@Observable` (Swift 5.9+) are **not** automatically `@MainActor`. The macro synthesizes observation tracking, but it does not change actor isolation. If your model mutates properties that drive UI updates, those mutations must happen on the main actor — otherwise you get a data race warning (or a runtime crash in strict concurrency).

The correct pattern is to annotate the class explicitly:

```swift
@MainActor
@Observable
class ViewModel {
    var items: [String] = []

    func load() async {
        let fetched = await DataService.shared.fetchItems()
        items = fetched  // safe: already @MainActor
    }
}
```

Without `@MainActor`, calling `items = fetched` from a background context is a data race even if `items` is only read from `body`.

## Async in Event Handlers

SwiftUI action closures (Button, onTapGesture, etc.) are synchronous — they cannot be `async`. The correct pattern for kicking off async work from a button is to create an unstructured `Task`:

```swift
Button("Load") {
    Task {
        await vm.load()
    }
}
```

The `Task { }` inherits the actor context of the enclosing scope. Because `body` is `@MainActor`, the task starts on the main actor and `vm.load()` can freely hop to a background executor inside its own implementation.

Do **not** write `Button("Load") { await vm.load() }` — action closures are not async and the compiler will reject it.

## Common SwiftUI Mistakes to Avoid

**Using Task.detached in a button action**
`Task.detached` explicitly discards actor context and is not tied to the view's lifetime. It will keep running after the view is gone and loses access to `@MainActor` context. Use `Task { }` instead — it inherits context and is cancellable via the parent scope.

**Calling DispatchQueue.main.async inside .task**
You are already on the main actor inside `.task` (unless you explicitly hop away). Wrapping a mutation in `DispatchQueue.main.async` inside a `.task` block adds a queue hop and a context switch for no benefit. Write the mutation directly.

**Accessing @State from a background Task**
`@State` properties are main-actor-isolated. Capturing them in a `Task.detached` or reading them from a non-isolated context is a data race. Pass the value as a local copy before entering the task, or keep the task `@MainActor`.

**Missing @MainActor on a ViewModel that mutates @Published or @Observable properties**
If a view model updates properties from a background async function without `@MainActor` isolation, SwiftUI may render inconsistent state or crash under Swift 6 strict concurrency. Annotate the class `@MainActor` unless you have a deliberate, carefully synchronized reason not to.
