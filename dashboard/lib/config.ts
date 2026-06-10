// Single source of truth for backend endpoints.
// The browser talks ONLY to this local backend; provider API keys live there.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000"

// Derive the WebSocket base from the API base (http -> ws, https -> wss).
export const WS_BASE = API_BASE.replace(/^http/, "ws")
