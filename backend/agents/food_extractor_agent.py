from models.extraction import FoodExtractionPayload

from .base import AgentConfig, BaseAgent
from config.variable import config as config_variable


def create_food_extractor_agent() -> BaseAgent:
    """Create an agent configured to extract food items from user messages."""

    system_prompt = """You are a food extraction specialist for Indonesian cuisine.
        
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
    - Each food should have its own meal_type based on when it was consumed
    - Infer portion_in_grams for each food using typical serving sizes when grams are not given; leave empty only if no reasonable guess exists"""

    config = AgentConfig(
        name="Food Extraction Agent",
        system_prompt=system_prompt,
        model_id=config_variable.model_id,
        temperature=0.3,
        debug_mode=True,
    )
    return BaseAgent(config)


async def extract_foods(message: str) -> FoodExtractionPayload:
    """Run the extractor with structured output for downstream use."""

    agent = create_food_extractor_agent()
    result = await agent.arun(message, output_schema=FoodExtractionPayload)
    return result.content


if __name__ == "__main__":
    import asyncio

    async def _async_main() -> None:
        # Example input to test the agent
        user_input = (
            "Kemarin pukul 06:30 saya sarapan dua porsi bubur ayam tanpa sambal dan segelas jus jambu."
            " Saat makan siang di kantor pukul 12:15 saya makan nasi padang dengan rendang, sayur nangka, telur balado, dan es teh tawar."
            " Sekitar pukul 16:00 saya ngemil dua pastel isi sayur dan kopi hitam."
            " Setelah futsal malam pukul 20:30 saya makan sop buntut dengan nasi putih setengah porsi serta tempe goreng."
        )
        result = await extract_foods(user_input)
        print("Agent Response:")
        print(result.model_dump_json(indent=2))

    asyncio.run(_async_main())
