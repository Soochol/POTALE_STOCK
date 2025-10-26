"""
DB Migration: Add Virtual Block System Fields

Adds columns to support the Virtual Block System:
- yaml_type: Original YAML block_type definition (immutable)
- logical_level: Actual surge order for cross-stock comparison
- pattern_sequence: Physical creation order within pattern
- is_virtual: Flag for spot-skipped virtual blocks

Date: 2025-10-26
Author: Claude
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def migrate_add_virtual_block_fields(db_path: str):
    """
    Add virtual block system fields to dynamic_block_detection table.

    New Columns:
    - yaml_type: INTEGER (YAML 정의 block_type, 불변)
    - logical_level: INTEGER (실제 급등 순서: 1, 2, 3, ...)
    - pattern_sequence: INTEGER (패턴 내 생성 순서: 1, 2, 3, ...)
    - is_virtual: INTEGER (0/1, Spot으로 스킵된 가상 블록 여부)

    Args:
        db_path: Database file path
    """
    print(f"[*] Migration: Add Virtual Block System Fields")
    print(f"    Database: {db_path}")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Check if columns already exist
        print("[*] Checking existing schema...")
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
        columns = {row[1] for row in cursor.fetchall()}

        new_columns = {
            'yaml_type': False,
            'logical_level': False,
            'pattern_sequence': False,
            'is_virtual': False
        }

        for col in new_columns:
            if col in columns:
                print(f"    [!] Column '{col}' already exists, skipping")
                new_columns[col] = True

        # Step 2: Add new columns
        print("\n[*] Adding new columns...")

        if not new_columns['yaml_type']:
            print("   Adding 'yaml_type' column...")
            cursor.execute("""
                ALTER TABLE dynamic_block_detection
                ADD COLUMN yaml_type INTEGER DEFAULT 0
            """)
            print("    [OK] yaml_type added")

        if not new_columns['logical_level']:
            print("   Adding 'logical_level' column...")
            cursor.execute("""
                ALTER TABLE dynamic_block_detection
                ADD COLUMN logical_level INTEGER DEFAULT 0
            """)
            print("    [OK] logical_level added")

        if not new_columns['pattern_sequence']:
            print("   Adding 'pattern_sequence' column...")
            cursor.execute("""
                ALTER TABLE dynamic_block_detection
                ADD COLUMN pattern_sequence INTEGER DEFAULT 0
            """)
            print("    [OK] pattern_sequence added")

        if not new_columns['is_virtual']:
            print("   Adding 'is_virtual' column...")
            cursor.execute("""
                ALTER TABLE dynamic_block_detection
                ADD COLUMN is_virtual INTEGER DEFAULT 0
            """)
            print("    [OK] is_virtual added")

        # Step 3: Populate existing records with backward-compatible values
        print("\n[*] Populating existing records...")

        # Count records to update
        cursor.execute("SELECT COUNT(*) FROM dynamic_block_detection WHERE yaml_type = 0")
        count = cursor.fetchone()[0]
        print(f"   Found {count:,} records to update")

        if count > 0:
            # For existing records:
            # - yaml_type = block_type (원래 YAML 정의값)
            # - logical_level = block_type (기존 데이터는 순차적이라 가정)
            # - pattern_sequence = block_type (기존 데이터는 순차적이라 가정)
            # - is_virtual = 0 (기존 데이터는 모두 real 블록)

            cursor.execute("""
                UPDATE dynamic_block_detection
                SET
                    yaml_type = block_type,
                    logical_level = block_type,
                    pattern_sequence = block_type,
                    is_virtual = 0
                WHERE yaml_type = 0
            """)

            print(f"    [OK] Updated {count:,} records")
            print(f"      yaml_type = block_type")
            print(f"      logical_level = block_type")
            print(f"      pattern_sequence = block_type")
            print(f"      is_virtual = 0")
        else:
            print("   No records to update (all already migrated)")

        # Step 4: Verify migration
        print("\n[*] Verification:")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT yaml_type) as distinct_yaml_types,
                COUNT(DISTINCT logical_level) as distinct_levels,
                SUM(CASE WHEN is_virtual = 1 THEN 1 ELSE 0 END) as virtual_count
            FROM dynamic_block_detection
        """)
        total, distinct_yaml, distinct_levels, virtual_count = cursor.fetchone()

        print(f"   Total records: {total:,}")
        print(f"   Distinct yaml_types: {distinct_yaml}")
        print(f"   Distinct logical_levels: {distinct_levels}")
        print(f"   Virtual blocks: {virtual_count}")

        # Commit changes
        conn.commit()
        print("\n[OK] Migration completed successfully!")
        print("\n[*] New Schema:")
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
        for row in cursor.fetchall():
            col_id, name, col_type, not_null, default, pk = row
            if name in ['yaml_type', 'logical_level', 'pattern_sequence', 'is_virtual']:
                print(f"   {name}: {col_type} (default: {default})")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise

    finally:
        conn.close()


def main():
    """Run migration"""
    db_path = project_root / "data" / "database" / "stock_data.db"

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        print("        Please check the database path.")
        sys.exit(1)

    print("=" * 70)
    print("MIGRATION: Add Virtual Block System Fields")
    print("=" * 70)
    print()
    print("[!] WARNING: This migration will modify the database schema.")
    print("    Make sure you have a backup before proceeding!")
    print()
    print(f"   Database: {db_path}")
    print()

    # Ask for confirmation
    response = input("Proceed with migration? (yes/no): ").strip().lower()

    if response != 'yes':
        print("\n[CANCELLED] Migration cancelled.")
        sys.exit(0)

    print()

    # Run migration
    migrate_add_virtual_block_fields(str(db_path))

    print()
    print("=" * 70)
    print("[OK] Migration completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
