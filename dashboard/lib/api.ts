import { API_BASE } from "./config"
import type { CallDetail, CallRow, Stats } from "./types"

// Thin REST helper around the local backend. Throws on network/HTTP errors so
// callers can surface a "backend unreachable" toast.

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store",
  })
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} for ${path}`)
  }
  return (await res.json()) as T
}

interface BackendStatsResponse {
  cost: { count: number; total: number; avg: number; min: number; max: number; model: string | null }
  latency: { p50: number; p90: number; p99: number } | null
  ttft: { p50: number; p90: number; p99: number } | null
  daily_spend: { date: string; total: number; count: number }[]
}

export async function fetchStats(signal?: AbortSignal): Promise<Stats> {
  const raw = await apiGet<BackendStatsResponse>("/stats", signal)
  return {
    total_spend_usd: raw.cost.total,
    avg_cost_per_call_usd: raw.cost.avg,
    call_count: raw.cost.count,
    latency_p50_ms: raw.latency?.p50 ?? 0,
    latency_p90_ms: raw.latency?.p90 ?? 0,
    latency_p99_ms: raw.latency?.p99 ?? 0,
  }
}

interface BackendCallSchema {
  id: number
  created_at: string
  provider: string
  model: string
  input_tokens: number
  output_tokens: number
  cost: number
  latency: number
  prompt: string
  answer: string
  max_tokens: number | null
  temperature: number | null
  top_p: number | null
  top_k: number | null
  ttft_ms: number | null
  response_status: string | null
  system_prompt: string | null
}

function toCallRow(raw: BackendCallSchema): CallRow {
  return {
    id: String(raw.id),
    time: raw.created_at,
    provider: raw.provider,
    model: raw.model,
    input_tokens: raw.input_tokens,
    output_tokens: raw.output_tokens,
    cost_usd: raw.cost,
    ttft_ms: raw.ttft_ms ?? 0,
    latency_ms: raw.latency,
    status: raw.response_status === "error" ? "error" : "ok",
  }
}

export async function fetchCalls(
  params: { limit?: number; offset?: number; model?: string } = {},
  signal?: AbortSignal,
): Promise<CallRow[]> {
  const q = new URLSearchParams()
  if (params.limit != null) q.set("limit", String(params.limit))
  if (params.offset != null) q.set("offset", String(params.offset))
  if (params.model) q.set("model", params.model)
  const raw = await apiGet<BackendCallSchema[]>(`/calls?${q}`, signal)
  return raw.map(toCallRow)
}

export async function fetchCallDetail(id: string, signal?: AbortSignal): Promise<CallDetail> {
  const raw = await apiGet<BackendCallSchema>(`/calls/${id}`, signal)
  return {
    ...toCallRow(raw),
    system_prompt: raw.system_prompt ?? "",
    user_prompt: raw.prompt,
    response_text: raw.answer,
    params: {
      temperature: raw.temperature ?? 1,
      top_p: raw.top_p ?? 1,
      top_k: raw.top_k ?? null,
      max_tokens: raw.max_tokens ?? 1024,
    },
  }
}
