import { httpRequest } from "@/lib/http"
import type { Note, PaginatedResponse, TranscribeResponse } from "@/lib/types"

export interface NoteFilters {
  source?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export class NoteService {
  async list(filters: NoteFilters = {}): Promise<PaginatedResponse<Note>> {
    const params = new URLSearchParams()
    if (filters.source) params.set("source", filters.source)
    if (filters.date_from) params.set("date_from", filters.date_from)
    if (filters.date_to) params.set("date_to", filters.date_to)
    if (filters.page) params.set("page", String(filters.page))
    if (filters.page_size) params.set("page_size", String(filters.page_size))
    return httpRequest<PaginatedResponse<Note>>(`/api/notes?${params}`)
  }

  async getById(id: string): Promise<Note> {
    return httpRequest<Note>(`/api/notes/${id}`)
  }

  async createFromText(transcript: string): Promise<TranscribeResponse> {
    return httpRequest<TranscribeResponse>("/api/notes", {
      method: "POST",
      body: JSON.stringify({ raw_transcript: transcript, source: "text" }),
    })
  }
}

export const noteService = new NoteService()
