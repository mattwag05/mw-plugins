---
name: testflight-triage
description: >-
  Scrape Apple App Store Connect TestFlight data using Chrome browser automation and triage it into
  beads issues for backlog tracking. Use this skill whenever the user says "/testflight-triage",
  "check testflight", "import testflight feedback", "triage beta feedback", "look at app store
  connect for issues", "pull in crash reports from testflight", "what are beta testers saying",
  or any request to import, sync, or review TestFlight feedback/crashes/builds into the backlog.
  Always use this skill when the user wants to turn TestFlight data into actionable work items.
user_invocable: true
---

# testflight-triage

Scrape App Store Connect TestFlight (feedback, crashes, builds, testers) and create or update
beads issues in the corresponding local repo. This skill drives Chrome via browser automation —
no API keys needed, just an active ASC session.

---

## APP_MAP

This inline mapping connects short app names to their Apple IDs and local beads repos. Edit this
section to add new apps. The Apple ID appears in the ASC URL when viewing the app:
`https://appstoreconnect.apple.com/apps/<apple_id>/...`

```
APP_MAP:
  headwater:
    apple_id: "6760972554"
    repo: "/Users/matthewwagner/Projects/Prevention Coach"
    display_name: "Headwater"
  swiftclaw:
    apple_id: ""
    repo: "/Users/matthewwagner/Projects/SwiftClaw"
    display_name: "SwiftClaw"
```

---

## Prerequisites

Before running, confirm:
- Chrome is open with the Claude-in-Chrome extension active
- The user is already signed in to App Store Connect (`appstoreconnect.apple.com`)
- The target repo exists and has a `.beads/` directory

If any prerequisite is missing, stop and tell the user what's needed.

---

## Argument Parsing

The user invokes this skill with an optional app name, section filter, and time filter:

```
/testflight-triage [app] [--section crashes|feedback|builds|testers|all] [--since 7d|30d|24h]
```

**Resolve the app:**
1. If `app` matches a key in APP_MAP (case-insensitive) → use that entry
2. If `app` is a numeric string → treat as Apple ID; ask the user which repo to target
3. If no `app` provided:
   - If APP_MAP has exactly one entry with a non-empty `apple_id` → use it automatically
   - Otherwise → list known apps and ask the user to pick one
4. Verify the repo path has a `.beads/` directory — abort with a clear message if not

**Section filter:** Default is `all`. If `--section` is given, only process that section.

**Time filter:** `--since` is advisory (mention it when displaying results). ASC does not always
expose reliable dates in the DOM, so use it as a display filter rather than a hard cutoff.

---

## Step 1 — Setup and Auth Check

Load Chrome tools using ToolSearch before calling any `mcp__claude-in-chrome__` tool. Load at
minimum: `tabs_context_mcp`, `tabs_create_mcp`, `navigate`, `read_page`, `get_page_text`, `find`,
`computer`, `javascript_tool`, `read_network_requests`.

Then:

1. Call `tabs_context_mcp` to get the current tab group
2. Call `tabs_create_mcp` to get a fresh `tabId`
3. Call `update_plan` with `domains: ["appstoreconnect.apple.com"]` to get domain approval
4. Navigate to `https://appstoreconnect.apple.com` — the home/apps list, NOT a deep link (ASC is
   a React SPA that must initialize team context on the home page; direct deep links cause a
   `teams/undefined` error before the session is established)
5. Use `computer` with `action: "wait"` for 4 seconds (SPA render time)
6. Call `get_page_text` to read the page

**Auth detection:** If the page text contains "Sign in", "Apple ID", or "idmsa.apple.com" appears
in the URL → stop immediately. Tell the user:

> "You're not signed in to App Store Connect. Please sign in manually in Chrome and then run
> `/testflight-triage` again."

Do not attempt to fill in credentials or navigate the sign-in flow.

If the apps list loads → auth confirmed.

**Section navigation pattern (Steps 2-5):** For each section, navigate to the tab, wait 4 seconds
for the SPA to render, then extract. Use the resolved team-scoped URL visible in the address bar
after the session initializes (e.g., `https://appstoreconnect.apple.com/teams/<team_id>/apps/<apple_id>/testflight/<section>`)
rather than constructing it from the apple_id alone.

