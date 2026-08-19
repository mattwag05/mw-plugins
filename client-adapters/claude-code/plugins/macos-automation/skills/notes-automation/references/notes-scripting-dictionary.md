# Notes.app scripting dictionary

## Core objects

### Note
**Properties:**
- `name()` - Note title
- `body()` - Note content (HTML)
- `creationDate()` - Date created
- `modificationDate()` - Date modified
- `container()` - Parent folder

**Create note:**
```javascript
const Notes = Application('Notes')
const note = Notes.Note({
  name: "Meeting Notes",
  body: "Discussion points:\n- Topic 1\n- Topic 2"
})
Notes.notes.push(note)
```

### Folder
**Properties:**
- `name()` - Folder name

**Collections:**
- `notes()` - Notes in folder

## Common patterns

**List all notes:**
```javascript
const Notes = Application('Notes')
Notes.notes().map(n => n.name())
```

**Search notes:**
```javascript
const Notes = Application('Notes')
Notes.notes().filter(n =>
  n.name().includes('project') ||
  n.body().includes('project')
)
```

**Create and add to folder:**
```javascript
const Notes = Application('Notes')
const folder = Notes.folders.byName('Work')
const note = Notes.Note({ name: "Title", body: "Content" })
folder.notes.push(note)
```
