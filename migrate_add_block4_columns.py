"""
Database migration: Add Block4 columns to preset tables

Adds:
- block4_volume_ratio
- block4_low_price_margin
- block4_min_candles_after_block3
- block4_tolerance_pct (for redetection)
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Add Block4 columns to seed and redetection preset tables"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Mapping: {table_name: [(column_name, column_type, default_value), ...]}
    add_columns_mapping = {
        'seed_condition_preset': [
            ('block4_volume_ratio', 'REAL', 0.3),
            ('block4_low_price_margin', 'REAL', 10.0),
            ('block4_min_candles_after_block3', 'INTEGER', 1),
        ],
        'redetection_condition_preset': [
            ('block4_volume_ratio', 'REAL', 0.3),
            ('block4_low_price_margin', 'REAL', 10.0),
            ('block4_min_candles_after_block3', 'INTEGER', 1),
            ('block4_tolerance_pct', 'REAL', 25.0),
        ],
    }

    total_added = 0

    for table_name, columns in add_columns_mapping.items():
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            print(f"[SKIP] Table {table_name} does not exist")
            continue

        print(f"\n[{table_name}]")

        # Get existing columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]

        for column_name, column_type, default_value in columns:
            if column_name in column_names:
                print(f"  {column_name} [{column_type}] [ALREADY EXISTS]")
                continue

            # Add column with default value
            try:
                cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                )
                print(f"  {column_name} [{column_type}] DEFAULT {default_value} [OK]")
                total_added += 1
            except sqlite3.OperationalError as e:
                print(f"  {column_name} [{column_type}] [ERROR]: {e}")

    conn.commit()
    conn.close()

    print(f"\n[SUMMARY]")
    print(f"Total columns added: {total_added}")
    print(f"Migration completed successfully!")

if __name__ == "__main__":
    db_path = "data/database/stock_data.db"

    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        exit(1)

    print("="*80)
    print("Database Migration: Add Block4 Columns")
    print("="*80)
    print(f"Database: {db_path}\n")

    migrate_database(db_path)
