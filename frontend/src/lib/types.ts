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
  tasks: Task[]
  note_actions: ActionResult[]
}

export interface ActionResult {
  intent: IntentType
  tasks: Task[]
}

export interface TranscribeResponse {
  note: Note
  actions: ActionResult[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
