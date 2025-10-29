"use client"

import { useState, useRef, useEffect } from "react"
import { MessageList } from "./message-list"
import { ChatInput } from "./chat-input"
import { ChatHeader } from "./chat-header"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [nextActions, setNextActions] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Set mounted state on client-side
  useEffect(() => {
    setMounted(true)
  }, [])

  // Load chat history from localStorage after mount
  useEffect(() => {
    if (!mounted) return
    
    const saved = localStorage.getItem("chatHistory")
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setMessages(parsed.map((msg: any) => ({ ...msg, timestamp: new Date(msg.timestamp) })))
      } catch (e) {
        console.error("Failed to load chat history:", e)
      }
    }
  }, [mounted])

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (mounted) {
      localStorage.setItem("chatHistory", JSON.stringify(messages))
    }
  }, [messages, mounted])

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setError(null)
    setIsLoading(true)

    // Add placeholder for assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, assistantMessage])

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      if (!response.body) {
        throw new Error("No response body")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullContent = ""

      // Get next_actions from response headers
      const actionsHeader = response.headers.get("X-Next-Actions")
      if (actionsHeader) {
        try {
          const actions = JSON.parse(actionsHeader)
          setNextActions(actions)
        } catch (e) {
          console.error("Failed to parse next actions:", e)
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        fullContent += chunk

        // Update the assistant message with streamed content
        setMessages((prev) =>
          prev.map((msg) => (msg.id === assistantMessageId ? { ...msg, content: fullContent } : msg)),
        )
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to get response"
      setError(errorMessage)

      // Remove the placeholder assistant message on error
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearHistory = () => {
    setMessages([])
    localStorage.removeItem("chatHistory")
  }

  const handleActionClick = (action: string) => {
    // Clear the actions when user clicks one
    setNextActions([])
    // Send the action as a message
    handleSendMessage(action)
  }

  return (
    <div className="flex h-full flex-col bg-background">
      <ChatHeader onClearHistory={handleClearHistory} />

      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} isLoading={isLoading} messagesEndRef={messagesEndRef} />
      </div>

      {nextActions.length > 0 && (
        <div className="border-t border-border bg-muted/30 px-4 py-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Quick actions:</p>
          <div className="flex flex-wrap gap-2">
            {nextActions.map((action) => (
              <button
                key={action}
                onClick={() => handleActionClick(action)}
                disabled={isLoading}
                className="rounded-md border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {action.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="border-t border-border bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline hover:no-underline">
            Dismiss
          </button>
        </div>
      )}

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}
