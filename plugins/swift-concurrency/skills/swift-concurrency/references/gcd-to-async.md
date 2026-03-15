# GCD to Swift Concurrency Translation Guide

## 1. Mental Model Shift

GCD is a **push** model: you push closures onto queues and the runtime decides when to drain them. Queues are objects you hold references to, and synchronization is achieved by serializing access through a specific queue.

Swift structured concurrency is a **pull** model: tasks run where they are needed, based on actor isolation and executor annotations. The compiler tracks which actor a function runs on at the type level. Instead of pushing work onto a queue, you declare where code runs (via `@MainActor`, `@concurrent`, or actor types) and the runtime routes execution accordingly.

The key shift: stop thinking in terms of "which queue does this go on" and start thinking in terms of "what actor owns this state."

---

## 2. DispatchQueue.global().async — Background Work

**Before (GCD):**
```swift
func parseJSON(data: Data, completion: @escaping (Result<[Item], Error>) -> Void) {
    DispatchQueue.global(qos: .userInitiated).async {
        do {
            let items = try JSONDecoder().decode([Item].self, from: data)
            completion(.success(items))
        } catch {
            completion(.failure(error))
        }
    }
}
```

**After (Swift Concurrency):**
```swift
func parseJSON(data: Data) async throws -> [Item] {
    try JSONDecoder().decode([Item].self, from: data)
}
// Call from a non-isolated or @concurrent context; the runtime schedules on
// the cooperative thread pool automatically.
```

Non-isolated `async` functions run on the cooperative thread pool — equivalent to `DispatchQueue.global()` without the manual queue management.

---

## 3. DispatchQueue.main.async — UI Updates

**Before (GCD):**
```swift
DispatchQueue.global().async {
    let result = expensiveComputation()
    DispatchQueue.main.async {
        self.label.text = result
    }
}
```

**After (Swift Concurrency):**
```swift
@MainActor
func updateUI(with result: String) {
    label.text = result
}

Task {
    let result = await expensiveComputation()
    await updateUI(with: result)  // hops to main actor automatically
}
```

Or with `@MainActor` on the call site directly:
```swift
Task {
    let result = await expensiveComputation()
    await MainActor.run { label.text = result }
}
```

---

## 4. DispatchGroup.enter/leave — Parallel Work

**Before (GCD):**
```swift
let group = DispatchGroup()
var results: [Data] = []
let lock = NSLock()

for url in urls {
    group.enter()
    URLSession.shared.dataTask(with: url) { data, _, _ in
        if let data { lock.lock(); results.append(data); lock.unlock() }
        group.leave()
    }.resume()
}

group.notify(queue: .main) {
    process(results)
}
```

**After (Swift Concurrency):**
```swift
let results = try await withTaskGroup(of: Data.self) { group in
    for url in urls {
        group.addTask { try await URLSession.shared.data(from: url).0 }
    }
    var collected: [Data] = []
    for try await data in group {
        collected.append(data)
    }
    return collected
}
```

No locks, no `enter`/`leave` bookkeeping. `withTaskGroup` is structured — all child tasks complete before the group returns.

---

## 5. DispatchSemaphore — DANGER: Never Use in Async Context

**Before (GCD):**
```swift
let semaphore = DispatchSemaphore(value: 1)
DispatchQueue.global().async {
    semaphore.wait()
    doWork()
    semaphore.signal()
}
```

**WARNING:** Calling `semaphore.wait()` inside an `async` context blocks the underlying thread. The Swift cooperative thread pool has a limited number of threads (roughly matching CPU core count). Blocking threads with semaphores can exhaust the pool, causing all other async tasks to deadlock — the system has no free threads to run the task that would eventually call `semaphore.signal()`.

**Never do this:**
```swift
Task {
    semaphore.wait()  // DEADLOCK RISK — blocks cooperative thread
    await doWork()
    semaphore.signal()
}
```

**After (Swift Concurrency) — use an actor for mutual exclusion:**
```swift
actor WorkSerializer {
    func doWork() async {
        // Actor guarantees serial access — no semaphore needed
        await actualWork()
    }
}
```

