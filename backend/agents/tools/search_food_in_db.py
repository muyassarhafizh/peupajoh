"""
Food Database Search Tool

Simple fuzzy search for food names in a local SQLite database.
Note: Will be updated to use semantic search in the future.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import aiosqlite
from rapidfuzz import fuzz, process
from config.settings import settings

# Get database path from settings
# Convert SQLAlchemy URL to file path if needed
if settings.db_path.startswith("sqlite:///"):
    DB_PATH = Path(settings.db_path.replace("sqlite:///", ""))
else:
    DB_PATH = Path(settings.db_path)


@dataclass(slots=True)
class DatabaseFoodMatch:
    """Represents a fuzzy match to a food item stored in the database."""

    name: str
    score: float
    index: int

    def __repr__(self) -> str:  # pragma: no cover - repr for debugging only
        return f"{self.name} (score={self.score:.2f}, index={self.index})"


async def get_all_food_names(db_path: Path | str = DB_PATH) -> list[str]:
    """Fetch all food item names from the local SQLite database."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT name FROM food_items") as cursor:
            rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def search_food_in_db(
    query: str,
    *,
    threshold: float = 0.85,
    max_results: int | None = None,
    db_path: Path | str = DB_PATH,
) -> list[DatabaseFoodMatch]:
    """Perform a fuzzy search against the internal food database.

    Args:
        query: Raw search text from the user.
    threshold: Minimum similarity score (0.0 - 1.0) required to keep a match.
        max_results: Optional maximum number of matches to return.
        db_path: Optional override for the database path.

    Returns:
    Sorted list of matches with similarity scores on a 0-100 scale.
    """
    if not query:
        return []

    # Use default DB_PATH if db_path is empty or None
    if not db_path or db_path == "":
        db_path = DB_PATH

    all_names = await get_all_food_names(db_path)

    # `score_cutoff` expects 0-100 range whereas our threshold is 0.0-1.0.
    raw_results: Iterable[tuple[str, float, int]] = process.extract(
        query,
        all_names,
        scorer=fuzz.token_set_ratio,
        processor=str.casefold,
        score_cutoff=threshold * 100,
        limit=max_results,
    )

    result = [
        DatabaseFoodMatch(name=match, score=score, index=index)
        for match, score, index in raw_results
    ]
    print(f"Found {len(result)} matches for query '{query}'")  # Debug log
    return result


__all__ = ["DatabaseFoodMatch", "get_all_food_names", "search_food_in_db"]
