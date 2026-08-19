---
name: xcode-testing
description: Use when the user asks to "run tests", "run unit tests", "run UI tests", "run a specific test", "check test coverage", "run the test suite", "why is this test failing", "set up a test plan", "XCTest", or any task involving running or analyzing tests in an Xcode project.
metadata:
  version: "1.0.0"
---

# Xcode testing via MCP

Use the Xcode MCP to run tests, inspect results, and manage test plans. The MCP routes requests to Xcode's test runner, which provides live feedback and integrates with Test Navigator.

## Running tests

### Run all tests

```
"Run all tests in the project"
"Run the full test suite"
"Build and test the MyApp scheme"
```

### Run a specific test target

```
"Run all tests in the MyAppTests target"
"Run the MyAppUITests UI test target"
```

### Run a specific test class

```
"Run all tests in the UserRepositoryTests test class"
"Run the LoginViewModelTests test class"
```

### Run a single test method

```
"Run the test UserRepositoryTests/testFetchUserReturnsCorrectData"
"Run only the testLoginWithValidCredentials test method in AuthTests"
```

### Run tests matching a pattern

```
"Run all tests whose names contain 'Network'"
"Run tests in the DataLayer group"
```

## Interpreting test results

The MCP response includes Xcode's test output. Key patterns to look for:

```
Test Suite 'MyAppTests' started
Test Case '-[MyAppTests.UserRepositoryTests testFetchUser]' started
Test Case '-[MyAppTests.UserRepositoryTests testFetchUser]' passed (0.032 seconds)
Test Case '-[MyAppTests.UserRepositoryTests testFetchUserFailsOnNetworkError]' failed (0.015 seconds)
...
Executed 47 tests, with 2 failures (0 unexpected) in 1.203 (1.421) seconds
```

When tests fail, the output includes:
- **Failure location:** `file.swift:42: error: XCTAssertEqual failed`
- **Expected vs actual:** `("expected") is not equal to ("actual")`
- **Custom message:** The message passed to XCTAssert calls

## Common test failure patterns

### Assertion failure

```
// XCTAssertEqual(result, expected) failed: ("42") is not equal to ("0")
// → The function returned 0 instead of 42. Check the implementation logic.
```

### Async test timeout

```
// Asynchronous wait failed - Exceeded timeout of 2 seconds
// → Either the async operation is too slow or the expectation was never fulfilled
// Fix: Increase timeout or mock the slow dependency
```

### Force unwrap crash

```
// Fatal error: Unexpectedly found nil while unwrapping an Optional value
// → XCTest crashes, reporting as a test failure
// Fix: Use guard let or XCTUnwrap() in the test
```

### Actor isolation (Swift 6)

```
// Expression is 'async' but is not marked with 'await'
// Fix: Mark test method as async and add await
```

## Test coverage

```
"Show test coverage for the MyApp target"
"Which files have less than 80% test coverage?"
"Show coverage report after running tests"
```

Request coverage after running tests. Xcode generates coverage data per-file and per-function.

## Test plans

Test plans (`.xctestplan` files) configure which tests run and with what settings.

```
"Create a test plan called SmokeSuite that runs only the critical tests"
"Add the UserRepositoryTests and AuthTests classes to the SmokeSuite test plan"
"Set the test plan to run tests in parallel on the MyApp scheme"
"Enable code coverage collection in the default test plan"
"Set environment variable API_BASE_URL=https://staging.api.com in the test plan"
```

Useful test plan configurations:
- **Parallelization:** Run tests in parallel across available simulators
- **Randomized order:** Catch order-dependent test failures
- **Environment variables:** Inject test-specific config without code changes
- **Sanitizers:** Enable Address Sanitizer or Thread Sanitizer for a test run

## Simulator and device selection

```
"Run tests on the iPhone 16 Pro simulator"
"Run tests on iOS 17.0 and iOS 18.0 simulators"
"Run tests on the connected device"
```

## Writing testable code (guidance)

When asked to write tests or make code more testable:

- **Prefer protocol injection** over concrete type dependencies: allows mocking
- **Use `@testable import`** to access internal types in test targets
- **Async tests:** Mark test functions `async` and use `await` on the system under test
- **Actor-isolated code:** Call from a `@MainActor`-isolated test or use `await MainActor.run { ... }`
- **Use `XCTUnwrap()`** instead of force unwrapping in tests: provides better failure messages
- **`XCTExpectFailure()`** marks known failures to prevent CI flakiness while tracking issues

## When to use xcodebuild test instead

Use `xcodebuild test` via Bash when:
- Running tests in a CI/CD pipeline without a GUI session
- Need `-resultBundlePath` for artifact collection
- Need to test on multiple destination simultaneously in a script
- Xcode is not open

```bash
xcodebuild test \
  -scheme MyApp \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -resultBundlePath TestResults.xcresult
```
