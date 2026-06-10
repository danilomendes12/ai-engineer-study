"use client"

import { useState } from "react"
import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useDashboard } from "./use-dashboard"
import { StatCards } from "./stat-cards"
import { CostByModelChart } from "./cost-by-model-chart"
import { CallsTable } from "./calls-table"
import { CallDetailSheet } from "./call-detail-sheet"
import { cn } from "@/lib/utils"

export function DashboardClient() {
  const {
    stats,
    calls,
    loading,
    offset,
    pageSize,
    total,
    hasNext,
    hasPrev,
    refresh,
    nextPage,
    prevPage,
  } = useDashboard()

  const [activeCallId, setActiveCallId] = useState<string | null>(null)
  const [sheetOpen, setSheetOpen] = useState(false)

  const costByModel = stats?.cost_by_model

  return (
    <main className="flex-1 overflow-auto bg-background">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 p-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              Cost Dashboard
            </h1>
            <p className="text-xs text-muted-foreground">
              Spend, latency and per-call observability for today.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            disabled={loading}
            onClick={refresh}
          >
            <RefreshCw className={cn("size-3.5", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>

        <StatCards stats={stats} loading={loading} />

        {costByModel && costByModel.length > 0 && (
          <CostByModelChart data={costByModel} />
        )}

        <CallsTable
          calls={calls}
          loading={loading}
          offset={offset}
          pageSize={pageSize}
          total={total}
          hasNext={hasNext}
          hasPrev={hasPrev}
          onNext={nextPage}
          onPrev={prevPage}
          onRowClick={(id) => {
            setActiveCallId(id)
            setSheetOpen(true)
          }}
        />
      </div>

      <CallDetailSheet
        callId={activeCallId}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
      />
    </main>
  )
}
