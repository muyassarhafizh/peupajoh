from agents.nutrition_advisor import NutritionAdvisorAgent
from models.food import FoodItem
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import json


class DailyMealData(BaseModel):
    """
    Firm input schema for nutrition advisor agent.

    Contains lists of FoodItem organized by meal type.
    All FoodItems must have NutritionInfo (from database).

    Expected meal types: Breakfast, Lunch, Dinner, Snack
    """

    Breakfast: List[FoodItem] = Field(
        default_factory=list, description="Foods consumed at breakfast"
    )
    Lunch: List[FoodItem] = Field(
        default_factory=list, description="Foods consumed at lunch"
    )
    Dinner: List[FoodItem] = Field(
        default_factory=list, description="Foods consumed at dinner"
    )
    Snack: List[FoodItem] = Field(
        default_factory=list, description="Snacks consumed throughout the day"
    )

    class Config:
        # Allow additional meal types if needed (e.g., "Brunch", "Supper")
        extra = "allow"


class NutritionSummary(BaseModel):
    """Daily nutrition summary calculated by the AI"""

    total_calories: float = Field(description="Total calories for the day")
    total_protein: float = Field(description="Total protein in grams")
    total_carbohydrates: float = Field(description="Total carbohydrates in grams")
    total_fat: float = Field(description="Total fat in grams")
    total_fiber: float = Field(description="Total fiber in grams")
    total_sugar: float = Field(description="Total sugar in grams")
    total_sodium: float = Field(description="Total sodium in mg")
    meals_breakdown: Dict[str, Dict[str, float]] = Field(
        description="Nutrition breakdown by meal type (Breakfast, Lunch, Dinner, Snack)"
    )
    portion_assumptions: List[str] = Field(
        description="List of assumptions made about portion sizes"
    )


class NutritionAdvice(BaseModel):
    """Personalized nutrition advice and recommendations"""

    overall_assessment: str = Field(
        description="Overall assessment of the daily nutrition intake"
    )
    strengths: List[str] = Field(description="Positive aspects of the diet")
    areas_for_improvement: List[str] = Field(description="Areas that need improvement")
    specific_recommendations: List[str] = Field(
        description="Specific actionable recommendations"
    )
    macro_balance_score: int = Field(
        description="Score from 1-10 rating the macronutrient balance", ge=1, le=10
    )
    meal_distribution_score: int = Field(
        description="Score from 1-10 rating how well meals are distributed", ge=1, le=10
    )


class DailyNutritionAnalysis(BaseModel):
    """Complete daily nutrition analysis with advice"""

    summary: NutritionSummary
    advice: NutritionAdvice


