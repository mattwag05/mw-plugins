// sendable-conformance.swift
// Demonstrates all 6 Sendable strategies in order of preference.
// Compile with: swiftc -swift-version 6 sendable-conformance.swift

import Foundation

// ─────────────────────────────────────────────────────────────
// STRATEGY 1: Proper conformance — value types (preferred)
// Structs with all-Sendable stored properties conform automatically
// under SE-0418; explicit conformance documents intent.
// ─────────────────────────────────────────────────────────────

struct MailMessage: Sendable {
    let id: String
    let subject: String
    let from: String
    let body: String?          // String? is Sendable
    let attachmentURLs: [URL]  // [URL] is Sendable (URL: Sendable)
}

// Enums are Sendable when all associated values are Sendable
enum MailResult: Sendable {
    case success([MailMessage])
    case failure(String)
}

// ─────────────────────────────────────────────────────────────
// STRATEGY 2: Move to an actor
// Mutable reference types accessed from multiple isolation domains
// belong in actors. The compiler enforces all access rules.
// ─────────────────────────────────────────────────────────────

actor MailCache {
    private var messages: [String: MailMessage] = [:]
    private var lastFetched: Date?

    func store(_ message: MailMessage) {
        messages[message.id] = message
        lastFetched = Date()
    }

    func lookup(id: String) -> MailMessage? {
        messages[id]
    }
}

// ─────────────────────────────────────────────────────────────
// STRATEGY 3: `sending` parameter annotation (SE-0430)
// Transfer ownership of a non-Sendable value across isolation
// boundaries exactly once. Caller cannot use it after the call.
// ─────────────────────────────────────────────────────────────

// A non-Sendable work item (reference type, no internal sync)
class RenderJob {
    let payload: Data
    var result: UIImage?   // hypothetical
    init(payload: Data) { self.payload = payload }
}

// typealias UIImage = AnyObject  // (for compilation without UIKit)

actor RenderQueue {
    func enqueue(_ job: sending RenderJob) async {
        // job is exclusively ours now — safe to mutate
        _ = job.payload  // process
    }
}

// ─────────────────────────────────────────────────────────────
// STRATEGY 4: @Sendable closure
// For closure parameters that cross isolation domains.
// ─────────────────────────────────────────────────────────────

struct WorkItem {
    let name: String
    let action: @Sendable () async -> Void  // closure is Sendable
}

func schedule(_ items: [WorkItem]) async {
    await withTaskGroup(of: Void.self) { group in
        for item in items {
            group.addTask {
                await item.action()   // safe: action is @Sendable
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────
// STRATEGY 5: nonisolated(unsafe) — requires external lock
// ONLY when an external synchronization mechanism exists that
// the compiler cannot see. Always name the lock in a comment.
// ─────────────────────────────────────────────────────────────

final class SharedRegistry {
    // Protected by `_lock` — all access must hold this lock.
    private let _lock = NSLock()
    nonisolated(unsafe) private var _storage: [String: Any] = [:]

    func set(_ value: Any, for key: String) {
        _lock.withLock { _storage[key] = value }
    }

    func get(_ key: String) -> Any? {
        _lock.withLock { _storage[key] }
    }
}

extension SharedRegistry: Sendable {}  // safe: all access through _lock

// ─────────────────────────────────────────────────────────────
// STRATEGY 6: @unchecked Sendable — absolute last resort
// Only for third-party/ObjC types you cannot modify.
// Document WHY it's safe. Never use for your own mutable types.
// ─────────────────────────────────────────────────────────────

// Hypothetical ObjC wrapper — thread-safe internally per its documentation.
// NSXPCConnection is documented as thread-safe in Apple's API reference.
struct XPCBridge: @unchecked Sendable {
    // SAFETY: NSXPCConnection is documented thread-safe (Apple API reference).
    // All method calls are dispatched through XPC's internal queue.
    private let connection: AnyObject  // represents NSXPCConnection
}
