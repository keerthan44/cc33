import { httpRequest } from "@/lib/http"
import type { TranscribeResponse } from "@/lib/types"

export class VoiceService {
  async transcribeFile(file: File): Promise<TranscribeResponse> {
    const fd = new FormData()
    fd.append("file", file)
    return httpRequest<TranscribeResponse>("/api/voice/transcribe", {
      method: "POST",
      body: fd,
    })
  }
}

export const voiceService = new VoiceService()
