"use client"

import { AlertTriangle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { ColumnState } from "./use-playground"

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="font-mono text-xs text-foreground">{value}</span>
    </div>
  )
}

export function ComparisonColumn({ column }: { column: ColumnState }) {
  const { provider, model, status, text, error, ignoredParams } = column

  return (
    <div className="flex min-w-0 flex-col rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
        <div className="flex min-w-0 flex-col">
          <span className="truncate font-mono text-xs font-medium text-foreground">
            {model}
          </span>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            {provider}
          </span>
        </div>
        <StatusDot status={status} />
      </div>

      {/* Body */}
      <div className="min-h-0 flex-1 overflow-auto p-3">
        {status === "error" ? (
          <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-2.5 text-xs text-destructive">
            <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
            <span className="break-words">{error}</span>
          </div>
        ) : text ? (
          <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-foreground">
            {text}
            {status === "streaming" && (
              <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-primary align-middle" />
            )}
          </pre>
        ) : status === "streaming" ? (
          <span className="font-mono text-xs text-muted-foreground">
            Waiting for first token
            <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-primary align-middle" />
          </span>
        ) : (
          <span className="font-mono text-xs text-muted-foreground">
            Idle — press Run.
          </span>
        )}
      </div>

      {/* Footer (on completion) */}
      {status === "done" && (
        <div className="flex flex-col gap-2 border-t border-border px-3 py-2.5">
          {ignoredParams.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {ignoredParams.map((p) => (
                <Badge
                  key={p}
                  variant="outline"
                  className="border-amber-500/40 bg-amber-500/10 font-mono text-[10px] text-amber-500"
                >
                  {p} ignored
                </Badge>
              ))}
            </div>
          )}
          <div className="grid grid-cols-3 gap-x-3 gap-y-2">
            <Stat label="TTFT" value={fmtMs(column.ttftMs)} />
            <Stat label="Latency" value={fmtMs(column.latencyMs)} />
            <Stat label="Cost" value={fmtUsd(column.costUsd)} />
            <Stat label="In tok" value={fmtNum(column.inputTokens)} />
            <Stat label="Out tok" value={fmtNum(column.outputTokens)} />
          </div>
        </div>
      )}
    </div>
  )
}

function StatusDot({ status }: { status: ColumnState["status"] }) {
  const map: Record<ColumnState["status"], { cls: string; label: string }> = {
    idle: { cls: "bg-muted-foreground", label: "idle" },
    streaming: { cls: "bg-primary animate-pulse", label: "streaming" },
    done: { cls: "bg-primary", label: "done" },
    error: { cls: "bg-destructive", label: "error" },
  }
  const { cls, label } = map[status]
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn("size-1.5 rounded-full", cls)} />
      <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </span>
  )
}

function fmtMs(v: number | null) {
  return v == null ? "—" : `${Math.round(v)} ms`
}
function fmtNum(v: number | null) {
  return v == null ? "—" : v.toLocaleString("en-US")
}
function fmtUsd(v: number | null) {
  return v == null ? "—" : `$${v.toFixed(4)}`
}
