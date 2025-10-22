"""
Rename volume_high_months and price_high_months columns to _days

배경:
- 기존에는 개월 단위로 신고거래량/신고가 기간을 설정했지만,
  더 정확한 계산을 위해 달력 기준 일수로 변경
- 예: 3개월 -> 90일, 6개월 -> 180일, 12개월 -> 365일

변경사항:
- SeedConditionPreset: block1/2/3/4_entry_volume_high_months -> _days
- SeedConditionPreset: block1/2/3/4_entry_price_high_months -> _days
- RedetectionConditionPreset: block1/2/3/4_entry_volume_high_months -> _days
- RedetectionConditionPreset: block1/2/3/4_entry_price_high_months -> _days

실행방법:
    python migrations/migrate_rename_months_to_days.py
"""

import sqlite3
from pathlib import Path


def migrate():
    db_path = Path("data/database/stock_data.db")

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        return

    print(f"=== Renaming months columns to days in {db_path} ===\n")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 1. SeedConditionPreset 마이그레이션
        print("1. Migrating seed_condition_preset table...")
        migrate_seed_condition_preset(cursor)

        # 2. RedetectionConditionPreset 마이그레이션
        print("\n2. Migrating redetection_condition_preset table...")
        migrate_redetection_condition_preset(cursor)

        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")


