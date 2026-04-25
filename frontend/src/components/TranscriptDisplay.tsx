"use client"

import type { ActionResult, IntentType, Task } from "@/lib/types"

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

const STATUS_COLORS: Record<string, string> = {
  PENDING: "text-yellow-700",
  IN_PROGRESS: "text-blue-700",
  COMPLETED: "text-emerald-700",
  CANCELLED: "text-gray-500",
}

export function TaskChip({ task, variant }: { task: Task; variant: "created" | "updated" | "found" }) {
  const colors = {
    created: "border-emerald-200 bg-emerald-50",
    updated: "border-blue-200 bg-blue-50",
    found: "border-amber-200 bg-amber-50",
  }

  return (
    <div className={`rounded-lg border p-3 ${colors[variant]}`}>
      <p className="text-sm font-medium text-gray-900">{task.title}</p>
      <div className="flex items-center gap-3 mt-1 flex-wrap">
        <span className={`text-xs font-medium ${STATUS_COLORS[task.status] ?? "text-gray-600"}`}>
          {task.status.replace("_", " ")}
        </span>
        {task.priority && (
          <span className="text-xs text-gray-500">{task.priority}</span>
        )}
        {task.due_date && (
          <span className="text-xs text-gray-500">
            Due <time dateTime={task.due_date}>{task.due_date}</time>
          </span>
        )}
      </div>
    </div>
  )
}

export function ActionSection({ action }: { action: ActionResult }) {
  const { intent, tasks } = action

  if (intent === "CREATE_TASK" && tasks.length > 0) {
    return (
      <div role="region" aria-label={`${tasks.length} task${tasks.length > 1 ? "s" : ""} created`} className="space-y-2">
        <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">
          {tasks.length === 1 ? "Task created" : `${tasks.length} tasks created`}
        </p>
        {tasks.map((task) => (
          <TaskChip key={task.id} task={task} variant="created" />
        ))}
      </div>
    )
  }

  if (intent === "UPDATE_TASK_STATUS") {
    return (
      <div role="region" aria-label={tasks.length > 0 ? "Updated task" : "No task found to update"} className="space-y-2">
        {tasks.length > 0 ? (
          <>
            <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Task updated</p>
            {tasks.map((task) => (
              <TaskChip key={task.id} task={task} variant="updated" />
            ))}
          </>
        ) : (
          <p className="text-xs text-gray-400 italic">No matching task found to update.</p>
        )}
      </div>
    )
  }

  if (intent === "QUERY_TASKS") {
    return (
      <div role="region" aria-label={tasks.length > 0 ? `${tasks.length} tasks found` : "No tasks found"} className="space-y-2">
        {tasks.length > 0 ? (
          <>
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
              {tasks.length === 1 ? "1 task found" : `${tasks.length} tasks found`}
            </p>
            {tasks.map((task) => (
              <TaskChip key={task.id} task={task} variant="found" />
            ))}
          </>
        ) : (
          <p className="text-xs text-gray-400 italic">No tasks match your query.</p>
        )}
      </div>
    )
  }

  return null
}

interface TranscriptDisplayProps {
  partialText: string
  finalTranscript: string
  actions: ActionResult[]
  error: string | null
}

export function TranscriptDisplay({
  partialText,
  finalTranscript,
  actions,
  error,
}: TranscriptDisplayProps) {
  return (
    <div className="mt-6 w-full space-y-3 min-h-[120px]">
      {error && (
        <p role="alert" className="text-sm text-red-600 bg-red-50 rounded-md p-3">
          {error}
        </p>
      )}

      {/* Partial text changes rapidly — aria-live="off" prevents screen reader flooding */}
      {!finalTranscript && partialText && (
        <p
          className="text-sm italic text-gray-400"
          aria-live="off"
          aria-label="Partial transcript"
        >
          {partialText}
        </p>
      )}

      {/* Final transcript announced once */}
      {finalTranscript && (
        <p className="text-sm text-gray-800" aria-live="polite" aria-label="Final transcript">
          {finalTranscript}
        </p>
      )}

      {actions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {actions.map((a, i) => (
            <span
              key={i}
              className={`inline-flex items-center rounded-full px-3 py-0.5 text-xs font-medium ${INTENT_COLORS[a.intent]}`}
              aria-label={`Detected intent: ${INTENT_LABELS[a.intent]}`}
            >
              {INTENT_LABELS[a.intent]}
            </span>
          ))}
        </div>
      )}

      {/* Action results announced once when they appear */}
      {actions.length > 0 && (
        <div aria-live="polite" aria-atomic="false" className="space-y-3">
          {actions.map((action, i) => (
            <ActionSection key={i} action={action} />
          ))}
        </div>
      )}
    </div>
  )
}
