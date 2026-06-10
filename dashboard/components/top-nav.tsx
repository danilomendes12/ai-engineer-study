"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Activity, Terminal } from "lucide-react"
import { cn } from "@/lib/utils"
import { API_BASE } from "@/lib/config"

const tabs = [
  { href: "/playground", label: "Playground", icon: Terminal },
  { href: "/dashboard", label: "Dashboard", icon: Activity },
]

export function TopNav() {
  const pathname = usePathname()

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-border bg-sidebar px-4">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <div className="flex size-5 items-center justify-center rounded-sm bg-primary text-primary-foreground">
            <Terminal className="size-3" />
          </div>
          <span className="text-sm font-semibold tracking-tight">LLM Playground</span>
        </div>
        <nav className="flex items-center gap-1">
          {tabs.map((tab) => {
            const active = pathname.startsWith(tab.href)
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-accent text-foreground"
                    : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                )}
              >
                <Icon className="size-3.5" />
                {tab.label}
              </Link>
            )
          })}
        </nav>
      </div>
      <div className="flex items-center gap-2 font-mono text-xs text-muted-foreground">
        <span className="inline-block size-1.5 rounded-full bg-primary" />
        {API_BASE}
      </div>
    </header>
  )
}
