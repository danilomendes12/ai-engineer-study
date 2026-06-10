"use client"

import { useCallback, useRef, useState } from "react"
import { WS_BASE } from "@/lib/config"
import type { GenFrame, GenParams, ModelOption } from "@/lib/types"

export type ColumnStatus = "idle" | "streaming" | "done" | "error"

export interface ColumnState {
  id: string
  provider: string
  model: string
  status: ColumnStatus
  text: string
  error: string | null
  // populated on "done"
  ttftMs: number | null
  latencyMs: number | null
  inputTokens: number | null
  outputTokens: number | null
  costUsd: number | null
  ignoredParams: string[]
}

function makeColumn(option: ModelOption): ColumnState {
  return {
    id: `${option.provider}/${option.model}`,
    provider: option.provider,
    model: option.model,
    status: "idle",
    text: "",
    error: null,
    ttftMs: null,
    latencyMs: null,
    inputTokens: null,
    outputTokens: null,
    costUsd: null,
    ignoredParams: [],
  }
}

interface RunArgs {
  models: ModelOption[]
  systemPrompt: string
  userPrompt: string
  params: GenParams
}

export function usePlayground() {
  const [columns, setColumns] = useState<ColumnState[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const socketsRef = useRef<WebSocket[]>([])
  const openCountRef = useRef(0)

  const patch = useCallback((id: string, update: Partial<ColumnState>) => {
    setColumns((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...update } : c)),
    )
  }, [])

  const closeAll = useCallback(() => {
    socketsRef.current.forEach((ws) => {
      try {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close()
        }
      } catch {
        // ignore
      }
    })
    socketsRef.current = []
    openCountRef.current = 0
    setIsStreaming(false)
  }, [])

  const finishOne = useCallback(() => {
    openCountRef.current -= 1
    if (openCountRef.current <= 0) {
      openCountRef.current = 0
      setIsStreaming(false)
    }
  }, [])

  const run = useCallback(
    ({ models, systemPrompt, userPrompt, params }: RunArgs) => {
      // Reset to fresh columns for the selected models.
      const fresh = models.map(makeColumn)
      setColumns(fresh)

      // Close any leftover sockets.
      socketsRef.current.forEach((ws) => {
        try {
          ws.close()
        } catch {
          // ignore
        }
      })
      socketsRef.current = []
      openCountRef.current = models.length
      setIsStreaming(true)

      fresh.forEach((col) => {
        let ws: WebSocket
        try {
          ws = new WebSocket(`${WS_BASE}/ws/generate`)
        } catch {
          patch(col.id, {
            status: "error",
            error: "Failed to open WebSocket connection",
          })
          finishOne()
          return
        }
        socketsRef.current.push(ws)

        ws.onopen = () => {
          patch(col.id, { status: "streaming" })
          ws.send(
            JSON.stringify({
              provider: col.provider,
              model: col.model,
              system_prompt: systemPrompt,
              user_prompt: userPrompt,
              params: {
                temperature: params.temperature,
                top_p: params.top_p,
                top_k: params.top_k,
                max_tokens: params.max_tokens,
              },
            }),
          )
        }

        ws.onmessage = (event) => {
          let frame: GenFrame
          try {
            frame = JSON.parse(event.data) as GenFrame
          } catch {
            return
          }
          if (frame.type === "token") {
            setColumns((prev) =>
              prev.map((c) =>
                c.id === col.id ? { ...c, text: c.text + frame.content } : c,
              ),
            )
          } else if (frame.type === "done") {
            patch(col.id, {
              status: "done",
              ttftMs: frame.ttft_ms,
              latencyMs: frame.latency_ms,
              inputTokens: frame.usage?.input_tokens ?? null,
              outputTokens: frame.usage?.output_tokens ?? null,
              costUsd: frame.cost_usd,
              ignoredParams: frame.ignored_params ?? [],
            })
            try {
              ws.close()
            } catch {
              // ignore
            }
            finishOne()
          } else if (frame.type === "error") {
            patch(col.id, { status: "error", error: frame.message })
            try {
              ws.close()
            } catch {
              // ignore
            }
            finishOne()
          }
        }

        ws.onerror = () => {
          // Only surface the error if we haven't already finished this column.
          setColumns((prev) =>
            prev.map((c) =>
              c.id === col.id && c.status === "streaming"
                ? {
                    ...c,
                    status: "error",
                    error: "Connection error — is the backend running?",
                  }
                : c,
            ),
          )
        }

        ws.onclose = () => {
          // If the socket closed before "done"/"error", treat as ended.
          setColumns((prev) =>
            prev.map((c) =>
              c.id === col.id && c.status === "streaming"
                ? { ...c, status: c.text ? "done" : "error", error: c.text ? null : "Stream closed unexpectedly" }
                : c,
            ),
          )
        }
      })
    },
    [patch, finishOne],
  )

  const stop = useCallback(() => {
    closeAll()
    setColumns((prev) =>
      prev.map((c) =>
        c.status === "streaming" ? { ...c, status: "done" } : c,
      ),
    )
  }, [closeAll])

  return { columns, isStreaming, run, stop }
}
