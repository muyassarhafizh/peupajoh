import { ApiFactory } from "../api.factory";
import { v4 as uuidv4 } from 'uuid';
import { ChatResponse } from "@/entities/chat-response.entity";

export interface SSEEvent {
  type: 'content' | 'metadata' | 'error' | 'done';
  data: any;
}

export interface StreamCallbacks {
  onContent: (content: string) => void;
  onMetadata?: (metadata: { next_actions?: string[]; session_state?: string }) => void;
  onError?: (error: string) => void;
  onDone?: () => void;
}

export class ChatRepository extends ApiFactory {
  async chat(message: string) {
    let sessionId = uuidv4();

    
    let response = await this.fetch<ChatResponse>('/api/v1/chat', {
      method: 'POST',
      body: { message, session_id: sessionId },
    });

    return response;
  }

  /**
   * Stream chat response using Server-Sent Events (SSE)
   * @param message User message
   * @param sessionId Optional session ID (generates new one if not provided)
   * @param callbacks Callbacks for handling stream events
   */
  async streamChat(
    message: string,
    sessionId: string | null,
    callbacks: StreamCallbacks
  ): Promise<void> {
    const sid = sessionId || uuidv4();
    const url = new URL('/api/v1/chat/stream', this.baseUrl);

    try {
      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ message, session_id: sid }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          callbacks.onDone?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim() || line.startsWith(':')) {
            // Skip empty lines and comments
            continue;
          }

          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              callbacks.onDone?.();
              continue;
            }

            try {
              const event: SSEEvent = JSON.parse(data);
              
              switch (event.type) {
                case 'content':
                  callbacks.onContent(event.data);
                  break;
                case 'metadata':
                  callbacks.onMetadata?.(event.data);
                  break;
                case 'error':
                  callbacks.onError?.(event.data);
                  break;
                case 'done':
                  callbacks.onDone?.();
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e, data);
            }
          }
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      callbacks.onError?.(errorMessage);
      throw error;
    }
  }
}   