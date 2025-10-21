"""
Migration: Change entry condition fields to nullable in preset tables

This migration changes 4 entry condition fields from NOT NULL to nullable
to align DB schema with Checker logic that treats None as "skip condition".

Background:
- Checker logic uses `if value is not None:` to skip conditions
- But DB enforced NOT NULL for surge_rate, deviation_ratio, min_trading_value, volume_spike_ratio
- This inconsistency prevented flexible condition configuration via YAML

Changes (both SeedConditionPreset and RedetectionConditionPreset):
- block1_entry_surge_rate: nullable=False → nullable=True
- block1_entry_max_deviation_ratio: nullable=False → nullable=True
- block1_entry_min_trading_value: nullable=False → nullable=True
- block1_entry_volume_spike_ratio: nullable=False → nullable=True

Strategy:
SQLite doesn't support ALTER COLUMN to change nullable constraint.
We need to recreate tables with new schema:
1. Create temporary table with new schema
2. Copy all data
3. Drop old table
4. Rename temporary table
5. Recreate indexes

Usage:
    python migrations/migrate_nullable_entry_conditions.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def migrate():
    """Migrate preset tables to make entry conditions nullable"""
    db = DatabaseConnection()

    print("=" * 80)
    print("Migration: Make entry conditions nullable in preset tables")
    print("=" * 80)

    with db.session_scope() as session:
        # ========================================
        # 1. Migrate seed_condition_preset table
        # ========================================
        print("\n[1/2] Migrating seed_condition_preset table...")

        # Drop temporary table if exists (from previous failed migration)
        print("  - Cleaning up any previous failed migration...")
        session.execute(text("DROP TABLE IF EXISTS seed_condition_preset_new"))

        # Create temporary table with new schema
        print("  - Creating temporary table with new schema...")
        session.execute(text("""
            CREATE TABLE seed_condition_preset_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description VARCHAR(500),

                -- Block1 진입 조건 (nullable 변경)
                block1_entry_surge_rate FLOAT,  -- nullable=True
                block1_entry_ma_period INTEGER NOT NULL,
                block1_entry_high_above_ma INTEGER DEFAULT 1,
                block1_entry_max_deviation_ratio FLOAT,  -- nullable=True
                block1_entry_min_trading_value FLOAT,  -- nullable=True
                block1_entry_volume_high_months INTEGER,
                block1_entry_volume_spike_ratio FLOAT,  -- nullable=True
                block1_entry_price_high_months INTEGER,

                -- 종료 조건
                block1_exit_condition_type VARCHAR(50) NOT NULL,
                block1_exit_ma_period INTEGER,

                -- 시스템
                block1_cooldown_days INTEGER NOT NULL DEFAULT 20,

                -- Block2/3/4 추가 조건
                block2_volume_ratio FLOAT,
                block2_low_price_margin FLOAT,
                block2_min_candles_after_block1 INTEGER,
                block2_max_candles_after_block1 INTEGER,

                block3_volume_ratio FLOAT,
                block3_low_price_margin FLOAT,
                block3_min_candles_after_block2 INTEGER,
                block3_max_candles_after_block2 INTEGER,

                block4_volume_ratio FLOAT,
                block4_low_price_margin FLOAT,
                block4_min_candles_after_block3 INTEGER,
                block4_max_candles_after_block3 INTEGER,

                -- Block2/3/4 전용 파라미터
                block2_entry_surge_rate FLOAT,
                block2_entry_ma_period INTEGER,
                block2_entry_high_above_ma INTEGER,
                block2_entry_max_deviation_ratio FLOAT,
                block2_entry_min_trading_value FLOAT,
                block2_entry_volume_high_months INTEGER,
                block2_entry_volume_spike_ratio FLOAT,
                block2_entry_price_high_months INTEGER,
                block2_exit_condition_type VARCHAR(50),
                block2_exit_ma_period INTEGER,
                block2_cooldown_days INTEGER,

                block3_entry_surge_rate FLOAT,
                block3_entry_ma_period INTEGER,
                block3_entry_high_above_ma INTEGER,
                block3_entry_max_deviation_ratio FLOAT,
                block3_entry_min_trading_value FLOAT,
                block3_entry_volume_high_months INTEGER,
                block3_entry_volume_spike_ratio FLOAT,
                block3_entry_price_high_months INTEGER,
                block3_exit_condition_type VARCHAR(50),
                block3_exit_ma_period INTEGER,
                block3_cooldown_days INTEGER,

                block4_entry_surge_rate FLOAT,
                block4_entry_ma_period INTEGER,
                block4_entry_high_above_ma INTEGER,
                block4_entry_max_deviation_ratio FLOAT,
                block4_entry_min_trading_value FLOAT,
                block4_entry_volume_high_months INTEGER,
                block4_entry_volume_spike_ratio FLOAT,
                block4_entry_price_high_months INTEGER,
                block4_exit_condition_type VARCHAR(50),
                block4_exit_ma_period INTEGER,
                block4_cooldown_days INTEGER,

                -- 메타데이터
                is_active INTEGER DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))

        # Copy data
        print("  - Copying data from old table...")
        session.execute(text("""
            INSERT INTO seed_condition_preset_new
            SELECT * FROM seed_condition_preset
        """))

        # Drop old table
        print("  - Dropping old table...")
        session.execute(text("DROP TABLE seed_condition_preset"))

        # Rename new table
        print("  - Renaming new table...")
        session.execute(text("ALTER TABLE seed_condition_preset_new RENAME TO seed_condition_preset"))

        # Recreate indexes
        print("  - Recreating indexes...")
        session.execute(text("CREATE UNIQUE INDEX ix_seed_condition_name ON seed_condition_preset(name)"))
        session.execute(text("CREATE INDEX ix_seed_condition_active ON seed_condition_preset(is_active)"))

        print("  [OK] seed_condition_preset migration completed")

        # ========================================
        # 2. Migrate redetection_condition_preset table
        # ========================================
        print("\n[2/2] Migrating redetection_condition_preset table...")

        # Drop temporary table if exists (from previous failed migration)
        print("  - Cleaning up any previous failed migration...")
        session.execute(text(
            "DROP TABLE IF EXISTS redetection_condition_preset_new"
        ))

        # Create temporary table with new schema
        print("  - Creating temporary table with new schema...")
        session.execute(text("""
            CREATE TABLE redetection_condition_preset_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description VARCHAR(500),

                -- Block1 진입 조건 (nullable 변경)
                block1_entry_surge_rate FLOAT,  -- nullable=True
                block1_entry_ma_period INTEGER NOT NULL,
                block1_entry_high_above_ma INTEGER DEFAULT 1,
                block1_entry_max_deviation_ratio FLOAT,  -- nullable=True
                block1_entry_min_trading_value FLOAT,  -- nullable=True
                block1_entry_volume_high_months INTEGER,
                block1_entry_volume_spike_ratio FLOAT,  -- nullable=True
                block1_entry_price_high_months INTEGER,

                -- 재탐지 전용: 가격 범위
                block1_tolerance_pct FLOAT NOT NULL DEFAULT 10.0,
                block2_tolerance_pct FLOAT NOT NULL DEFAULT 15.0,
                block3_tolerance_pct FLOAT NOT NULL DEFAULT 20.0,
                block4_tolerance_pct FLOAT NOT NULL DEFAULT 25.0,

                -- 재탐지 전용: 기간 범위
                block1_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
                block1_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
                block2_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
                block2_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
                block3_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
                block3_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
                block4_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
                block4_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,

                -- 종료 조건
                block1_exit_condition_type VARCHAR(50) NOT NULL,
                block1_exit_ma_period INTEGER,

                -- 시스템
                block1_cooldown_days INTEGER NOT NULL DEFAULT 20,

                -- Block2/3/4 추가 조건
                block2_volume_ratio FLOAT,
                block2_low_price_margin FLOAT,

                block3_volume_ratio FLOAT,
                block3_low_price_margin FLOAT,

                block4_volume_ratio FLOAT,
                block4_low_price_margin FLOAT,

                -- Block2/3/4 전용 파라미터
                block2_entry_surge_rate FLOAT,
                block2_entry_ma_period INTEGER,
                block2_entry_high_above_ma INTEGER,
                block2_entry_max_deviation_ratio FLOAT,
                block2_entry_min_trading_value FLOAT,
                block2_entry_volume_high_months INTEGER,
                block2_entry_volume_spike_ratio FLOAT,
                block2_entry_price_high_months INTEGER,
                block2_exit_condition_type VARCHAR(50),
                block2_exit_ma_period INTEGER,
                block2_cooldown_days INTEGER,

                block3_entry_surge_rate FLOAT,
                block3_entry_ma_period INTEGER,
                block3_entry_high_above_ma INTEGER,
                block3_entry_max_deviation_ratio FLOAT,
                block3_entry_min_trading_value FLOAT,
                block3_entry_volume_high_months INTEGER,
                block3_entry_volume_spike_ratio FLOAT,
                block3_entry_price_high_months INTEGER,
                block3_exit_condition_type VARCHAR(50),
                block3_exit_ma_period INTEGER,
                block3_cooldown_days INTEGER,

                block4_entry_surge_rate FLOAT,
                block4_entry_ma_period INTEGER,
                block4_entry_high_above_ma INTEGER,
                block4_entry_max_deviation_ratio FLOAT,
                block4_entry_min_trading_value FLOAT,
                block4_entry_volume_high_months INTEGER,
                block4_entry_volume_spike_ratio FLOAT,
                block4_entry_price_high_months INTEGER,
                block4_exit_condition_type VARCHAR(50),
                block4_exit_ma_period INTEGER,
                block4_cooldown_days INTEGER,

                -- 메타데이터
                is_active INTEGER DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))

        # Copy data
        print("  - Copying data from old table...")
        session.execute(text("""
            INSERT INTO redetection_condition_preset_new
            SELECT * FROM redetection_condition_preset
        """))

        # Drop old table
        print("  - Dropping old table...")
        session.execute(text("DROP TABLE redetection_condition_preset"))

        # Rename new table
        print("  - Renaming new table...")
        session.execute(text("ALTER TABLE redetection_condition_preset_new RENAME TO redetection_condition_preset"))

        # Recreate indexes
        print("  - Recreating indexes...")
        session.execute(text("CREATE UNIQUE INDEX ix_redetection_condition_name ON redetection_condition_preset(name)"))
        session.execute(text("CREATE INDEX ix_redetection_condition_active ON redetection_condition_preset(is_active)"))

        print("  [OK] redetection_condition_preset migration completed")

        # Commit changes
        session.commit()

        # Verify changes
        print("\n" + "=" * 80)
        print("Verification")
        print("=" * 80)

        # Check seed_condition_preset
        result = session.execute(text("PRAGMA table_info(seed_condition_preset)")).fetchall()
        print("\n[seed_condition_preset] Column nullability:")
        for row in result:
            col_name = row[1]
            is_not_null = row[3]  # 0=nullable, 1=NOT NULL
            if 'surge_rate' in col_name or 'deviation' in col_name or 'trading_value' in col_name or 'spike_ratio' in col_name:
                nullable_status = "NOT NULL" if is_not_null else "nullable"
                print(f"  - {col_name}: {nullable_status}")

        # Check redetection_condition_preset
        result = session.execute(text("PRAGMA table_info(redetection_condition_preset)")).fetchall()
        print("\n[redetection_condition_preset] Column nullability:")
        for row in result:
            col_name = row[1]
            is_not_null = row[3]
            if 'surge_rate' in col_name or 'deviation' in col_name or 'trading_value' in col_name or 'spike_ratio' in col_name:
                nullable_status = "NOT NULL" if is_not_null else "nullable"
                print(f"  - {col_name}: {nullable_status}")

        # Count records
        seed_count = session.execute(text("SELECT COUNT(*) FROM seed_condition_preset")).scalar()
        redetect_count = session.execute(text("SELECT COUNT(*) FROM redetection_condition_preset")).scalar()

        print("\n[OK] Data preserved:")
        print(f"  - seed_condition_preset: {seed_count} records")
        print(f"  - redetection_condition_preset: {redetect_count} records")

    print("\n" + "=" * 80)
    print("Migration completed successfully!")
    print("=" * 80)
    print("\nChanges:")
    print("[OK] 4 fields changed to nullable in both tables:")
    print("  - block1_entry_surge_rate")
    print("  - block1_entry_max_deviation_ratio")
    print("  - block1_entry_min_trading_value")
    print("  - block1_entry_volume_spike_ratio")
    print("\nBenefit:")
    print("  Now you can set these fields to NULL in YAML to skip conditions!")
    print("\nNext steps:")
    print("  1. Test with existing YAML configurations")
    print("  2. (Optional) Add NULL values to YAML to test condition skipping")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
