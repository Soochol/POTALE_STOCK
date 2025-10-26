"""
Migration: Add Virtual Block System columns to dynamic_block_detection table

Date: 2025-10-26
Purpose: Add yaml_type, logical_level, pattern_sequence, is_virtual columns
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def migrate():
    """Add Virtual Block System columns"""
    db_path = project_root / "data" / "database" / "stock_data.db"

    print(f"Connecting to: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
        columns = [row[1] for row in cursor.fetchall()]

        columns_to_add = []

        if 'yaml_type' not in columns:
            columns_to_add.append(('yaml_type', 'INTEGER DEFAULT 0'))

        if 'logical_level' not in columns:
            columns_to_add.append(('logical_level', 'INTEGER DEFAULT 0'))

        if 'pattern_sequence' not in columns:
            columns_to_add.append(('pattern_sequence', 'INTEGER DEFAULT 0'))

        if 'is_virtual' not in columns:
            columns_to_add.append(('is_virtual', 'BOOLEAN DEFAULT 0'))

        if not columns_to_add:
            print("All columns already exist. No migration needed.")
            return

        # Add columns
        for col_name, col_def in columns_to_add:
            sql = f"ALTER TABLE dynamic_block_detection ADD COLUMN {col_name} {col_def}"
            print(f"Adding column: {col_name}")
            cursor.execute(sql)

        conn.commit()
        print(f"\nMigration completed successfully!")
        print(f"Added {len(columns_to_add)} columns to dynamic_block_detection table")

        # Verify
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
        all_columns = cursor.fetchall()
        print(f"\nCurrent table schema ({len(all_columns)} columns):")
        for col in all_columns:
            print(f"  {col[1]} ({col[2]})")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: Migration failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
