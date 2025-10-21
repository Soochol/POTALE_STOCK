"""
Migration: Add peak_volume column to block1_detection table

This migration adds the peak_volume (BigInteger) column to the block1_detection table.
This field was previously defined in the Block1Detection entity but missing from the database model.

Background:
- peak_volume tracks the highest trading volume during Block1 period
- It's already being updated in Block1Detection.update_peak() method
- But it wasn't being persisted to the database

Changes:
- Add peak_volume column (BigInteger, nullable)
- No data migration needed (existing records will have NULL, which is correct for historical data)

Usage:
    python migrations/migrate_add_peak_volume_to_block1.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def migrate():
    """Add peak_volume column to block1_detection table"""
    db = DatabaseConnection()

    print("=" * 60)
    print("Migration: Add peak_volume to block1_detection")
    print("=" * 60)

    with db.session_scope() as session:
        # Check if column already exists
        result = session.execute(text("PRAGMA table_info(block1_detection)")).fetchall()
        columns = [row[1] for row in result]

        if 'peak_volume' in columns:
            print("[OK] peak_volume column already exists. Skipping migration.")
            return

        print("\n1. Adding peak_volume column...")
        session.execute(text("""
            ALTER TABLE block1_detection
            ADD COLUMN peak_volume INTEGER
        """))
        session.commit()
        print("   [OK] peak_volume column added")

        # Verify the change
        print("\n2. Verifying column...")
        result = session.execute(text("PRAGMA table_info(block1_detection)")).fetchall()
        columns = [row[1] for row in result]

        if 'peak_volume' in columns:
            print("   [OK] Verification successful")
        else:
            print("   [ERROR] Verification failed - column not found!")
            return

        # Show some statistics
        print("\n3. Statistics:")
        count = session.execute(text("SELECT COUNT(*) FROM block1_detection")).scalar()
        print(f"   - Total Block1 records: {count}")
        print(f"   - All records will have peak_volume=NULL (expected for historical data)")

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
