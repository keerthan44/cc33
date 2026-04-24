"use client"

import { MicButton } from "@/components/MicButton"
import { TranscriptDisplay } from "@/components/TranscriptDisplay"
import { TaskList } from "@/components/TaskList"
import { useVoiceStream } from "@/hooks/useVoiceStream"

export default function DashboardPage() {
  const {
    status,
    partialText,
    finalTranscript,
    intent,
    task,
    error,
    start,
    stop,
  } = useVoiceStream()

  return (
    <main className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Voice Note Taker</h1>
        <p className="text-sm text-gray-500 mt-1">
          Press the mic, speak a task or note, and let AI handle the rest.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-700 mb-6">Record</h2>
          <div className="flex flex-col items-center">
            <MicButton status={status} onStart={start} onStop={stop} />
            <TranscriptDisplay
              partialText={partialText}
              finalTranscript={finalTranscript}
              intent={intent}
              task={task}
              error={error}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <TaskList />
        </div>
      </div>
    </main>
  )
}
