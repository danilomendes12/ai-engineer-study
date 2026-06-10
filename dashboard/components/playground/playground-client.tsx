"use client"

import { useState } from "react"
import { toast } from "sonner"
import { API_BASE } from "@/lib/config"
import type { GenParams, ModelOption } from "@/lib/types"
import { ConfigRail } from "./config-rail"
import { ComparisonColumn } from "./comparison-column"
import { usePlayground } from "./use-playground"

const DEFAULT_MODELS: ModelOption[] = [
  { provider: "anthropic", model: "claude-haiku-4-5" },
  { provider: "openai", model: "gpt-4o-mini" },
]

export function PlaygroundClient() {
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful assistant.")
  const [userPrompt, setUserPrompt] = useState("")
  const [params, setParams] = useState<GenParams>({
    temperature: null,
    top_p: null,
    top_k: null,
    max_tokens: 1024,
  })
  const [models, setModels] = useState<ModelOption[]>(DEFAULT_MODELS)

  const { columns, isStreaming, run, stop } = usePlayground()

  const handleRun = () => {
    if (models.length === 0 || !userPrompt.trim()) return
    // Optimistically detect an unreachable backend by probing the WS base.
    try {
      run({ models, systemPrompt, userPrompt, params })
    } catch {
      toast.error(`Backend unreachable at ${API_BASE}`)
    }
  }

  const gridCols =
    columns.length >= 3
      ? "lg:grid-cols-3"
      : columns.length === 2
        ? "lg:grid-cols-2"
        : "lg:grid-cols-1"

  return (
    <div className="flex min-h-0 flex-1">
      <ConfigRail
        systemPrompt={systemPrompt}
        setSystemPrompt={setSystemPrompt}
        userPrompt={userPrompt}
        setUserPrompt={setUserPrompt}
        params={params}
        setParams={setParams}
        models={models}
        setModels={setModels}
        isStreaming={isStreaming}
        onRun={handleRun}
        onStop={stop}
      />

      <main className="min-w-0 flex-1 overflow-auto bg-background p-4">
        {columns.length === 0 ? (
          <EmptyState modelCount={models.length} />
        ) : (
          <div className={`grid h-full grid-cols-1 gap-3 ${gridCols}`}>
            {columns.map((c) => (
              <ComparisonColumn key={c.id} column={c} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

function EmptyState({ modelCount }: { modelCount: number }) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="max-w-sm text-center">
        <p className="text-sm font-medium text-foreground">No comparison yet</p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {modelCount === 0
            ? "Add up to 3 models in the rail, enter a prompt, then press Run to stream responses side by side."
            : "Enter a user prompt and press Run to stream responses from the selected models side by side."}
        </p>
      </div>
    </div>
  )
}
