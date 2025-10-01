import uuid
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from typing import Optional, List, Any, Dict
import asyncio
from dotenv import load_dotenv

# Import your models
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.models import FoodExtractionResult, ClarificationRequest, ClarificationType
from search.search import search_food_db
from search.search import DB_PATH as FOOD_DB_PATH
import aiosqlite

load_dotenv()


class AgentConfig:
    """Simple configuration class for your agents"""

    def __init__(
        self,
        name: str,
        model_id: str = "gpt-5-nano",
        system_prompt: Optional[str] = None,
        db_file: str = "agno.db",
        temperature: float = 0.7,
        debug_mode: bool = False,
        tools: Optional[List] = None,
        output_schema: Optional[Any] = None,
    ):
        self.name = name
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.db_file = db_file
        self.temperature = temperature
        self.debug_mode = debug_mode
        self.tools = tools or []
        self.output_schema = output_schema


def create_agent(config: AgentConfig) -> Agent:
    """Factory function to create configured agents"""
    agent = Agent(
        name=config.name,
        model=OpenAIChat(id=config.model_id),
        db=SqliteDb(db_file=config.db_file),
        debug_mode=config.debug_mode,
        add_history_to_context=True,
        markdown=True,
        tools=config.tools,
        output_schema=config.output_schema,  # Native structured output!
    )

    # Set system prompt if provided
    if config.system_prompt:
        agent.description = config.system_prompt

    return agent


# Predefined agent configurations
AGENT_CONFIGS = {
    "food_extraction": AgentConfig(
        name="Food Extraction Agent",
        system_prompt="""You are a food extraction specialist for Indonesian cuisine.
        
        Extract food items, portions, and meal types from user messages.
        
        IMPORTANT MEAL TYPE MAPPING:
        - "sarapan" = breakfast
        - "lunch" or "makan siang" = lunch  
        - "malam" or "dinner" or "makan malam" = dinner
        - "snack" or "cemilan" = snack
        
        Rules:
        - Extract ALL food items mentioned
        - Map Indonesian food terms to English (bubur -> rice porridge, steak ayam -> chicken steak)
        - Assign the correct meal_type to EACH food item based on context
        - Set needs_clarification=true if portions are unclear or food items are ambiguous
        - confidence should reflect how certain you are about the extraction
        - Each food should have its own meal_type based on when it was consumed""",
        output_schema=FoodExtractionResult,  # Native structured output!
    ),
    "nutrition_calculator": AgentConfig(
        name="Nutrition Calculator",
        system_prompt="""You are a nutrition calculation expert.
        Calculate nutritional values for Indonesian foods.
        Be precise with portion sizes and nutritional data.""",
    ),
    "clarification": AgentConfig(
        name="Clarification Agent",
        system_prompt="""You are a clarification specialist.
        Ask clear, specific questions when food descriptions are ambiguous.
        Keep questions concise and user-friendly.""",
        output_schema=ClarificationRequest,
    ),
}


def get_agent(agent_type: str) -> Agent:
    """Get a pre-configured agent by type"""
    if agent_type not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return create_agent(AGENT_CONFIGS[agent_type])


def extract_foods_structured(message: str) -> FoodExtractionResult:
    """Extract foods with native structured output"""
    agent = get_agent("food_extraction")
    # With output_schema, the agent returns a RunOutput object with the structured content
    run_output = agent.run(message)
    # The actual structured data is in the content attribute
    return run_output.content


# Helpers to support both dict and Pydantic model items
def _get_field(item: Any, field: str) -> Any:
    if isinstance(item, dict):
        return item.get(field)
    # pydantic v2 models expose attributes directly
    return getattr(item, field, None)


def _to_raw_item(item: Any) -> Dict[str, Any]:
    # Prefer pydantic v2 model_dump if available
    if hasattr(item, "model_dump") and callable(getattr(item, "model_dump")):
        try:
            return item.model_dump()
        except Exception:
            pass
    if isinstance(item, dict):
        return item
    # Fallback minimal projection
    return {
        "name": _get_field(item, "name"),
        "local_name": _get_field(item, "local_name"),
        "portion_description": _get_field(item, "portion_description"),
        "quantity": _get_field(item, "quantity"),
        "meal_type": str(_get_field(item, "meal_type")) if _get_field(item, "meal_type") is not None else None,
    }


