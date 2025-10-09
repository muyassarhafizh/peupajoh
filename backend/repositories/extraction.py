from repositories.models.extraction import FoodExtractionResult
from agents.food_extractor import FoodExtractorAgent

def extract_foods_structured(message: str) -> FoodExtractionResult:
    """Extract foods with native structured output"""
    agent = FoodExtractorAgent
    run_output = agent.run(message, output_schema=FoodExtractionResult)
    return run_output.content


if __name__ == "__main__":
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
