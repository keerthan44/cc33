"use client"

import { useEffect, useState } from "react"
import { useTasks } from "@/hooks/useTasks"
import { TaskCard } from "./TaskCard"
import type { Task, TaskPriority, TaskStatus } from "@/lib/types"

const STATUS_OPTIONS: Array<{ value: TaskStatus | ""; label: string }> = [
  { value: "", label: "All statuses" },
  { value: "PENDING", label: "Pending" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "CANCELLED", label: "Cancelled" },
]

const PRIORITY_OPTIONS: Array<{ value: TaskPriority | ""; label: string }> = [
  { value: "", label: "All priorities" },
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
]

interface TaskListProps {
  refreshTrigger?: number
}

export function TaskList({ refreshTrigger = 0 }: TaskListProps) {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("")
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | "">("")

  const { tasks, total, loading, error, updateTask, deleteTask, refetch } = useTasks({
    status: statusFilter || undefined,
    priority: priorityFilter || undefined,
  })

  useEffect(() => {
    if (refreshTrigger > 0) refetch()
  }, [refreshTrigger]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section aria-labelledby="tasks-heading">
      <div className="flex items-center justify-between mb-4">
        <h2 id="tasks-heading" className="text-lg font-semibold text-gray-900">
          Tasks{" "}
          {!loading && (
            <span
              className="text-sm font-normal text-gray-500"
              aria-live="polite"
              aria-atomic="true"
            >
              ({total})
            </span>
          )}
        </h2>
      </div>

      <div className="flex gap-2 mb-4" role="group" aria-label="Filter tasks">
        <label className="sr-only" htmlFor="status-filter">
          Filter by status
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "")}
          className="text-sm border border-gray-200 rounded-md px-2 py-1.5 bg-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <label className="sr-only" htmlFor="priority-filter">
          Filter by priority
        </label>
        <select
          id="priority-filter"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as TaskPriority | "")}
          className="text-sm border border-gray-200 rounded-md px-2 py-1.5 bg-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        >
          {PRIORITY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div role="status" aria-label="Loading tasks" className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-24 rounded-lg bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-600 bg-red-50 rounded-md p-3">
          {error}
        </p>
      )}

      {!loading && !error && tasks.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-8">
          No tasks yet. Start recording!
        </p>
      )}

      <ul className="space-y-3" aria-label="Task list">
        {tasks.map((task) => (
          <li key={task.id}>
            <TaskCard task={task} onUpdate={updateTask} onDelete={deleteTask} />
          </li>
        ))}
      </ul>
    </section>
  )
}
