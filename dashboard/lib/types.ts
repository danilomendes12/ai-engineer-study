// Shared types for the LLM Playground & Cost Dashboard.

export interface ModelOption {
  provider: string
  model: string
}

export interface GenParams {
  temperature: number | null
  top_p: number | null
  top_k: number | null
  max_tokens: number
}

export interface Usage {
  input_tokens: number
  output_tokens: number
}

// --- WebSocket frames from {WS_BASE}/ws/generate ---

export interface TokenFrame {
  type: "token"
  content: string
}

export interface DoneFrame {
  type: "done"
  call_id: string
  usage: Usage
  cost_usd: number
  ttft_ms: number
  latency_ms: number
  // Some providers ignore params like top_k; backend may flag them here.
  ignored_params?: string[]
}

export interface ErrorFrame {
  type: "error"
  message: string
}

export type GenFrame = TokenFrame | DoneFrame | ErrorFrame

// --- Dashboard REST shapes ---

export interface Stats {
  total_spend_usd: number
  avg_cost_per_call_usd: number
  latency_p50_ms: number
  latency_p90_ms: number
  latency_p99_ms: number
  call_count: number
  cost_by_model?: { model: string; cost_usd: number }[]
}

export interface CallRow {
  id: string
  time: string
  provider: string
  model: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
  ttft_ms: number
  latency_ms: number
  status: "ok" | "error"
}

export interface CallDetail extends CallRow {
  system_prompt: string
  user_prompt: string
  params: GenParams
  response_text: string
}
