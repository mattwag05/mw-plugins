---
name: doc-navigator
description: This skill should be used when the user asks to "check the docs", "look up in docs", "what does the documentation say", "find in the docs", references a known harvested documentation set by name, or needs to navigate previously harvested documentation stored in the Claude Context Library.
version: 1.0.0
---

# Documentation Navigator

Navigate harvested documentation stored in the Claude Context Library using progressive disclosure — load only what's needed to answer the user's question.

## When to Use

- User asks about content from a previously harvested documentation set
- User references a known doc set by name (e.g., "check the Apple HIG", "what do the Tailscale docs say")
- User asks to "look up" or "find" something in documentation
- User asks "what does the documentation say about X"

## Navigation Protocol

**Always follow this progressive disclosure pattern — never load all pages at once.**

### Step 1: Identify the Doc Set

Read the known-docs registry to find the relevant documentation:

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/doc-navigator/references/known-docs.md
```

Match the user's request to a known doc set by name, slug, or source domain.

### Step 2: Read the Root Index

Read the doc set's root `_index.md` to understand its structure:

```
Read ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Claude Context Library/contexts/technical/{slug}/_index.md
```

This gives you:
- Overview of the documentation
- Section listing with page counts
- Metadata (source URL, harvest date)

### Step 3: Navigate to the Right Section

Based on the user's question, read the relevant section's `_index.md`:

```
Read ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Claude Context Library/contexts/technical/{slug}/{section}/_index.md
```

This lists all pages in that section with descriptions.

### Step 4: Read the Specific Page

Read only the page(s) that answer the user's question:

```
Read ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Claude Context Library/contexts/technical/{slug}/{section}/{page}.md
```

### Step 5: Cite the Source

When providing information from harvested docs:
- Reference the original source URL (in page frontmatter)
- Note the harvest date so the user knows freshness
- If content seems outdated, suggest re-harvesting with `/harvest-docs`

## Key Principles

1. **Progressive disclosure**: Root index -> section index -> specific page. Never bulk-read.
2. **Cite sources**: Always mention which doc page the answer came from.
3. **Suggest re-harvest**: If docs are old or user needs updated content, point to `/harvest-docs`.
4. **Cross-reference**: If multiple pages are relevant, read them sequentially, not all at once.
5. **Admit gaps**: If the harvested docs don't cover the topic, say so and suggest the original URL.

## Quick Reference

| Action | How |
|--------|-----|
| Find a doc set | Read `references/known-docs.md` |
| Get doc overview | Read `{ccl_path}/_index.md` |
| List section pages | Read `{ccl_path}/{section}/_index.md` |
| Get specific content | Read `{ccl_path}/{section}/{page}.md` |
| Re-harvest docs | Use `/harvest-docs` command |

## Error Handling

- **Doc set not found**: Tell user it hasn't been harvested yet, suggest `/harvest-docs <url>`
- **Section not found**: List available sections from root `_index.md`
- **Page not found**: List available pages from section `_index.md`
- **Stale docs**: Check `harvested` date in frontmatter, warn if > 30 days old
