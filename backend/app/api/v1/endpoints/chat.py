"""Chat endpoint for main user interaction."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from usecase.main_workflow import MainWorkflow
from models.session import SessionState
from app.api.deps import get_workflow
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.exceptions import WorkflowError

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
    response_model=ChatResponse,
    summary="Process user message",
    description=(
        "Main chat endpoint for food tracking and nutrition analysis. "
        "Delegates to the MainWorkflow to process user input."
    ),
)
async def chat_endpoint(
    request: ChatRequest,
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    Process user message through the MainWorkflow.

    Args:
        request: Chat request with session_id and message
        workflow: MainWorkflow instance (injected)

    Returns:
        ChatResponse with agent response and session state

    Raises:
        HTTPException: If workflow execution fails
    """
    try:
        logger.info(f"Processing chat request for session: {request.session_id}")

        # Process user input through workflow
        result = await workflow.process_user_input(
            session_id=request.session_id,
            user_message=request.message,
        )

        # Extract session state
        session_state_str = result.get("current_state", "initial")
        try:
            session_state = SessionState(session_state_str.lower())
        except ValueError:
            logger.warning(
                f"Invalid session state '{session_state_str}', defaulting to INITIAL"
            )
            session_state = SessionState.INITIAL

        # Build response
        response = ChatResponse(
            session_id=request.session_id,
            response=result.get("message", "No response generated."),
            session_state=session_state,
            data=result.get("data", {}),
            next_actions=_determine_next_actions(session_state),
        )

        logger.info(
            f"""Chat request processed successfully. Initial state: {session_state.value}
            Final state: {response.session_state.value}"""
        )
        return response

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        ) from e
