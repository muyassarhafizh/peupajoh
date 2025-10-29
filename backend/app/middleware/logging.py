"""Request/response logging middleware."""

import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    """
    Log incoming requests and outgoing responses.
    """
    # Start timer
    start_time = time.time()

    # Log request
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client": request.client.host if request.client else None,
        },
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"Completed request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {duration:.3f}s",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
        },
    )

    return response