---

## Step 2 — Crashes

Click the app tile → TestFlight tab → Crashes, or use the resolved team-scoped URL from the
address bar. Wait 4 seconds. Then extract crash groups using this sequence:

1. `get_page_text` for raw text content
2. `read_page` with `filter: "all"` for structured accessibility data
3. `read_network_requests` with `urlPattern: "api"` — if JSON responses contain crash data, prefer
   that over DOM text; it will have cleaner structured fields

**Handle pagination:** After reading, use `javascript_tool` to check if a "Load More" or "Show More"
button exists, or if the list is truncated. If so, scroll down (`computer` scroll + 2s wait),
re-read, and repeat — up to 5 cycles or until row count stabilizes.

**For each crash group, extract:**
- Exception type / crash group name
- Occurrence count
- Affected build version(s)
- Most recent occurrence date (if shown)
- Device types affected

If the page lets you click into a crash group for a stack trace, navigate to the detail page,
extract the top-level stack trace (first 10-15 frames), then navigate back. Do this for the top 3
crash groups by occurrence count only — don't deep-dive every crash.

**If no crashes:** Note "No crash data" and skip to Step 3.

---

## Step 3 — Feedback

Navigate to the Feedback tab (resolved URL pattern from Step 1). Wait 4 seconds. Extract using
`get_page_text` and `read_page`. Handle pagination the same way as crashes (scroll + re-read,
max 5 cycles).

**For each feedback item, extract:**
- Feedback text (verbatim)
- Submission date
- Build version
- Device model and OS version
- Tester name or email (if shown)
- Whether a screenshot is attached (yes/no — note existence only, you cannot download it)

**Classify each feedback item** as bug or feature:
- Something broken, incorrect, or not working → `bug`
- A suggestion, wish, or request for something new → `feature`
- Ambiguous → default to `bug`

**If no feedback:** Note "No feedback" and skip to Step 4.

---

## Step 4 — Builds

Navigate to the Builds tab (resolved URL pattern from Step 1). Wait 4 seconds. Extract the build
list using `get_page_text` — build data is tabular and doesn't require the fuller extraction used
for crashes and feedback.

**For each build, extract:**
- Version string and build number
- Status (Ready to Test, Processing, Failed, Expired, etc.)
- Upload date
- Expiration date (if shown)
- Tester install count (if shown)

**Only create beads issues for problematic builds.** Healthy builds (Ready to Test, active) are
mentioned in the summary only — not turned into issues.

Problematic conditions:
- Processing Failed
- Missing export compliance
- Expired with no replacement
- Zero testers installed on the most recent build

**If all builds are healthy:** Note summary info and skip beads issue creation for this section.

---

## Step 5 — Testers

Navigate to the Testers tab (resolved URL pattern from Step 1). Wait 4 seconds. Extract tester
summary using `get_page_text`.

**Extract (aggregate stats, not individual records):**
- Total tester count
- Count by status (Invited, Accepted, Installed)
- Build adoption: how many testers are on the latest build vs. older builds

**Testers do not produce individual beads issues.** Summarize in the final output only. A beads
issue is warranted only for notable conditions:
- 0 testers installed on the current build
- Tester count dropped significantly (hard to detect without history — note if the number looks
  very low relative to the app stage)

---

## Step 6 — Dedup and Issue Creation

Change directory to the target repo before running any `bd` commands:

```bash
cd "<repo_path>"
```

**Before processing any items, capture existing testflight issues once:**

```bash
bd list 2>/dev/null | grep -i testflight > /tmp/tf_existing.txt
```

Work through each extracted item (crashes first, then feedback, then build problems). For each
item, check `/tmp/tf_existing.txt` first (broad), then run a narrow search if needed:

```bash
# Narrow: search by key term
bd search "<key_term>" 2>/dev/null
```

Search terms:
- **Crash:** Exception type keyword (e.g., `bd search "EXC_BAD_ACCESS"`)
- **Feedback:** 2-3 distinctive words from the core of the feedback text (e.g., `bd search "due dates"`)
- **Build:** The build number (e.g., `bd search "build 3"`)

Match on meaning, not exact title — if an existing issue clearly describes the same problem (even
in slightly different words), treat it as a match rather than creating a duplicate.

