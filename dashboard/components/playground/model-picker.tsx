"use client"

import { useEffect, useState } from "react"
import { Plus, X } from "lucide-react"
import { apiGet } from "@/lib/api"
import type { ModelOption } from "@/lib/types"
import { cn } from "@/lib/utils"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const FALLBACK_MODELS: ModelOption[] = [
  { provider: "anthropic", model: "claude-haiku-4-5" },
  { provider: "anthropic", model: "claude-sonnet-4-6" },
  { provider: "openai", model: "gpt-4o-mini" },
  { provider: "groq", model: "llama-3.3-70b" },
]

const MAX_COLUMNS = 3

function keyOf(o: ModelOption) {
  return `${o.provider}/${o.model}`
}

export function ModelPicker({
  selected,
  onChange,
}: {
  selected: ModelOption[]
  onChange: (next: ModelOption[]) => void
}) {
  const [options, setOptions] = useState<ModelOption[]>(FALLBACK_MODELS)

  useEffect(() => {
    let cancelled = false
    apiGet<ModelOption[]>("/models")
      .then((data) => {
        if (!cancelled && Array.isArray(data) && data.length > 0) {
          setOptions(data)
        }
      })
      .catch(() => {
        // 404 / unreachable -> keep fallback list
      })
    return () => {
      cancelled = true
    }
  }, [])

  const available = options.filter(
    (o) => !selected.some((s) => keyOf(s) === keyOf(o)),
  )

  const canAdd = selected.length < MAX_COLUMNS && available.length > 0

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-1.5">
        {selected.map((m) => (
          <div
            key={keyOf(m)}
            className="flex items-center justify-between rounded-md border border-border bg-secondary/50 px-2.5 py-1.5"
          >
            <div className="flex min-w-0 flex-col">
              <span className="truncate font-mono text-xs text-foreground">
                {m.model}
              </span>
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                {m.provider}
              </span>
            </div>
            <button
              type="button"
              aria-label={`Remove ${m.model}`}
              onClick={() => onChange(selected.filter((s) => keyOf(s) !== keyOf(m)))}
              className="rounded p-0.5 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="size-3.5" />
            </button>
          </div>
        ))}
      </div>

      {selected.length === 0 && (
        <p className="text-xs text-muted-foreground">No models selected.</p>
      )}

      <Select
        value=""
        disabled={!canAdd}
        onValueChange={(val) => {
          const opt = options.find((o) => keyOf(o) === val)
          if (opt) onChange([...selected, opt])
        }}
      >
        <SelectTrigger
          className={cn(
            "h-8 w-full justify-start gap-1.5 text-xs",
            !canAdd && "opacity-50",
          )}
        >
          <Plus className="size-3.5" />
          <SelectValue
            placeholder={
              selected.length >= MAX_COLUMNS
                ? `Max ${MAX_COLUMNS} models`
                : "Add model"
            }
          />
        </SelectTrigger>
        <SelectContent>
          {available.map((o) => (
            <SelectItem key={keyOf(o)} value={keyOf(o)} className="font-mono text-xs">
              <span className="text-muted-foreground">{o.provider}/</span>
              {o.model}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
