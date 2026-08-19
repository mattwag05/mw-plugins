# Swift concurrency

Current Swift concurrency guidance for implementation, review, and migration work.

## Skills

| Skill | Purpose |
| --- | --- |
| `swift-concurrency` | Write code with strict isolation, Sendable, tasks, actors, and current language behavior. |
| `swift-concurrency-review` | Audit code for traceable concurrency defects and report them by severity. |
| `swift-concurrency-migration` | Inspect a codebase and plan staged adoption of strict concurrency. |

References cover actor patterns, feature flags, GCD migration, Sendable work, SwiftUI, and Swift 6.3 to 6.4 changes. Runnable examples live under `skills/swift-concurrency/examples/`.

The generated Claude Code adapter keeps `/swift-audit`, `concurrency-reviewer`, and `swift-migration-planner` as thin wrappers around the portable skills.
