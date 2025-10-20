from typing import Optional, Dict, Any
from dotenv import load_dotenv
from models.extraction import FoodSearchPayload, FoodNames, FoodSearchResult
from models.session import SessionState
from models.food import FoodItem
from repositories.session import SessionRepository
from repositories.extraction import extract_foods_structured
from repositories.analyze_nutrition import analyze_daily_nutrition, DailyMealData
from agents.food_search_agent import create_food_search_agent
from config.sqlite import SQLiteDB

# Load environment variables from .env file
load_dotenv()


class MainWorkflow:
    """Session-based Router/Dispatcher for Multi-Agent Food Tracking Workflow"""

    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    def _get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get or create session state from database"""
        # Use repository method which already handles parsing
        return self.session_repo.get_or_create_session(session_id)

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
                return await self._route_to_search_agent(session_id, session_state)

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
                        normalized_eng_name=food_data.get("name", ""),
                        normalized_id_name=food_data.get("local_name"),
                        original_text=food_data.get("local_name")
                        or food_data.get("name", ""),
                    )
                )

            search_payload = FoodSearchPayload(foods=food_names, notes=[])

            # Create and call search agent with structured output
            food_search_agent = create_food_search_agent()
            search_result = await food_search_agent.arun(
                search_payload,
                input_schema=FoodSearchPayload,
                output_schema=FoodSearchResult,
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
            # Extract structured data from RunOutput
            food_search_data: FoodSearchResult = (
                search_result.content
                if hasattr(search_result, "content")
                else search_result
            )

            # Convert FoodSearchResult to DailyMealData format
            meal_data = self._convert_to_daily_meal_data(food_search_data)

            # Call nutrition advisor with structured data
            advice = analyze_daily_nutrition(meal_data)

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

    def _convert_to_daily_meal_data(
        self, search_result: FoodSearchResult
    ) -> DailyMealData:
        """Convert FoodSearchResult to DailyMealData format for nutrition advisor."""
        meal_dict = {"Breakfast": [], "Lunch": [], "Dinner": [], "Snack": []}

        for food_item in search_result.foods:
            # Create FoodItem for the advisor
            food = FoodItem(
                id=f"{food_item.name.lower().replace(' ', '_')}",
                name=food_item.name,
                local_name=food_item.local_name,
                category="other",  # Can be enhanced later
                nutrition_per_100g=food_item.nutrition_per_100g,
                standard_portions={"serving_size": food_item.portion_grams}
                if food_item.portion_grams
                else None,
            )

            # Add to appropriate meal type
            if food_item.meal_type:
                meal_key = food_item.meal_type.value.capitalize()
                if meal_key in meal_dict:
                    meal_dict[meal_key].append(food)
                else:
                    meal_dict["Snack"].append(food)  # Default to snack if unknown
            else:
                meal_dict["Snack"].append(food)  # Default to snack if no meal type

        return DailyMealData(**meal_dict)

    def _is_search_complete(self, search_result) -> bool:
        """Determine if search results are complete enough for advice"""
        # Check if we have structured data
        if hasattr(search_result, "content"):
            search_data = search_result.content
            if isinstance(search_data, FoodSearchResult):
                # Complete if we have at least one food item
                return len(search_data.foods) > 0
        return False

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
        session_id = "test_session_3"

        print("=== Testing Clean Repository-Based Workflow ===")

        # Initial food tracking
        print("\n1. Initial food tracking:")
        result1 = await workflow.process_user_input(
            "Sarapan: nasi ikan, Lunch: mie goreng, Snack: sushi hiro", session_id
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