def analyze_daily_nutrition(
    meal_data: Dict[str, List[Dict[str, Any]]] | DailyMealData,
) -> DailyNutritionAnalysis:
    """
    Main function to analyze daily nutrition and get AI-powered advice.

    Validates input against DailyMealData schema (ensures NutritionInfo from database),
    then passes to AI agent for comprehensive analysis.

    Args:
        meal_data: Dictionary with meal types as keys and list of food items as values,
                   or a DailyMealData Pydantic model. Each food item must have:
                   - nutrition_per_100g: NutritionInfo object (from database)
                   - standard_portions: dict/None (flexible)
                   - category: string (flexible)

    Returns:
        DailyNutritionAnalysis: Contains both nutrition summary (calculations)
                                and personalized advice (recommendations)

    Raises:
        ValidationError: If input doesn't match DailyMealData schema
                         (e.g., nutrition_per_100g is dict instead of NutritionInfo)

    Example:
        >>> from mock_meal_data import mock_meal_data
        >>> analysis = analyze_daily_nutrition(mock_meal_data)
        >>> print(f"Total calories: {analysis.summary.total_calories}")
        >>> print(f"Macro score: {analysis.advice.macro_balance_score}/10")
        >>>
        >>> # Access meal breakdown
        >>> for meal, nutrients in analysis.summary.meals_breakdown.items():
        ...     print(f"{meal}: {nutrients['calories']} kcal")
    """
    # Validate input against firm schema
    if isinstance(meal_data, dict):
        validated_data = DailyMealData(**meal_data)
    else:
        validated_data = meal_data

    # Create the advisor agent
    agent = NutritionAdvisorAgent

    # Convert to dict for JSON serialization
    meal_dict = validated_data.model_dump(exclude_none=False)

    # Simple prompt - all instructions are in system_prompt
    prompt = json.dumps(meal_dict, indent=2)

    # Get the complete analysis from AI
    run_output = agent.run(prompt)
    analysis: DailyNutritionAnalysis = run_output.content

    return analysis


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    from repositories.mock_data.mock_meal_data import (
        mock_meal_data,
        mock_meal_data_no_portions,
    )

    print("=" * 70)
    print("TEST 1: MEAL DATA WITH STANDARD PORTIONS")
    print("=" * 70)

    analysis = analyze_daily_nutrition(mock_meal_data)

    # Print summary
    print("\n📊 NUTRITION SUMMARY:")
    print("-" * 70)
    print(f"Total Calories: {analysis.summary.total_calories} kcal")
    print(f"Protein: {analysis.summary.total_protein}g")
    print(f"Carbohydrates: {analysis.summary.total_carbohydrates}g")
    print(f"Fat: {analysis.summary.total_fat}g")
    print(f"Fiber: {analysis.summary.total_fiber}g")
    print(f"Sugar: {analysis.summary.total_sugar}g")
    print(f"Sodium: {analysis.summary.total_sodium}mg")

    print("\n🍽️ MEALS BREAKDOWN:")
    print("-" * 70)
    for meal_type, nutrients in analysis.summary.meals_breakdown.items():
        print(f"\n{meal_type}: {nutrients['calories']:.1f} kcal")
        print(
            f"  P: {nutrients['protein']:.1f}g | C: {nutrients['carbohydrates']:.1f}g | F: {nutrients['fat']:.1f}g"
        )

    # Print portion assumptions
    if analysis.summary.portion_assumptions:
        print("\n📏 PORTION ASSUMPTIONS:")
        print("-" * 70)
        for assumption in analysis.summary.portion_assumptions:
            print(f"  • {assumption}")

    # Print advice
    print("\n" + "=" * 70)
    print("💡 NUTRITION ADVICE")
    print("=" * 70)
    print("\nOverall Assessment:")
    print(analysis.advice.overall_assessment)

    print("\n✅ Strengths:")
    for strength in analysis.advice.strengths:
        print(f"  • {strength}")

    print("\n⚠️ Areas for Improvement:")
    for area in analysis.advice.areas_for_improvement:
        print(f"  • {area}")

    print("\n🎯 Recommendations:")
    for rec in analysis.advice.specific_recommendations:
        print(f"  • {rec}")

    print("\n📈 Scores:")
    print(f"  Macro Balance: {analysis.advice.macro_balance_score}/10")
    print(f"  Meal Distribution: {analysis.advice.meal_distribution_score}/10")

    # Test 2: Data with missing portions
    print("\n\n" + "=" * 70)
    print("TEST 2: MEAL DATA WITH MISSING PORTIONS (AI ASSUMES)")
    print("=" * 70)

    analysis2 = analyze_daily_nutrition(mock_meal_data_no_portions)

    print("\n📊 NUTRITION SUMMARY:")
    print("-" * 70)
    print(f"Total Calories: {analysis2.summary.total_calories} kcal")
    print(f"Protein: {analysis2.summary.total_protein}g")
    print(f"Carbohydrates: {analysis2.summary.total_carbohydrates}g")
    print(f"Fat: {analysis2.summary.total_fat}g")

    if analysis2.summary.portion_assumptions:
        print("\n📏 PORTION ASSUMPTIONS (AI-GENERATED):")
        print("-" * 70)
        for assumption in analysis2.summary.portion_assumptions:
            print(f"  • {assumption}")

    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
