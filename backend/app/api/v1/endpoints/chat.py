"""Chat endpoint for main user interaction."""

import logging
import json
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from usecase.main_workflow import MainWorkflow
from models.session import SessionState
from app.api.deps import get_workflow
from app.api.v1.schemas import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _determine_next_actions(session_state: SessionState) -> list[str]:
    """Determine suggested next actions based on session state."""
    actions = {
        SessionState.INITIAL: ["start_tracking"],
        SessionState.CLARIFYING: ["provide_clarification"],
        SessionState.ADVISING: ["wait_for_analysis"],
        SessionState.ADVISED: ["view_summary", "add_more_food", "reset"],
    }
    return actions.get(session_state, [])


@router.post(
    "/chat",
    summary="Process user message with streaming",
    description=(
        "Main chat endpoint for food tracking and nutrition analysis. "
        "Streams LLM responses in real-time using Server-Sent Events (SSE). "
        "Delegates to the MainWorkflow to process user input."
    ),
)
async def chat_endpoint(
    request: ChatRequest,
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    Process user message through the MainWorkflow with SSE streaming.

    Args:
        request: Chat request with session_id and message
        workflow: MainWorkflow instance (injected)

    Returns:
        EventSourceResponse streaming SSE events:
        - event: metadata - Session state updates and extracted data
        - event: token - Individual LLM response tokens
        - event: done - Final complete response
        - event: error - Error information

    Raises:
        HTTPException: If workflow initialization fails
    """
    logger.info(f"Processing streaming chat request for session: {request.session_id}")

    async def event_generator():
        """Generate SSE events from workflow stream."""
        try:
            async for event in workflow.process_user_input_stream(
                session_id=request.session_id,
                user_message=request.message,
            ):
                event_type = event.get("event", "message")
                event_data = event.get("data", {})
                data_json = json.dumps(event_data, ensure_ascii=False, default=str)

                yield {
                    "event": event_type,
                    "data": data_json,
                }

                logger.debug(
                    f"Sent {event_type} event for session {request.session_id}"
                )

                if event_type in ["done", "error"]:
                    logger.info(
                        f"Stream completed with {event_type} for session {request.session_id}"
                    )
                    break

        except Exception as e:
            logger.error(
                f"Error in stream for session {request.session_id}: {str(e)}",
                exc_info=True,
            )
            error_data = json.dumps(
                {"error": "stream_error", "detail": str(e)},
                ensure_ascii=False,
            )
            yield {
                "event": "error",
                "data": error_data,
            }

    return EventSourceResponse(event_generator())
