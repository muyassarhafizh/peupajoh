"use client"

import { Button } from "@/components/ui/button"
import { Trash2 } from "lucide-react"

interface ChatHeaderProps {
  onClearHistory: () => void
}

export function ChatHeader({ onClearHistory }: ChatHeaderProps) {
  return (
    <div className="border-b border-border bg-card px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Nutrition Advisor</h1>
          <p className="text-sm text-muted-foreground">Chat with your AI nutritionist for personalized guidance</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearHistory}
          className="text-muted-foreground hover:text-foreground"
        >
          <Trash2 className="h-4 w-4" />
          <span className="ml-2 hidden sm:inline">Clear</span>
        </Button>
      </div>
    </div>
  )
}
