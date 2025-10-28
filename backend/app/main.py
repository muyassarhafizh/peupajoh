"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from config.database import init_db
from app.api.v1.router import api_v1_router
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging import logging_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Peupajoh API...")
    logger.info(f"API Version: {settings.api_version}")

    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Log configuration
    try:
        logger.info(f"LLM Provider: {settings.llm_provider}")
        logger.info(f"Model ID: {settings.model_id}")
        logger.info(f"Framework: {settings.framework}")
        logger.info(f"Database: {settings.db_path}")
        logger.info(f"Server: {settings.host}:{settings.port}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

    logger.info("Peupajoh API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Peupajoh API...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add custom middleware
    app.middleware("http")(logging_middleware)
    app.middleware("http")(error_handler_middleware)

    # Include API router
    app.include_router(api_v1_router, prefix=settings.api_prefix)

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Peupajoh API",
            "version": settings.api_version,
            "docs": settings.docs_url,
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