| Match | Action |
|-------|--------|
| Found (exact or related) | Append a note with the new data using `bd note` |
| None | Create a new issue using `bd create` |

### Appending to an existing issue

```bash
bd note <issue_id> "Updated <YYYY-MM-DD>: <brief summary of new data>"
```

For crashes with new occurrence count:
```bash
bd note <issue_id> "Occurrence count now <N>. Last seen <date>. Additional build: <version>."
```

### Creating a new issue

Use the templates below. Fill in the `<placeholders>` from the extracted data.

**Crash:**
```bash
bd create "[Crash] <exception_type> in <build_version>" \
  --type bug \
  --priority <priority> \
  --labels "testflight,crash" \
  --description "**Source:** TestFlight crash report
**Occurrences:** <count>
**Builds affected:** <versions>
**Last seen:** <date>
**Devices:** <device_list>

## Stack trace
<stack_trace_summary_or_'Not available'>

## Triage
Imported via testflight-triage on <today>."
```

Priority scale for crashes:
- 10 or more occurrences → priority 0 (critical)
- 3–9 occurrences → priority 1 (high)
- 1–2 occurrences → priority 2 (medium)

**Feedback:**
```bash
bd create "[Feedback] <short_summary>" \
  --type <bug_or_feature> \
  --priority 2 \
  --labels "testflight,feedback" \
  --description "**Source:** TestFlight tester feedback
**Tester:** <name_or_email_or_'Unknown'>
**Build:** <version>
**Device:** <device> (<os_version>)
**Date:** <date>
**Screenshot attached:** <yes/no>

## Feedback
<verbatim_text>

## Triage
Imported via testflight-triage on <today>."
```

**Build problem:**
```bash
bd create "[Build] <version> (<build_number>) — <issue_summary>" \
  --type task \
  --priority 3 \
  --labels "testflight,build" \
  --description "**Build:** <version> (<build_number>)
**Status:** <status>
**Uploaded:** <date>
**Issue:** <description_of_the_problem>

## Triage
Imported via testflight-triage on <today>."
```

---

## Step 7 — Summary

After processing all sections, display a structured summary:

```
## TestFlight Triage Summary — <Display Name>
Date: <today>
Repo: <repo_path>

### Crashes
- <N> crash groups found
- <X> new issues created | <Y> existing issues updated
- Highest priority: <top crash title>

### Feedback
- <N> feedback items found
- <X> new issues created | <Y> existing issues updated

### Builds
- Current: <version> (<status>)
- <X> build issues created (or "No build issues")

### Testers
- <N> total | Installed: <N> | On latest build: <N> (<pct>%)

### Sections skipped
<list any sections skipped and why, or "None">

### Actions taken
| Action  | Issue ID | Title                              | Type    |
|---------|----------|------------------------------------|---------|
| Created | bd-xxx   | [Crash] EXC_BAD_ACCESS in 1.2.3   | bug     |
| Updated | bd-yyy   | [Feedback] App crashes on launch   | bug     |
```

That's it — the summary is the final output. No sync step is needed.

---

## Error Handling

| Failure | Detection | Response |
|---------|-----------|----------|
| Not signed in | Page contains "Sign in" or Apple ID redirect | Abort. Instruct user to sign in manually. |
| App not found | Page shows 404 or "not found" | Abort. List known apps. Ask user to verify Apple ID. |
| Section fails to load | Empty page after 8s wait | Skip section. Note in summary. Retry once before skipping. |
| Section has no data | "No crashes", "No feedback", etc. in page text | Skip section. Note "No data" in summary. Not an error. |
| Pagination stuck | Row count unchanged across 2 scroll+read cycles | Stop paginating. Use data collected so far. |
| `bd` command fails | Non-zero exit or error output | Log error in summary. Continue with remaining items. |
| Repo missing `.beads/` | `ls <repo>/.beads/` fails | Abort immediately. Tell user which repo is not beads-enabled. |
| Chrome not available | `tabs_context_mcp` fails or errors | Tell user to open Chrome and ensure the Claude-in-Chrome extension is connected. |

**General principle:** Partial success beats full abort. If one section fails, continue with the
others and clearly report what was skipped. Always show the summary, even if incomplete.
