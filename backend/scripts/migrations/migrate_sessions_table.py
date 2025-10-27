"""
Migration script: Rename agno_sessions to app_sessions

This script:
1. Renames the agno_sessions table to app_sessions
2. Preserves all existing session data
3. Allows Agno framework to create its own agno_sessions table with required schema

Run this script after updating the SQLAlchemy models.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text
from config.database import engine, init_db


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
        )
        return result.fetchone() is not None


def migrate():
    """Migrate agno_sessions table to app_sessions."""
    print("=" * 80)
    print("Database Migration: agno_sessions -> app_sessions")
    print("=" * 80)

    # Check if old table exists
    if not check_table_exists("agno_sessions"):
        print("\n[OK] No migration needed - agno_sessions table doesn't exist")
        print("  Creating fresh app_sessions table...")
        init_db()
        print("[OK] app_sessions table created successfully")
        return

    # Check if new table already exists
    if check_table_exists("app_sessions"):
        print("\n[OK] Migration already completed - app_sessions table exists")
        print("  Skipping migration")
        return

    print("\nMigration Plan:")
    print("  1. Rename agno_sessions -> app_sessions")
    print("  2. Preserve all existing session data")
    print("  3. Let Agno framework create new agno_sessions table\n")

    # Count existing sessions
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM agno_sessions"))
        count = result.fetchone()[0]
        print(f"  Found {count} existing sessions to migrate\n")

    # Perform migration
    try:
        with engine.begin() as conn:
            print("[MIGRATING] Renaming table...")
            conn.execute(text("ALTER TABLE agno_sessions RENAME TO app_sessions"))
            print("[OK] Table renamed successfully")

        print("\n[SUCCESS] Migration completed successfully!")
        print(f"   - {count} sessions migrated to app_sessions")
        print("   - Agno framework will create new agno_sessions table on next run")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print("\nPlease check the error and try again.")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
