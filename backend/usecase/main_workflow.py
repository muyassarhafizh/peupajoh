from typing import Optional, Dict, Any, AsyncGenerator
from dotenv import load_dotenv
from models.extraction import FoodSearchPayload, FoodNames, FoodSearchResult
from models.session import SessionState
from models.food import FoodItem
from repositories.session import SessionRepository
from repositories.extraction import extract_foods_structured
from repositories.analyze_nutrition import DailyMealData
from agents.food_search_agent import create_food_search_agent
from agents.nutrition_advisor import NutritionAdvisorAgent
from config.sqlite import SQLiteDB
from agno.agent import RunEvent
import json
import asyncio

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

    async def process_user_input_stream(
        self, user_message: str, session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user input and stream the final LLM response.

        Only the nutrition advisor agent streams tokens to the user.
        Intermediate agents process internally without streaming.

        Yields SSE events:
        - token: streaming LLM response tokens (from nutrition advisor only)
        - done: final complete response with session state
        - error: if something goes wrong
        """
        try:
            session_state = self._get_session_state(session_id)
            current_state = session_state["current_state"]

            if current_state == SessionState.INITIAL.value:
                async for event in self._route_to_extractor(
                    session_id, session_state, user_message
                ):
                    yield event
            elif current_state == SessionState.CLARIFYING.value:
                async for event in self._handle_clarification(
                    session_id, session_state, user_message
                ):
                    yield event
            elif current_state == SessionState.ADVISING.value:
                async for event in self._route_to_search_agent(
                    session_id, session_state
                ):
                    yield event
            elif current_state == SessionState.ADVISED.value:
                async for event in self._handle_post_advice(
                    session_id, session_state, user_message
                ):
                    yield event
            else:
                yield {
                    "event": "error",
                    "data": {
                        "error": "unknown_state",
                        "detail": f"Unknown session state: {current_state}",
                    },
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": "workflow_error", "detail": str(e)},
            }

    async def _route_to_extractor(
        self, session_id: str, session_state: Dict, user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Extract foods from user message (internal processing, no streaming)."""
        try:
            extraction_result = await extract_foods_structured(user_message)

            session_state["extracted_foods"] = [
                food.model_dump() for food in extraction_result.foods
            ]
            session_state["user_message"] = user_message

            # Check if clarification is needed
            needs_clarification = []
            for food in extraction_result.foods:
                if hasattr(food, "needs_clarification") and food.needs_clarification:
                    needs_clarification.append(
                        food.name if hasattr(food, "name") else str(food)
                    )

            if needs_clarification:
                # Transition to clarifying state
                session_state["pending_clarifications"] = needs_clarification
                session_state["current_state"] = SessionState.CLARIFYING.value
                self._save_session_state(session_id, session_state)

                yield {
                    "event": "done",
                    "data": {
                        "session_id": session_id,
                        "response": f"I found {len(extraction_result.foods)} food items, but need clarification on: {', '.join(needs_clarification)}",
                        "session_state": session_state["current_state"],
                        "data": {
                            "status": "needs_clarification",
                            "clarifications_needed": needs_clarification,
                            "extracted_foods": session_state["extracted_foods"],
                        },
                        "next_actions": ["provide_clarification"],
                    },
                }
            else:
                # Everything is clear, move to advising
                session_state["current_state"] = SessionState.ADVISING.value
                self._save_session_state(session_id, session_state)

                # Continue to search agent
                async for event in self._route_to_search_agent(
                    session_id, session_state
                ):
                    yield event

        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": "extraction_failed", "detail": str(e)},
            }

    async def _handle_clarification(
        self, session_id: str, session_state: Dict, user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle user clarification response."""
        session_state["clarification_responses"]["latest"] = user_message

        # Transition to advising state
        session_state["current_state"] = SessionState.ADVISING.value
        self._save_session_state(session_id, session_state)

        # Route to search agent
        async for event in self._route_to_search_agent_stream(
            session_id, session_state
        ):
            yield event

    async def _route_to_search_agent(
        self, session_id: str, session_state: Dict
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Search for food nutrition data (internal processing, no streaming)."""
        try:
            extracted_foods = session_state.get("extracted_foods", [])

            if not extracted_foods:
                yield {
                    "event": "error",
                    "data": {
                        "error": "no_foods",
                        "detail": "No foods found to analyze",
                    },
                }
                return

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

            # Create and call search agent (internal, no streaming)
            food_search_agent = create_food_search_agent()
            search_result = await food_search_agent.arun(
                search_payload,
                input_schema=FoodSearchPayload,
                output_schema=FoodSearchResult,
            )

            # Check if everything is completed or needs more clarification
            if self._is_search_complete(search_result):
                # Route to advisor agent - THIS IS WHERE STREAMING HAPPENS
                async for event in self._route_to_advisor_stream(
                    session_id, session_state, search_result
                ):
                    yield event
            else:
                # Need more clarification
                session_state["current_state"] = SessionState.CLARIFYING.value
                self._save_session_state(session_id, session_state)

                yield {
                    "event": "done",
                    "data": {
                        "session_id": session_id,
                        "response": "I need more details about some food items.",
                        "session_state": session_state["current_state"],
                        "data": {
                            "status": "needs_more_clarification",
                            "search_results": search_result.content,
                        },
                        "next_actions": ["provide_clarification"],
                    },
                }

        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": "search_failed", "detail": str(e)},
            }

    async def _route_to_advisor_stream(
        self, session_id: str, session_state: Dict, search_result
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate nutrition advice and stream the response to the user."""
        try:
            food_search_data: FoodSearchResult = (
                search_result.content
                if hasattr(search_result, "content")
                else search_result
            )

            meal_data = self._convert_to_daily_meal_data(food_search_data)
            meal_dict = meal_data.model_dump(exclude_none=False)
            prompt = json.dumps(meal_dict, indent=2)

            stream_iterator = await asyncio.to_thread(
                NutritionAdvisorAgent.run_stream, prompt
            )

            full_response_parts = []
            final_analysis = None

            for chunk in stream_iterator:
                if chunk.event == RunEvent.run_content:
                    content = chunk.content
                    if content:
                        full_response_parts.append(content)
                        yield {"event": "token", "data": content}

                elif chunk.event == RunEvent.run_completed:
                    if hasattr(chunk, "content") and chunk.content:
                        final_analysis = chunk.content

            if final_analysis:
                advice_text = self._format_nutrition_analysis(final_analysis)
            else:
                advice_text = "".join(full_response_parts)

            session_state["advisor_recommendations"] = advice_text
            session_state["current_state"] = SessionState.ADVISED.value
            self._save_session_state(session_id, session_state)

            yield {
                "event": "done",
                "data": {
                    "session_id": session_id,
                    "response": advice_text,
                    "session_state": session_state["current_state"],
                    "data": {
                        "status": "advice_provided",
                        "foods_analyzed": session_state["extracted_foods"],
                        "nutrition_summary": final_analysis.summary.model_dump()
                        if final_analysis and hasattr(final_analysis, "summary")
                        else {},
                    },
                    "next_actions": ["view_summary", "add_more_food", "reset"],
                },
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": "analysis_failed", "detail": str(e)},
            }

    async def _handle_post_advice(
        self, session_id: str, session_state: Dict, user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle follow-up questions or new food tracking after advice is provided."""
        if self._is_new_food_tracking(user_message):
            # Reset session for new tracking
            session_state["current_state"] = SessionState.INITIAL.value
            session_state["extracted_foods"] = []
            session_state["pending_clarifications"] = []
            session_state["clarification_responses"] = {}
            session_state["advisor_recommendations"] = None

            async for event in self._route_to_extractor_stream(
                session_id, session_state, user_message
            ):
                yield event
        else:
            # Handle as follow-up question
            yield {
                "event": "done",
                "data": {
                    "session_id": session_id,
                    "response": "I can help with follow-up questions or track new foods. What would you like to do?",
                    "session_state": session_state["current_state"],
                    "data": {
                        "status": "follow_up",
                        "previous_advice": session_state["advisor_recommendations"],
                    },
                    "next_actions": ["add_more_food", "ask_question", "reset"],
                },
            }

    def _format_nutrition_analysis(self, analysis) -> str:
        """Format DailyNutritionAnalysis into readable text."""
        try:
            parts = []

            if hasattr(analysis, "advice") and hasattr(
                analysis.advice, "overall_assessment"
            ):
                parts.append(
                    f"**Overall Assessment:**\n{analysis.advice.overall_assessment}\n"
                )

            if hasattr(analysis, "summary"):
                parts.append(
                    f"**Daily Totals:**\n"
                    f"- Calories: {analysis.summary.total_calories:.0f} kcal\n"
                    f"- Protein: {analysis.summary.total_protein:.1f}g\n"
                    f"- Carbohydrates: {analysis.summary.total_carbohydrates:.1f}g\n"
                    f"- Fat: {analysis.summary.total_fat:.1f}g\n"
                    f"- Fiber: {analysis.summary.total_fiber:.1f}g\n"
                )

            if (
                hasattr(analysis, "advice")
                and hasattr(analysis.advice, "specific_recommendations")
                and analysis.advice.specific_recommendations
            ):
                parts.append("**Recommendations:**")
                for rec in analysis.advice.specific_recommendations:
                    parts.append(f"- {rec}")

            return "\n\n".join(parts) if parts else "Analysis completed."
        except Exception:
            return str(analysis)

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
