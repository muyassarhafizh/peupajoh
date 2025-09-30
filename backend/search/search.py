# Standard library imports
import asyncio
from pathlib import Path

# Third-party imports
import aiosqlite
from rapidfuzz import process, fuzz

DB_PATH = Path(__file__).parent.parent / "data" / "peupajoh.sqlite3"

async def get_all_food_names():
    """Get all names from the food_items table"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name FROM food_items") as cursor:
            results = await cursor.fetchall()
            return [row[0] for row in results]

async def search_food_db(query: str, threshold: float = 0.85):
    """
    Search for food names using fuzzy matching from internal database
    
    Args:
        query: The search query
        threshold: Minimum similarity score (0.0 to 1.0), default 0.85
    
    Returns:
        List of tuples (food_name, score) sorted by score descending
    """
    all_names = await get_all_food_names()
    
    # scorer parameter uses token_set_ratio (per words)
    # score_cutoff is on 0-100 scale
    # Results are sorted by score (highest first)
    results = process.extract(
        query,
        all_names,
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold * 100,
        limit=None
    )
    
    return [(match, score, index) for match, score, index in results]

if __name__ == "__main__":
    all_names = asyncio.run(get_all_food_names())
    # print("All food names:", all_names)
    print(f"\nTotal food items: {len(all_names)}")
    
    #Test search query
    query = "Telur dadar"
    print(f"\n--- Fuzzy Search Results for: '{query}' ---")
    search_results = asyncio.run(search_food_db(query, threshold=0.70))
    
    if search_results:
        print(f"Found {len(search_results)} matches:")
        for name, score, _ in search_results:
            print(f"  - {name} (score: {score:.2f})")
    else:
        print("No matches found")