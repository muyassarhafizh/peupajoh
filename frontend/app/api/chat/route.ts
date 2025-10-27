import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json()

    if (!message || typeof message !== "string") {
      return NextResponse.json({ error: "Invalid message" }, { status: 400 })
    }

    // For now, this is a mock implementation that echoes the message
    // In production, this should call your Python backend

    const mockResponse = `I received your message: "${message}". 
    
This is a placeholder response. Once connected to the backend, I'll provide personalized nutrition analysis based on your food intake.

To integrate with your backend:
1. Replace this mock with an actual API call to your Python backend
2. Implement streaming response handling
3. Parse nutrition data from the backend response`

    // Simulate streaming by sending chunks
    const encoder = new TextEncoder()
    const chunks = mockResponse.split(" ")

    const stream = new ReadableStream({
      async start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk + " "))
          // Simulate network delay
          await new Promise((resolve) => setTimeout(resolve, 50))
        }
        controller.close()
      },
    })

    return new NextResponse(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Transfer-Encoding": "chunked",
      },
    })
  } catch (error) {
    console.error("Chat API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
