import { type NextRequest, NextResponse } from "next/server"
import { ChatRepository } from "@/api/repositories/chat.repository"

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json()

    const chatRepository = new ChatRepository()
    const response = await chatRepository.chat(message)

    console.log(response.data.response);
    // Return as streaming text response
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        // Send the response text directly
        controller.enqueue(encoder.encode(response.data.response))
        controller.close()
      },
    })

    return new NextResponse(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
      },
    })
  } catch (error) {
    console.error("Chat API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
