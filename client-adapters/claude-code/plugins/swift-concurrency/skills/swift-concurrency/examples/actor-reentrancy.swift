// actor-reentrancy.swift
// Shows the actor reentrancy hazard and the correct fix.
// The BankAccount actor suspends during logTransaction(), which
// allows concurrent callers to interleave — stale state after resume.

import Foundation

// ─────────────────────────────────────────────────────────────
// WRONG: Check-then-act across an await (stale state hazard)
//
// Timeline with two concurrent callers (balance = 100):
//
//   Caller A: guard 100 >= 80 ✓          │
//   Caller A: await logTransaction(80)   ← suspends
//             ↓                          │
//   Caller B: guard 100 >= 90 ✓          ← stale! sees pre-suspend balance
//   Caller B: await logTransaction(90)   ← suspends
//             ↓                          │
//   Caller A: balance -= 80  → 20        │
//   Caller B: balance -= 90  → -70  ← OVERDRAFT, no error thrown
// ─────────────────────────────────────────────────────────────

actor BankAccountWrong {
    var balance: Double

    init(balance: Double) { self.balance = balance }

    enum BankError: Error { case insufficient }

    func withdraw(_ amount: Double) async throws {
        guard balance >= amount else { throw BankError.insufficient }
        await logTransaction(amount)   // ← suspends; another caller may run
        balance -= amount              // ← WRONG: balance may have changed
    }

    private func logTransaction(_ amount: Double) async {
        // simulate async I/O (database write, audit log, etc.)
        try? await Task.sleep(for: .milliseconds(10))
    }
}

// ─────────────────────────────────────────────────────────────
// CORRECT: Re-validate actor state after every suspension point
// ─────────────────────────────────────────────────────────────

actor BankAccount {
    var balance: Double

    init(balance: Double) { self.balance = balance }

    enum BankError: Error { case insufficient }

    func withdraw(_ amount: Double) async throws {
        // 1. Pre-check before suspending
        guard balance >= amount else { throw BankError.insufficient }

        await logTransaction(amount)   // ← suspends here

        // 2. Re-validate after resuming — another caller may have run
        guard balance >= amount else { throw BankError.insufficient }

        // 3. Now safe to mutate
        balance -= amount
    }

    private func logTransaction(_ amount: Double) async {
        try? await Task.sleep(for: .milliseconds(10))
    }
}

// ─────────────────────────────────────────────────────────────
// ALSO CORRECT: Capture state to a local before suspending,
// then use the local for the computation (avoids re-read).
// Pattern: "snapshot the inputs you need before any await".
// ─────────────────────────────────────────────────────────────

actor DataProcessor {
    private var pendingItems: [String] = []

    func processBatch() async {
        // Snapshot the list BEFORE suspending so we work on a stable set.
        let batch = pendingItems
        pendingItems.removeAll()

        for item in batch {
            await processItem(item)   // ← suspends; pendingItems may grow
            // We don't re-read pendingItems here — we work from `batch`.
        }
    }

    private func processItem(_ item: String) async {
        try? await Task.sleep(for: .milliseconds(5))
    }

    func add(_ item: String) { pendingItems.append(item) }
}
