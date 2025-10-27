"""Custom exceptions for the API."""

from typing import Any, Optional


class PeupajohAPIException(Exception):
    """Base exception for Peupajoh API."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class SessionNotFoundError(PeupajohAPIException):
    """Raised when a session is not found."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            status_code=404,
            details={"session_id": session_id},
        )


class ValidationError(PeupajohAPIException):
    """Raised when validation fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            details=details,
        )


class WorkflowError(PeupajohAPIException):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details,
        )


class DatabaseError(PeupajohAPIException):
    """Raised when database operation fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details,
        )
