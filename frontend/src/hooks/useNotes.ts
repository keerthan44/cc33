"use client"

import { useCallback, useEffect, useState } from "react"
import { noteService, type NoteFilters } from "@/services/NoteService"
import type { Note } from "@/lib/types"

interface NotesState {
  notes: Note[]
  total: number
  loading: boolean
  error: string | null
}

export function useNotes(filters: NoteFilters = {}) {
  const [state, setState] = useState<NotesState>({
    notes: [],
    total: 0,
    loading: true,
    error: null,
  })

  const filterKey = JSON.stringify(filters)

  const fetchNotes = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await noteService.list(filters)
      setState({ notes: data.items, total: data.total, loading: false, error: null })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load notes"
      setState((s) => ({ ...s, loading: false, error: message }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey])

  useEffect(() => {
    fetchNotes()
  }, [fetchNotes])

  return { ...state, refetch: fetchNotes }
}
