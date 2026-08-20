---
name: doc-harvest
description: Harvest a documentation website into a local, indexed reference set. Use for site discovery, batch scraping, content cleanup, and progressive-disclosure indexes.
metadata:
  version: "1.2.1"
allowed-tools: Bash Read Write Edit Glob Grep WebFetch AskUserQuestion
---

# Harvest documentation command

Scrape a documentation website, clean the content, and organize it into the Claude Context Library for progressive-disclosure navigation.

## Instructions

### 1. Get the target URL

If the user didn't provide a URL, ask:
- What documentation site to harvest
- Any specific sections to include or exclude

### 2. Parse the URL and suggest a slug

Extract the domain and path prefix from the URL. Suggest a slug name:
- `developer.apple.com/design/human-interface-guidelines/` → `apple-hig`
- `docs.tailscale.com/` → `tailscale-docs`
- `react.dev/reference/` → `react-reference`

### 3. Discover pages

Run the discovery script:

```bash
python3 "scripts/harvest.py" discover "<url>"
```

This will:
- Try sitemap.xml first
- Fall back to link crawling if no sitemap
- Output a JSON manifest of discovered pages

**If discovery returns 0 (or very few) pages, the site is likely a JS/SPA** whose
nav and sitemap don't work with a static fetch (e.g. Apple, Google AI docs).
Render the landing page with Scrapling, then re-run discovery against the real DOM:

```bash
SCRAPLING_HTML=/tmp/doc-harvest/landing.html \
  "scripts/scrapling-fetch.sh" "<url>" fetch >/dev/null
python3 "scripts/harvest.py" discover "<url>" --html /tmp/doc-harvest/landing.html
```

### 4. Present pages for approval

Show the user the discovered pages as a tree structure. Include:
- Total page count
- Sections/categories found
- Estimated scrape time (pages × 2 seconds)

Use AskUserQuestion to let the user:
- Approve all pages
- Exclude specific sections or pages
- Modify the slug name
- Adjust the CCL output path (default: `contexts/technical/{slug}/`)

### 5. Scrape pages

**If 50+ pages**: Use parallel doc-harvester agents (see Section Analysis below).

**If < 50 pages**: Process interactively:

For each approved page:

a. Fetch content as clean Markdown with the Scrapling wrapper (renders JS,
   bypasses anti-bot, and applies `--ai-targeted` main-content extraction):
```bash
"scripts/scrapling-fetch.sh" "<url>" auto \
  | python3 "scripts/harvest.py" clean --base-url "<domain>" > "/tmp/doc-harvest/<page>.md"
```
   - `auto` (default) does a fast static fetch, then auto-escalates to a JS
     browser fetch if the result looks like an unrendered SPA shell.
   - Force a mode when you know the site: `fetch` (JS/SPA), `stealthy`
     (Cloudflare/anti-bot), or `get` (plain static).
   - The wrapper prints Markdown to stdout; its progress/logs go to stderr.

b. The `clean` step is now a light post-pass (heading normalization, image
   absolutization, whitespace): Scrapling's `--ai-targeted` already removed
   nav/footer/cookie/share boilerplate at the DOM level.

c. Report progress: `[n/total] Fetched: <title>`

d. Wait 2 seconds between requests.

> Ad-hoc alternative: the Scrapling **MCP server** is registered in this plugin's
> `mcp.json`. For one-off interactive fetches you can call its tools directly
> instead of the wrapper; the wrapper is the path for batch harvesting. Both
> paths use Apple Container, so `container system start` must succeed first.

### 5b. section analysis and parallel Agent launch (50+ pages only)

When the approved page count is ≥ 50:

**Group pages by section**: extract the first URL path segment after the base prefix:
- `apple-hig/foundations/color` → section `foundations`
- `apple-hig/getting-started` → section `getting-started` (treat as its own group)
- Pages with no subsection → section `root`

**Parallelization decision:**
- Only 1 section → launch 1 `doc-harvester` agent (same as before)
- 2+ sections → apply binning and launch N parallel agents

**Binning rules (max 6 agents):**
1. Any section with < 10 pages is merged into a `misc` group
2. If the merged `misc` group has pages, it becomes one agent
3. If total groups still > 6, merge the two smallest groups repeatedly until ≤ 6
4. Never launch an agent with 0 pages

**Write the root `_index.md` first** (before launching any agents):
- This prevents race conditions if multiple agents would try to create it

**Show the proposed split to the user** before launching:
```
Launching 4 parallel harvester agents:
  Agent 1: foundations     — 18 pages
  Agent 2: components      — 63 pages
  Agent 3: patterns        — 25 pages
  Agent 4: misc (inputs, getting-started, technologies) — 49 pages
```

**Launch all agents in a single message** (multiple parallel Agent tool calls). Each agent receives:
- `section_name`: the section label (for progress logs like `[3/18] foundations/color`)
- `pages`: the filtered manifest (only pages for this section)
- `slug`, `display_name`, `ccl_path`: same as the full harvest
- `skip_index_update: true`: agent must NOT run `update-index` or update `known-docs.md`

**After all agents complete**, run `update-index` and update `known-docs.md` once (steps 8-9 below).

### 6. Organize into CCL

Generate the file tree plan:

```bash
python3 "scripts/harvest.py" organize --slug "<slug>" --manifest "<manifest_path>"
```

Review the plan, then write files with `--write`:

```bash
python3 "scripts/harvest.py" organize --slug "<slug>" --manifest "<manifest_path>" --write --ccl-root "<ccl_path>"
```

The CCL root path is:
```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Claude Context Library/
```

### 7. Write page content

For each page, write the cleaned content to its CCL location. Each file needs frontmatter:

```yaml
---
name: <Page Title> - <Doc Set Name>
source_url: <original_url>
parent: <section>/_index.md
last_updated: <today's date>
---
```

The root `_index.md` gets extra metadata:

```yaml
---
name: <Doc Set Display Name>
domain: technical
source_url: <base_url>
harvested: <today's date>
page_count: <count>
triggers:
  - "<keyword1>"
  - "<keyword2>"
related_contexts: []
last_updated: <today's date>
---
```

### 8. Update CCL root index

```bash
python3 "scripts/harvest.py" update-index \
  --ccl-root "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Claude Context Library/" \
  --slug "<slug>" \
  --name "<display_name>"
```

### 9. Update known docs registry

Add an entry to the doc-navigator registry:

```
Edit ../doc-navigator/references/known-docs.md
```

Add a row to the table:
```
| <Name> | <slug> | contexts/technical/<slug>/ | <source_domain> | <page_count> | <today's date> |
```

### 10. Report summary

Show the user:
- Pages scraped successfully (and any failures)
- Files created with directory tree
- Total content size
- How to navigate: "Ask me about these docs anytime: I'll use progressive disclosure to find the right page."
- How to re-harvest: "Run `/harvest-docs <url>` again to update."

## Tips

- `scrapling-fetch.sh` (auto mode) is the fetch path for all sites: it renders JS and applies `--ai-targeted`, so it handles SPAs that WebFetch returned empty on
- Scrapling runs through Apple's `container` CLI. Start it with `container system start` before harvesting
- For a known JS/SPA site, skip the auto-escalation and pass `fetch` directly; for Cloudflare/anti-bot sites use `stealthy`
- Scrapling's `--ai-targeted` does the heavy de-boilerplating; the `clean` step is now just a light post-pass (headings, images, whitespace)
- If a site has > 100 pages, strongly suggest the doc-harvester agent
- Always respect rate limits: 2-second minimum between requests
