"""
Database migration: Drop unused candle columns from preset tables

Removes min_candles_after_block* and max_candles_after_block* columns from
redetection_condition_preset table as they are not used in redetection logic.

Note: These columns are still needed in seed_condition_preset for seed detection.
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Drop unused candle columns from redetection preset table"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check SQLite version (DROP COLUMN requires SQLite 3.35.0+)
    cursor.execute("SELECT sqlite_version()")
    sqlite_version = cursor.fetchone()[0]
    print(f"SQLite version: {sqlite_version}")

    # Columns to drop from redetection_condition_preset
    drop_columns = [
        'block2_min_candles_after_block1',
        'block2_max_candles_after_block1',
        'block3_min_candles_after_block2',
        'block3_max_candles_after_block2',
        'block4_min_candles_after_block3',
        'block4_max_candles_after_block3',
    ]

    table_name = 'redetection_condition_preset'

    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    if not cursor.fetchone():
        print(f"[SKIP] Table {table_name} does not exist")
        conn.close()
        return

    # Get existing columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]

    print(f"\n[{table_name}]")
    print(f"Columns to drop: {len(drop_columns)}")

    # Check version and drop columns
    version_parts = [int(x) for x in sqlite_version.split('.')]
    supports_drop_column = (version_parts[0] > 3) or \
                          (version_parts[0] == 3 and version_parts[1] >= 35)

    if supports_drop_column:
        # SQLite 3.35.0+ supports DROP COLUMN
        total_dropped = 0
        for column_name in drop_columns:
            if column_name not in column_names:
                print(f"  {column_name} [NOT EXISTS]")
                continue

            try:
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                print(f"  {column_name} [DROPPED]")
                total_dropped += 1
            except sqlite3.OperationalError as e:
                print(f"  {column_name} [ERROR]: {e}")

        conn.commit()
        print(f"\n[SUMMARY]")
        print(f"Total columns dropped: {total_dropped}")

    else:
        # Older SQLite: Need to recreate table
        print(f"\n[WARNING] SQLite {sqlite_version} does not support DROP COLUMN")
        print("Using table recreation method...")

        # Get all columns except the ones to drop
        columns_to_keep = [col for col in columns_info if col[1] not in drop_columns]

        # Build column definitions for new table
        new_columns = []
        for col in columns_to_keep:
            col_name = col[1]
            col_type = col[2]
            col_notnull = col[3]
            col_default = col[4]
            col_pk = col[5]

            col_def = f"{col_name} {col_type}"
            if col_pk:
                col_def += " PRIMARY KEY"
            if col_notnull:
                col_def += " NOT NULL"
            if col_default is not None:
                col_def += f" DEFAULT {col_default}"

            new_columns.append(col_def)

        # Get column names for data copy
        keep_column_names = [col[1] for col in columns_to_keep]
        columns_str = ", ".join(keep_column_names)

        try:
            # Create new table
            cursor.execute(f"""
                CREATE TABLE {table_name}_new (
                    {', '.join(new_columns)}
                )
            """)
            print(f"  Created temporary table: {table_name}_new")

            # Copy data
            cursor.execute(f"""
                INSERT INTO {table_name}_new ({columns_str})
                SELECT {columns_str} FROM {table_name}
            """)
            print(f"  Copied data to new table")

            # Drop old table
            cursor.execute(f"DROP TABLE {table_name}")
            print(f"  Dropped old table")

            # Rename new table
            cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
            print(f"  Renamed new table")

            # Recreate indexes
            cursor.execute(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_redetection_condition_name
                ON {table_name}(name)
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS ix_redetection_condition_active
                ON {table_name}(is_active)
            """)
            print(f"  Recreated indexes")

            conn.commit()
            print(f"\n[SUMMARY]")
            print(f"Table recreated without {len(drop_columns)} columns")

        except sqlite3.OperationalError as e:
            print(f"[ERROR]: {e}")
            conn.rollback()

    conn.close()
    print(f"Migration completed successfully!")

if __name__ == "__main__":
    db_path = "data/database/stock_data.db"

    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        exit(1)

    print("="*80)
    print("Database Migration: Drop Unused Candle Columns")
    print("="*80)
    print(f"Database: {db_path}\n")

    migrate_database(db_path)
