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
from models.models import FoodExtractionResult, BatchClarificationQuestions
from search.search import search_food_db
from search.search import DB_PATH as FOOD_DB_PATH
import aiosqlite

load_dotenv()


class AgentConfig:
    """Simple configuration class for your agents"""

    def __init__(
        self,
        name: str,
        model_id: str = "gpt-4o",
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
        system_prompt="""You are a friendly clarification specialist for Indonesian food tracking and don't be monotonous.

        You will receive a list of food items that user has already eaten where each has multiple possible matches (options) from the database.
        Your job is to narrow down by asking questions to user to get the correct food item match. 
        Feel free to narrow down the options to be empty.

        For each item:
        1. Select only multiple possible options that the user could reasonably mean based on:
            - The exact words/phrases they used
            - Common sense interpretation
        2. You can even add any other options that has more relationship with the food item given by the user
        3. Present the options clearly

        Guidelines:
        - Use friendly, conversational Indonesian, remember to not be monotonous
        - Keep questions short and clear
        - Be helpful and not robotic
        - Make a good bridging for each question based on the order.

        Return structured questions for ALL items that need clarification.""",
        output_schema=BatchClarificationQuestions,
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
