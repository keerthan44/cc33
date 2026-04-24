"use client"

import { useEffect } from "react"
import { useNotes } from "@/hooks/useNotes"

interface NoteListProps {
  refreshTrigger?: number
}

export function NoteList({ refreshTrigger = 0 }: NoteListProps) {
  const { notes, total, loading, error, refetch } = useNotes()

  useEffect(() => {
    if (refreshTrigger > 0) refetch()
  }, [refreshTrigger]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section aria-labelledby="notes-heading">
      <div className="flex items-center gap-2 mb-4">
        <h2 id="notes-heading" className="text-lg font-semibold text-gray-900">
          Recent Notes
        </h2>
        {!loading && (
          <span className="text-sm font-normal text-gray-500" aria-live="polite">
            ({total})
          </span>
        )}
        {loading && (
          <svg
            aria-label="Refreshing notes"
            className="animate-spin h-4 w-4 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        )}
      </div>

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
