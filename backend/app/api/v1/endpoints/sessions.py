"""Session management endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from usecase.main_workflow import MainWorkflow
from models.session import SessionState
from app.api.deps import get_workflow
from app.api.v1.schemas import (
    SessionInfoResponse,
    SessionStateResponse,
    SessionListResponse,
    SessionListItem,
    SessionResetRequest,
)
from app.core.responses import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{session_id}",
    response_model=SessionInfoResponse,
    summary="Get session information",
    description="Retrieve detailed information about a specific session.",
)
async def get_session_info(
    session_id: str,
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    Get detailed session information.

    Args:
        session_id: Session identifier
        workflow: MainWorkflow instance (injected)

    Returns:
        SessionInfoResponse with detailed session data

    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Fetching session info for: {session_id}")

        session_info = workflow.get_session_info(session_id)

        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found",
            )

        # Parse session state
        state_str = session_info.get("current_state", "initial")
        try:
            current_state = SessionState(state_str.lower())
        except ValueError:
            current_state = SessionState.INITIAL

        # Build response
        response = SessionInfoResponse(
            session_id=session_id,
            current_state=current_state,
            extracted_foods=session_info.get("extracted_foods", []),
            pending_clarifications=session_info.get("pending_clarifications", []),
            has_analysis=bool(session_info.get("advisor_recommendations")),
            advisor_recommendations=session_info.get("advisor_recommendations"),
            created_at=session_info.get("created_at"),
            updated_at=session_info.get("updated_at"),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session info: {str(e)}",
        ) from e


@router.get(
    "/{session_id}/state",
    response_model=SessionStateResponse,
    summary="Get session state",
    description="Retrieve the current state of a session.",
)
async def get_session_state(
    session_id: str,
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    Get current session state.

    Args:
        session_id: Session identifier
        workflow: MainWorkflow instance (injected)

    Returns:
        SessionStateResponse with current state

    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Fetching session state for: {session_id}")

        state_data = workflow.get_session_state(session_id)

        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found",
            )

        # Parse session state
        state_str = state_data.get("current_state", "initial")
        try:
            current_state = SessionState(state_str.lower())
        except ValueError:
            current_state = SessionState.INITIAL

        response = SessionStateResponse(
            session_id=session_id,
            current_state=current_state,
            created_at=state_data.get("created_at"),
            updated_at=state_data.get("updated_at"),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session state: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session state: {str(e)}",
        ) from e


@router.post(
    "/{session_id}/reset",
    response_model=StandardResponse,
    summary="Reset session",
    description="Reset a session to initial state.",
)
async def reset_session(
    session_id: str,
    request: SessionResetRequest,
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    Reset session to initial state.

    Args:
        session_id: Session identifier
        request: Reset confirmation request
        workflow: MainWorkflow instance (injected)

    Returns:
        StandardResponse with success status

    Raises:
        HTTPException: If reset fails
    """
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset confirmation required",
            )

        logger.info(f"Resetting session: {session_id}")

        workflow.reset_session(session_id)

        return StandardResponse.success_response(
            message=f"Session '{session_id}' reset successfully",
            data={"session_id": session_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset session: {str(e)}",
        ) from e


@router.delete(
    "/{session_id}",
    response_model=StandardResponse,
    summary="Delete session",
    description="Delete a session completely.",
)
async def delete_session(
    session_id: str,
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    Delete a session.

    Args:
        session_id: Session identifier
        workflow: MainWorkflow instance (injected)

    Returns:
        StandardResponse with success status

    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info(f"Deleting session: {session_id}")

        # Reset is the same as delete in current implementation
        workflow.reset_session(session_id)

        return StandardResponse.success_response(
            message=f"Session '{session_id}' deleted successfully",
            data={"session_id": session_id},
        )

    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}",
        ) from e


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List all sessions",
    description="Retrieve a list of all sessions.",
)
async def list_sessions(
    workflow: MainWorkflow = Depends(get_workflow),
):
    """
    List all sessions.

    Args:
        workflow: MainWorkflow instance (injected)

    Returns:
        SessionListResponse with list of sessions

    Raises:
        HTTPException: If listing fails
    """
    try:
        logger.info("Listing all sessions")

        sessions_data = workflow.list_sessions()

        # Convert to response format
        session_items = []
        for session_data in sessions_data:
            state_str = session_data.get("current_state", "initial")
            try:
                current_state = SessionState(state_str.lower())
            except ValueError:
                current_state = SessionState.INITIAL

            session_items.append(
                SessionListItem(
                    session_id=session_data["session_id"],
                    current_state=current_state,
                    updated_at=session_data.get("updated_at"),
                )
            )

        response = SessionListResponse(
            sessions=session_items,
            total=len(session_items),
        )

        return response

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}",
        ) from e
