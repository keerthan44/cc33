"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { IntentType, Note, Task } from "@/lib/types"

export type StreamStatus = "idle" | "recording" | "processing" | "done" | "error"

interface StreamState {
  status: StreamStatus
  partialText: string
  finalTranscript: string
  intent: IntentType | null
  task: Task | null
  note: Note | null
  error: string | null
}

const INITIAL_STATE: StreamState = {
  status: "idle",
  partialText: "",
  finalTranscript: "",
  intent: null,
  task: null,
  note: null,
  error: null,
}

type WsMessage =
  | { type: "ready" }
  | { type: "partial"; text: string }
  | { type: "final"; transcript: string }
  | { type: "intent"; intent: IntentType }
  | { type: "task"; task: Task }
  | { type: "note"; note: Note }
  | { type: "done" }

export function useVoiceStream() {
  const wsUrl =
    (typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000"
      : "ws://localhost:8000") + "/api/voice/stream"

  const [state, setState] = useState<StreamState>(INITIAL_STATE)
  const wsRef = useRef<WebSocket | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stop = useCallback(() => {
    if (recorderRef.current?.state !== "inactive") {
      recorderRef.current?.stop()
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "stop" }))
      setState((s) => ({ ...s, status: "processing" }))
    }
  }, [])

  const start = useCallback(async () => {
    setState({ ...INITIAL_STATE, status: "recording" })
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onmessage = (ev: MessageEvent<string>) => {
        const msg = JSON.parse(ev.data) as WsMessage
        switch (msg.type) {
          case "ready": {
            const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
              ? "audio/webm;codecs=opus"
              : "audio/webm"
            const recorder = new MediaRecorder(stream, { mimeType })
            recorderRef.current = recorder
            recorder.ondataavailable = (e: BlobEvent) => {
              if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                ws.send(e.data)
              }
            }
            recorder.start(2000)
            break
          }
          case "partial":
            setState((s) => ({ ...s, partialText: msg.text }))
            break
          case "final":
            setState((s) => ({ ...s, finalTranscript: msg.transcript, partialText: "" }))
            break
          case "intent":
            setState((s) => ({ ...s, intent: msg.intent }))
            break
          case "task":
            setState((s) => ({ ...s, task: msg.task }))
            break
          case "note":
            setState((s) => ({ ...s, note: msg.note }))
            break
          case "done":
            setState((s) => ({ ...s, status: "done" }))
            break
        }
      }

      ws.onerror = () => {
        setState((s) => ({ ...s, status: "error", error: "WebSocket connection failed" }))
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Microphone access denied"
      setState((s) => ({ ...s, status: "error", error: message }))
    }
  }, [wsUrl])

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop())
      wsRef.current?.close()
    }
  }, [])

  return { ...state, start, stop }
}
