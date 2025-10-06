from typing import Optional, List, Any, Dict
import asyncio
import sys
import os
import uuid
import aiosqlite
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from search.search import search_food_db
from search.search import DB_PATH as FOOD_DB_PATH
from agents import extract_foods_structured
from helper.helper import _get_field, _to_raw_item
from helper.logger import log_to_file

# Database path for session/log storage (using agno.db)
SESSION_DB_PATH = Path(__file__).parent.parent / "agno.db"


# ============================================================================
# DATABASE SCHEMA INITIALIZATION
# ============================================================================


async def init_database():
    """Initialize database tables for food logs and meal sessions"""
    async with aiosqlite.connect(SESSION_DB_PATH) as db:
        # Create meal_sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meal_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                original_message TEXT
            )
        """)

        # Create food_logs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS food_logs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                food_item_id INTEGER,
                food_name TEXT NOT NULL,
                local_name TEXT,
                meal_type TEXT NOT NULL,
                quantity REAL DEFAULT 1.0,
                portion_description TEXT,
                calories REAL,
                proteins REAL,
                fat REAL,
                carbohydrate REAL,
                image TEXT,
                match_score REAL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES meal_sessions(session_id)
            )
        """)

        await db.commit()


async def _fetch_nutrition_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Fetch nutrition data from food database"""
    async with aiosqlite.connect(FOOD_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, name, calories, proteins, fat, carbohydrate, image
            FROM food_items
            WHERE name = ?
            """,
            (name,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def _log_food_to_db(session_id: str, food_data: Dict[str, Any]) -> str:
    """Log a confirmed food item to the database"""
    food_log_id = uuid.uuid4().hex

    async with aiosqlite.connect(SESSION_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO food_logs (
                id, session_id, food_item_id, food_name, local_name,
                meal_type, quantity, portion_description,
                calories, proteins, fat, carbohydrate, image, match_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                food_log_id,
                session_id,
                food_data.get("nutrition", {}).get("id"),
                food_data.get("match_name"),
                food_data.get("query"),
                food_data.get("meal_type"),
                food_data.get("quantity", 1.0),
                food_data.get("portion_description"),
                food_data.get("nutrition", {}).get("calories"),
                food_data.get("nutrition", {}).get("proteins"),
                food_data.get("nutrition", {}).get("fat"),
                food_data.get("nutrition", {}).get("carbohydrate"),
                food_data.get("nutrition", {}).get("image"),
                food_data.get("score", 0.0),
            ),
        )
        await db.commit()

    return food_log_id


async def _create_session(session_id: str, original_message: str, user_id: str = None):
    """Create a new meal session"""
    async with aiosqlite.connect(SESSION_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO meal_sessions (session_id, user_id, original_message, status)
            VALUES (?, ?, ?, 'active')
        """,
            (session_id, user_id, original_message),
        )
        await db.commit()


# ============================================================================
# MAIN WORKFLOW
# ============================================================================


async def main_workflow_async(
    food_items: List[Any],
    session_id: str,
    original_message: str = "",
    threshold: float = 0.80,
    user_id: str = None,
) -> Dict[str, Any]:
    """
    Main workflow for processing food items:
    1. Search for each food item in database
    2. If exactly 1 match: log to database immediately
    3. If multiple matches: add to clarification queue
    4. If 0 matches: skip for now (TODO: smarter model with MCP)
    5. Return structured result with logged items and clarifications
    """
    # Initialize database
    await init_database()

    # Create session
    await _create_session(session_id, original_message, user_id)

    logged_items: List[Dict[str, Any]] = []
    needs_clarification: List[Dict[str, Any]] = []
    skipped_items: List[Dict[str, Any]] = []

    for item in food_items:
        food_request_id = uuid.uuid4().hex
        query = (
            _get_field(item, "local_name") or _get_field(item, "name") or ""
        ).strip()

        if not query:
            skipped_items.append(
                {
                    "request_id": food_request_id,
                    "reason": "empty_query",
                    "item": _to_raw_item(item),
                }
            )
            continue

        # Search in database
        results = await search_food_db(query, threshold=threshold)
        num_results = len(results) if results else 0

        meal_type = _get_field(item, "meal_type")
        meal_type_str = (
            meal_type.value
            if hasattr(meal_type, "value")
            else str(meal_type)
            if meal_type
            else "snack"
        )
        quantity = _get_field(item, "quantity") or 1.0
        portion_desc = _get_field(item, "portion_description")

        if num_results == 1:
            # Exactly 1 match - log immediately
            match_name, score, _ = results[0]
            if score < os.getenv("THRESHOLD", 85):
                skipped_items.append(
                    {
                        "request_id": food_request_id,
                        "reason": "low_score",
                        "item": _to_raw_item(item),
                    }
                )
                continue
            nutrition = await _fetch_nutrition_by_name(match_name)

            food_data = {
                "match_name": match_name,
                "query": query,
                "score": float(score) / 100.0,
                "nutrition": nutrition,
                "meal_type": meal_type_str,
                "quantity": quantity,
                "portion_description": portion_desc,
                "raw_item": _to_raw_item(item),
            }

            log_id = await _log_food_to_db(session_id, food_data)
            food_data["log_id"] = log_id
            food_data["request_id"] = food_request_id
            logged_items.append(food_data)

        elif num_results > 1:
            # Multiple matches - needs clarification
            options = [f"{name} (score: {score:.0f})" for name, score, _ in results[:5]]
            needs_clarification.append(
                {
                    "request_id": food_request_id,
                    "query": query,
                    "options": options,
                    "raw_results": [
                        (name, float(score) / 100.0) for name, score, _ in results[:5]
                    ],
                    "meal_type": meal_type_str,
                    "quantity": quantity,
                    "portion_description": portion_desc,
                    "item": _to_raw_item(item),
                }
            )

        else:
            # No matches - skip for now (TODO: use smarter model)
            skipped_items.append(
                {
                    "request_id": food_request_id,
                    "query": query,
                    "reason": "no_matches",
                    "meal_type": meal_type_str,
                    "item": _to_raw_item(item),
                }
            )

    return {
        "session_id": session_id,
        "logged_items": logged_items,
        "needs_clarification": needs_clarification,
        "skipped_items": skipped_items,
        "summary": {
            "total_items": len(food_items),
            "logged": len(logged_items),
            "needs_clarification": len(needs_clarification),
            "skipped": len(skipped_items),
        },
    }


async def get_meals_by_session(session_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve all logged meals for a session, grouped by meal type.
    Returns data in the format specified in requirements.
    """
    async with aiosqlite.connect(SESSION_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM food_logs
            WHERE session_id = ?
            ORDER BY meal_type, logged_at
        """,
            (session_id,),
        ) as cur:
            rows = await cur.fetchall()

    # Group by meal type
    meals_by_type: Dict[str, List[Dict[str, Any]]] = {
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "snack": [],
    }

    for row in rows:
        row_dict = dict(row)
        meal_type = row_dict.get("meal_type", "snack").lower()

        # Format according to requirements
        food_entry = {
            "id": row_dict["id"],
            "name": row_dict["food_name"],
            "local_name": row_dict["local_name"],
            "category": "PROTEIN",  # TODO: Add category to food_logs table
            "subcategory": None,
            "nutrition_per_100g": {
                "calories": row_dict["calories"],
                "protein": row_dict["proteins"],
                "carbohydrates": row_dict["carbohydrate"],
                "fat": row_dict["fat"],
                "fiber": 0,  # TODO: Add to database
                "sugar": 0,  # TODO: Add to database
                "sodium": 0,  # TODO: Add to database
            },
            "standard_portions": {"serving_size": 100, "unit": "grams"},
            "quantity": row_dict["quantity"],
            "portion_description": row_dict["portion_description"],
            "image": row_dict["image"],
            "match_score": row_dict["match_score"],
            "variations": [],
            "tags": [],
            "is_composite": False,
            "embeddings": None,
        }

        if meal_type in meals_by_type:
            meals_by_type[meal_type].append(food_entry)
        else:
            meals_by_type["snack"].append(food_entry)

    # Capitalize meal type keys for output
    return {
        "Breakfast": meals_by_type["breakfast"],
        "Lunch": meals_by_type["lunch"],
        "Dinner": meals_by_type["dinner"],
        "Snack": meals_by_type["snack"],
    }


# ============================================================================
# CLARIFICATION HANDLING (TODO: Implement with Agno agent)
# ============================================================================


async def handle_clarifications_batch(
    clarifications: List[Dict[str, Any]], session_id: str
) -> Dict[str, Any]:
    """
    Handle batch clarifications using the clarification agent.
    This will be stored in agno.db automatically with session_id.

    TODO: Implement this properly with the clarification agent
    """
    # Placeholder for clarification agent implementation
    # The agent will use session_id to maintain conversation context
    return {
        "session_id": session_id,
        "clarifications_sent": len(clarifications),
        "status": "pending_user_response",
        "message": "Clarification questions have been sent to the user",
    }


# ============================================================================
# SYNCHRONOUS WRAPPERS
# ============================================================================


def main_workflow(
    food_items: List[Any],
    session_id: str,
    original_message: str = "",
    threshold: float = 0.80,
    user_id: str = None,
) -> Dict[str, Any]:
    """Synchronous wrapper for main workflow"""
    return asyncio.run(
        main_workflow_async(
            food_items, session_id, original_message, threshold, user_id
        )
    )


def get_meals_by_session_sync(session_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Synchronous wrapper for getting meals"""
    return asyncio.run(get_meals_by_session(session_id))


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    session_id = uuid.uuid4().hex
    print(f"Session ID: {session_id}\n")

    # log to {yymmdd}-log-{session_id}.txt
    yymmdd = datetime.now().strftime("%y%m%d %H:%M:%S")
    log_file = f"{yymmdd}-log-{session_id}.txt"
    log_to_file(f"Session ID: {session_id}\n", log_file)

    message = """Kemarin saya makan Sarapan: bubur  1 porsi dengan satu telur mata sapi
Lunch : Sushi tei
Malam: Steak ayam 200 gram dengan kentang goreng
Snack: Mie ayam yamin 1 porsi jumbo"""

    log_to_file(f"Message: {message}\n", log_file)

    # Step 1: Extract foods from message
    log_to_file("=== STEP 1: EXTRACTING FOODS ===", log_file)
    result = extract_foods_structured(message)
    log_to_file(f"Found {len(result.foods)} food items", log_file)
    log_to_file(f"Confidence: {result.confidence}\n", log_file)

    # Step 2: Run main workflow
    log_to_file("=== STEP 2: PROCESSING WORKFLOW ===", log_file)
    workflow_result = main_workflow(result.foods, session_id, message)

    log_to_file(
        f"✓ Logged immediately: {workflow_result['summary']['logged']}", log_file
    )
    log_to_file(
        f"? Needs clarification: {workflow_result['summary']['needs_clarification']}",
        log_file,
    )

    log_to_file(
        workflow_result["needs_clarification"],
        log_file,
    )

    log_to_file(
        f"⊘ Skipped (no matches): {workflow_result['summary']['skipped']}\n", log_file
    )

    # Show logged items
    if workflow_result["logged_items"]:
        log_to_file("=== LOGGED ITEMS ===", log_file)
        for item in workflow_result["logged_items"]:
            log_to_file(
                f"  - {item['match_name']} ({item['meal_type']}) - Score: {item['score']:.2f}",
                log_file,
            )

    # Show items needing clarification
    if workflow_result["needs_clarification"]:
        log_to_file("\n=== NEEDS CLARIFICATION ===", log_file)
        for item in workflow_result["needs_clarification"]:
            log_to_file(
                f"  - '{item['query']}' has {len(item['options'])} possible matches:",
                log_file,
            )
            for opt in item["options"][:3]:
                log_to_file(f"    - {opt}", log_file)

    # Show skipped items
    if workflow_result["skipped_items"]:
        log_to_file("\n=== SKIPPED (No Matches) ===", log_file)
        for item in workflow_result["skipped_items"]:
            log_to_file(f"  - '{item['query']}' - {item['reason']}", log_file)

    # Step 3: Get final meal data
    log_to_file("\n=== STEP 3: FINAL MEAL DATA ===", log_file)
    meals_data = get_meals_by_session_sync(session_id)

    for meal_type, foods in meals_data.items():
        if foods:
            log_to_file(f"\n{meal_type}:", log_file)
            for food in foods:
                log_to_file(f"  - {food['name']} ({food['local_name']})", log_file)
                log_to_file(
                    f"    Calories: {food['nutrition_per_100g']['calories']} kcal",
                    log_file,
                )
                log_to_file(
                    f"    Protein: {food['nutrition_per_100g']['protein']}g", log_file
                )
