from typing import Optional, List
from pydantic import BaseModel, Field
from models.food import FoodCategory, MealType


class ExtractedFood(BaseModel):
    """Individual food item extracted from user message"""

    name: str = Field(..., description="Food name in English")
    local_name: Optional[str] = Field(
        None, description="Local/Indonesian name if mentioned"
    )
    food_category: Optional[FoodCategory] = Field(
        None, description="Category of the food"
    )
    portion_description: Optional[str] = Field(
        None, description="Portion as described by user"
    )
    quantity: float = Field(default=1.0, gt=0, description="Number of portions")
    meal_type: Optional[MealType] = Field(
        None, description="Which meal this food belongs to"
    )
    needs_clarification: bool = Field(
        default=False, description="Whether this item needs clarification"
    )


class FoodExtractionResult(BaseModel):
    """Result from food extraction agent"""

    foods: List[ExtractedFood]
    ambiguities: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
