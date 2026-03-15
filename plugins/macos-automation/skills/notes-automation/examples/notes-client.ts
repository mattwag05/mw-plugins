/**
 * TypeScript client for Notes.app automation
 */

async function runJXA<T>(script: string): Promise<T> {
  const proc = Bun.spawn(['osascript', '-l', 'JavaScript', '-e', script], {
    stdout: 'pipe', stderr: 'pipe'
  })
  const output = await new Response(proc.stdout).text()
  const error = await new Response(proc.stderr).text()
  if (error && !error.includes('Warning')) throw new Error(`JXA failed: ${error}`)
  return output.trim() ? JSON.parse(output) : [] as T
}

export interface Note {
  name: string
  body: string
  creationDate: string
  folder: string
}

export class NotesClient {
  async getRecentNotes(limit: number = 10): Promise<Note[]> {
    const script = `
      const Notes = Application('Notes')
      const notes = Notes.notes()
      return JSON.stringify(notes.slice(0, ${limit}).map(note => ({
        name: note.name(),
        body: note.body().substring(0, 500),
        creationDate: note.creationDate().toISOString(),
        folder: note.container().name()
      })))
    `
    return await runJXA<Note[]>(script)
  }

  async searchNotes(query: string): Promise<Note[]> {
    const script = `
      const Notes = Application('Notes')
      const matching = Notes.notes().filter(note =>
        note.name().toLowerCase().includes("${query.toLowerCase()}") ||
        note.body().toLowerCase().includes("${query.toLowerCase()}")
      )
      return JSON.stringify(matching.slice(0, 20).map(note => ({
        name: note.name(),
        body: note.body().substring(0, 200),
        creationDate: note.creationDate().toISOString(),
        folder: note.container().name()
      })))
    `
    return await runJXA<Note[]>(script)
  }

  async createNote(title: string, content: string): Promise<void> {
    const escaped = content.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')
    const script = `
      const Notes = Application('Notes')
      const note = Notes.Note({ name: "${title}", body: "${escaped}" })
      Notes.notes.push(note)
      return "Note created"
    `
    await runJXA<string>(script)
  }

  async listFolders(): Promise<string[]> {
    const script = `
      const Notes = Application('Notes')
      return JSON.stringify(Notes.folders().map(f => f.name()))
    `
    return await runJXA<string[]>(script)
  }
}

if (import.meta.main) {
  const notes = new NotesClient()
  console.log('Recent notes:', await notes.getRecentNotes(5))
  console.log('Folders:', await notes.listFolders())
}
