"""Database configuration and session management using SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from config.settings import settings

# Create database URL from settings
# Support both SQLite and other databases (PostgreSQL, MySQL, etc.)
if settings.db_path.startswith("sqlite:///") or settings.db_path.startswith("postgresql://") or settings.db_path.startswith("mysql://"):
    DATABASE_URL = settings.db_path
else:
    # Assume it's a file path for SQLite
    db_dir = os.path.dirname(settings.db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{settings.db_path}"

# Create SQLAlchemy engine
# For SQLite, we need to enable check_same_thread=False to work with async/threading
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["pool_pre_ping"] = True
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)
