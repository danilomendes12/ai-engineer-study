"use client"

import { useEffect, useState } from "react"
import { fetchCallDetail } from "@/lib/api"
import type { CallDetail } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

function Field({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className={mono ? "font-mono text-xs text-foreground" : "text-xs text-foreground"}>
        {value}
      </span>
    </div>
  )
}

function Block({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-secondary/40 p-2.5 font-mono text-xs leading-relaxed text-foreground">
        {value || "—"}
      </pre>
    </div>
  )
}

export function CallDetailSheet({
  callId,
  open,
  onOpenChange,
}: {
  callId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [detail, setDetail] = useState<CallDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open || !callId) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setDetail(null)
    fetchCallDetail(callId)
      .then((data) => {
        if (!cancelled) setDetail(data)
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load call detail.")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [open, callId])

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="font-mono text-sm">
            {detail ? `${detail.provider}/${detail.model}` : "Call detail"}
          </SheetTitle>
          <SheetDescription className="font-mono text-xs">
            {callId ?? "—"}
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-5 px-4 pb-6">
          {loading && (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          )}

          {error && (
            <p className="text-xs text-destructive">{error}</p>
          )}

          {detail && !loading && (
            <>
              <div className="flex items-center justify-between">
                <Badge
                  variant="outline"
                  className={
                    detail.status === "ok"
                      ? "border-primary/40 bg-primary/10 text-primary"
                      : "border-destructive/40 bg-destructive/10 text-destructive"
                  }
                >
                  {detail.status}
                </Badge>
                <span className="font-mono text-xs text-muted-foreground">
                  {new Date(detail.time).toLocaleString()}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 rounded-md border border-border p-3">
                <Field label="In tok" value={detail.input_tokens.toLocaleString("en-US")} />
                <Field label="Out tok" value={detail.output_tokens.toLocaleString("en-US")} />
                <Field label="Cost" value={`$${detail.cost_usd.toFixed(4)}`} />
                <Field label="TTFT" value={`${Math.round(detail.ttft_ms)} ms`} />
                <Field label="Latency" value={`${Math.round(detail.latency_ms)} ms`} />
              </div>

              <div className="grid grid-cols-2 gap-3 rounded-md border border-border p-3">
                <Field label="temperature" value={String(detail.params.temperature)} />
                <Field label="top_p" value={String(detail.params.top_p)} />
                <Field label="top_k" value={detail.params.top_k == null ? "—" : String(detail.params.top_k)} />
                <Field label="max_tokens" value={String(detail.params.max_tokens)} />
              </div>

              <Block label="System prompt" value={detail.system_prompt} />
              <Block label="User prompt" value={detail.user_prompt} />
              <Block label="Response" value={detail.response_text} />
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
