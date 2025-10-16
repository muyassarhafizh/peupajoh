from typing import Optional, Dict, Any
from models.extraction import FoodSearchPayload, FoodNames
from models.session import SessionState
from repositories.session import SessionRepository
from repositories.extraction import extract_foods_structured
from repositories.analyze_nutrition import analyze_daily_nutrition
from config.sqlite import SQLiteDB


class MainWorkflow:
    """Session-based Router/Dispatcher for Multi-Agent Food Tracking Workflow"""

    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    def _get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get or create session state from database"""
        # Try to get existing session
        result = self.session_repo.get_session_state(session_id)

        if result:
            import json

            return json.loads(result[0][0])
        else:
            # Create new session with initial state
            initial_state = {
                "current_state": SessionState.INITIAL.value,
                "extracted_foods": [],
                "pending_clarifications": [],
                "clarification_responses": {},
                "advisor_recommendations": None,
                "user_message": None,
            }
            self._save_session_state(session_id, initial_state)
            return initial_state

    def _save_session_state(self, session_id: str, state: Dict[str, Any]):
        """Save session state to database"""
        self.session_repo.save_session_state(session_id, state)

    async def process_user_input(
        self, user_message: str, session_id: str
    ) -> Dict[str, Any]:
        """Main entry point - routes to appropriate agent based on session state"""
        # Get current session state
        session_state = self._get_session_state(session_id)
        current_state = session_state["current_state"]

        # Route based on current state
        if current_state == SessionState.INITIAL.value:
            return await self._route_to_extractor(
                session_id, session_state, user_message
            )
        elif current_state == SessionState.CLARIFYING.value:
            return await self._handle_clarification(
                session_id, session_state, user_message
            )
        elif current_state == SessionState.ADVISING.value:
            return await self._route_to_search_agent(session_id, session_state)
        elif current_state == SessionState.ADVISED.value:
            return await self._handle_post_advice(
                session_id, session_state, user_message
            )
        else:
            return {"error": f"Unknown session state: {current_state}"}

    async def _route_to_extractor(
        self, session_id: str, session_state: Dict, user_message: str
    ) -> Dict[str, Any]:
        """Route to Food Extractor Agent"""
        try:
            # Call extractor agent
            extraction_result = await extract_foods_structured(user_message)

            # Update session state with results
            session_state["extracted_foods"] = [
                food.model_dump() for food in extraction_result.foods
            ]
            session_state["user_message"] = user_message

            # Check if clarification is needed
            needs_clarification = []
            for food in extraction_result.foods:
                if hasattr(food, "needs_clarification") and food.needs_clarification:
                    needs_clarification.append(food)

            if needs_clarification:
                # Transition to clarifying state
                session_state["pending_clarifications"] = needs_clarification
                session_state["current_state"] = SessionState.CLARIFYING.value
                self._save_session_state(session_id, session_state)

                return {
                    "status": "needs_clarification",
                    "state": session_state["current_state"],
                    "message": f"I found {len(extraction_result.foods)} food items, but need clarification on: {', '.join(needs_clarification)}",
                    "clarifications_needed": needs_clarification,
                    "extracted_foods": session_state["extracted_foods"],
                }
            else:
                # Everything is clear, move to advising
                session_state["current_state"] = SessionState.ADVISING.value
                self._save_session_state(session_id, session_state)

                # Automatically route to search agent
                return await self._route_to_advisor(session_id, session_state)

        except Exception as e:
            return {"error": f"Error in food extraction: {str(e)}"}

    async def _handle_clarification(
        self, session_id: str, session_state: Dict, user_message: str
    ) -> Dict[str, Any]:
        """Handle user clarification and route to next agent"""

        session_state["clarification_responses"]["latest"] = user_message

        # Transition to advising state
        session_state["current_state"] = SessionState.ADVISING.value
        self._save_session_state(session_id, session_state)

        # Route to search agent
        return await self._route_to_search_agent(session_id, session_state)

    async def _route_to_search_agent(
        self, session_id: str, session_state: Dict
    ) -> Dict[str, Any]:
        """Route to Food Search Agent for nutrition analysis"""
        try:
            extracted_foods = session_state.get("extracted_foods", [])

            if not extracted_foods:
                return {"error": "No foods found to analyze"}

            # Prepare search payload
            food_names = []
            for food_data in extracted_foods:
                food_names.append(
                    FoodNames(
                        normalized_id_name=food_data.get("normalized_id_name", ""),
                        normalized_eng_name=food_data.get("normalized_eng_name", ""),
                        original_text=food_data.get("original_text", ""),
                    )
                )

            search_payload = FoodSearchPayload(foods=food_names, notes=[])

            # Call search agent
            search_result = await self.food_search_agent.arun(
                search_payload, input_schema=FoodSearchPayload
            )

            # Check if everything is completed or needs more clarification
            if self._is_search_complete(search_result):
                # Route to advisor agent
                return await self._route_to_advisor(
                    session_id, session_state, search_result
                )
            else:
                # Need more clarification
                session_state["current_state"] = SessionState.CLARIFYING.value
                self._save_session_state(session_id, session_state)

                # Call food search agent to get more details
                # result = await self.food_search_agent.arun(
                #     search_payload, input_schema=FoodSearchPayload
                # )
                return {
                    "status": "needs_more_clarification",
                    "state": session_state["current_state"],
                    "message": "I need more details about some food items.",
                    "search_results": search_result.content,
                }

        except Exception as e:
            return {"error": f"Error in food search: {str(e)}"}

    async def _route_to_advisor(
        self, session_id: str, session_state: Dict, search_result
    ) -> Dict[str, Any]:
        """Route to Advisor Agent for final recommendations"""
        try:
            advice = await analyze_daily_nutrition(search_result)

            # Update session state
            session_state["advisor_recommendations"] = advice
            session_state["current_state"] = SessionState.ADVISED.value
            self._save_session_state(session_id, session_state)

            return {
                "status": "advice_provided",
                "state": session_state["current_state"],
                "advice": advice,
                "foods_analyzed": session_state["extracted_foods"],
            }

        except Exception as e:
            return {"error": f"Error generating advice: {str(e)}"}

    async def _handle_post_advice(
        self, session_id: str, session_state: Dict, user_message: str
    ) -> Dict[str, Any]:
        """Handle follow-up questions or new food tracking"""
        # Check if user wants to start new tracking
        if self._is_new_food_tracking(user_message):
            # Reset session for new tracking
            session_state["current_state"] = SessionState.INITIAL.value
            session_state["extracted_foods"] = []
            session_state["pending_clarifications"] = []
            session_state["clarification_responses"] = {}
            session_state["advisor_recommendations"] = None

            return await self._route_to_extractor(
                session_id, session_state, user_message
            )
        else:
            # Handle as follow-up question
            return {
                "status": "follow_up",
                "state": session_state["current_state"],
                "message": "I can help with follow-up questions or track new foods. What would you like to do?",
                "previous_advice": session_state["advisor_recommendations"],
            }

    def _is_search_complete(self, search_result) -> bool:
        """Determine if search results are complete enough for advice"""

        return len(search_result.content) > 50

    def _is_new_food_tracking(self, message: str) -> bool:
        """Determine if message is a new food tracking request"""
        food_keywords = [
            "makan",
            "sarapan",
            "lunch",
            "dinner",
            "snack",
            "ate",
            "eating",
            "food",
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in food_keywords)

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state information"""
        return self.session_repo.get_or_create_session(session_id)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata and summary"""
        return self.session_repo.get_session_info(session_id)

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset session to initial state"""
        self.session_repo.reset_session(session_id)

        return {
            "status": "session_reset",
            "message": "Session has been reset. Ready for new food tracking.",
        }

    def list_sessions(self) -> list[Dict[str, Any]]:
        """List all active sessions"""
        return self.session_repo.list_sessions()


DEFAULT_DB_RELATIVE = "agno.db"

# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def test_workflow():
        sqlite_db = SQLiteDB(DEFAULT_DB_RELATIVE)
        session_repo = SessionRepository(sqlite_db)
        workflow = MainWorkflow(session_repo)
        session_id = "test_session_1"

        print("=== Testing Clean Repository-Based Workflow ===")

        # Initial food tracking
        print("\n1. Initial food tracking:")
        result1 = await workflow.process_user_input(
            "Sarapan: nasi goreng, Lunch: soto ayam", session_id
        )
        print(result1)

        # Check session state
        print("\n2. Session state:")
        state = workflow.get_session_state(session_id)
        print(f"Current State: {state['current_state']}")
        print(f"Extracted Foods: {len(state['extracted_foods'])}")

        # Session info
        print("\n3. Session info:")
        info = workflow.get_session_info(session_id)
        print(info)

    asyncio.run(test_workflow())
