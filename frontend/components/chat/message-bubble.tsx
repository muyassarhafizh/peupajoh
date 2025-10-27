"use client"

import { useState, useEffect } from "react"
import type { Message } from "./chat-container"
import { cn } from "@/lib/utils"

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user"
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-xs rounded-lg px-4 py-3 sm:max-w-md md:max-w-lg",
          isUser ? "bg-primary text-primary-foreground" : "bg-card text-card-foreground border border-border",
        )}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        {mounted && (
          <span className="mt-2 block text-xs opacity-70">
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        )}
      </div>
    </div>
  )
}
