"""
Database migration: Rename Block2/3 parameter names

Renames:
- block_volume_ratio -> block2_volume_ratio / block3_volume_ratio
- low_price_margin -> block2_low_price_margin / block3_low_price_margin
- min_candles_after_block1 -> block2_min_candles_after_block1
- min_candles_after_block2 -> block3_min_candles_after_block2
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Rename Block2/3 parameter columns in all preset tables"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Mapping: {table_name: [(old_name, new_name), ...]}
    rename_mapping = {
        'block2_condition_presets': [
            ('block_volume_ratio', 'block2_volume_ratio'),
            ('low_price_margin', 'block2_low_price_margin'),
            ('min_candles_after_block1', 'block2_min_candles_after_block1'),
        ],
        'block3_condition_presets': [
            ('block_volume_ratio', 'block3_volume_ratio'),
            ('low_price_margin', 'block3_low_price_margin'),
            ('min_candles_after_block1', 'block2_min_candles_after_block1'),
            ('min_candles_after_block2', 'block3_min_candles_after_block2'),
        ],
        'seed_condition_presets': [
            ('block2_volume_ratio', 'block2_volume_ratio'),  # already correct, but keep for reference
            ('block2_low_price_margin', 'block2_low_price_margin'),
            ('block2_min_candles_after_block1', 'block2_min_candles_after_block1'),
            ('block3_volume_ratio', 'block3_volume_ratio'),
            ('block3_low_price_margin', 'block3_low_price_margin'),
            ('block3_min_candles_after_block2', 'block3_min_candles_after_block2'),
        ],
        'redetection_condition_presets': [
            ('block2_volume_ratio', 'block2_volume_ratio'),  # already correct
            ('block2_low_price_margin', 'block2_low_price_margin'),
            ('block2_min_candles_after_block1', 'block2_min_candles_after_block1'),
            ('block3_volume_ratio', 'block3_volume_ratio'),
            ('block3_low_price_margin', 'block3_low_price_margin'),
            ('block3_min_candles_after_block2', 'block3_min_candles_after_block2'),
        ],
    }

    total_renamed = 0

    for table_name, columns in rename_mapping.items():
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            print(f"[SKIP] Table {table_name} does not exist")
            continue

        print(f"\n[{table_name}]")

        for old_name, new_name in columns:
            # Skip if already renamed (seed/redetection tables)
            if old_name == new_name:
                print(f"  {old_name} -> {new_name} [ALREADY CORRECT]")
                continue

            # Check if old column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            if old_name not in column_names:
                if new_name in column_names:
                    print(f"  {old_name} -> {new_name} [ALREADY RENAMED]")
                else:
                    print(f"  {old_name} -> {new_name} [COLUMN NOT FOUND]")
                continue

            # Rename column using ALTER TABLE
            try:
                cursor.execute(
                    f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}"
                )
                print(f"  {old_name} -> {new_name} [OK]")
                total_renamed += 1
            except sqlite3.OperationalError as e:
                print(f"  {old_name} -> {new_name} [ERROR]: {e}")

    conn.commit()
    conn.close()

    print(f"\n[SUMMARY]")
    print(f"Total columns renamed: {total_renamed}")
    print(f"Migration completed successfully!")

if __name__ == "__main__":
    db_path = "data/database/stock_data.db"

    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        exit(1)

    print("="*80)
    print("Database Migration: Rename Block2/3 Parameters")
    print("="*80)
    print(f"Database: {db_path}\n")

    migrate_database(db_path)
