---
name: xcode-docs-and-search
description: This skill should be used when the user asks to "generate documentation", "add DocC comments", "document this function", "document this class", "search apple documentation", "look up in apple docs", "search the apple developer docs", "how does [Apple API] work", "build the documentation", or any task involving DocC documentation generation or searching Apple's developer documentation through Xcode.
version: 1.0.0
---

# Xcode Documentation and Apple Docs Search

Use the Xcode MCP to generate DocC documentation for Swift symbols and search Apple's developer documentation. Both operations use Xcode's built-in intelligence and require the project to be open.

## Searching Apple Developer Documentation

Search Apple's developer documentation through Xcode's integrated docs:

```
"Search Apple documentation for URLSession async await"
"Look up the SwiftData @Model macro in Apple docs"
"Find the Apple documentation for WidgetKit timeline"
"Search docs for AVFoundation capture session setup"
"How does NavigationStack work? Search Apple docs"
"Look up the documentation for withAnimation in SwiftUI"
```

**Effective search strategies:**
- Include the **framework name** for faster results: "SwiftUI Text", "Foundation URLSession", "Combine Publisher"
- Search by **task**, not just symbol: "SwiftUI list selection", "Core Data batch delete"
- Search for **protocol/type requirements**: "Transferable conformance", "Sendable protocol requirements"
- For new APIs: include version context: "iOS 17 SwiftData", "Swift 6 actor isolation"

**Fallback:** When Xcode is not open, use WebFetch on `https://developer.apple.com/documentation/` or the Apple JSON API:
```
https://developer.apple.com/tutorials/data/{framework}/{slug}.json
```

## Generating DocC Documentation

### Document a Symbol

Xcode generates DocC-style comments (triple-slash `///`) above Swift symbols:

```
"Generate documentation for the UserRepository class"
"Generate DocC comments for the fetchUser(id:) method"
"Document all public functions in NetworkManager.swift"
"Add DocC documentation to the ContentView struct"
```

Xcode will generate:
- `///` Summary line
- `/// - Parameters:` block with each parameter described
- `/// - Returns:` line if the function returns a value
- `/// - Throws:` line if the function throws

### Document an Entire File

```
"Generate DocC documentation for all public symbols in UserRepository.swift"
"Add documentation comments to all undocumented functions in the Models group"
```

### Build the Documentation

After generating comments, build a DocC documentation catalog:

```
"Build documentation for the MyApp target"
"Build the DocC documentation and open it in the documentation viewer"
```

This produces a `.doccarchive` that can be viewed in Xcode's documentation window (Product → Build Documentation) and exported for hosting.

## DocC Comment Format Reference

When writing or reviewing DocC comments manually:

```swift
/// A brief one-line summary.
///
/// Extended discussion can follow after a blank `///` line.
/// Supports **bold**, `code`, and [links](https://developer.apple.com).
///
/// ## Topics
///
/// ### Fetching Data
///
/// - ``fetchUser(id:)``
/// - ``fetchAllUsers()``
///
/// - Parameters:
///   - id: The unique identifier for the user to fetch.
///   - completion: Called when the fetch completes.
/// - Returns: The user with the matching ID, or nil if not found.
/// - Throws: `NetworkError.notFound` if the server returns 404.
/// - Note: This method caches results for 5 minutes.
/// - Important: Must be called from a non-main thread.
func fetchUser(id: String) async throws -> User?
```

## Playground Generation

Use Xcode's playground macro for exploring APIs interactively:

```
"Generate a playground to demonstrate the NetworkManager fetch workflow"
"Add a playground macro to test the UserRepository"
"Create a SwiftUI preview playground for ContentView with sample data"
```

Playgrounds generated via MCP appear in the file with `#Preview` or `#Playground` macros and render in Xcode's canvas.

## Tips for Effective Documentation

- **Request documentation by scope:** "Document the public API of UserRepository" is better than "document everything"
- **Review generated docs:** Xcode generates reasonable summaries but parameter descriptions may be generic — refine them with Edit tool
- **DocC links:** Use backtick-escaped symbol names (`` ``SymbolName`` ``) to create cross-references that work in Xcode's documentation viewer
- **Markdown in DocC:** Standard CommonMark markdown works inside DocC comments including code blocks, lists, and headers
