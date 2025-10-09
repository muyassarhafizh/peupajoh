from typing import Optional
from pydantic import BaseModel, Field


class NutritionInfo(BaseModel):
    """
    Nutritional information per 100g or per serving.
    Used throughout the system for nutrition data representation.
    """

    calories: float = Field(..., ge=0, description="Calories in kcal")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbohydrates: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    fiber: Optional[float] = Field(None, ge=0, description="Fiber in grams")
    sugar: Optional[float] = Field(None, ge=0, description="Sugar in grams")
    sodium: Optional[float] = Field(None, ge=0, description="Sodium in mg")
