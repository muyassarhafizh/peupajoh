from typing import Dict, Any, Optional
import json
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import AppSession
from models.session import SessionState


class SessionRepository:
    """Repository for managing application session state persistence using SQLAlchemy"""

    def __init__(self, db: Session):
        """
        Initialize repository with SQLAlchemy session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state from database"""
        session = self.db.query(AppSession).filter(AppSession.session_id == session_id).first()

        if session and session.session_data:
            try:
                return json.loads(session.session_data)
            except json.JSONDecodeError as e:
                print(f"Error deserializing session state for {session_id}: {e}")
                return None
        return None

    def save_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save or update session state in database"""
        try:
            serialized_state = json.dumps(state)

            # Check if session exists
            existing = self.db.query(AppSession).filter(AppSession.session_id == session_id).first()

            if existing:
                # Update existing session
                existing.session_data = serialized_state
                existing.session_type = "workflow"
            else:
                # Create new session
                new_session = AppSession(
                    session_id=session_id,
                    session_type="workflow",
                    session_data=serialized_state,
                )
                self.db.add(new_session)

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error saving session state for {session_id}: {e}")
            return False

    def create_initial_session(self, session_id: str) -> Dict[str, Any]:
        """Create a new session with initial state"""
        initial_state = {
            "current_state": SessionState.INITIAL.value,
            "extracted_foods": [],
            "pending_clarifications": [],
            "clarification_responses": {},
            "advisor_recommendations": None,
            "user_message": None,
        }

        success = self.save_session_state(session_id, initial_state)
        if success:
            return initial_state
        else:
            raise Exception(f"Failed to create initial session for {session_id}")

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Get existing session or create new one if it doesn't exist"""
        existing_state = self.get_session_state(session_id)

        if existing_state is not None:
            return existing_state
        else:
            return self.create_initial_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from database"""
        try:
            session = self.db.query(AppSession).filter(AppSession.session_id == session_id).first()
            if session:
                self.db.delete(session)
                self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting session {session_id}: {e}")
            return False

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset session to initial state"""
        return self.create_initial_session(session_id)

    def list_sessions(self) -> list[Dict[str, Any]]:
        """List all sessions with basic info"""
        try:
            sessions_query = (
                self.db.query(AppSession)
                .order_by(AppSession.updated_at.desc())
                .all()
            )

            sessions = []
            for session in sessions_query:
                sessions.append({
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                })

            return sessions
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata and current state info"""
        session = self.db.query(AppSession).filter(AppSession.session_id == session_id).first()

        if session and session.session_data:
            try:
                state = json.loads(session.session_data)
                return {
                    "session_id": session.session_id,
                    "current_state": state.get("current_state"),
                    "extracted_foods": state.get("extracted_foods", []),
                    "pending_clarifications": state.get("pending_clarifications", []),
                    "advisor_recommendations": state.get("advisor_recommendations"),
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                }
            except json.JSONDecodeError:
                return None
        return None
