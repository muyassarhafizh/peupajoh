"use client"

import type React from "react"

import type { Message, LoadingState } from "./chat-container"
import { MessageBubble } from "./message-bubble"
import { Spinner } from "@/components/ui/spinner"
import { Loader2 } from "lucide-react"

interface MessageListProps {
  messages: Message[]
  loadingState: LoadingState
  messagesEndRef: React.RefObject<HTMLDivElement | null>
}

export function MessageList({ messages, loadingState, messagesEndRef }: MessageListProps) {
  const renderLoadingIndicator = () => {
    if (loadingState === 'connecting') {
      return (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Connecting to server...</span>
        </div>
      )
    }
    
    if (loadingState === 'streaming') {
      return (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
          <div className="flex gap-1">
            <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
            <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
            <div className="h-2 w-2 rounded-full bg-primary animate-bounce" />
          </div>
          <span>Receiving response...</span>
        </div>
      )
    }
    
    return null
  }

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
          {(loadingState === 'connecting' || loadingState === 'streaming') && (
            <div className="flex justify-start">
              {renderLoadingIndicator()}
            </div>
          )}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  )
}
