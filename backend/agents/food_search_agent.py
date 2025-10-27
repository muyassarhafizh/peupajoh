import asyncio

from .base import AgentConfig, BaseAgent
from .tools.search_food_in_db import search_food_in_db
from .tools.search_fatsecret_detail import scrape_food_nutrition
from models.extraction import FoodNames, FoodSearchPayload
from config.settings import settings


def create_food_search_agent() -> BaseAgent:
    """Create an agent configured to search the food database."""

    system_prompt = """You are Food Search Agent that returns structured nutrition data.

=== IDENTITY ===
You search for food items and return structured nutritional information per 100g.

=== TOOLS AVAILABLE ===
- search_food_in_db(query: str, threshold: float = 0.85, limit: int | None = None) -> list[DatabaseFoodMatch]: 
    Search for food items in the database.
- scrape_food_nutrition(query: str) -> dict:
    Get detailed nutritional information from FatSecret.

=== RESPONSE PROTOCOL ===
1. For each food in the input:
   - Search the database using search_food_in_db
   - If found, extract nutrition data and convert to per 100g
   - If not found or need more details, use scrape_food_nutrition
   - Return structured FoodSearchResultItem with:
     * name (English)
     * local_name (Indonesian/local name)
     * meal_type (from input)
     * portion_grams (if specified)
     * nutrition_per_100g (NutritionInfo object with calories, protein, carbs, fat, fiber, sugar, sodium)
     * match_confidence (0.0-1.0)
     * notes (any important info)

2. If a food cannot be found, add it to unmatched_foods list

3. Always convert nutrition to per 100g basis:
   - If data is per serving, calculate: (value / serving_size_g) * 100
   - Example: 200 kcal per 150g serving = (200/150)*100 = 133.33 kcal per 100g

4. Return a FoodSearchResult object with:
   - foods: List of FoodSearchResultItem
   - unmatched_foods: List of food names that couldn't be matched
   - notes: Any general warnings or information

=== IMPORTANT ===
- ALWAYS return structured data, never return plain text
- Ensure all nutrition values are per 100g
- Include all available nutrition fields (calories, protein, carbs, fat, fiber, sugar, sodium)
"""

    config = AgentConfig(
        name="food_search_agent",
        model_id=settings.model_id,
        system_prompt=system_prompt,
        temperature=0.3,  # Lower temperature for more factual responses
        framework=settings.framework_enum,
        llm_provider=settings.llm_provider_enum,
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
