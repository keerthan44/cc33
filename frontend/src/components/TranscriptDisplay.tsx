"use client"

import type { IntentType, Task } from "@/lib/types"

const INTENT_COLORS: Record<IntentType, string> = {
  CREATE_TASK: "bg-emerald-100 text-emerald-800",
  UPDATE_TASK_STATUS: "bg-blue-100 text-blue-800",
  QUERY_TASKS: "bg-amber-100 text-amber-800",
  GENERAL_NOTE: "bg-gray-100 text-gray-700",
}

const INTENT_LABELS: Record<IntentType, string> = {
  CREATE_TASK: "Create Task",
  UPDATE_TASK_STATUS: "Update Status",
  QUERY_TASKS: "Query Tasks",
  GENERAL_NOTE: "General Note",
}

interface TranscriptDisplayProps {
  partialText: string
  finalTranscript: string
  intent: IntentType | null
  task: Task | null
  error: string | null
}

export function TranscriptDisplay({
  partialText,
  finalTranscript,
  intent,
  task,
  error,
}: TranscriptDisplayProps) {
  return (
    <div className="mt-6 w-full space-y-3 min-h-[120px]">
      {error && (
        <p role="alert" className="text-sm text-red-600 bg-red-50 rounded-md p-3">
          {error}
        </p>
      )}

      {!finalTranscript && partialText && (
        <p
          className="text-sm italic text-gray-400"
          aria-live="polite"
          aria-label="Partial transcript"
        >
          {partialText}
        </p>
      )}

      {finalTranscript && (
        <p className="text-sm text-gray-800" aria-label="Final transcript">
          {finalTranscript}
        </p>
      )}

      {intent && (
        <span
          className={`inline-flex items-center rounded-full px-3 py-0.5 text-xs font-medium ${INTENT_COLORS[intent]}`}
          aria-label={`Detected intent: ${INTENT_LABELS[intent]}`}
        >
          {INTENT_LABELS[intent]}
        </span>
      )}

      {task && intent === "CREATE_TASK" && (
        <div
          className="rounded-lg border border-emerald-200 bg-emerald-50 p-3"
          role="region"
          aria-label="Created task"
        >
          <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-1">
            Task created
          </p>
          <p className="text-sm font-medium text-gray-900">{task.title}</p>
          {task.due_date && (
            <p className="text-xs text-gray-500 mt-1">
              Due: <time dateTime={task.due_date}>{task.due_date}</time>
            </p>
          )}
        </div>
      )}
    </div>
  )
}
