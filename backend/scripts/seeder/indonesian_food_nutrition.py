import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Optional


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


class SQLiteDB:
    """Lightweight SQLite manager for this project."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    calories REAL,
                    proteins REAL,
                    fat REAL,
                    carbohydrate REAL,
                    image TEXT
                );
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_name ON {TABLE_NAME}(name);"
            )


class NutritionSeeder:
    """Seeds nutrition data into SQLite from a CSV file."""

    def __init__(self, db: SQLiteDB):
        self.db = db

    @staticmethod
    def _upsert_row(conn: sqlite3.Connection, row: dict) -> None:
        conn.execute(
            f"""
            INSERT INTO {TABLE_NAME} (id, name, calories, proteins, fat, carbohydrate, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                calories=excluded.calories,
                proteins=excluded.proteins,
                fat=excluded.fat,
                carbohydrate=excluded.carbohydrate,
                image=excluded.image;
            """,
            (
                int(row["id"]) if row.get("id") not in (None, "") else None,
                (row.get("name") or "").strip(),
                _to_float(row.get("calories", "")),
                _to_float(row.get("proteins", "")),
                _to_float(row.get("fat", "")),
                _to_float(row.get("carbohydrate", "")),
                (row.get("image") or "").strip() or None,
            ),
        )


    def seed_from_csv(self, csv_path: Path) -> int:
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"id", "calories", "proteins", "fat", "carbohydrate", "name", "image"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"CSV missing required columns: {sorted(missing)}")

            count = 0
            with self.db.connect() as conn:
                for row in reader:
                    self._upsert_row(conn, row)
                    count += 1
            return count


def main():
    parser = argparse.ArgumentParser(description="Seed SQLite with Indonesian food nutrition data.")
    parser.add_argument(
        "--csv",
        type=str,
        default=str((Path(__file__).resolve().parents[2] / "data" / "nutrition.csv").resolve()),
        help="Path to nutrition CSV (defaults to backend/data/nutrition.csv)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str((Path(__file__).resolve().parents[2] / "data" / "peupajoh.sqlite3").resolve()),
        help="Path to SQLite DB (defaults to backend/data/peupajoh.sqlite3)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    db_path = Path(args.db).expanduser().resolve()

    db = SQLiteDB(db_path)
    db.create_schema()
    seeder = NutritionSeeder(db)
    inserted = seeder.seed_from_csv(csv_path)
    print(f"Seeded {inserted} rows into '{TABLE_NAME}' at {db_path}")


if __name__ == "__main__":
    main()

