from typing import Optional, List, Dict, Any, Tuple, Protocol
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

# class PortionSize(str, Enum):
#     SMALL = "small"
#     MEDIUM = "medium"
#     LARGE = "large"
#     CUSTOM = "custom"

class ConversationState(str, Enum):
    INITIAL = "initial"
    CLARIFYING_FOOD = "clarifying_food"
    CLARIFYING_PORTION = "clarifying_portion"
    CLARIFYING_VARIATION = "clarifying_variation"
    COMPLETE = "complete"
    FAILED = "failed"

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

class ClarificationType(str, Enum):
    FOOD_TYPE = "food_type"
    VARIATION = "variation"
    # PORTION_SIZE = "portion_size"
    QUANTITY = "quantity"
    PREPARATION = "preparation"



# ============================================================================
# DATA MODELS
# ============================================================================

class NutritionInfo(BaseModel):
    """Nutritional information per 100g or per serving"""
    calories: float = Field(..., ge=0, description="Calories in kcal")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbohydrates: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    fiber: Optional[float] = Field(None, ge=0, description="Fiber in grams")
    sugar: Optional[float] = Field(None, ge=0, description="Sugar in grams")
    sodium: Optional[float] = Field(None, ge=0, description="Sodium in mg")

class PortionDefinition(BaseModel):
    """Defines standard portion sizes for a food item"""
    small_grams: float = Field(..., gt=0, description="Small portion in grams")
    medium_grams: float = Field(..., gt=0, description="Medium portion in grams")
    large_grams: float = Field(..., gt=0, description="Large portion in grams")
    unit_description: str = Field(default="serving", description="e.g., 'bowl', 'plate', 'piece'")

class FoodItem(BaseModel):
    """Represents a food item in the database"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Food name in English")
    local_name: Optional[str] = Field(None, description="Local/Indonesian name")
    category: FoodCategory
    subcategory: Optional[str] = None
    nutrition_per_100g: NutritionInfo
    standard_portions: PortionDefinition
    variations: List[str] = Field(default_factory=list, description="Common variations")
    tags: List[str] = Field(default_factory=list, description="Search tags for matching")
    is_composite: bool = Field(default=False, description="Whether this is a composite dish")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings for similarity search")

class ConsumedFood(BaseModel):
    """Represents a food item consumed by the user"""
    food_item: FoodItem
    portion_size: PortionSize
    custom_grams: Optional[float] = Field(None, gt=0)
    quantity: float = Field(default=1.0, gt=0, description="Number of portions")
    confidence_score: float = Field(..., ge=0, le=1, description="Matching confidence")
    variation: Optional[str] = Field(None, description="Specific variation consumed")
    notes: Optional[str] = None

class Meal(BaseModel):
    """Represents a meal containing multiple food items"""
    id: str = Field(default_factory=lambda: f"meal_{datetime.now().timestamp()}")
    meal_type: MealType
    foods: List[ConsumedFood] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    raw_input: str = Field(..., description="Original user input")
    total_confidence: Optional[float] = Field(None, ge=0, le=1)

class DailySummary(BaseModel):
    """Daily nutrition summary"""
    date: datetime
    meals: List[Meal]
    total_nutrition: NutritionInfo
    macro_percentages: Dict[str, float]
    meal_count: Dict[MealType, int]

# ============================================================================
# INTERACTION MODELS
# ============================================================================

class ClarificationRequest(BaseModel):
    """Request for clarification from the user"""
    type: ClarificationType
    question: str
    options: Optional[List[str]] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    is_required: bool = Field(default=True)

class UserResponse(BaseModel):
    """User's response to clarification or initial message"""
    message: str
    session_id: str
    selected_option: Optional[str] = None
    is_clarification_response: bool = Field(default=False)

class ConversationContext(BaseModel):
    """Maintains conversation state and history"""
    session_id: str
    state: ConversationState = ConversationState.INITIAL
    original_message: str
    current_meal_type: Optional[MealType] = None
    identified_foods: List[Dict[str, Any]] = Field(default_factory=list)
    clarifications_made: List[ClarificationRequest] = Field(default_factory=list)
    pending_clarification: Optional[ClarificationRequest] = None
    max_clarifications: int = Field(default=3)
    confidence_threshold: float = Field(default=0.7)

# ============================================================================
# LLM MODELS
# ============================================================================

class LLMRequest(BaseModel):
    """Standard request format for LLM"""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0)
    response_format: Optional[str] = Field(None, description="'json' or 'text'")
    context: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    """Standard response format from LLM"""
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)

class FoodExtractionResult(BaseModel):
    """Result from food extraction agent"""
    foods: List[Dict[str, Any]]
    meal_type: Optional[MealType]
    needs_clarification: bool
    ambiguities: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)

class PortionEstimationResult(BaseModel):
    """Result from portion estimation agent"""
    portion_size: PortionSize
    estimated_grams: Optional[float] = None
    confidence: float = Field(..., ge=0, le=1)
    reasoning: Optional[str] = None

# ============================================================================
# DATABASE MODELS
# ============================================================================

class FoodMatchResult(BaseModel):
    """Result from food matching operation"""
    food_item: FoodItem
    match_score: float = Field(..., ge=0, le=1)
    match_type: str = Field(..., description="'exact', 'fuzzy', 'semantic'")
    matched_on: List[str] = Field(default_factory=list, description="Fields that matched")

class DatabaseQuery(BaseModel):
    """Query parameters for database search"""
    text: str
    category: Optional[FoodCategory] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=10, gt=0)
    threshold: float = Field(default=0.7, ge=0, le=1)
    use_embeddings: bool = Field(default=True)