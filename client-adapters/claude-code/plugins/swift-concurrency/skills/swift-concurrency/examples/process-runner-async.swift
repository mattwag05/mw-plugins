// process-runner-async.swift
// Transforms the MailBridge / MemosCommand GCD-based Process runner
// into a proper Swift 6.2 async function.
//
// SOURCE PATTERN (pippin/MailBridge/MailBridge.swift:620-691):
//   DispatchGroup + DispatchQueue.global().async for pipe draining
//   DispatchWorkItem timeout on DispatchQueue.global()
//   process.waitUntilExit() blocking the current thread
//
// PROBLEM: In Swift 6.2 with NonisolatedNonsendingByDefault, a
// nonisolated async function stays on the caller's actor. A blocking
// waitUntilExit() inside an @MainActor context starves the main actor.
//
// SOLUTION: Mark the function @concurrent (runs on global executor) and
// wrap the blocking pipe + wait in withCheckedThrowingContinuation.

import Foundation

// ─────────────────────────────────────────────────────────────
// BEFORE (GCD pattern — DO NOT generate for Swift 6.2)
// ─────────────────────────────────────────────────────────────

enum ScriptError: Error {
    case timeout
    case scriptFailed(String)
}

// This function blocks whatever thread calls it, and in async contexts
// can starve the actor it's running on (main actor starvation).
private func runScriptGCD(_ script: String, timeoutSeconds: Int = 10) throws -> String {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
    process.arguments = ["-l", "JavaScript", "-e", script]

    let stdoutPipe = Pipe()
    let stderrPipe = Pipe()
    process.standardOutput = stdoutPipe
    process.standardError  = stderrPipe

    try process.run()

    var stdoutData = Data()
    var stderrData = Data()
    let group = DispatchGroup()

    group.enter()
    DispatchQueue.global().async {
        stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        group.leave()
    }
    group.enter()
    DispatchQueue.global().async {
        stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
        group.leave()
    }

    let timeoutItem = DispatchWorkItem {
        guard process.isRunning else { return }
        process.terminate()
    }
    DispatchQueue.global().asyncAfter(
        deadline: .now() + .seconds(timeoutSeconds),
        execute: timeoutItem
    )

    process.waitUntilExit()  // ← BLOCKS current thread
    timeoutItem.cancel()
    group.wait()

    if process.terminationReason == .uncaughtSignal { throw ScriptError.timeout }
    let out = String(data: stdoutData, encoding: .utf8) ?? ""
    let err = String(data: stderrData, encoding: .utf8) ?? ""
    guard process.terminationStatus == 0 else { throw ScriptError.scriptFailed(err) }
    return out.trimmingCharacters(in: .whitespacesAndNewlines)
}

// ─────────────────────────────────────────────────────────────
// AFTER (Swift 6.2 — @concurrent + structured concurrency)
// ─────────────────────────────────────────────────────────────

// @concurrent: runs on the global executor regardless of caller's isolation.
// This is correct because Process.waitUntilExit() is blocking — it must
// never run on a cooperative actor thread.
@concurrent
func runScript(_ script: String, timeoutSeconds: Int = 10) async throws -> String {
    // Launch in a throwing task group so the timeout can race the process.
    return try await withThrowingTaskGroup(of: String.self) { group in

        // Task A: run the process, drain pipes, return stdout
        group.addTask {
            try await withCheckedThrowingContinuation { continuation in
                // Move blocking work onto a plain OS thread via a detached
                // DispatchQueue to avoid consuming cooperative thread pool.
                DispatchQueue.global(qos: .userInitiated).async {
                    do {
                        let result = try runProcessBlocking(
                            script: script
                        )
                        continuation.resume(returning: result)
                    } catch {
                        continuation.resume(throwing: error)
                    }
                }
            }
        }

        // Task B: timeout sentinel
        group.addTask {
            try await Task.sleep(for: .seconds(timeoutSeconds))
            throw ScriptError.timeout
        }

        // First to finish wins; cancel the other.
        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}

// Synchronous blocking helper — called on a DispatchQueue thread, not
// on the cooperative thread pool. Safe to call waitUntilExit() here.
private func runProcessBlocking(script: String) throws -> String {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
    process.arguments = ["-l", "JavaScript", "-e", script]

    let stdoutPipe = Pipe()
    let stderrPipe = Pipe()
    process.standardOutput = stdoutPipe
    process.standardError  = stderrPipe

    try process.run()

    // Drain concurrently on two DispatchQueue threads to avoid pipe buffer deadlock
    var stdoutData = Data()
    var stderrData = Data()
    let drainGroup = DispatchGroup()

    drainGroup.enter()
    DispatchQueue.global().async {
        stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        drainGroup.leave()
    }
    drainGroup.enter()
    DispatchQueue.global().async {
        stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
        drainGroup.leave()
    }

    process.waitUntilExit()  // safe here — we're on a DispatchQueue thread
    drainGroup.wait()

    if process.terminationReason == .uncaughtSignal { throw ScriptError.timeout }

    let stdout = (String(data: stdoutData, encoding: .utf8) ?? "")
        .trimmingCharacters(in: .whitespacesAndNewlines)
    let stderr = (String(data: stderrData, encoding: .utf8) ?? "")
        .trimmingCharacters(in: .whitespacesAndNewlines)

    guard process.terminationStatus == 0 else { throw ScriptError.scriptFailed(stderr) }
    if !stderr.isEmpty { throw ScriptError.scriptFailed(stderr) }
    return stdout
}

// ─────────────────────────────────────────────────────────────
// Usage from any isolation context:
// ─────────────────────────────────────────────────────────────

@MainActor
func exampleCaller() async throws {
    // Even though we're on the main actor, runScript runs on the global
    // executor (@concurrent). The main actor is freed during the await.
    let output = try await runScript("JSON.stringify({ok: true})", timeoutSeconds: 30)
    print(output)
}
