from typing import Dict, Any, Optional
import json
from agno.db.sqlite import SqliteDb
from models.session import SessionState

class SessionRepository:
    """Repository for managing session state persistence"""
    
    def __init__(self, db_file: str = "agno.db"):
        self.db = SqliteDb(db_file=db_file)
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize database tables for session management"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS agno_sessions (
                session_id TEXT PRIMARY KEY,
                session_state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state from database"""
        result = self.db.execute(
            "SELECT session_state FROM agno_sessions WHERE session_id = ?",
            (session_id,)
        )
        
        if result and len(result) > 0:
            try:
                return json.loads(result[0][0])
            except (json.JSONDecodeError, IndexError) as e:
                print(f"Error deserializing session state for {session_id}: {e}")
                return None
        return None
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Save or update session state in database"""
        try:
            serialized_state = json.dumps(state)
            
            self.db.execute("""
                INSERT OR REPLACE INTO agno_sessions (session_id, session_state, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (session_id, serialized_state))
            
            return True
        except Exception as e:
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
            "user_message": None
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
            self.db.execute(
                "DELETE FROM agno_sessions WHERE session_id = ?",
                (session_id,)
            )
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset session to initial state"""
        return self.create_initial_session(session_id)
    
    def list_sessions(self) -> list[Dict[str, Any]]:
        """List all sessions with basic info"""
        try:
            result = self.db.execute("""
                SELECT session_id, created_at, updated_at 
                FROM agno_sessions 
                ORDER BY updated_at DESC
            """)
            
            sessions = []
            for row in result:
                sessions.append({
                    "session_id": row[0],
                    "created_at": row[1],
                    "updated_at": row[2]
                })
            
            return sessions
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata and current state info"""
        result = self.db.execute("""
            SELECT session_id, session_state, created_at, updated_at 
            FROM agno_sessions 
            WHERE session_id = ?
        """, (session_id,))
        
        if result and len(result) > 0:
            row = result[0]
            try:
                state = json.loads(row[1])
                return {
                    "session_id": row[0],
                    "current_state": state.get("current_state"),
                    "extracted_foods_count": len(state.get("extracted_foods", [])),
                    "pending_clarifications_count": len(state.get("pending_clarifications", [])),
                    "has_advice": bool(state.get("advisor_recommendations")),
                    "created_at": row[2],
                    "updated_at": row[3]
                }
            except json.JSONDecodeError:
                return None
        return None