import { ApiFactory } from "../api.factory";
import { v4 as uuidv4 } from 'uuid';
import { ChatResponse } from "@/entities/chat-response.entity";

export class ChatRepository extends ApiFactory {
  async chat(message: string) {
    let sessionId = uuidv4();

    // const mockData: ChatResponse = {
    //   session_id: sessionId,
    //   response: 'I received your message: "' + message + '".',
    //   session_state: 'initial',
    //   next_actions: [],
    // }

    // return mockData;
    let response = await this.fetch<ChatResponse>('/api/v1/chat', {
      method: 'POST',
      body: { message, session_id: sessionId },
    });

    return response;
  }
}   