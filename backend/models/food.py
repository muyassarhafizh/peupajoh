from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from .nutrition import NutritionInfo


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class FoodCategory(str, Enum):
    RICE_DISHES = "rice_dishes"
    NOODLE_DISHES = "noodle_dishes"
    PROTEIN = "protein"
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    BEVERAGE = "beverage"
    SNACK = "snack"
    DESSERT = "dessert"
    SOUP = "soup"
    TRADITIONAL = "traditional"
    OTHER = "other"


class PortionDefinition(BaseModel):
    """Defines standard portion sizes for a food item"""

    small_grams: float = Field(..., gt=0, description="Small portion in grams")
    medium_grams: float = Field(..., gt=0, description="Medium portion in grams")
    large_grams: float = Field(..., gt=0, description="Large portion in grams")
    unit_description: str = Field(
        default="serving", description="e.g., 'bowl', 'plate', 'piece'"
    )


class FoodItem(BaseModel):
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Food name in English")
    local_name: Optional[str] = Field(None, description="Local/Indonesian name")
    category: FoodCategory
    subcategory: Optional[str] = None
    nutrition_per_100g: NutritionInfo
    standard_portions: Optional[Union[PortionDefinition, Dict[str, Any]]] = Field(
        None,
        description="Standard portions - PortionDefinition (S/M/L), dict with serving_size, or None for AI to assume",
    )
    variations: List[str] = Field(default_factory=list, description="Common variations")
    tags: List[str] = Field(
        default_factory=list,
        description="Search tags for matching (e.g., 'breakfast', 'protein')",
    )
    is_composite: bool = Field(
        default=False,
        description="Whether this is a composite dish with multiple ingredients",
    )
    embeddings: Optional[Union[List[float], Any]] = Field(
        None, description="Vector embeddings for semantic similarity search"
    )
