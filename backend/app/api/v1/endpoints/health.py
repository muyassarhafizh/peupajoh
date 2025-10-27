"""Health check endpoint."""

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse
from config.settings import settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health status.",
    tags=["health"],
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with API status
    """
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        message="Peupajoh API is running",
    )
