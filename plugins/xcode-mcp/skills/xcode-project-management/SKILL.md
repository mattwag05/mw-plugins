---
name: xcode-project-management
description: This skill should be used when the user asks to "add a file to xcode", "add a new target", "add an entitlement", "enable a capability", "add a Swift package", "add an SPM dependency", "add a framework", "change deployment target", "configure code signing", "add a build phase", "create a new group in xcode", or any task that requires modifying the Xcode project structure rather than just editing Swift source code.
version: 1.0.0
---

# Xcode Project Management

Use the Xcode MCP to modify project structure — adding files, targets, entitlements, capabilities, and dependencies. These operations modify the `.xcodeproj` or `Package.swift` and are best done via MCP rather than manual XML editing, which can corrupt project state.

## Adding Files to the Project

Creating a Swift file and adding it to an Xcode project are two separate steps:

1. **Create the file** using the Write tool (writes to disk)
2. **Register it** with Xcode using the MCP

```
"Add Sources/Features/LoginView.swift to the MyApp target in the Features group"
"Add the newly created NetworkManager.swift file to the MyApp target under the Networking group"
"Create a new Swift file called UserRepository.swift in the Data group of the MyApp target"
```

**Group hierarchy tip:** Specify the parent group to place the file in the right location in Xcode's navigator. Xcode groups don't have to match the filesystem structure, but keeping them aligned is best practice.

## Adding New Targets

```
"Add a new SwiftUI iOS app target called MyAppWidget"
"Add a Widget Extension target called HomeWidget to the project"
"Add a unit test target called MyAppTests"
"Add a UI test target called MyAppUITests"
"Add a framework target called CoreData for sharing code"
"Add a Swift package product to the existing Package.swift"
```

After adding a target, set its deployment target and bundle ID:
```
"Set the deployment target for the HomeWidget target to iOS 17.0"
"Set the bundle identifier for the HomeWidget target to com.mycompany.myapp.homewidget"
```

## Entitlements and Capabilities

### Adding Entitlements

```
"Add the com.apple.security.network.client entitlement to the MyApp target"
"Add the HealthKit entitlement to the main app target"
"Add the background fetch background mode entitlement"
```

### Enabling Capabilities (Xcode Managed)

Xcode capabilities (which modify both entitlements and provisioning) are best requested as:

```
"Enable the Push Notifications capability for the MyApp target"
"Enable iCloud with CloudKit for the MyApp target"
"Enable HealthKit for the MyApp target"
"Enable App Groups and add the group com.mycompany.shared"
"Enable Sign In with Apple for the main target"
"Enable Background Modes with background fetch and remote notifications"
```

Common capabilities: Push Notifications, iCloud, HealthKit, HomeKit, App Groups, Sign In with Apple, In-App Purchase, Wallet, Network Extensions, Associated Domains.

### Associated Domains

```
"Add the associated domain webcredentials:myapp.com to the main target"
"Add applinks:myapp.com to the associated domains entitlement"
```

## Swift Package Manager Dependencies

### Adding Packages (App Targets)

For app targets (not package-only projects), use Xcode MCP to avoid manual xcodeproj edits:

```
"Add the Swift package at https://github.com/apple/swift-algorithms.git to the project"
"Add swift-algorithms version 1.2.0 as a dependency and link it to the MyApp target"
"Add the Alamofire package (https://github.com/Alamofire/Alamofire.git) with version up to next major from 5.0.0"
```

### For Package.swift Projects

For Swift package targets, directly edit `Package.swift` using the Edit tool — SPM reads it directly without Xcode registration:

```swift
// Edit Package.swift directly: add to dependencies array
.package(url: "https://github.com/apple/swift-algorithms.git", from: "1.2.0"),
// and to target's dependencies:
.product(name: "Algorithms", package: "swift-algorithms"),
```

Then resolve via Xcode MCP:
```
"Resolve Swift package dependencies in the current project"
```

## Build Settings

```
"Set the Swift language version to Swift 6 for the MyApp target"
"Set SWIFT_STRICT_CONCURRENCY to complete for the MyApp target"
"Set the deployment target to iOS 17.0 for all targets"
"Add DEBUG_MODE=1 to the debug build configuration preprocessor macros"
"Enable whole module optimization for the release configuration"
"Set ENABLE_TESTABILITY to YES for the debug configuration"
```

## Build Phases

```
"Add a Run Script build phase to the MyApp target that runs swiftlint"
"Add SwiftLint as a build phase that runs: ${BUILD_DIR}/../../SourcePackages/checkouts/SwiftLint/.build/debug/swiftlint"
"Add a Copy Files build phase to embed the framework in the app bundle"
"Move the Compile Sources phase before the Run Script phase in MyApp"
```

## Code Signing

For code signing issues, Xcode MCP can configure but the provisioning profile must exist in your Apple Developer account:

```
"Set automatic signing for the MyApp target with team [TEAM_ID]"
"Set the provisioning profile to MyApp Distribution for the release configuration"
"Set CODE_SIGN_IDENTITY to Apple Development for the debug configuration"
```

## Project Configuration Tips

- **Xcodeproj edits via MCP** are tracked in Xcode's conversation history and can be rolled back
- **Package.swift edits** via Write/Edit tool are not tracked by Xcode's history — use version control
- **Entitlement keys** follow Apple's reverse-DNS convention: `com.apple.developer.*` for managed capabilities, `com.apple.security.*` for sandbox
- **Target membership** must be set when adding files — a file on disk but not in the project is invisible to the compiler