Or use `async let` / `TaskGroup` for limiting concurrency (see section 8).

---

## 6. Process + Pipe Synchronous Runner — The Pippin MailBridge Pattern

This is the pattern used in Pippin's `MailBridge` to run `osascript` and collect output without blocking the main thread.

**Before (synchronous GCD wrapper):**
```swift
func runScript(_ script: String) throws -> String {
    let process = Process()
    let pipe = Pipe()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
    process.arguments = ["-l", "JavaScript", "-e", script]
    process.standardOutput = pipe
    process.launch()
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    process.waitUntilExit()
    return String(data: data, encoding: .utf8) ?? ""
}
// Called from DispatchQueue.global().async { ... }
```

**After (async with continuation):**
```swift
func runScript(_ script: String) async throws -> String {
    try await withCheckedThrowingContinuation { continuation in
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let process = Process()
                let stdoutPipe = Pipe()
                let stderrPipe = Pipe()
                process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
                process.arguments = ["-l", "JavaScript", "-e", script]
                process.standardOutput = stdoutPipe
                process.standardError = stderrPipe
                try process.run()
                // Drain pipes concurrently to avoid deadlock on large output
                let stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
                let stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                if process.terminationStatus != 0 {
                    let msg = String(data: stderrData, encoding: .utf8) ?? "unknown error"
                    continuation.resume(throwing: MailBridgeError.scriptFailed(msg))
                } else {
                    let output = String(data: stdoutData, encoding: .utf8) ?? ""
                    continuation.resume(returning: output)
                }
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
}
```

The `withCheckedThrowingContinuation` bridges the callback-based `Process` API into the async world. The GCD dispatch inside is intentional — `Process` is not async-native and must block a thread; isolating it in a GCD async call prevents it from blocking the cooperative pool directly.

---

## 7. Completion Handlers — Bridging to async throws

**Before (GCD completion handler):**
```swift
func fetch(url: URL, completion: @escaping (Result<Data, Error>) -> Void) {
    URLSession.shared.dataTask(with: url) { data, _, error in
        if let error { completion(.failure(error)); return }
        completion(.success(data ?? Data()))
    }.resume()
}
```

**After (async throws):**
```swift
func fetch(url: URL) async throws -> Data {
    try await withCheckedThrowingContinuation { continuation in
        URLSession.shared.dataTask(with: url) { data, _, error in
            if let error {
                continuation.resume(throwing: error)
            } else {
                continuation.resume(returning: data ?? Data())
            }
        }.resume()
    }
}
```

Rules for `withCheckedThrowingContinuation`:
- Resume **exactly once** — resuming zero times leaks the task; resuming twice crashes.
- Use `withCheckedContinuation` (non-throwing) when the callback never fails.
- `withUnsafeThrowingContinuation` skips the double-resume check — only use in performance-critical hot paths where you are certain of correctness.

---

## 8. OperationQueue with maxConcurrentOperationCount — TaskGroup with Concurrency Limit

**Before (GCD / OperationQueue):**
```swift
let queue = OperationQueue()
queue.maxConcurrentOperationCount = 4
for item in items {
    queue.addOperation { process(item) }
}
queue.waitUntilAllOperationsAreFinished()
```

**After (TaskGroup with actor-based concurrency limiter):**
```swift
actor ConcurrencyLimiter {
    private let max: Int
    private var running = 0
    private var waiting: [CheckedContinuation<Void, Never>] = []

    init(max: Int) { self.max = max }

    func acquire() async {
        if running < max { running += 1; return }
        await withCheckedContinuation { waiting.append($0) }
        running += 1
    }

    func release() {
        running -= 1
        if let next = waiting.first {
            waiting.removeFirst()
            next.resume()
        }
    }
}

let limiter = ConcurrencyLimiter(max: 4)

await withTaskGroup(of: Void.self) { group in
    for item in items {
        await limiter.acquire()
        group.addTask {
            defer { Task { await limiter.release() } }
            await process(item)
        }
    }
}
```

For simpler cases where order does not matter and you only need to limit fan-out, chunking the input array into batches of N and processing each batch with `withTaskGroup` is often sufficient and easier to reason about.
