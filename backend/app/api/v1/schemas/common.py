"""Common schemas used across endpoints."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    message: str = Field(..., description="Status message")
