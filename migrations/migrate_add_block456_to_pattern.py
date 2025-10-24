"""
Database migration: Add seed_block4_id, seed_block5_id, seed_block6_id to block_pattern table

Adds optional columns for Block4/5/6 seed references to the block_pattern table.
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Add Block4/5/6 seed ID columns to block_pattern table"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    table_name = 'block_pattern'

    # Columns to add: (name, type, nullable)
    columns_to_add = [
        ('seed_block4_id', 'VARCHAR(50)', True),
        ('seed_block5_id', 'VARCHAR(50)', True),
        ('seed_block6_id', 'VARCHAR(50)', True),
    ]

    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    if not cursor.fetchone():
        print(f"[SKIP] Table {table_name} does not exist")
        conn.close()
        return

    print(f"\n[{table_name}]")

    # Get existing columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    total_added = 0

    for column_name, column_type, nullable in columns_to_add:
        if column_name in existing_columns:
            print(f"  [SKIP] Column '{column_name}' already exists")
            continue

        try:
            # Add column (NULL by default since they're optional)
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} NULL")
            conn.commit()
            print(f"  [ADD] Column '{column_name}' added successfully")
            total_added += 1
        except Exception as e:
            print(f"  [ERROR] Failed to add column '{column_name}': {e}")
            conn.rollback()

    conn.close()

    print(f"\n[COMPLETE] {total_added} columns added to {table_name}")
    print("\nMigration completed successfully!")


if __name__ == "__main__":
    db_path = "data/database/stock_data.db"

    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        exit(1)

    print("=" * 70)
    print("Migration: Add Block4/5/6 seed IDs to block_pattern table")
    print("=" * 70)

    migrate_database(db_path)
