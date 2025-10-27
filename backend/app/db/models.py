"""SQLAlchemy models for database tables."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from config.database import Base


class FoodItem(Base):
    """
    Model for food_items table.

    Stores Indonesian food nutrition data per 100g.
    """

    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    calories = Column(Float, nullable=True)
    proteins = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    carbohydrate = Column(Float, nullable=True)
    image = Column(String, nullable=True)

    def __repr__(self):
        return f"<FoodItem(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "calories": self.calories,
            "proteins": self.proteins,
            "fat": self.fat,
            "carbohydrate": self.carbohydrate,
            "image": self.image,
        }


class AppSession(Base):
    """
    Model for app_sessions table.

    Stores application session state and workflow progression.
    Note: Separate from Agno framework's agno_sessions table which stores agent conversation history.
    """

    __tablename__ = "app_sessions"

    session_id = Column(String, primary_key=True, index=True)
    session_type = Column(String, nullable=True)
    session_data = Column(Text, nullable=True)  # JSON stored as TEXT
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    def __repr__(self):
        return (
            f"<AppSession(session_id='{self.session_id}', type='{self.session_type}')>"
        )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type,
            "session_data": self.session_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
