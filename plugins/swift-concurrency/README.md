# swift-concurrency Plugin

A Claude Code plugin that teaches correct Swift 6.2 concurrency patterns, provides
proactive code review, and generates phased migration plans.

## Why This Plugin Exists

Swift 6.2 introduced "approachable concurrency" — a paradigm shift with changes that
Claude doesn't know about by default:

- **`@concurrent` attribute (SE-0461)** — `nonisolated async` now runs on the *caller's*
  actor, not the global executor. `@concurrent` opts back into global executor.
- **`NonisolatedNonsendingByDefault`** — the feature flag enabling the above
- **Default MainActor isolation (SE-0466)** — opt entire targets into implicit `@MainActor`
- **`Task.immediate` (SE-0472)** — starts synchronously on caller's executor
- **Isolated conformances (SE-0470)** — protocol conformances can be actor-scoped
- **Five feature flags** — each with different risk levels and adoption order

Without this plugin, Claude generates pre-6.2 patterns: `DispatchQueue.global().async`
wrappers, blanket `@unchecked Sendable`, and `nonisolated async` functions that now
block the main actor.

## Components

### Skill: `swift-concurrency`

Auto-activates when writing or reviewing Swift code with async/await, actors, or GCD.

- Swift 6.2 approachable concurrency model (3 phases)
- `@concurrent` attribute usage rules
- Sendable enforcement hierarchy (6 strategies, prefer order)
- Feature flags quick reference table
- 7 anti-patterns to never generate
- Actor reentrancy hazards and fixes
- GCD→async migration decision tree
- SwiftLint concurrency rule configuration

### Reference Documents

| File | Purpose |
|------|---------|
| `references/sendable-migration.md` | Diagnosing warnings, 6 strategies, checklist |
| `references/actor-patterns.md` | Reentrancy, `@concurrent`, SE-0470/466/472/371 |
| `references/swiftui-concurrency.md` | @MainActor views, .task, @Observable |
| `references/gcd-to-async.md` | 8 GCD→async translations with code |
| `references/feature-flags.md` | 5 flags, adoption order, Package.swift syntax |
| `references/modern-swift.md` | Typed throws, InlineArray, weak let, etc. |

### Example Code

| File | Shows |
|------|-------|
| `examples/sendable-conformance.swift` | All 6 Sendable strategies in runnable code |
| `examples/actor-reentrancy.swift` | Wrong vs correct reentrancy patterns |
| `examples/process-runner-async.swift` | MailBridge GCD runner → `@concurrent` + continuation |
| `examples/concurrent-attribute.swift` | `@concurrent` vs `nonisolated async` side-by-side |

### Agents

**`concurrency-reviewer`** (red) — Proactive code review after writing Swift concurrency code.
Reviews 6 categories: Sendable gaps, actor isolation, reentrancy, GCD, missing @MainActor, task hygiene.

**`swift-migration-planner`** (blue) — Analyzes a codebase and produces a 4-phase migration
plan to Swift 6.2 strict concurrency. Use with "plan my Swift 6 migration".

### Command: `/swift-audit [path]`

On-demand concurrency audit. Scans the specified file, directory, or entire project.
Reports issues by severity with actionable fixes.

```
/swift-audit                        # audit all .swift files
/swift-audit pippin/MailBridge/     # audit a directory
/swift-audit pippin/MailBridge/MailBridge.swift  # audit one file
```

## Compatibility

This plugin complements `swift-lsp@claude-plugins-official` (build diagnostics, code
navigation). No build hooks — zero conflicts.

SwiftLint rules referenced (all in `.swiftlint.yml`):
- `async_without_await` (opt-in)
- `incompatible_concurrency_annotation` (opt-in)
- `unhandled_throwing_task` (opt-in)
- `redundant_sendable` (enabled by default, has auto-fix)
