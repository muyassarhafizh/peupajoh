"""Standardized response utilities."""

from typing import Any, Optional
from pydantic import BaseModel


class StandardResponse(BaseModel):
    """Wrapper for all API responses."""

    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None

    @classmethod
    def success_response(
        cls,
        data: Any = None,
        message: Optional[str] = None,
    ) -> "StandardResponse":
        """Create a success response."""
        return cls(
            success=True,
            data=data,
            message=message,
        )

    @classmethod
    def error_response(
        cls,
        error: str,
        data: Any = None,
    ) -> "StandardResponse":
        """Create an error response."""
        return cls(
            success=False,
            error=error,
            data=data,
        )
