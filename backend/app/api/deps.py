"""Dependency injection for API endpoints."""

from fastapi import Depends
from sqlalchemy.orm import Session
from usecase.main_workflow import MainWorkflow
from repositories.session import SessionRepository
from config.database import get_db
from config.settings import Settings, settings


def get_session_repo(db: Session = Depends(get_db)) -> SessionRepository:
    """
    Get SessionRepository instance with database session.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        SessionRepository instance
    """
    return SessionRepository(db)


def get_workflow(db: Session = Depends(get_db)) -> MainWorkflow:
    """
    Get MainWorkflow instance with fresh database session.

    Creates a new SessionRepository for each request to avoid threading issues.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        MainWorkflow instance
    """
    session_repo = SessionRepository(db)
    return MainWorkflow(session_repo)


def get_settings() -> Settings:
    """Get the unified settings instance."""
    return settings
