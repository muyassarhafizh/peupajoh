import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.models import BatchClarificationQuestions
from agents import get_agent


def generate_clarification_questions(
    clarification_items: List[Dict[str, Any]], session_id: str = None
) -> BatchClarificationQuestions:
    """
    Generate user-friendly clarification questions for items with multiple matches.

    This function takes a list of food items that have multiple possible matches
    and uses an AI agent to generate natural Indonesian questions to ask the user.

    Args:
        clarification_items: List of items needing clarification. Each item should have:
            - request_id: Unique identifier for the item
            - query: Original food query from user
            - options: List of possible matches (e.g., ["bubur (score: 100)", ...])
            - meal_type: breakfast, lunch, dinner, or snack
            - quantity: Number of portions
            - portion_description: Optional description (e.g., "1 porsi jumbo")
        session_id: Optional session ID for conversation tracking in agno.db

    Returns:
        BatchClarificationQuestions with:
            - questions: List of UserClarificationQuestion objects
            - message: Optional introductory message

    Example:
        >>> items = [{
        ...     'request_id': 'abc123',
        ...     'query': 'bubur',
        ...     'options': ['bubur (score: 100)', 'bubur sagu (score: 100)'],
        ...     'meal_type': 'breakfast',
        ...     'quantity': 1.0,
        ...     'portion_description': '1 porsi'
        ... }]
        >>> result = generate_clarification_questions(items, session_id='session123')
        >>> print(result.questions[0].question)
        'Untuk sarapan bubur tadi, yang mana nih?'
    """
    agent = get_agent("clarification")

    # Format the input message for the agent
    message = _format_clarification_request(clarification_items)

    # Run the agent with structured output
    if session_id:
        run_output = agent.run(message, session_id=session_id)
    else:
        run_output = agent.run(message)

    # The agent returns BatchClarificationQuestions directly
    return run_output.content


def _format_clarification_request(clarification_items: List[Dict[str, Any]]) -> str:
    """
    Format clarification items into a clear request for the agent.

    Args:
        clarification_items: List of items needing clarification

    Returns:
        Formatted message string
    """
    message = "Generate friendly clarification questions in Indonesian for these food items:\n\n"

    for idx, item in enumerate(clarification_items, 1):
        message += f"{idx}. Query: '{item['query']}'\n"
        message += f"   Meal Type: {item['meal_type']}\n"
        message += f"   Quantity: {item['quantity']}"

        if item.get("portion_description"):
            message += f" ({item['portion_description']})"

        message += f"\n   Options:\n"
        for opt in item["options"]:
            # Clean up the option to just show the food name
            food_name = opt.split(" (score:")[0] if " (score:" in opt else opt
            message += f"     - {food_name}\n"

        message += f"   Request ID: {item['request_id']}\n\n"

    return message


def extract_food_name_from_option(option: str) -> str:
    """
    Extract clean food name from option string.

    Converts "bubur (score: 100)" -> "bubur"

    Args:
        option: Option string with score

    Returns:
        Clean food name
    """
    if " (score:" in option:
        return option.split(" (score:")[0].strip()
    return option.strip()


if __name__ == "__main__":
    # Example usage
    import uuid

    session_id = uuid.uuid4().hex
    print(f"Session ID: {session_id}\n")

    # Sample clarification items (from main_workflow.py)
    clarification_items = [
        {
            "request_id": uuid.uuid4().hex,
            "query": "bubur",
            "options": [
                "bubur (score: 100)",
                "bubur sagu (score: 100)",
                "bubur tinotuan (manado) (score: 100)",
            ],
            "meal_type": "breakfast",
            "quantity": 1.0,
            "portion_description": "1 porsi",
        },
        {
            "request_id": uuid.uuid4().hex,
            "query": "mie ayam yamin",
            "options": ["ayam (score: 100)", "mie ayam (score: 100)"],
            "meal_type": "snack",
            "quantity": 1.0,
            "portion_description": "1 porsi jumbo",
        },
    ]

    print("=== GENERATING CLARIFICATION QUESTIONS ===")
    for idx, item in enumerate(clarification_items, 1):
        print(f"{idx}. {item['query']} ({item['meal_type']})")
        print(f"   {len(item['options'])} possible matches")

    print("\n=== CLARIFICATION QUESTIONS FOR USER ===")
    result = generate_clarification_questions(
        clarification_items, session_id=session_id
    )

    if result.message:
        print(f"Intro: {result.message}\n")

    for idx, question in enumerate(result.questions, 1):
        print(f"{idx}. {question.question}")
        print(f"   Options:")
        for opt_idx, opt in enumerate(question.options, 1):
            print(f"     {opt_idx}. {opt}")
        print(f"   (Request ID: {question.request_id})")
        print()
