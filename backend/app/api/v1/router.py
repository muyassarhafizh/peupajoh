"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, sessions, health

# Create v1 router
api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(
    chat.router,
    tags=["chat"],
)

api_v1_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"],
)

api_v1_router.include_router(
    health.router,
    tags=["health"],
)
