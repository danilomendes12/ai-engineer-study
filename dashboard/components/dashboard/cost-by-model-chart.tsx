"use client"

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { Card } from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

const chartConfig = {
  cost_usd: {
    label: "Cost (USD)",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig

export function CostByModelChart({
  data,
}: {
  data: { model: string; cost_usd: number }[]
}) {
  return (
    <Card className="gap-4 p-4">
      <div className="flex flex-col gap-0.5">
        <span className="text-sm font-medium text-foreground">Cost by model</span>
        <span className="text-xs text-muted-foreground">Spend today, USD</span>
      </div>
      <ChartContainer config={chartConfig} className="h-56 w-full">
        <BarChart accessibilityLayer data={data} margin={{ left: 4, right: 4 }}>
          <CartesianGrid vertical={false} stroke="var(--border)" />
          <XAxis
            dataKey="model"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={56}
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            tickFormatter={(v) => `$${Number(v).toFixed(2)}`}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value) => `$${Number(value).toFixed(4)}`}
              />
            }
          />
          <Bar dataKey="cost_usd" fill="var(--color-cost_usd)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ChartContainer>
    </Card>
  )
}
