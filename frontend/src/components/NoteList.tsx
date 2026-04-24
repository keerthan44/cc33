"use client"

import { useNotes } from "@/hooks/useNotes"

export function NoteList() {
  const { notes, total, loading, error } = useNotes()

  return (
    <section aria-labelledby="notes-heading" className="mt-8">
      <h2 id="notes-heading" className="text-lg font-semibold text-gray-900 mb-4">
        Recent Notes{" "}
        {!loading && (
          <span className="text-sm font-normal text-gray-500" aria-live="polite">
            ({total})
          </span>
        )}
      </h2>

      {loading && (
        <div role="status" aria-label="Loading notes" className="space-y-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-600 bg-red-50 rounded-md p-3">
          {error}
        </p>
      )}

      {!loading && !error && notes.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-6">No notes yet.</p>
      )}

      <ul className="space-y-2" aria-label="Note list">
        {notes.map((note) => (
          <li
            key={note.id}
            className="rounded-lg border border-gray-100 bg-gray-50 p-3"
          >
            <p className="text-xs text-gray-500 mb-1">
              <time dateTime={note.created_at}>
                {new Date(note.created_at).toLocaleString()}
              </time>
              {" · "}
              <span className="capitalize">{note.source}</span>
            </p>
            <p className="text-sm text-gray-800 line-clamp-3">
              {note.raw_transcript}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}
