"""
Migration: Create seed_pattern table

Creates the seed_pattern table for high-quality seed detection results.

Date: 2025-10-24
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "database" / "stock_data.db"


def migrate():
    """Create seed_pattern table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seed_pattern (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name VARCHAR(100) NOT NULL UNIQUE,
                ticker VARCHAR(20) NOT NULL,
                yaml_config_path VARCHAR(500) NOT NULL,
                detection_date DATE NOT NULL,
                block_features TEXT NOT NULL,
                price_shape TEXT NOT NULL,
                volume_shape TEXT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                description TEXT,
                custom_metadata TEXT NOT NULL DEFAULT '{}'
            )
        """)

        # Create indexes
        indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_sp_pattern_name ON seed_pattern(pattern_name)",
            "CREATE INDEX IF NOT EXISTS idx_sp_ticker ON seed_pattern(ticker)",
            "CREATE INDEX IF NOT EXISTS idx_sp_detection_date ON seed_pattern(detection_date)",
            "CREATE INDEX IF NOT EXISTS idx_sp_status ON seed_pattern(status)",
            "CREATE INDEX IF NOT EXISTS idx_sp_ticker_detection_date ON seed_pattern(ticker, detection_date)",
            "CREATE INDEX IF NOT EXISTS idx_sp_ticker_status ON seed_pattern(ticker, status)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        print("[OK] seed_pattern table created successfully")

        # Verify table structure
        cursor.execute("PRAGMA table_info(seed_pattern)")
        columns = cursor.fetchall()
        print(f"\nTable structure ({len(columns)} columns):")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Starting migration: create seed_pattern table")
    print(f"Database: {DB_PATH}")
    print("-" * 60)
    migrate()
    print("-" * 60)
    print("Migration complete!")
