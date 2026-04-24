export type TaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED"
export type TaskPriority = "LOW" | "MEDIUM" | "HIGH"
export type IntentType =
  | "CREATE_TASK"
  | "UPDATE_TASK_STATUS"
  | "QUERY_TASKS"
  | "GENERAL_NOTE"
export type NoteSource = "voice" | "text"

export interface Task {
  id: string
  title: string
  description?: string
  status: TaskStatus
  priority?: TaskPriority
  due_date?: string
  created_at: string
  updated_at: string
}

export interface Note {
  id: string
  raw_transcript: string
  source: NoteSource
  created_at: string
  task?: Task
}

export interface ActionResult {
  type: string
  task?: Task
}

export interface TranscribeResponse {
  note: Note
  intent: IntentType
  action: ActionResult
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
