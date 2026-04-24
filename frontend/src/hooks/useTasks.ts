"use client"

import { useCallback, useEffect, useState } from "react"
import { taskService, type TaskFilters } from "@/services/TaskService"
import type { Task } from "@/lib/types"

interface TasksState {
  tasks: Task[]
  total: number
  loading: boolean
  error: string | null
}

export function useTasks(filters: TaskFilters = {}) {
  const [state, setState] = useState<TasksState>({
    tasks: [],
    total: 0,
    loading: true,
    error: null,
  })

  const filterKey = JSON.stringify(filters)

  const fetchTasks = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await taskService.list(filters)
      setState({ tasks: data.items, total: data.total, loading: false, error: null })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load tasks"
      setState((s) => ({ ...s, loading: false, error: message }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const updateTask = async (id: string, data: Partial<Task>): Promise<Task> => {
    const updated = await taskService.update(id, data)
    setState((s) => ({
      ...s,
      tasks: s.tasks.map((t) => (t.id === id ? updated : t)),
    }))
    return updated
  }

  const deleteTask = async (id: string): Promise<void> => {
    await taskService.delete(id)
    setState((s) => ({
      ...s,
      tasks: s.tasks.filter((t) => t.id !== id),
      total: s.total - 1,
    }))
  }

  return { ...state, refetch: fetchTasks, updateTask, deleteTask }
}
