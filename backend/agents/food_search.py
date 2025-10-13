import sys
import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional

# Standard path setup for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from agents import get_agent
from models.models import FoodExtractionResult, ExtractedFood
from agents import extract_foods_structured
from search.search import search_food_db


async def process_user_food_input(
    user_message: str, 
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    threshold: float = 0.80
) -> Dict[str, Any]:
    """
    Main function to process user food input and determine what needs clarification.
    
    This function handles the search workflow:
    1. Extracts food items from user messages using the food extraction agent
    2. Searches the SQLite database for matches using fuzzy matching
    3. Categorizes results based on match quality:
       - exact_matches: Single high-confidence match (auto-log ready)
       - needs_clarification: Multiple matches or ambiguous results
       - no_matches: Items too different from database entries
    
    Args:
        user_message: User's message containing food information
        session_id: Optional session ID, will generate UUID if not provided
        user_id: Optional user ID for tracking purposes
        threshold: Minimum similarity threshold for fuzzy matching (0.0-1.0)
        
    Returns:
        Dict containing:
        - session_id: Session identifier
        - extraction_result: Raw food extraction result
        - exact_matches: Items ready for auto-logging
        - needs_clarification: Items requiring user clarification
        - no_matches: Items with no good database matches
        - summary: Processing summary statistics
        
    Example:
        >>> result = await process_user_food_input("Sarapan: bubur ayam")
        >>> print(f"Exact matches: {len(result['exact_matches'])}")
        >>> print(f"Need clarification: {len(result['needs_clarification'])}")
    """
    if not session_id:
        session_id = uuid.uuid4().hex
    
    # Step 1: Extract food items from user message
    extraction_result = await _extract_foods_from_message(user_message)
    
    if not extraction_result.foods:
        return _create_empty_search_response(session_id, extraction_result)
    
    # Step 2: Search database for each extracted food item
    search_results = await asyncio.gather(
        *[_search_single_food_item(food_item, threshold) for food_item in extraction_result.foods]
    )
    
    exact_matches = [result for result in search_results if result["category"] == "exact_match"]
    needs_clarification = [result for result in search_results if result["category"] == "needs_clarification"]
    needs_smart_agent = [result for result in search_results if result["category"] == "needs_smart_agent"]
    no_matches = [result for result in search_results if result["category"] == "no_match"]
    return {
        "session_id": session_id,
        "extraction_result": extraction_result,
        "exact_matches": exact_matches,
        "needs_clarification": needs_clarification,
        "needs_smart_agent": needs_smart_agent,
        "no_matches": no_matches,
        "summary": {
            "total_extracted": len(extraction_result.foods),
            "exact_matches": len(exact_matches),
            "needs_clarification": len(needs_clarification),
            "needs_smart_agent": len(needs_smart_agent),
            "no_matches": len(no_matches),
            "confidence": extraction_result.confidence
        }
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _extract_foods_from_message(user_message: str) -> FoodExtractionResult:
    """Extract food items from user message using the food extraction agent."""
    return extract_foods_structured(user_message)


async def _search_single_food_item(food_item: ExtractedFood, threshold: float) -> Dict[str, Any]:
    """
    Search database for a single food item and categorize the result.
    
    Args:
        food_item: Extracted food item from user message
        threshold: Minimum similarity threshold for matching
        
    Returns:
        Dict with categorized search result:
        - category: "exact_match", "needs_clarification", or "no_match"
        - food_item: Original extracted food item
        - search_results: Raw database search results
        - match_info: Additional match information
    """
    # Get the query string (prefer local_name, fallback to name)
    query = food_item.local_name or food_item.name
    if not query:
        return _create_no_match_result(food_item, "empty_query")
    
    # Search the database
    search_results = await search_food_db(query, threshold=threshold)
    
    if not search_results:
        return _create_no_match_result(food_item, "no_database_matches")
    
    # Apply your criteria for categorization
    if len(search_results) == 1 and search_results[0][1] >= 85.0:
        # Single high-confidence match - ready for auto-logging
        return _create_exact_match_result(food_item, search_results[0])
    elif len(search_results) > 1:
        # Use LLM to determine specificity
        specificity_result = await _determine_specificity_with_llm(query, search_results)
        
        if specificity_result == "needs_smart_agent":
            return _create_smart_agent_result(food_item, search_results)
        elif specificity_result == "exact_match":
            # LLM determined this is actually an exact match
            return _create_exact_match_result(food_item, search_results[0])
        else:  # "needs_clarification"
            return _create_clarification_result(food_item, search_results)
    else:
        # Low confidence single match - treat as no match
        return _create_no_match_result(food_item, "low_confidence")

def _create_exact_match_result(food_item: ExtractedFood, match_result: tuple) -> Dict[str, Any]:
    """Create result for exact match (ready for auto-logging)."""
    match_name, score, _ = match_result
    return {
        "category": "exact_match",
        "request_id": uuid.uuid4().hex,
        "food_item": food_item,
        "match_name": match_name,
        "match_score": float(score) / 100.0,
        "query": food_item.local_name or food_item.name,
        "meal_type": food_item.meal_type.value if food_item.meal_type else "snack",
        "quantity": food_item.quantity,
        "portion_description": food_item.portion_description
    }


def _create_clarification_result(food_item: ExtractedFood, search_results: List[tuple]) -> Dict[str, Any]:
    """Create result for items needing clarification."""
    return {
        "category": "needs_clarification",
        "request_id": uuid.uuid4().hex,
        "food_item": food_item,
        "query": food_item.local_name or food_item.name,
        "options": [f"{name} (score: {score:.0f})" for name, score, _ in search_results[:5]],
        "raw_results": [(name, float(score) / 100.0) for name, score, _ in search_results[:5]],
        "meal_type": food_item.meal_type.value if food_item.meal_type else "snack",
        "quantity": food_item.quantity,
        "portion_description": food_item.portion_description
    }


def _create_no_match_result(food_item: ExtractedFood, reason: str) -> Dict[str, Any]:
    """Create result for items with no good matches."""
    return {
        "category": "no_match",
        "request_id": uuid.uuid4().hex,
        "food_item": food_item,
        "query": food_item.local_name or food_item.name,
        "reason": reason,
        "meal_type": food_item.meal_type.value if food_item.meal_type else "snack"
    }

async def _determine_specificity_with_llm(query: str, search_results: List[tuple]) -> str:
    """Use LLM to determine if user input is more specific than database options."""
    agent = get_agent("specificity")
    
    # Format the context for the LLM
    context = {
        "user_query": query,
        "database_options": [name for name, score, _ in search_results]
    }
    
    result = agent.run(json.dumps(context))
    return result.content.category  # "exact_match", "needs_clarification", "needs_smart_agent"

def _create_smart_agent_result(food_item: ExtractedFood, search_results: List[tuple]) -> Dict[str, Any]:
    """Create result for items needing smart agent processing."""
    return {
        "category": "needs_smart_agent",
        "request_id": uuid.uuid4().hex,
        "food_item": food_item,
        "query": food_item.local_name or food_item.name,
        "options": [f"{name} (score: {score:.0f})" for name, score, _ in search_results[:5]],
        "raw_results": [(name, float(score) / 100.0) for name, score, _ in search_results[:5]],
        "meal_type": food_item.meal_type.value if food_item.meal_type else "snack",
        "quantity": food_item.quantity,
        "portion_description": food_item.portion_description,
        "reason": "user_input_more_specific"
    }

def _create_empty_search_response(session_id: str, extraction_result: FoodExtractionResult) -> Dict[str, Any]:
    """Create response when no foods are detected."""
    return {
        "session_id": session_id,
        "extraction_result": extraction_result,
        "exact_matches": [],
        "needs_clarification": [],
        "needs_smart_agent": [],  # Add this line
        "no_matches": [],
        "summary": {
            "total_extracted": 0,
            "exact_matches": 0,
            "needs_clarification": 0,
            "needs_smart_agent": 0,  # Add this line
            "no_matches": 0,
            "confidence": extraction_result.confidence
        }
    }

# ============================================================================
# SYNCHRONOUS WRAPPERS
# ============================================================================

def process_user_food_input_sync(
    user_message: str, 
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    threshold: float = 0.80
) -> Dict[str, Any]:
    """Synchronous wrapper for processing user food input."""
    return asyncio.run(process_user_food_input(user_message, session_id, user_id, threshold))


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    async def test_search_agent():
        """Test the search agent with sample input."""
        print("=" * 70)
        print("TESTING FOOD SEARCH AGENT - CATEGORIZATION")
        print("=" * 70)
        
        test_message = """Sarapan: bubur ayam, telur mata sapi
        Makan siang: nasi gudeg, ayam betutu
        Malam: mie ayam yamin"""
        
        print(f"Input: {test_message}\n")
        
        result = await process_user_food_input(test_message)
        
        print("📊 SEARCH RESULTS:")
        print(f"Total extracted: {result['summary']['total_extracted']}")
        print(f"Exact matches: {result['summary']['exact_matches']}")
        print(f"Need clarification: {result['summary']['needs_clarification']}")
        print(f"No matches: {result['summary']['no_matches']}")
        
        if result['exact_matches']:
            print("\n✅ EXACT MATCHES (Ready for auto-log):")
            for item in result['exact_matches']:
                print(f"  • {item['query']} → {item['match_name']} (score: {item['match_score']:.2f})")
        
        if result['needs_clarification']:
            print("\n❓ NEEDS CLARIFICATION:")
            for item in result['needs_clarification']:
                print(f"  • {item['query']} → {len(item['options'])} options:")
                for i, option in enumerate(item['options'], 1):
                    print(f"    {i}. {option}")
                print()

        if result['needs_smart_agent']:
            print("\n🤖 NEEDS SMART AGENT:")
            for item in result['needs_smart_agent']:
                print(f"  • {item['query']} → {len(item['options'])} options (user input more specific):")
                for i, option in enumerate(item['options'], 1):
                    print(f"    {i}. {option}")
                print()

        if result['no_matches']:
            print("\n❌ NO MATCHES:")
            for item in result['no_matches']:
                print(f"  • {item['query']} → {item['reason']}")
        
        print("\n" + "=" * 70)
        print("✅ TESTING COMPLETED!")
        
        return result
    
    # Run the test
    asyncio.run(test_search_agent())