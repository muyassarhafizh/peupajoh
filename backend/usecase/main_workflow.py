from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from agno.db.sqlite import SqliteDb

from repositories.models.extraction import FoodExtractionResult, ExtractedFood
from repositories.extraction import extract_foods_structured


class SessionState(str, Enum):
    """Enumeration of possible session states in the food tracking workflow"""
    INITIAL = "initial"  # First action from user
    CLARIFYING = "clarifying"  # Search food agent responding to user
    ADVISING = "advising"  # Search food agent forwarding to advisor agent
    ADVISED = "advised"  # Advisors sent to user


class SessionData(BaseModel):
    """Model to store session state and related data"""
    session_id: str = Field(..., description="Unique session identifier")
    current_state: SessionState = Field(default=SessionState.INITIAL)
    user_message: Optional[str] = Field(None, description="Latest user message")
    extracted_foods: Optional[List[ExtractedFood]] = Field(None, description="Foods extracted from user message")
    pending_clarifications: List[str] = Field(default_factory=list, description="Foods that need clarification")
    clarification_responses: Dict[str, str] = Field(default_factory=dict, description="User responses to clarifications")
    advisor_recommendations: Optional[str] = Field(None, description="Nutritional advice generated")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update_state(self, new_state: SessionState):
        """Update the session state and timestamp"""
        self.current_state = new_state
        self.updated_at = datetime.now()


