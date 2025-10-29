import { type NextRequest, NextResponse } from "next/server"
import { ChatRepository } from "@/api/repositories/chat.repository"

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json()

    const chatRepository = new ChatRepository()
    const result = await chatRepository.chat(message)

    // Return as streaming text response
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        // TODO: need to structurize the response with the BE
        controller.enqueue(encoder.encode(result.response))
        controller.close()
      },
    })

    return new NextResponse(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        // @ts-ignore - TODO: Fix type mismatch between backend response and ApiEnvelope
        "X-Next-Actions": JSON.stringify(result.next_actions || []),
      },
    })
  } catch (error) {
    console.error("Chat API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
