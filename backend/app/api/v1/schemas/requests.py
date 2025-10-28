"""Request schemas for API endpoints."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    session_id: str = Field(
        ...,
        description="Unique session identifier for the user",
        min_length=1,
        max_length=255,
    )
    message: str = Field(
        ...,
        description="User message for food tracking or nutrition questions",
        min_length=1,
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context (user profile, preferences, etc.)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "user-123",
                    "message": "Sarapan nasi goreng 2 porsi, lunch mie goreng",
                    "context": None,
                }
            ]
        }
    }


class SessionResetRequest(BaseModel):
    """Request schema for session reset."""

    confirm: bool = Field(
        True,
        description="Confirmation flag to reset session",
    )
