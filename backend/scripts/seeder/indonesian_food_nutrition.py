import argparse
import csv
import sys
from pathlib import Path
from typing import Optional

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.orm import Session
from config.database import SessionLocal, init_db
from app.db.models import FoodItem


DEFAULT_DB_RELATIVE = "backend/data/peupajoh.sqlite3"
TABLE_NAME = "food_items"


def _to_float(val: str) -> Optional[float]:
    try:
        v = val.strip()
        if v == "" or v.lower() == "null" or v.lower() == "none":
            return None
        return float(v)
    except Exception:
        return None


class NutritionSeeder:
    """Seeds nutrition data into database from a CSV file using SQLAlchemy."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _upsert_row(self, row: dict) -> None:
        """Insert or update a food item row."""
        # Normalize name: remove common suffix words like 'masakan', 'segar', 'matang'
        name_parts = (row.get("name") or "").strip().split()
        name_parts = [
            word.lower()
            for word in name_parts
            if word.lower() not in ("masakan", "segar", "matang")
        ]
        name = " ".join(name_parts)

        # Get the ID
        food_id = int(row["id"]) if row.get("id") not in (None, "") else None

        # Check if food item exists
        existing = None
        if food_id:
            existing = self.db.query(FoodItem).filter(FoodItem.id == food_id).first()

        if existing:
            # Update existing
            existing.name = name.strip()
            existing.calories = _to_float(row.get("calories", ""))
            existing.proteins = _to_float(row.get("proteins", ""))
            existing.fat = _to_float(row.get("fat", ""))
            existing.carbohydrate = _to_float(row.get("carbohydrate", ""))
            existing.image = (row.get("image") or "").strip() or None
        else:
            # Create new
            food_item = FoodItem(
                id=food_id,
                name=name.strip(),
                calories=_to_float(row.get("calories", "")),
                proteins=_to_float(row.get("proteins", "")),
                fat=_to_float(row.get("fat", "")),
                carbohydrate=_to_float(row.get("carbohydrate", "")),
                image=(row.get("image") or "").strip() or None,
            )
            self.db.add(food_item)

    def seed_from_csv(self, csv_path: Path) -> int:
        """Seed food items from CSV file."""
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {
                "id",
                "calories",
                "proteins",
                "fat",
                "carbohydrate",
                "name",
                "image",
            }
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"CSV missing required columns: {sorted(missing)}")

            count = 0
            for row in reader:
                self._upsert_row(row)
                count += 1

                # Commit in batches of 100 for better performance
                if count % 100 == 0:
                    self.db.commit()

            # Commit remaining rows
            self.db.commit()
            return count


def main():
    parser = argparse.ArgumentParser(
        description="Seed database with Indonesian food nutrition data using SQLAlchemy."
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=str(
            (Path(__file__).resolve().parents[2] / "data" / "nutrition.csv").resolve()
        ),
        help="Path to nutrition CSV (defaults to backend/data/nutrition.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()

    # Initialize database (create tables if they don't exist)
    print("Initializing database schema...")
    init_db()

    # Create a database session
    db_session = SessionLocal()

    try:
        seeder = NutritionSeeder(db_session)
        print(f"Seeding data from {csv_path}...")
        inserted = seeder.seed_from_csv(csv_path)
        print(f"Successfully seeded {inserted} rows into '{TABLE_NAME}'")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
