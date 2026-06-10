"use client"

import { Play, Square } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { GenParams, ModelOption } from "@/lib/types"
import { ModelPicker } from "./model-picker"

interface ConfigRailProps {
  systemPrompt: string
  setSystemPrompt: (v: string) => void
  userPrompt: string
  setUserPrompt: (v: string) => void
  params: GenParams
  setParams: (updater: (p: GenParams) => GenParams) => void
  models: ModelOption[]
  setModels: (next: ModelOption[]) => void
  isStreaming: boolean
  onRun: () => void
  onStop: () => void
}

export function ConfigRail({
  systemPrompt,
  setSystemPrompt,
  userPrompt,
  setUserPrompt,
  params,
  setParams,
  models,
  setModels,
  isStreaming,
  onRun,
  onStop,
}: ConfigRailProps) {
  const canRun = models.length > 0 && userPrompt.trim().length > 0 && !isStreaming

  return (
    <aside className="flex w-[340px] shrink-0 flex-col border-r border-border bg-sidebar">
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-5 p-4">
          {/* Prompts */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="system-prompt" className="text-xs font-medium">
              System prompt
            </Label>
            <Textarea
              id="system-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="You are a helpful assistant."
              className="min-h-20 resize-y font-mono text-xs leading-relaxed"
            />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="user-prompt" className="text-xs font-medium">
              User prompt
            </Label>
            <Textarea
              id="user-prompt"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Ask something..."
              className="min-h-36 resize-y font-mono text-xs leading-relaxed"
            />
          </div>

          <Separator />

          {/* Parameters */}
          <div className="flex flex-col gap-4">
            <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Parameters
            </span>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    id="temp-enabled"
                    checked={params.temperature !== null}
                    onChange={(e) =>
                      setParams((p) => ({ ...p, temperature: e.target.checked ? 1.0 : null }))
                    }
                    className="h-3 w-3 cursor-pointer accent-primary"
                  />
                  <Label htmlFor="temp-enabled" className="cursor-pointer text-xs text-muted-foreground">
                    temperature
                  </Label>
                </div>
                <span className="font-mono text-xs text-foreground">
                  {params.temperature !== null ? params.temperature.toFixed(1) : "—"}
                </span>
              </div>
              <Slider
                min={0}
                max={2}
                step={0.1}
                value={params.temperature ?? 1.0}
                disabled={params.temperature === null}
                onValueChange={(v) => setParams((p) => ({ ...p, temperature: v as number }))}
              />
            </div>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    id="top-p-enabled"
                    checked={params.top_p !== null}
                    onChange={(e) =>
                      setParams((p) => ({ ...p, top_p: e.target.checked ? 1.0 : null }))
                    }
                    className="h-3 w-3 cursor-pointer accent-primary"
                  />
                  <Label htmlFor="top-p-enabled" className="cursor-pointer text-xs text-muted-foreground">
                    top_p
                  </Label>
                </div>
                <span className="font-mono text-xs text-foreground">
                  {params.top_p !== null ? params.top_p.toFixed(2) : "—"}
                </span>
              </div>
              <Slider
                min={0}
                max={1}
                step={0.05}
                value={params.top_p ?? 1.0}
                disabled={params.top_p === null}
                onValueChange={(v) => setParams((p) => ({ ...p, top_p: v as number }))}
              />
            </div>

            <div className="flex items-center justify-between gap-3">
              <Label htmlFor="top-k" className="text-xs text-muted-foreground">
                top_k
              </Label>
              <Input
                id="top-k"
                type="number"
                inputMode="numeric"
                min={0}
                value={params.top_k ?? ""}
                placeholder="—"
                onChange={(e) =>
                  setParams((p) => ({
                    ...p,
                    top_k: e.target.value === "" ? null : Number(e.target.value),
                  }))
                }
                className="h-8 w-24 text-right font-mono text-xs"
              />
            </div>
            <p className="-mt-1 text-[11px] leading-relaxed text-muted-foreground">
              Only applied by providers that support it (e.g. Anthropic). Columns
              where it was ignored are flagged.
            </p>

            <div className="flex items-center justify-between gap-3">
              <Label htmlFor="max-tokens" className="text-xs text-muted-foreground">
                max_tokens
              </Label>
              <Input
                id="max-tokens"
                type="number"
                inputMode="numeric"
                min={1}
                value={params.max_tokens}
                onChange={(e) =>
                  setParams((p) => ({
                    ...p,
                    max_tokens: Number(e.target.value) || 0,
                  }))
                }
                className="h-8 w-24 text-right font-mono text-xs"
              />
            </div>
          </div>

          <Separator />

          {/* Models */}
          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Models{" "}
              <span className="font-mono normal-case text-muted-foreground">
                ({models.length}/3)
              </span>
            </span>
            <ModelPicker selected={models} onChange={setModels} />
          </div>
        </div>
      </ScrollArea>

      {/* Actions */}
      <div className="flex shrink-0 items-center gap-2 border-t border-border p-3">
        <Button
          className="flex-1 gap-1.5"
          disabled={!canRun}
          onClick={onRun}
        >
          <Play className="size-3.5" />
          Run
        </Button>
        {isStreaming && (
          <Button variant="destructive" className="gap-1.5" onClick={onStop}>
            <Square className="size-3.5" />
            Stop
          </Button>
        )}
      </div>
    </aside>
  )
}
