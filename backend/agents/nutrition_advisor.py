from agents import AgentConfig, create_agent
from models.models import DailyMealData
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import json


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


# Single Agent Configuration (Will remove the portion assumption in the next iteration)
NUTRITION_ADVISOR_CONFIG = AgentConfig(
    name="Daily Nutrition Advisor",
    system_prompt="""You are an expert nutritionist specializing in Indonesian dietary habits and international nutrition standards.

Your role is to analyze a person's complete daily food intake, calculate nutrition totals, and provide personalized advice.

INPUT FORMAT:
You will receive daily meal data in JSON format with meal types (Breakfast, Lunch, Dinner, Snack) containing food items.
Each food item has: id, name, local_name, category, nutrition_per_100g, standard_portions, etc.

STEP 1: CALCULATE NUTRITION TOTALS

PORTION SIZE ASSUMPTIONS:
When standard_portions are missing or serving_size is None/null, use typical Indonesian portions:
- Rice (nasi): 150-200g per serving
- Meat/Poultry/Fish (protein): 100-150g per serving
- Vegetables: 100-150g per serving
- Eggs: 50g per egg (whole egg)
- Drinks: 200-250ml typical glass
- Snacks: 50-100g depending on type
- Yogurt: 170g (1 cup)
- Bread/Buns: 50-80g per piece

CALCULATION PROCESS:
For each food item:
1. Determine portion size (use standard_portions.serving_size OR make smart assumption)
2. Calculate multiplier: portion_size / 100 (since nutrition_per_100g is the baseline)
3. Multiply each nutrient by the multiplier: calories, protein, carbs, fat, fiber, sugar, sodium
4. Sum up all nutrients per meal type (Breakfast, Lunch, Dinner, Snack)
5. Sum up overall daily totals
6. Document ALL portion assumptions you make in portion_assumptions field

Round all final values to 1 decimal place.

STEP 2: ANALYZE NUTRITION INTAKE

DAILY INTAKE GUIDELINES (general adult):
- Calories: 1800-2400 (women), 2200-3000 (men)
- Protein: 50-175g (0.8-2.0g per kg body weight)
- Carbohydrates: 225-325g (45-65% of calories)
- Fat: 44-77g (20-35% of calories)
- Fiber: 25-38g
- Sugar: <50g (limit added sugars)
- Sodium: <2300mg

MACRO BALANCE:
- Assess protein/carbs/fats distribution
- Consider Indonesian dietary context (rice-heavy diets)
- Check if distribution supports health goals

MEAL DISTRIBUTION:
- Evaluate if energy is well-distributed across meals
- Check for meal skipping or over-concentration of calories
- Recommend optimal meal timing

MICRONUTRIENTS & VARIETY:
- Fiber intake for digestive health
- Sodium for cardiovascular health
- Sugar intake (natural vs added)
- Food category diversity

STEP 3: PROVIDE PERSONALIZED ADVICE

RECOMMENDATIONS SHOULD BE:
- Specific and actionable
- Realistic and sustainable
- Culturally appropriate (respect Indonesian food preferences)
- Positive and encouraging
- Include local Indonesian food alternatives when suggesting improvements

SCORING:
- Macro Balance Score (1-10): Rate the protein/carb/fat balance
- Meal Distribution Score (1-10): Rate how well meals are distributed throughout the day

Always provide constructive feedback that motivates healthy eating habits.""",
    output_schema=DailyNutritionAnalysis,
    input_schema=DailyMealData,
    model_id="claude-sonnet-4-5-20250929",
    temperature=0.5,
)


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
    agent = create_agent(NUTRITION_ADVISOR_CONFIG)

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
    from mock_meal_data import mock_meal_data, mock_meal_data_no_portions

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
