"use client"

import { useState, useRef, useEffect } from "react"
import { MessageList } from "./message-list"
import { ChatInput } from "./chat-input"
import { ChatHeader } from "./chat-header"
import { ChatRepository } from "@/api/repositories/chat.repository"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export type LoadingState = 'idle' | 'connecting' | 'streaming' | 'error'

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [nextActions, setNextActions] = useState<string[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatRepository = useRef(new ChatRepository())

  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  
  useEffect(() => {
    setMounted(true)
  }, [])

  
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

  
  useEffect(() => {
    if (mounted) {
      localStorage.setItem("chatHistory", JSON.stringify(messages))
    }
  }, [messages, mounted])

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || loadingState !== 'idle') return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setError(null)
    setLoadingState('connecting')

    // Create placeholder for assistant message
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, assistantMessage])

    try {
      let fullContent = ""
      let hasReceivedFirstChunk = false

      await chatRepository.current.streamChat(
        content,
        sessionId,
        {
          onContent: (chunk: string) => {
            if (!hasReceivedFirstChunk) {
              hasReceivedFirstChunk = true
              setLoadingState('streaming')
            }
            
            fullContent += chunk
            
            // Update message content
            setMessages((prev) =>
              prev.map((msg) => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: fullContent } 
                  : msg
              ),
            )
          },
          onMetadata: (metadata) => {
            if (metadata.next_actions) {
              setNextActions(metadata.next_actions)
            }
            if (metadata.session_state) {
              // Store session state if needed
            }
          },
          onError: (errorMsg) => {
            setError(errorMsg)
            setLoadingState('error')
            // Remove the empty assistant message on error
            setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))
          },
          onDone: () => {
            setLoadingState('idle')
          },
        }
      )
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to get response"
      setError(errorMessage)
      setLoadingState('error')
      
      // Remove the empty assistant message on error
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId))
      
      // Reset to idle after showing error
      setTimeout(() => setLoadingState('idle'), 2000)
    }
  }

  const handleClearHistory = () => {
    setMessages([])
    localStorage.removeItem("chatHistory")
  }

  const handleActionClick = (action: string) => {
    
    setNextActions([])
    
    handleSendMessage(action)
  }

  return (
    <div className="flex h-full flex-col bg-background">
      <ChatHeader onClearHistory={handleClearHistory} />

      <div className="flex-1 overflow-hidden">
        <MessageList 
          messages={messages} 
          loadingState={loadingState}
          messagesEndRef={messagesEndRef} 
        />
      </div>

      {nextActions.length > 0 && (
        <div className="border-t border-border bg-muted/30 px-4 py-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Quick actions:</p>
          <div className="flex flex-wrap gap-2">
            {nextActions.map((action) => (
              <button
                key={action}
                onClick={() => handleActionClick(action)}
                disabled={loadingState !== 'idle'}
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

      <ChatInput onSendMessage={handleSendMessage} isLoading={loadingState !== 'idle'} />
    </div>
  )
}