def migrate_seed_condition_preset(cursor):
    """SeedConditionPreset 테이블에서 _months를 _days로 변경"""

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM seed_condition_preset")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    # 변경할 컬럼 매핑
    column_rename_map = {
        'block1_entry_volume_high_months': 'block1_entry_volume_high_days',
        'block1_entry_price_high_months': 'block1_entry_price_high_days',
        'block2_entry_volume_high_months': 'block2_entry_volume_high_days',
        'block2_entry_price_high_months': 'block2_entry_price_high_days',
        'block3_entry_volume_high_months': 'block3_entry_volume_high_days',
        'block3_entry_price_high_months': 'block3_entry_price_high_days',
        'block4_entry_volume_high_months': 'block4_entry_volume_high_days',
        'block4_entry_price_high_months': 'block4_entry_price_high_days',
    }

    # 새 컬럼 리스트
    new_columns = [column_rename_map.get(col, col) for col in columns]

    # 임시 테이블 생성
    print("   - Creating new table with _days columns...")
    cursor.execute("DROP TABLE IF EXISTS seed_condition_preset_new")
    cursor.execute("""
        CREATE TABLE seed_condition_preset_new (
            id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(500),
            block1_entry_surge_rate FLOAT,
            block1_entry_ma_period INTEGER NOT NULL,
            block1_entry_max_deviation_ratio FLOAT,
            block1_entry_min_trading_value FLOAT,
            block1_entry_volume_high_days INTEGER,
            block1_entry_volume_spike_ratio FLOAT,
            block1_entry_price_high_days INTEGER,
            block1_exit_condition_type VARCHAR(50) NOT NULL,
            block1_exit_ma_period INTEGER,
            block1_cooldown_days INTEGER NOT NULL,
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
            block2_entry_surge_rate FLOAT,
            block2_entry_ma_period INTEGER,
            block2_entry_max_deviation_ratio FLOAT,
            block2_entry_min_trading_value FLOAT,
            block2_entry_volume_high_days INTEGER,
            block2_entry_volume_spike_ratio FLOAT,
            block2_entry_price_high_days INTEGER,
            block2_exit_condition_type VARCHAR(50),
            block2_exit_ma_period INTEGER,
            block2_cooldown_days INTEGER,
            block3_entry_surge_rate FLOAT,
            block3_entry_ma_period INTEGER,
            block3_entry_max_deviation_ratio FLOAT,
            block3_entry_min_trading_value FLOAT,
            block3_entry_volume_high_days INTEGER,
            block3_entry_volume_spike_ratio FLOAT,
            block3_entry_price_high_days INTEGER,
            block3_exit_condition_type VARCHAR(50),
            block3_exit_ma_period INTEGER,
            block3_cooldown_days INTEGER,
            block4_entry_surge_rate FLOAT,
            block4_entry_ma_period INTEGER,
            block4_entry_max_deviation_ratio FLOAT,
            block4_entry_min_trading_value FLOAT,
            block4_entry_volume_high_days INTEGER,
            block4_entry_volume_spike_ratio FLOAT,
            block4_entry_price_high_days INTEGER,
            block4_exit_condition_type VARCHAR(50),
            block4_exit_ma_period INTEGER,
            block4_cooldown_days INTEGER,
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)

    # 데이터 복사
    print("   - Copying data to new table...")
    if data:
        placeholders = ', '.join(['?' for _ in new_columns])
        insert_sql = f"INSERT INTO seed_condition_preset_new ({', '.join(new_columns)}) VALUES ({placeholders})"

        for row in data:
            cursor.execute(insert_sql, row)

    # 테이블 교체
    print("   - Replacing old table...")
    cursor.execute("DROP TABLE seed_condition_preset")
    cursor.execute("ALTER TABLE seed_condition_preset_new RENAME TO seed_condition_preset")

    # 인덱스 재생성
    print("   - Re-creating indexes...")
    cursor.execute("CREATE UNIQUE INDEX ix_seed_condition_name ON seed_condition_preset (name)")
    cursor.execute("CREATE INDEX ix_seed_condition_active ON seed_condition_preset (is_active)")

    print(f"   [OK] Migrated {len(data)} rows")


def migrate_redetection_condition_preset(cursor):
    """RedetectionConditionPreset 테이블에서 _months를 _days로 변경"""

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM redetection_condition_preset")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    # 변경할 컬럼 매핑
    column_rename_map = {
        'block1_entry_volume_high_months': 'block1_entry_volume_high_days',
        'block1_entry_price_high_months': 'block1_entry_price_high_days',
        'block2_entry_volume_high_months': 'block2_entry_volume_high_days',
        'block2_entry_price_high_months': 'block2_entry_price_high_days',
        'block3_entry_volume_high_months': 'block3_entry_volume_high_days',
        'block3_entry_price_high_months': 'block3_entry_price_high_days',
        'block4_entry_volume_high_months': 'block4_entry_volume_high_days',
        'block4_entry_price_high_months': 'block4_entry_price_high_days',
    }

    # 새 컬럼 리스트
    new_columns = [column_rename_map.get(col, col) for col in columns]

    # 임시 테이블 생성
    print("   - Creating new table with _days columns...")
    cursor.execute("DROP TABLE IF EXISTS redetection_condition_preset_new")
    cursor.execute("""
        CREATE TABLE redetection_condition_preset_new (
            id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(500),
            block1_entry_surge_rate FLOAT,
            block1_entry_ma_period INTEGER NOT NULL,
            block1_entry_max_deviation_ratio FLOAT,
            block1_entry_min_trading_value FLOAT,
            block1_entry_volume_high_days INTEGER,
            block1_entry_volume_spike_ratio FLOAT,
            block1_entry_price_high_days INTEGER,
            block1_tolerance_pct FLOAT NOT NULL,
            block2_tolerance_pct FLOAT NOT NULL,
            block3_tolerance_pct FLOAT NOT NULL,
            block4_tolerance_pct FLOAT NOT NULL,
            block1_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block1_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block2_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block2_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block3_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block3_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block4_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block4_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block1_exit_condition_type VARCHAR(50) NOT NULL,
            block1_exit_ma_period INTEGER,
            block1_cooldown_days INTEGER NOT NULL,
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
            block2_entry_surge_rate FLOAT,
            block2_entry_ma_period INTEGER,
            block2_entry_max_deviation_ratio FLOAT,
            block2_entry_min_trading_value FLOAT,
            block2_entry_volume_high_days INTEGER,
            block2_entry_volume_spike_ratio FLOAT,
            block2_entry_price_high_days INTEGER,
            block2_exit_condition_type VARCHAR(50),
            block2_exit_ma_period INTEGER,
            block2_cooldown_days INTEGER,
            block3_entry_surge_rate FLOAT,
            block3_entry_ma_period INTEGER,
            block3_entry_max_deviation_ratio FLOAT,
            block3_entry_min_trading_value FLOAT,
            block3_entry_volume_high_days INTEGER,
            block3_entry_volume_spike_ratio FLOAT,
            block3_entry_price_high_days INTEGER,
            block3_exit_condition_type VARCHAR(50),
            block3_exit_ma_period INTEGER,
            block3_cooldown_days INTEGER,
            block4_entry_surge_rate FLOAT,
            block4_entry_ma_period INTEGER,
            block4_entry_max_deviation_ratio FLOAT,
            block4_entry_min_trading_value FLOAT,
            block4_entry_volume_high_days INTEGER,
            block4_entry_volume_spike_ratio FLOAT,
            block4_entry_price_high_days INTEGER,
            block4_exit_condition_type VARCHAR(50),
            block4_exit_ma_period INTEGER,
            block4_cooldown_days INTEGER,
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)

    # 데이터 복사
    print("   - Copying data to new table...")
    if data:
        placeholders = ', '.join(['?' for _ in new_columns])
        insert_sql = f"INSERT INTO redetection_condition_preset_new ({', '.join(new_columns)}) VALUES ({placeholders})"

        for row in data:
            cursor.execute(insert_sql, row)

    # 테이블 교체
    print("   - Replacing old table...")
    cursor.execute("DROP TABLE redetection_condition_preset")
    cursor.execute("ALTER TABLE redetection_condition_preset_new RENAME TO redetection_condition_preset")

    # 인덱스 재생성
    print("   - Re-creating indexes...")
    cursor.execute("CREATE UNIQUE INDEX ix_redetection_condition_name ON redetection_condition_preset (name)")
    cursor.execute("CREATE INDEX ix_redetection_condition_active ON redetection_condition_preset (is_active)")

    print(f"   [OK] Migrated {len(data)} rows")


if __name__ == "__main__":
    migrate()