async def _fetch_nutrition_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Fetch a single food item row by exact name from SQLite (async)."""
    async with aiosqlite.connect(FOOD_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, name, calories, proteins, fat, carbohydrate, image
            FROM food_items
            WHERE name = ?
            """,
            (name,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def main_workflow_async(
    food_items: List[Dict[str, Any]], request_id: str, threshold: float = 0.80
) -> Dict[str, Any]:
    """
    - For each food item, search in local DB using fuzzy search (by local_name if present, else name).
    - Attach request_id to each result.
    - If not found, add a clarification request for that specific item.
    Returns a dict with:
      {
        'request_id': str,
        'matched': [ { query, match_name, score, nutrition } ],
        'clarifications': [ ClarificationRequest.model_dump() ]
    """
    matched: List[Dict[str, Any]] = []
    clarifications: List[ClarificationRequest] = []

    for item in food_items:
        food_request_id = uuid.uuid4().hex
        query = (_get_field(item, "local_name") or _get_field(item, "name") or "").strip()
        if not query:
            clarifications.append(
                ClarificationRequest(
                    type=ClarificationType.FOOD_TYPE,
                    question="Saya tidak bisa mengenali makanan. Tolong sebutkan nama makanan secara jelas?",
                    options=None,
                    context={"request_id": food_request_id, "item": _to_raw_item(item)},
                    is_required=True,
                )
            )
            continue

        results = await search_food_db(query, threshold=threshold)
        if results:
            top_name, score, _ = results[0]
            nutrition = await _fetch_nutrition_by_name(top_name)
            matched.append(
                {
                    "request_id": food_request_id,
                    "query": query,
                    "match_name": top_name,
                    "score": float(score) / 100.0,
                    "nutrition": nutrition,
                    "raw_item": _to_raw_item(item),
                }
            )
        else:
            clarifications.append(
                ClarificationRequest(
                    type=ClarificationType.FOOD_TYPE,
                    question=f"Maksud Anda '{query}' itu makanan apa? Bisa berikan nama lain atau deskripsi singkat?",
                    options=None,
                    context={"request_id": food_request_id, "item": _to_raw_item(item)},
                    is_required=True,
                )
            )

    return {
        "request_id": request_id,
        "matched": matched,
        "clarifications": [c.model_dump() for c in clarifications],
    }


def main_workflow(
    food_items: List[Dict[str, Any]], request_id: str, threshold: float = 0.80
) -> Dict[str, Any]:
    """Synchronous wrapper for environments that prefer sync calls."""
    return asyncio.run(main_workflow_async(food_items, request_id, threshold))


if __name__ == "__main__":
    request_id = uuid.uuid4().hex
    print(f"Request ID: {request_id}")

    message = """Kemarin saya makan Sarapan: bubur  1 porsi
Lunch : sushi tei
Malam: Steak ayam
Snack: roti kukus"""

    # Use native structured output - much cleaner!
    result = extract_foods_structured(message)

    print("=== NATIVE STRUCTURED OUTPUT ===")
    print(f"Type: {type(result)}")
    # print(f"Needs Clarification: {result.needs_clarification}")
    print(f"Confidence: {result.confidence}")
    print(f"Foods Found: {len(result.foods)}")

    print("\n=== EXTRACTED FOODS WITH MEAL TYPES ===")
    for i, food in enumerate(result.foods, 1):
        print(f"  {i}. {food.name} ({food.local_name if food.local_name else 'N/A'})")
        print(f"     Meal Type: {food.meal_type}")
        print(
            f"     Portion: {food.portion_description if food.portion_description else 'N/A'}"
        )
        print(f"     Quantity: {food.quantity}")
        print()

    if result.ambiguities:
        print(f"Ambiguities: {result.ambiguities}")

    print("\n=== PYDANTIC MODEL JSON ===")
    print(result.model_dump_json(indent=2))

    # Run main workflow
    workflow_result = main_workflow(result.foods, request_id)
    print("\n=== WORKFLOW RESULT ===")
    print(workflow_result)
