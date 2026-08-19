---
name: notes-automation
description: Use when the user asks to "automate Notes app", "read notes programmatically", "create notes", "search notes", "access note folders", "get note content", or mentions Notes.app automation, note scripting, or macOS notes workflows.
metadata:
  version: "1.0.0"
---

# Notes.app automation

Automate Notes.app using JXA for reading, creating, and searching notes programmatically.

## Overview

Notes.app provides scripting support for note management. Use this skill for knowledge management automation, note search, and integration with other workflows.

## Prerequisites

- **Notes.app** with iCloud or local notes
- **Automation permissions** granted
- **Notes.app running**
- **macos-automation-core** loaded

## Core capabilities

| Category | Operations | JXA Support |
|----------|------------|-------------|
| Reading | Access notes, read content, check properties | Yes Full |
| Creating | Create notes, set content | Yes Full |
| Searching | Search by title, content, folder | Yes Full |
| Folders | List folders, access notes in folder | Yes Full |

## Quick reference

| Task | JXA Pattern |
|------|-------------|
| Get all notes | `Notes.notes()` |
| Get note name | `note.name()` |
| Get note content | `note.body()` |
| Get creation date | `note.creationDate()` |
| Create note | `Notes.Note({name: '...', body: '...'})` |
| List folders | `Notes.folders()` |

## TypeScript integration

```typescript
interface Note {
  name: string
  body: string
  creationDate: string
  folder: string
}

async function getRecentNotes(limit: number = 10): Promise<Note[]> {
  const script = `
    const Notes = Application('Notes')
    const notes = Notes.notes()

    return JSON.stringify(
      notes.slice(0, ${limit}).map(note => ({
        name: note.name(),
        body: note.body(),
        creationDate: note.creationDate().toISOString(),
        folder: note.container().name()
      }))
    )
  `
  return await runJXA<Note[]>(script)
}
```

## Common patterns

### Search notes

```typescript
async function searchNotes(query: string): Promise<Note[]> {
  const script = `
    const Notes = Application('Notes')
    const allNotes = Notes.notes()
    const matching = allNotes.filter(note =>
      note.name().toLowerCase().includes("${query.toLowerCase()}") ||
      note.body().toLowerCase().includes("${query.toLowerCase()}")
    )

    return JSON.stringify(
      matching.slice(0, 20).map(note => ({
        name: note.name(),
        body: note.body().substring(0, 200),
        creationDate: note.creationDate().toISOString()
      }))
    )
  `
  return await runJXA<Note[]>(script)
}
```

### Create note

```typescript
async function createNote(title: string, content: string): Promise<void> {
  const script = `
    const Notes = Application('Notes')
    const note = Notes.Note({
      name: "${title}",
      body: "${content}"
    })
    Notes.notes.push(note)
    return "Note created"
  `
  await runJXA<string>(script)
}
```

## Limitations

### Known issues

- No HTML content rendering varies
- No Attachments have limited support
- No Sync timing can affect availability
- Warning: Large notes may take time to load

## Additional resources

- **notes-scripting-dictionary.md** - Complete API reference

## Examples

- **notes-client.ts** - Full TypeScript client
- **read-notes.jxa** - List recent notes
- **create-note.jxa** - Create new note
- **search-notes.jxa** - Search by keyword
