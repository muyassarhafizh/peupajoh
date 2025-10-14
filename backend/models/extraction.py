"""Schemas for structured output from the food extraction agent."""

from typing import List, Optional

from pydantic import BaseModel, Field

from .food import MealType


class FoodNames(BaseModel):
    """Food identification with multiple name formats."""

    normalized_eng_name: str = Field(
        ...,
        description="English-friendly name of the food",
    )
    normalized_id_name: Optional[str] = Field(
        None,
        description="Indonesian-friendly name for Indonesian databases",
    )
    original_text: Optional[str] = Field(
        None,
        description="Exact user wording if different from normalized names",
    )


class ExtractedFoodItem(FoodNames):
    """Food item with names, portions, and meal context."""

    meal_type: Optional[MealType] = Field(
        None,
        description="Meal context (breakfast, lunch, etc.)",
    )
    quantity: Optional[float] = Field(
        None,
        gt=0,
        description="Numeric quantity (e.g., 2 bowls)",
    )
    portion: Optional[str] = Field(
        None,
        description="Portion description ('1 porsi', 'half plate')",
    )
    portion_in_grams: Optional[float] = Field(
        None,
        gt=0,
        description="Estimated portion mass in grams",
    )

    @property
    def names_only(self) -> FoodNames:
        """Get just the name fields for search."""
        return FoodNames(
            normalized_eng_name=self.normalized_eng_name,
            normalized_id_name=self.normalized_id_name,
            original_text=self.original_text,
        )


class FoodSearchPayload(BaseModel):
    """Payload for the search agent."""

    foods: List[FoodNames] = Field(
        default_factory=list,
        description="Food items to search",
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Comments or uncertainties for search",
    )


class FoodExtractionPayload(BaseModel):
    """Container for extracted foods from the agent."""

    foods: List[ExtractedFoodItem] = Field(
        default_factory=list,
        description="Extracted foods ready for lookup",
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Comments for the next agent",
    )

    def to_search_payload(self) -> FoodSearchPayload:
        """Create search payload with only name fields."""
        return FoodSearchPayload(
            foods=[food.names_only for food in self.foods], notes=self.notes
        )
