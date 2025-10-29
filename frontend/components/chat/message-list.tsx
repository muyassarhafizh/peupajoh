"use client"

import type React from "react"

import type { Message } from "./chat-container"
import { MessageBubble } from "./message-bubble"
import { Spinner } from "@/components/ui/spinner"

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  messagesEndRef: React.RefObject<HTMLDivElement | null>
}

export function MessageList({ messages, isLoading, messagesEndRef }: MessageListProps) {
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4 sm:p-6">
      {messages.length === 0 ? (
        <div className="flex h-full items-center justify-center">
          <div className="text-center">
            <h2 className="mb-2 text-xl font-semibold text-foreground">Welcome to Nutrition Advisor</h2>
            <p className="text-muted-foreground">
              Tell me about what you ate today, and I'll provide personalized nutrition insights.
            </p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex justify-center py-4">
              <Spinner />
            </div>
          )}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  )
}
