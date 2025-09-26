
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
from ..models.models import *
class LLMProvider(Protocol):
    """Protocol for LLM providers - implement this for different LLMs"""
    
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate completion from LLM"""
        ...
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text (optional)"""
        ...

class FoodDatabase(ABC):
    """Abstract interface for food database"""
    
    @abstractmethod
    def get_food_by_id(self, food_id: str) -> Optional[FoodItem]:
        """Retrieve specific food item by ID"""
        pass
    
    @abstractmethod
    def search_foods(self, query: DatabaseQuery) -> List[FoodMatchResult]:
        """Search foods with advanced matching"""
        pass
    
    @abstractmethod
    def add_food(self, food: FoodItem) -> bool:
        """Add new food item to database"""
        pass
    
    @abstractmethod
    def update_food(self, food_id: str, food: FoodItem) -> bool:
        """Update existing food item"""
        pass
    
    @abstractmethod
    def get_foods_by_category(self, category: FoodCategory) -> List[FoodItem]:
        """Get all foods in a category"""
        pass

class FoodMatcher(ABC):
    """Abstract interface for food matching algorithms"""
    
    @abstractmethod
    def match(self, query: str, candidates: List[FoodItem]) -> List[FoodMatchResult]:
        """Match query against candidate foods"""
        pass
    
    @abstractmethod
    def calculate_similarity(self, query: str, food_item: FoodItem) -> float:
        """Calculate similarity score between query and food item"""
        pass

class Agent(ABC):
    """Base interface for LLM-powered agents"""
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return agent-specific output"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass

class FoodExtractionAgent(Agent):
    """Interface for food extraction from natural language"""
    
    @abstractmethod
    def extract_foods(self, message: str) -> FoodExtractionResult:
        """Extract food items from user message"""
        pass

class ClarificationAgent(Agent):
    """Interface for generating clarification questions"""
    
    @abstractmethod
    def generate_clarification(
        self, 
        context: ConversationContext
    ) -> ClarificationRequest:
        """Generate appropriate clarification based on context"""
        pass

class PortionEstimationAgent(Agent):
    """Interface for portion size estimation"""
    
    @abstractmethod
    def estimate_portion(
        self, 
        description: str, 
        food_item: FoodItem
    ) -> PortionEstimationResult:
        """Estimate portion size from description"""
        pass

class NutritionCalculator(ABC):
    """Interface for nutrition calculations"""
    
    @abstractmethod
    def calculate_meal_nutrition(self, meal: Meal) -> NutritionInfo:
        """Calculate total nutrition for a meal"""
        pass
    
    @abstractmethod
    def calculate_daily_nutrition(self, meals: List[Meal]) -> DailySummary:
        """Calculate daily nutrition summary"""
        pass
    
    @abstractmethod
    def scale_nutrition(self, nutrition: NutritionInfo, factor: float) -> NutritionInfo:
        """Scale nutrition values by a factor"""
        pass

class ConversationManager(ABC):
    """Interface for managing conversation flow"""
    
    @abstractmethod
    def start_conversation(self, user_input: UserResponse) -> ConversationContext:
        """Initialize a new conversation"""
        pass
    
    @abstractmethod
    def process_message(
        self, 
        user_input: UserResponse,
        context: ConversationContext
    ) -> Tuple[Optional[Meal], Optional[ClarificationRequest]]:
        """Process user message and return meal or clarification"""
        pass
    
    @abstractmethod
    def handle_clarification(
        self,
        response: UserResponse,
        context: ConversationContext
    ) -> Tuple[Optional[Meal], Optional[ClarificationRequest]]:
        """Handle clarification response"""
        pass

class NutritionTracker(ABC):
    """Main interface for the nutrition tracking system"""
    
    @abstractmethod
    def track_meal(self, user_input: UserResponse) -> Tuple[Optional[Meal], Optional[ClarificationRequest]]:
        """Main entry point for tracking meals"""
        pass
    
    @abstractmethod
    def get_daily_summary(self, date: datetime) -> Optional[DailySummary]:
        """Get nutrition summary for a specific day"""
        pass
    
    @abstractmethod
    def export_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Export nutrition data for a date range"""
        pass