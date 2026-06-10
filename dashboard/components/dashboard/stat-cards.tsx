"use client"

import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { Stats } from "@/lib/types"

function StatCard({
  label,
  value,
  sub,
}: {
  label: string
  value: string
  sub?: string
}) {
  return (
    <Card className="gap-1 p-4">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="font-mono text-2xl font-semibold tracking-tight text-foreground">
        {value}
      </span>
      {sub && <span className="font-mono text-xs text-muted-foreground">{sub}</span>}
    </Card>
  )
}

export function StatCards({
  stats,
  loading,
}: {
  stats: Stats | null
  loading: boolean
}) {
  if (loading && !stats) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="gap-2 p-4">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-7 w-24" />
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatCard
        label="Spend today"
        value={`$${stats.total_spend_usd.toFixed(4)}`}
        sub={`${stats.call_count.toLocaleString("en-US")} calls`}
      />
      <StatCard
        label="Avg cost / call"
        value={`$${stats.avg_cost_per_call_usd.toFixed(4)}`}
      />
      <StatCard
        label="Latency p50 / p90 / p99"
        value={`${Math.round(stats.latency_p50_ms)} ms`}
        sub={`p90 ${Math.round(stats.latency_p90_ms)} ms · p99 ${Math.round(stats.latency_p99_ms)} ms`}
      />
      <StatCard
        label="Call count"
        value={stats.call_count.toLocaleString("en-US")}
        sub="today"
      />
    </div>
  )
}
