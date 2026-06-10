"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { toast } from "sonner"
import { fetchCalls, fetchStats } from "@/lib/api"
import { API_BASE } from "@/lib/config"

const PAGE_SIZE = 50

export function useDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [calls, setCalls] = useState<CallRow[]>([])
  const [total, setTotal] = useState<number | null>(null)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [reachable, setReachable] = useState(true)
  const didInit = useRef(false)

  const load = useCallback(async (nextOffset: number) => {
    setLoading(true)
    try {
      const [statsData, callsData] = await Promise.all([
        fetchStats(),
        fetchCalls({ limit: PAGE_SIZE, offset: nextOffset }),
      ])
      setStats(statsData)
      setCalls(callsData)
      setTotal(null)
      setOffset(nextOffset)
      setReachable(true)
    } catch {
      setReachable(false)
      toast.error(`Backend unreachable at ${API_BASE}`)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (didInit.current) return
    didInit.current = true
    load(0)
  }, [load])

  const refresh = useCallback(() => load(offset), [load, offset])
  const nextPage = useCallback(() => load(offset + PAGE_SIZE), [load, offset])
  const prevPage = useCallback(
    () => load(Math.max(0, offset - PAGE_SIZE)),
    [load, offset],
  )

  const hasNext =
    total != null ? offset + PAGE_SIZE < total : calls.length === PAGE_SIZE
  const hasPrev = offset > 0

  return {
    stats,
    calls,
    loading,
    reachable,
    offset,
    pageSize: PAGE_SIZE,
    total,
    hasNext,
    hasPrev,
    refresh,
    nextPage,
    prevPage,
  }
}
