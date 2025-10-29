"""Response schemas for API endpoints."""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from models.session import SessionState


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    session_id: str = Field(..., description="Session identifier")
    response: str = Field(..., description="Agent response message")
    session_state: SessionState = Field(..., description="Current session state")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional data (extracted foods, nutrition analysis, etc.)",
    )
    next_actions: List[str] = Field(
        default_factory=list,
        description="Suggested next actions for the user",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "user-123",
                    "response": "I've tracked your meals. You had fried rice for breakfast...",
                    "session_state": "advised",
                    "data": {
                        "extracted_foods": [],
                        "nutrition_analysis": {},
                    },
                    "next_actions": ["view_summary", "add_more_food", "reset"],
                }
            ]
        }
    }


class SessionStateResponse(BaseModel):
    """Response schema for session state."""

    session_id: str
    current_state: SessionState
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SessionInfoResponse(BaseModel):
    """Response schema for detailed session information."""

    session_id: str
    current_state: SessionState
    extracted_foods: List[Any] = Field(default_factory=list)
    pending_clarifications: List[Any] = Field(default_factory=list)
    has_analysis: bool = False
    advisor_recommendations: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SessionListItem(BaseModel):
    """Single session in list response."""

    session_id: str
    current_state: SessionState
    updated_at: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response schema for listing sessions."""

    sessions: List[SessionListItem] = Field(default_factory=list)
    total: int = Field(0, description="Total number of sessions")


# ============================================================================
# STREAMING SSE SCHEMAS
# ============================================================================


class StreamEventBase(BaseModel):
    """Base schema for all SSE stream events."""

    event: str = Field(..., description="Event type")


class TokenStreamEvent(StreamEventBase):
    """Event for streaming individual LLM tokens."""

    event: Literal["token"] = "token"
    data: str = Field(..., description="Token content")


class MetadataStreamEvent(StreamEventBase):
    """Event for streaming session state metadata updates."""

    event: Literal["metadata"] = "metadata"
    data: Dict[str, Any] = Field(
        ..., description="Metadata (session state, extracted foods, etc.)"
    )


class DataStreamEvent(StreamEventBase):
    """Event for streaming structured data (nutrition analysis, etc.)."""

    event: Literal["data"] = "data"
    data: Dict[str, Any] = Field(..., description="Structured data payload")


class DoneStreamEvent(StreamEventBase):
    """Event indicating stream completion with final response."""

    event: Literal["done"] = "done"
    data: ChatResponse = Field(..., description="Complete final response")


class ErrorStreamEvent(StreamEventBase):
    """Event for streaming errors."""

    event: Literal["error"] = "error"
    data: Dict[str, str] = Field(
        ..., description="Error information with 'error' and 'detail' keys"
    )
