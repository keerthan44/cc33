"use client"

import { useState } from "react"
import { voiceService } from "@/services/VoiceService"
import type { TranscribeResponse } from "@/lib/types"

interface UploadState {
  loading: boolean
  result: TranscribeResponse | null
  error: string | null
}

export function useVoiceUpload() {
  const [state, setState] = useState<UploadState>({
    loading: false,
    result: null,
    error: null,
  })

  const upload = async (file: File): Promise<void> => {
    setState({ loading: true, result: null, error: null })
    try {
      const result = await voiceService.transcribeFile(file)
      setState({ loading: false, result, error: null })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Upload failed"
      setState({ loading: false, result: null, error: message })
    }
  }

  return { ...state, upload }
}
