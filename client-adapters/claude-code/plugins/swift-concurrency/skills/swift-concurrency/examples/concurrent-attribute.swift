// concurrent-attribute.swift
// Side-by-side: default nonisolated async (Swift 6.2) vs @concurrent.
// Illustrates the SE-0461 behavioral change and when to use each.

import Foundation

// ─────────────────────────────────────────────────────────────
// CONTEXT: Swift 6.2 NonisolatedNonsendingByDefault (SE-0461)
//
// Before Swift 6.2:
//   nonisolated async func → ran on global executor (implicit)
//
// After Swift 6.2 (with NonisolatedNonsendingByDefault enabled):
//   nonisolated async func → runs on CALLER'S actor (safer default)
//   @concurrent async func → runs on global executor (explicit opt-in)
// ─────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────
// PATTERN A: Default nonisolated async (stays on caller's actor)
//
// Use when: the function just chains other async calls, never
// blocks, and doesn't need background execution.
// ─────────────────────────────────────────────────────────────

struct UserRepository {
    private let database: DatabaseClient

    // Stays on caller's actor in Swift 6.2.
    // Safe when `database.fetch()` is also async and non-blocking.
    nonisolated func fetchUser(id: String) async throws -> User {
        try await database.fetch(User.self, id: id)
    }
}

// ─────────────────────────────────────────────────────────────
// PATTERN B: @concurrent — explicit global executor
//
// Use when: CPU-bound work, blocking I/O, or subprocess execution
// that must not run on the caller's actor thread.
// ─────────────────────────────────────────────────────────────

struct ImageProcessor {
    // @concurrent: always runs on global executor.
    // Safe to call from @MainActor — does NOT block the main actor
    // while decoding the image.
    @concurrent
    func decode(_ data: Data) async throws -> ProcessedImage {
        // Heavy CPU work — would stall main actor if not @concurrent
        let raw = try decodeJPEG(data)
        let filtered = applyFilters(raw)
        return filtered
    }

    // Private helpers (synchronous — called from @concurrent context)
    private func decodeJPEG(_ data: Data) throws -> RawImage { RawImage() }
    private func applyFilters(_ raw: RawImage) -> ProcessedImage { ProcessedImage() }
}

// ─────────────────────────────────────────────────────────────
// DEMONSTRATION: What happens when called from @MainActor
// ─────────────────────────────────────────────────────────────

@MainActor
final class ContentViewModel {
    var image: ProcessedImage?
    private let processor = ImageProcessor()
    private let repo = UserRepository(database: DatabaseClient())

    func loadImage(data: Data) async throws {
        // @concurrent → main actor is FREE during this await
        // (processor.decode runs on global executor)
        image = try await processor.decode(data)
    }

    func loadUser(id: String) async throws -> User {
        // nonisolated async → stays on main actor (SE-0461 default)
        // Fine here because database.fetch() is non-blocking async
        try await repo.fetchUser(id: id)
    }
}

// ─────────────────────────────────────────────────────────────
// DECISION RULE (comment this near your function declarations)
// ─────────────────────────────────────────────────────────────
//
//  Does this function...
//  ├── block a thread (waitUntilExit, semaphore, URLSessionData+completion)?
//  │   └── YES → @concurrent  (must not block cooperative thread pool)
//  ├── do CPU-bound work >5ms (image decode, JSON parse >100 KB)?
//  │   └── YES → @concurrent
//  ├── launch a subprocess (Process + Pipe)?
//  │   └── YES → @concurrent
//  └── just chain other async calls?
//      └── nonisolated (or omit — caller's isolation is fine)
//

// ─────────────────────────────────────────────────────────────
// Stubs to make the file self-contained (not runnable as-is)
// ─────────────────────────────────────────────────────────────

struct User { let id: String }
struct RawImage {}
struct ProcessedImage {}
struct DatabaseClient {
    func fetch<T>(_ type: T.Type, id: String) async throws -> T { fatalError() }
}