class MainWorkflow:
    """Main workflow orchestrator with session state management"""
    
    def __init__(self, db_file: str = "agno.db"):
        self.db = SqliteDb(db_file=db_file)
        self._sessions: Dict[str, SessionData] = {}
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database tables for session management"""
        # Create sessions table if it doesn't exist
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workflow_sessions (
                session_id TEXT PRIMARY KEY,
                current_state TEXT NOT NULL,
                user_message TEXT,
                extracted_foods TEXT,  -- JSON serialized
                pending_clarifications TEXT,  -- JSON serialized
                clarification_responses TEXT,  -- JSON serialized
                advisor_recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def get_or_create_session(self, session_id: str) -> SessionData:
        """Get existing session or create new one"""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # Try to load from database
        result = self.db.execute(
            "SELECT * FROM workflow_sessions WHERE session_id = ?",
            (session_id,)
        )
        
        if result:
            row = result[0]
            session_data = SessionData(
                session_id=row[0],
                current_state=SessionState(row[1]),
                user_message=row[2],
                extracted_foods=self._deserialize_json(row[3], []),
                pending_clarifications=self._deserialize_json(row[4], []),
                clarification_responses=self._deserialize_json(row[5], {}),
                advisor_recommendations=row[6],
                created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now()
            )
        else:
            # Create new session
            session_data = SessionData(session_id=session_id)
            self._save_session(session_data)
        
        self._sessions[session_id] = session_data
        return session_data
    
    def _save_session(self, session_data: SessionData):
        """Save session data to database"""
        import json
        
        self.db.execute("""
            INSERT OR REPLACE INTO workflow_sessions 
            (session_id, current_state, user_message, extracted_foods, 
             pending_clarifications, clarification_responses, advisor_recommendations, 
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data.session_id,
            session_data.current_state.value,
            session_data.user_message,
            json.dumps([food.model_dump() for food in session_data.extracted_foods]) if session_data.extracted_foods else None,
            json.dumps(session_data.pending_clarifications),
            json.dumps(session_data.clarification_responses),
            session_data.advisor_recommendations,
            session_data.created_at.isoformat(),
            session_data.updated_at.isoformat()
        ))
    
    def _deserialize_json(self, json_str: Optional[str], default: Any) -> Any:
        """Safely deserialize JSON string"""
        if not json_str:
            return default
        try:
            import json
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def process_user_input(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Main entry point for processing user input based on current session state"""
        session = self.get_or_create_session(session_id)
        
        # Route to appropriate handler based on current state
        if session.current_state == SessionState.INITIAL:
            return self._handle_initial_state(session, user_message)
        elif session.current_state == SessionState.CLARIFYING:
            return self._handle_clarifying_state(session, user_message)
        elif session.current_state == SessionState.ADVISING:
            return self._handle_advising_state(session, user_message)
        elif session.current_state == SessionState.ADVISED:
            return self._handle_advised_state(session, user_message)
        else:
            raise ValueError(f"Unknown session state: {session.current_state}")
    
    def _handle_initial_state(self, session: SessionData, user_message: str) -> Dict[str, Any]:
        """Handle the initial state - extract foods from user message"""
        session.user_message = user_message
        
        # Extract foods from user message
        extraction_result = extract_foods_structured(user_message)
        session.extracted_foods = extraction_result.foods
        
        # Check if any foods need clarification
        needs_clarification = []
        for food in extraction_result.foods:
            if food.needs_clarification:
                needs_clarification.append(food.name)
        
        if needs_clarification or extraction_result.ambiguities:
            # Transition to clarifying state
            session.pending_clarifications = needs_clarification + extraction_result.ambiguities
            session.update_state(SessionState.CLARIFYING)
            self._save_session(session)
            
            return {
                "status": "needs_clarification",
                "state": session.current_state.value,
                "message": "I need some clarification about the foods you mentioned.",
                "clarifications_needed": session.pending_clarifications,
                "extracted_foods": [food.model_dump() for food in session.extracted_foods]
            }
        else:
            # All foods are clear, move to advising
            session.update_state(SessionState.ADVISING)
            self._save_session(session)
            
            return self._generate_advice(session)
    
    def _handle_clarifying_state(self, session: SessionData, user_message: str) -> Dict[str, Any]:
        """Handle clarification responses from user"""
        # Store the clarification response
        # This is simplified - in practice, you'd parse which clarification this responds to
        session.clarification_responses["latest"] = user_message
        
        # For now, assume clarifications are resolved and move to advising
        session.update_state(SessionState.ADVISING)
        self._save_session(session)
        
        return self._generate_advice(session)
    
    def _handle_advising_state(self, session: SessionData, user_message: str) -> Dict[str, Any]:
        """Handle the advising state - generate nutritional advice"""
        return self._generate_advice(session)
    
    def _handle_advised_state(self, session: SessionData, user_message: str) -> Dict[str, Any]:
        """Handle post-advice state - user might ask follow-up questions or start new tracking"""
        # Check if this is a new food tracking request or follow-up question
        if self._is_new_food_tracking(user_message):
            # Reset session for new tracking
            session.update_state(SessionState.INITIAL)
            session.extracted_foods = None
            session.pending_clarifications = []
            session.clarification_responses = {}
            session.advisor_recommendations = None
            
            return self._handle_initial_state(session, user_message)
        else:
            # Handle as follow-up question
            return {
                "status": "follow_up",
                "state": session.current_state.value,
                "message": "I can help with follow-up questions or track new foods. What would you like to do?",
                "previous_advice": session.advisor_recommendations
            }
    
    def _generate_advice(self, session: SessionData) -> Dict[str, Any]:
        """Generate nutritional advice based on extracted foods"""
        # This is a placeholder - integrate with your nutrition advisor agent
        advice = f"Based on your food intake of {len(session.extracted_foods)} items, here's my nutritional advice..."
        
        session.advisor_recommendations = advice
        session.update_state(SessionState.ADVISED)
        self._save_session(session)
        
        return {
            "status": "advice_provided",
            "state": session.current_state.value,
            "advice": advice,
            "foods_analyzed": [food.model_dump() for food in session.extracted_foods]
        }
    
    def _is_new_food_tracking(self, message: str) -> bool:
        """Determine if message is a new food tracking request"""
        # Simple heuristic - check for food-related keywords
        food_keywords = ["makan", "sarapan", "lunch", "dinner", "snack", "ate", "eating", "food"]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in food_keywords)
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state information"""
        session = self.get_or_create_session(session_id)
        return {
            "session_id": session.session_id,
            "current_state": session.current_state.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "has_extracted_foods": bool(session.extracted_foods),
            "pending_clarifications": session.pending_clarifications,
            "has_advice": bool(session.advisor_recommendations)
        }
    
    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset session to initial state"""
        session = self.get_or_create_session(session_id)
        session.current_state = SessionState.INITIAL
        session.user_message = None
        session.extracted_foods = None
        session.pending_clarifications = []
        session.clarification_responses = {}
        session.advisor_recommendations = None
        session.updated_at = datetime.now()
        
        self._save_session(session)
        
        return {
            "status": "session_reset",
            "state": session.current_state.value,
            "message": "Session has been reset. Ready for new food tracking."
        }


# Example usage and testing
if __name__ == "__main__":
    workflow = MainWorkflow()
    
    # Test the workflow
    session_id = "test_session_1"
    
    # Initial food tracking
    result1 = workflow.process_user_input(session_id, "Sarapan: nasi goreng, Lunch: soto ayam")
    print("Initial processing:", result1)
    
    # Check session state
    state = workflow.get_session_state(session_id)
    print("Session state:", state)