import { ApiFactory } from "../api.factory";
import { v4 as uuidv4 } from 'uuid';
import { ChatResponse } from "@/entities/chat-response.entity";

export class ChatRepository extends ApiFactory {
  async chat(message: string) {
    let sessionId = uuidv4();

    
    let response = await this.fetch<ChatResponse>('/api/v1/chat', {
      method: 'POST',
      body: { message, session_id: sessionId },
    });

    return response;
  }
}   