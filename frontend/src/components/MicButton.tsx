"use client"

import type { StreamStatus } from "@/hooks/useVoiceStream"

interface MicButtonProps {
  status: StreamStatus
  onStart: () => void
  onStop: () => void
}

export function MicButton({ status, onStart, onStop }: MicButtonProps) {
  const isRecording = status === "recording"
  const isProcessing = status === "processing"

  const handleClick = () => {
    if (isProcessing) return
    if (isRecording) onStop()
    else onStart()
  }

  return (
    <div className="relative flex items-center justify-center">
      {isRecording && (
        <span
          aria-hidden="true"
          className="animate-ping absolute inline-flex h-24 w-24 rounded-full bg-red-400 opacity-60"
        />
      )}
      <button
        type="button"
        onClick={handleClick}
        disabled={isProcessing}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
        aria-pressed={isRecording}
        className={[
          "relative z-10 w-20 h-20 rounded-full flex items-center justify-center shadow-lg",
          "transition-colors focus:outline-none focus-visible:ring-4 focus-visible:ring-offset-2",
          isRecording
            ? "bg-red-500 hover:bg-red-600 focus-visible:ring-red-400"
            : isProcessing
            ? "bg-gray-300 cursor-not-allowed"
            : "bg-indigo-600 hover:bg-indigo-700 focus-visible:ring-indigo-400",
        ].join(" ")}
      >
        {isProcessing ? (
          <svg
            aria-hidden="true"
            className="animate-spin h-8 w-8 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
        ) : (
          <svg
            aria-hidden="true"
            className="h-9 w-9 text-white"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 1a4 4 0 014 4v6a4 4 0 01-8 0V5a4 4 0 014-4z" />
            <path d="M19 11a1 1 0 10-2 0 5 5 0 01-10 0 1 1 0 10-2 0 7 7 0 006 6.92V20H9a1 1 0 100 2h6a1 1 0 100-2h-2v-2.08A7 7 0 0019 11z" />
          </svg>
        )}
      </button>
    </div>
  )
}
