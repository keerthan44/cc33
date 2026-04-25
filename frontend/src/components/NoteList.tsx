"use client"

import { useEffect } from "react"
import { useNotes } from "@/hooks/useNotes"
import { ActionSection, TaskChip } from "@/components/TranscriptDisplay"
import type { ActionResult } from "@/lib/types"

interface NoteListProps {
  refreshTrigger?: number
}

export function NoteList({ refreshTrigger = 0 }: NoteListProps) {
  const { notes, total, loading, error, refetch } = useNotes()

  useEffect(() => {
    if (refreshTrigger > 0) refetch()
  }, [refreshTrigger, refetch])

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

      <ul className="space-y-3" aria-label="Note list">
        {notes.map((note) => {
          const actions: ActionResult[] = note.note_actions ?? []

          return (
            <li
              key={note.id}
              className="rounded-lg border border-gray-100 bg-gray-50 p-4"
            >
              <p className="text-xs text-gray-500 mb-1">
                <time dateTime={note.created_at}>
                  {new Date(note.created_at).toLocaleString()}
                </time>
                {" · "}
                <span className="capitalize">{note.source}</span>
              </p>
              <p className="text-sm text-gray-800 mb-3">
                {note.raw_transcript}
              </p>

              {actions.length > 0 ? (
                <div
                  className="flex gap-3 flex-wrap"
                  role="region"
                  aria-label="Task results for this note"
                >
                  {actions.map((action, i) => (
                    <div key={i} className="flex-1 min-w-[160px]">
                      <ActionSection action={action} />
                    </div>
                  ))}
                </div>
              ) : note.tasks.length > 0 ? (
                <div className="flex gap-3 flex-wrap" aria-label="Associated tasks">
                  {note.tasks.map((task) => (
                    <div key={task.id} className="flex-1 min-w-[160px]">
                      <TaskChip task={task} variant="created" />
                    </div>
                  ))}
                </div>
              ) : null}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
