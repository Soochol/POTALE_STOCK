"""
Migration: Add redetection period columns to redetection_condition_preset table

This migration adds 8 new columns to support Seed-relative redetection periods:
- block1_redetection_min_days_after_seed
- block1_redetection_max_days_after_seed
- block2_redetection_min_days_after_seed
- block2_redetection_max_days_after_seed
- block3_redetection_min_days_after_seed
- block3_redetection_max_days_after_seed
- block4_redetection_min_days_after_seed
- block4_redetection_max_days_after_seed

Background:
- Previously, redetection period was hardcoded as 5 years (timedelta(days=5*365))
- Now each Block can have independent min/max periods based on its Seed occurrence date
- Default values: min=0, max=1825 (5 years) to maintain backward compatibility

Changes:
- Add 8 INTEGER columns with NOT NULL and default values
- No data migration needed (default values maintain current behavior)

Usage:
    python migrations/migrate_add_redetection_period_columns.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def migrate():
    """Add redetection period columns to redetection_condition_preset table"""
    db = DatabaseConnection()

    print("=" * 80)
    print("Migration: Add redetection period columns to redetection_condition_preset")
    print("=" * 80)

    with db.session_scope() as session:
        # Check if columns already exist
        result = session.execute(text("PRAGMA table_info(redetection_condition_preset)")).fetchall()
        columns = [row[1] for row in result]

        new_columns = [
            'block1_redetection_min_days_after_seed',
            'block1_redetection_max_days_after_seed',
            'block2_redetection_min_days_after_seed',
            'block2_redetection_max_days_after_seed',
            'block3_redetection_min_days_after_seed',
            'block3_redetection_max_days_after_seed',
            'block4_redetection_min_days_after_seed',
            'block4_redetection_max_days_after_seed',
        ]

        existing_new_columns = [col for col in new_columns if col in columns]
        if existing_new_columns:
            print(f"[OK] Columns already exist: {existing_new_columns}")
            print("    Skipping migration.")
            return

        print("\n1. Adding redetection period columns...")

        # Add Block1 period columns
        print("   - Adding Block1 redetection period columns...")
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block1_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0
        """))
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block1_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825
        """))

        # Add Block2 period columns
        print("   - Adding Block2 redetection period columns...")
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block2_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0
        """))
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block2_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825
        """))

        # Add Block3 period columns
        print("   - Adding Block3 redetection period columns...")
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block3_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0
        """))
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block3_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825
        """))

        # Add Block4 period columns
        print("   - Adding Block4 redetection period columns...")
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block4_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0
        """))
        session.execute(text("""
            ALTER TABLE redetection_condition_preset
            ADD COLUMN block4_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825
        """))

        session.commit()
        print("   [OK] All 8 columns added successfully")

        # Verify the changes
        print("\n2. Verifying columns...")
        result = session.execute(text("PRAGMA table_info(redetection_condition_preset)")).fetchall()
        columns = [row[1] for row in result]

        missing_columns = [col for col in new_columns if col not in columns]
        if missing_columns:
            print(f"   [ERROR] Verification failed - columns not found: {missing_columns}")
            return

        print("   [OK] All columns verified successfully")

        # Show some statistics
        print("\n3. Statistics:")
        count = session.execute(text("SELECT COUNT(*) FROM redetection_condition_preset")).scalar()
        print(f"   - Total redetection presets: {count}")
        print(f"   - Default values applied:")
        print(f"     * min_days_after_seed: 0 (재탐지 시작 = Seed 발생일 당일부터)")
        print(f"     * max_days_after_seed: 1825 (재탐지 종료 = Seed 발생일 + 5년)")

        # Show sample values
        if count > 0:
            print("\n4. Sample values from 'default_redetect' preset:")
            result = session.execute(text("""
                SELECT
                    block1_redetection_min_days_after_seed,
                    block1_redetection_max_days_after_seed,
                    block2_redetection_min_days_after_seed,
                    block2_redetection_max_days_after_seed
                FROM redetection_condition_preset
                WHERE name = 'default_redetect'
            """)).fetchone()

            if result:
                print(f"   - Block1: {result[0]}일 ~ {result[1]}일")
                print(f"   - Block2: {result[2]}일 ~ {result[3]}일")

    print("\n" + "=" * 80)
    print("Migration completed successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python scripts/update_presets_from_yaml.py")
    print("   (This will update the database with YAML values)")
    print("2. Test redetection with new period configuration")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
