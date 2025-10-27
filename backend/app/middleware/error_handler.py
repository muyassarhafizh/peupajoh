"""Global error handling middleware."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import PeupajohAPIException

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware.

    Catches all exceptions and returns standardized error responses.
    """
    try:
        response = await call_next(request)
        return response

    except PeupajohAPIException as e:
        # Handle custom API exceptions
        logger.error(
            f"API Exception: {e.message}",
            extra={
                "status_code": e.status_code,
                "details": e.details,
                "path": request.url.path,
            },
        )

        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.message,
                "details": e.details,
            },
        )

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {str(e)}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation error",
                "details": str(e),
            },
        )

    except Exception as e:
        # Handle unexpected exceptions
        logger.error(
            f"Unexpected error: {str(e)}",
            exc_info=True,
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "details": "An unexpected error occurred",
            },
        )
