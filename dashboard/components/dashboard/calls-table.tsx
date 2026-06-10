"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { CallRow } from "@/lib/types"

interface CallsTableProps {
  calls: CallRow[]
  loading: boolean
  offset: number
  pageSize: number
  total: number | null
  hasNext: boolean
  hasPrev: boolean
  onNext: () => void
  onPrev: () => void
  onRowClick: (id: string) => void
}

export function CallsTable({
  calls,
  loading,
  offset,
  pageSize,
  total,
  hasNext,
  hasPrev,
  onNext,
  onPrev,
  onRowClick,
}: CallsTableProps) {
  const rangeStart = calls.length === 0 ? 0 : offset + 1
  const rangeEnd = offset + calls.length

  return (
    <Card className="gap-0 overflow-hidden p-0">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="text-sm font-medium text-foreground">Recent calls</span>
        <span className="font-mono text-xs text-muted-foreground">
          {rangeStart}–{rangeEnd}
          {total != null ? ` of ${total}` : ""}
        </span>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="text-xs">Time</TableHead>
              <TableHead className="text-xs">Provider</TableHead>
              <TableHead className="text-xs">Model</TableHead>
              <TableHead className="text-right text-xs">In tok</TableHead>
              <TableHead className="text-right text-xs">Out tok</TableHead>
              <TableHead className="text-right text-xs">Cost USD</TableHead>
              <TableHead className="text-right text-xs">TTFT ms</TableHead>
              <TableHead className="text-right text-xs">Latency ms</TableHead>
              <TableHead className="text-xs">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && calls.length === 0 ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i} className="hover:bg-transparent">
                  {Array.from({ length: 9 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-3.5 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : calls.length === 0 ? (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={9} className="py-10 text-center text-xs text-muted-foreground">
                  No calls recorded yet.
                </TableCell>
              </TableRow>
            ) : (
              calls.map((c) => (
                <TableRow
                  key={c.id}
                  onClick={() => onRowClick(c.id)}
                  className="cursor-pointer"
                >
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {new Date(c.time).toLocaleTimeString()}
                  </TableCell>
                  <TableCell className="text-xs">{c.provider}</TableCell>
                  <TableCell className="font-mono text-xs">{c.model}</TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {c.input_tokens.toLocaleString("en-US")}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {c.output_tokens.toLocaleString("en-US")}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    ${c.cost_usd.toFixed(4)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Math.round(c.ttft_ms)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Math.round(c.latency_ms)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={
                        c.status === "ok"
                          ? "border-primary/40 bg-primary/10 font-mono text-[10px] text-primary"
                          : "border-destructive/40 bg-destructive/10 font-mono text-[10px] text-destructive"
                      }
                    >
                      {c.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
        <Button variant="outline" size="sm" disabled={!hasPrev || loading} onClick={onPrev}>
          Previous
        </Button>
        <Button variant="outline" size="sm" disabled={!hasNext || loading} onClick={onNext}>
          Next
        </Button>
      </div>
    </Card>
  )
}
