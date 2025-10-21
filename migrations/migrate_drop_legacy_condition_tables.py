"""
Database migration: Drop legacy block condition preset tables

Drops:
- block1_condition_preset
- block2_condition_preset
- block3_condition_preset
- block4_condition_preset

These tables have been replaced by:
- seed_condition_preset (unified for seed detection)
- redetection_condition_preset (unified for redetection)
"""
import sqlite3
from pathlib import Path

def backup_legacy_tables(db_path: str, backup_path: str):
    """Backup legacy tables before dropping"""

    conn = sqlite3.connect(db_path)

    tables_to_backup = [
        'block1_condition_preset',
        'block2_condition_preset',
        'block3_condition_preset',
        'block4_condition_preset'
    ]

    with open(backup_path, 'w', encoding='utf-8') as f:
        for table in tables_to_backup:
            # Check if table exists
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if not cursor.fetchone():
                continue

            # Dump table
            for line in conn.iterdump():
                if table in line:
                    f.write(f'{line}\n')

    conn.close()
    print(f"[OK] Backup saved to: {backup_path}")


def drop_legacy_tables(db_path: str):
    """Drop legacy block condition preset tables"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables_to_drop = [
        'block1_condition_preset',
        'block2_condition_preset',
        'block3_condition_preset',
        'block4_condition_preset'
    ]

    total_dropped = 0

    for table_name in tables_to_drop:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            print(f"[SKIP] {table_name}: Table does not exist")
            continue

        # Check data count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

        print(f"\n[{table_name}]")
        print(f"  Records: {count}")

        if count > 0:
            # Show sample data
            cursor.execute(f"SELECT name FROM {table_name} LIMIT 5")
            names = [row[0] for row in cursor.fetchall()]
            print(f"  Sample names: {', '.join(names)}")

        # Drop table
        try:
            cursor.execute(f"DROP TABLE {table_name}")
            print(f"  Status: DROPPED ✓")
            total_dropped += 1
        except sqlite3.OperationalError as e:
            print(f"  Status: ERROR - {e}")

    conn.commit()
    conn.close()

    print(f"\n[SUMMARY]")
    print(f"Total tables dropped: {total_dropped}")
    print(f"Migration completed successfully!")


if __name__ == "__main__":
    db_path = "data/database/stock_data.db"
    backup_path = "data/database/backup_legacy_condition_tables.sql"

    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        exit(1)

    print("="*80)
    print("Database Migration: Drop Legacy Block Condition Preset Tables")
    print("="*80)
    print(f"Database: {db_path}\n")

    # Ask for confirmation
    print("⚠️  WARNING: This will permanently delete the following tables:")
    print("  - block1_condition_preset")
    print("  - block2_condition_preset")
    print("  - block3_condition_preset")
    print("  - block4_condition_preset")
    print("\nThese tables have been replaced by:")
    print("  ✅ seed_condition_preset")
    print("  ✅ redetection_condition_preset")
    print("\n" + "="*80)

    response = input("\nDo you want to continue? (yes/no): ").strip().lower()

    if response != 'yes':
        print("[CANCELLED] Migration aborted by user")
        exit(0)

    # Backup first
    print("\n[STEP 1] Creating backup...")
    backup_legacy_tables(db_path, backup_path)

    # Drop tables
    print("\n[STEP 2] Dropping legacy tables...")
    drop_legacy_tables(db_path)

    print("\n" + "="*80)
    print("✅ Migration completed!")
    print("="*80)
    print(f"\nBackup file: {backup_path}")
    print("\nNext steps:")
    print("1. Delete repository files:")
    print("   - src/infrastructure/repositories/block1_condition_preset_repository.py")
    print("   - src/infrastructure/repositories/block2_condition_preset_repository.py")
    print("   - src/infrastructure/repositories/block3_condition_preset_repository.py")
    print("   - src/infrastructure/repositories/block4_condition_preset_repository.py")
    print("\n2. Update src/infrastructure/repositories/__init__.py")
    print("   - Remove imports for Block[1-4]ConditionPresetRepository")
    print("   - Remove from __all__ list")
