import { httpRequest } from "@/lib/http"
import type { PaginatedResponse, Task, TaskPriority, TaskStatus } from "@/lib/types"

export interface TaskFilters {
  status?: TaskStatus
  priority?: TaskPriority
  page?: number
  page_size?: number
}

export class TaskService {
  async list(filters: TaskFilters = {}): Promise<PaginatedResponse<Task>> {
    const params = new URLSearchParams()
    if (filters.status) params.set("status", filters.status)
    if (filters.priority) params.set("priority", filters.priority)
    if (filters.page) params.set("page", String(filters.page))
    if (filters.page_size) params.set("page_size", String(filters.page_size))
    return httpRequest<PaginatedResponse<Task>>(`/api/tasks?${params}`)
  }

  async getById(id: string): Promise<Task> {
    return httpRequest<Task>(`/api/tasks/${id}`)
  }

  async update(
    id: string,
    data: Partial<Pick<Task, "status" | "priority" | "title" | "description" | "due_date">>
  ): Promise<Task> {
    return httpRequest<Task>(`/api/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async delete(id: string): Promise<void> {
    return httpRequest<void>(`/api/tasks/${id}`, { method: "DELETE" })
  }
}

export const taskService = new TaskService()
