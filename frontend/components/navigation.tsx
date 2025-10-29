"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-border bg-card">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-primary-foreground">PA</span>
          </div>
          <span className="hidden font-semibold text-foreground sm:inline">Peupajoh</span>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-1 sm:gap-2">
          <Link href="/">
            <Button
              variant="ghost"
              className={cn("text-muted-foreground hover:text-foreground", pathname === "/" && "text-foreground")}
            >
              Home
            </Button>
          </Link>
          <Link href="/chat">
            <Button
              variant={pathname === "/chat" ? "default" : "ghost"}
              className={cn(pathname === "/chat" && "bg-primary text-primary-foreground")}
            >
              Chat
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  )
}
