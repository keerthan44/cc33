"use client"

import { useState } from "react"
import type { Task, TaskStatus } from "@/lib/types"

const STATUS_COLORS: Record<TaskStatus, string> = {
  PENDING: "bg-yellow-100 text-yellow-800",
  IN_PROGRESS: "bg-blue-100 text-blue-800",
  COMPLETED: "bg-emerald-100 text-emerald-800",
  CANCELLED: "bg-gray-100 text-gray-500",
}

const PRIORITY_COLORS = {
  LOW: "bg-gray-100 text-gray-600",
  MEDIUM: "bg-orange-100 text-orange-700",
  HIGH: "bg-red-100 text-red-700",
} as const

const ALL_STATUSES: TaskStatus[] = [
  "PENDING",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
]

interface TaskCardProps {
  task: Task
  onUpdate: (id: string, data: Partial<Task>) => Promise<Task>
  onDelete: (id: string) => Promise<void>
}

export function TaskCard({ task, onUpdate, onDelete }: TaskCardProps) {
  const [status, setStatus] = useState<TaskStatus>(task.status)
  const [updating, setUpdating] = useState(false)
  const [updateError, setUpdateError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const handleStatusChange = async (next: TaskStatus) => {
    const previous = status
    setStatus(next)
    setUpdating(true)
    setUpdateError(null)
    try {
      await onUpdate(task.id, { status: next })
    } catch {
      setStatus(previous)
      setUpdateError("Failed to update status")
    } finally {
      setUpdating(false)
    }
  }

  return (
    <article
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-2"
      aria-label={`Task: ${task.title}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-900 leading-snug">
          {task.title}
        </h3>
        {task.priority && (
          <span
            className={`shrink-0 text-xs rounded-full px-2 py-0.5 font-medium ${PRIORITY_COLORS[task.priority]}`}
            aria-label={`Priority: ${task.priority}`}
          >
            {task.priority}
          </span>
        )}
      </div>

      {task.description && (
        <p className="text-xs text-gray-500 line-clamp-2">{task.description}</p>
      )}

      {task.due_date && (
        <p className="text-xs text-gray-400">
          Due <time dateTime={task.due_date}>{task.due_date}</time>
        </p>
      )}

      <div className="flex items-center justify-between pt-1">
        <label className="sr-only" htmlFor={`status-${task.id}`}>
          Change status for {task.title}
        </label>
        <select
          id={`status-${task.id}`}
          value={status}
          disabled={updating}
          onChange={(e) => handleStatusChange(e.target.value as TaskStatus)}
          className={`text-xs rounded-full px-2 py-1 font-medium border-0 cursor-pointer focus:ring-2 focus:ring-indigo-400 ${STATUS_COLORS[status]}`}
        >
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>

        {confirmDelete ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onDelete(task.id)}
              className="text-xs text-red-600 font-medium hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 rounded"
              aria-label={`Confirm delete task: ${task.title}`}
            >
              Confirm
            </button>
            <button
              type="button"
              onClick={() => setConfirmDelete(false)}
              className="text-xs text-gray-400 hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 rounded"
              aria-label="Cancel delete"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmDelete(true)}
            className="text-xs text-gray-400 hover:text-red-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 rounded"
            aria-label={`Delete task: ${task.title}`}
          >
            Delete
          </button>
        )}
      </div>

      {updateError && (
        <p role="alert" className="text-xs text-red-600">
          {updateError}
        </p>
      )}
    </article>
  )
}
