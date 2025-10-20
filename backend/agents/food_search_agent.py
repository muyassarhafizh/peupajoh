import asyncio

from .base import AgentConfig, BaseAgent
from .tools.search_food_in_db import search_food_in_db
from .tools.search_fatsecret_detail import scrape_food_nutrition
from models.extraction import FoodNames, FoodSearchPayload
from config.variable import config as config_variable


def create_food_search_agent() -> BaseAgent:
    """Create an agent configured to search the food database."""

    system_prompt = """You are Food Search Agent.

=== IDENTITY ===
When introducing yourself, keep it brief and natural. You're Food Search Agent who helps people find information about food items

=== TOOLS AVAILABLE ===
You have access to these tools to query the resume database:
- search_food_in_db(query: str, threshold: float = 0.85, limit: int | None = None) -> list[DatabaseFoodMatch]: 
    Use this to search for food items in the database. 
    - 'query' is the food name or keyword to search for.
    - 'threshold' is the minimum similarity score (0.0 - 1.0) to consider a match.
    - 'limit' is the maximum number of results to return (optional).
    Returns a list of matching food items with their similarity scores.
- scrape_food_nutrition(query: str) -> dict:
    Use this to get detailed nutritional information about a specific food item from FatSecret.
    - 'query' is the name of the food item to look up.
    - 'max_results' is the maximum number of results to return (optional).
    Returns a dictionary with nutritional details like calories, protein, fat, carbs, etc.

=== RESPONSE PROTOCOL ===
1. ALWAYS use tools to retrieve data before answering
2. Search the food in database first, then use scrape_food_nutrition to get more details if needed, 
Feel free to breakdown the food name into smaller parts to search more effectively.
3. ONLY state facts that come directly from tool results
4. Return the per 100g nutrition of each food(divide by serving size if needed)

"""

    config = AgentConfig(
        name="food_search_agent",
        model_id=config_variable.model_id,
        system_prompt=system_prompt,
        temperature=0.3,  # Lower temperature for more factual responses
        framework=config_variable.framework,
        llm_provider=config_variable.llm_provider,
        tools=[
            search_food_in_db,
            scrape_food_nutrition,
        ],  # Add the database search tools
        debug_mode=True,  # Enable debug mode for detailed logs
    )

    return BaseAgent(config)


###EXAMPLE USAGE
async def _async_main() -> None:
    agent = create_food_search_agent()
    # Example input to test the agent
    queries = FoodSearchPayload(
        foods=[
            FoodNames(
                normalized_id_name="nasi goreng",
                normalized_eng_name="fried rice",
                original_text="nasi goreng",
            ),
            FoodNames(
                normalized_id_name="steak ayam",
                normalized_eng_name="chicken steak",
                original_text="steak ayam",
            ),
            FoodNames(
                normalized_id_name="nasi uduk",
                normalized_eng_name="coconut rice",
                original_text="nasi uduk",
            ),
        ],
        notes=[],
    )
    result = await agent.arun(queries, input_schema=FoodSearchPayload)
    print("Agent Response:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(_async_main())
