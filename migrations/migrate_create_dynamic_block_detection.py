"""
Migration: Create dynamic_block_detection table

Creates the dynamic_block_detection table for YAML-based dynamic block detection system.

Date: 2025-10-24
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "database" / "stock_data.db"


def migrate():
    """Create dynamic_block_detection table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dynamic_block_detection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_id VARCHAR(50) NOT NULL,
                block_type INTEGER NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                pattern_id INTEGER,
                condition_name VARCHAR(50) NOT NULL,
                started_at DATE,
                ended_at DATE,
                status VARCHAR(20) NOT NULL,
                peak_price FLOAT,
                peak_volume INTEGER,
                peak_date DATE,
                parent_blocks TEXT NOT NULL DEFAULT '[]',
                custom_metadata TEXT NOT NULL DEFAULT '{}'
            )
        """)

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_dbd_block_id ON dynamic_block_detection(block_id)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_block_type ON dynamic_block_detection(block_type)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_ticker ON dynamic_block_detection(ticker)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_pattern_id ON dynamic_block_detection(pattern_id)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_condition_name ON dynamic_block_detection(condition_name)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_started_at ON dynamic_block_detection(started_at)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_status ON dynamic_block_detection(status)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_ticker_started ON dynamic_block_detection(ticker, started_at)",
            "CREATE INDEX IF NOT EXISTS idx_dbd_ticker_block_type ON dynamic_block_detection(ticker, block_type)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        print("[OK] dynamic_block_detection table created successfully")

        # Verify table structure
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
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
    print("Starting migration: create dynamic_block_detection table")
    print(f"Database: {DB_PATH}")
    print("-" * 60)
    migrate()
    print("-" * 60)
    print("Migration complete!")
