"""
마이그레이션: lookback_min/max_candles 파라미터 추가

배경:
- Block2-6 탐지 시 이전 블록이 일정 범위 내에 존재하는지 검증하는 기능 추가
- 이전 블록이 너무 오래전에 발생했거나 너무 최근에 발생한 경우 후보에서 제외

변경사항:
- 각 블록에 lookback_min_candles, lookback_max_candles 추가
- Block2~6의 모든 블록에 적용
- SeedConditionPreset 및 RedetectionConditionPreset 양쪽 모두

새 컬럼:
- blockN_lookback_min_candles: BlockN 후보일 기준 과거 최소 캔들 수 (null=체크 안함)
- blockN_lookback_max_candles: BlockN 후보일 기준 과거 최대 캔들 수 (null=체크 안함)

의미:
- lookback_min_candles=1: 후보일 기준 최소 1개 캔들 전에 이전 블록이 있어야 함
- lookback_max_candles=150: 후보일 기준 최대 150개 캔들 전까지 이전 블록이 있어야 함
- null: 해당 검증을 수행하지 않음

실행방법:
    # 백업 필수!
    copy data\database\stock_data.db data\database\stock_data_backup_lookback.db
    python migrations/migrate_add_lookback_candles.py
"""

import sqlite3
from pathlib import Path


def migrate():
    db_path = Path("data/database/stock_data.db")

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        return

    print(f"=== Adding lookback parameters to {db_path} ===\n")

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
        print("\n다음 단계:")
        print("1. python scripts/preset_management/update_presets_from_yaml.py  # YAML → DB 동기화")


def migrate_seed_condition_preset(cursor):
    """SeedConditionPreset 테이블에 lookback 파라미터 추가"""

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM seed_condition_preset")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    # 임시 테이블 생성
    print("   - Creating new table with lookback columns...")
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
            block1_min_start_interval_days INTEGER NOT NULL,
            block1_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block2_volume_ratio FLOAT,
            block2_low_price_margin FLOAT,
            block2_min_candles_from_block INTEGER,
            block2_max_candles_from_block INTEGER,
            block2_lookback_min_candles INTEGER,
            block2_lookback_max_candles INTEGER,
            block2_entry_surge_rate FLOAT,
            block2_entry_ma_period INTEGER,
            block2_entry_max_deviation_ratio FLOAT,
            block2_entry_min_trading_value FLOAT,
            block2_entry_volume_high_days INTEGER,
            block2_entry_volume_spike_ratio FLOAT,
            block2_entry_price_high_days INTEGER,
            block2_exit_condition_type VARCHAR(50),
            block2_exit_ma_period INTEGER,
            block2_min_start_interval_days INTEGER,
            block2_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block3_volume_ratio FLOAT,
            block3_low_price_margin FLOAT,
            block3_min_candles_from_block INTEGER,
            block3_max_candles_from_block INTEGER,
            block3_lookback_min_candles INTEGER,
            block3_lookback_max_candles INTEGER,
            block3_entry_surge_rate FLOAT,
            block3_entry_ma_period INTEGER,
            block3_entry_max_deviation_ratio FLOAT,
            block3_entry_min_trading_value FLOAT,
            block3_entry_volume_high_days INTEGER,
            block3_entry_volume_spike_ratio FLOAT,
            block3_entry_price_high_days INTEGER,
            block3_exit_condition_type VARCHAR(50),
            block3_exit_ma_period INTEGER,
            block3_min_start_interval_days INTEGER,
            block3_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block4_volume_ratio FLOAT,
            block4_low_price_margin FLOAT,
            block4_min_candles_from_block INTEGER,
            block4_max_candles_from_block INTEGER,
            block4_lookback_min_candles INTEGER,
            block4_lookback_max_candles INTEGER,
            block4_entry_surge_rate FLOAT,
            block4_entry_ma_period INTEGER,
            block4_entry_max_deviation_ratio FLOAT,
            block4_entry_min_trading_value FLOAT,
            block4_entry_volume_high_days INTEGER,
            block4_entry_volume_spike_ratio FLOAT,
            block4_entry_price_high_days INTEGER,
            block4_exit_condition_type VARCHAR(50),
            block4_exit_ma_period INTEGER,
            block4_min_start_interval_days INTEGER,
            block4_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block5_volume_ratio FLOAT,
            block5_low_price_margin FLOAT,
            block5_min_candles_from_block INTEGER,
            block5_max_candles_from_block INTEGER,
            block5_lookback_min_candles INTEGER,
            block5_lookback_max_candles INTEGER,
            block5_entry_surge_rate FLOAT,
            block5_entry_ma_period INTEGER,
            block5_entry_max_deviation_ratio FLOAT,
            block5_entry_min_trading_value FLOAT,
            block5_entry_volume_high_days INTEGER,
            block5_entry_volume_spike_ratio FLOAT,
            block5_entry_price_high_days INTEGER,
            block5_exit_condition_type VARCHAR(50),
            block5_exit_ma_period INTEGER,
            block5_min_start_interval_days INTEGER,
            block5_auto_exit_on_next_block INTEGER DEFAULT 0 NOT NULL,
            block6_volume_ratio FLOAT,
            block6_low_price_margin FLOAT,
            block6_min_candles_from_block INTEGER,
            block6_max_candles_from_block INTEGER,
            block6_lookback_min_candles INTEGER,
            block6_lookback_max_candles INTEGER,
            block6_entry_surge_rate FLOAT,
            block6_entry_ma_period INTEGER,
            block6_entry_max_deviation_ratio FLOAT,
            block6_entry_min_trading_value FLOAT,
            block6_entry_volume_high_days INTEGER,
            block6_entry_volume_spike_ratio FLOAT,
            block6_entry_price_high_days INTEGER,
            block6_exit_condition_type VARCHAR(50),
            block6_exit_ma_period INTEGER,
            block6_min_start_interval_days INTEGER,
            block6_auto_exit_on_next_block INTEGER DEFAULT 0 NOT NULL,
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)

    # 데이터 복사 (기존 컬럼만 복사, 새 lookback 컬럼은 NULL)
    print("   - Copying data to new table...")
    if data:
        # 새 테이블의 컬럼 순서에 맞춰 기존 데이터를 매핑
        cursor.execute("SELECT * FROM seed_condition_preset_new LIMIT 0")
        new_columns = [desc[0] for desc in cursor.description]

        # 기존 컬럼과 새 컬럼을 매핑
        for row in data:
            row_dict = dict(zip(columns, row))
            # 새 컬럼에 대해 기존 값이 있으면 사용, 없으면 NULL
            values = [row_dict.get(col, None) for col in new_columns]
            placeholders = ', '.join(['?' for _ in new_columns])
            insert_sql = f"INSERT INTO seed_condition_preset_new ({', '.join(new_columns)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)

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
    """RedetectionConditionPreset 테이블에 lookback 파라미터 추가"""

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM redetection_condition_preset")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    # 임시 테이블 생성
    print("   - Creating new table with lookback columns...")
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
            block1_exit_condition_type VARCHAR(50) NOT NULL,
            block1_exit_ma_period INTEGER,
            block1_min_start_interval_days INTEGER NOT NULL,
            block1_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block1_tolerance_pct FLOAT NOT NULL,
            block1_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block1_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block2_volume_ratio FLOAT,
            block2_low_price_margin FLOAT,
            block2_min_candles_from_block INTEGER,
            block2_max_candles_from_block INTEGER,
            block2_lookback_min_candles INTEGER,
            block2_lookback_max_candles INTEGER,
            block2_entry_surge_rate FLOAT,
            block2_entry_ma_period INTEGER,
            block2_entry_max_deviation_ratio FLOAT,
            block2_entry_min_trading_value FLOAT,
            block2_entry_volume_high_days INTEGER,
            block2_entry_volume_spike_ratio FLOAT,
            block2_entry_price_high_days INTEGER,
            block2_exit_condition_type VARCHAR(50),
            block2_exit_ma_period INTEGER,
            block2_min_start_interval_days INTEGER,
            block2_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block2_tolerance_pct FLOAT NOT NULL,
            block2_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block2_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block3_volume_ratio FLOAT,
            block3_low_price_margin FLOAT,
            block3_min_candles_from_block INTEGER,
            block3_max_candles_from_block INTEGER,
            block3_lookback_min_candles INTEGER,
            block3_lookback_max_candles INTEGER,
            block3_entry_surge_rate FLOAT,
            block3_entry_ma_period INTEGER,
            block3_entry_max_deviation_ratio FLOAT,
            block3_entry_min_trading_value FLOAT,
            block3_entry_volume_high_days INTEGER,
            block3_entry_volume_spike_ratio FLOAT,
            block3_entry_price_high_days INTEGER,
            block3_exit_condition_type VARCHAR(50),
            block3_exit_ma_period INTEGER,
            block3_min_start_interval_days INTEGER,
            block3_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block3_tolerance_pct FLOAT NOT NULL,
            block3_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block3_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block4_volume_ratio FLOAT,
            block4_low_price_margin FLOAT,
            block4_min_candles_from_block INTEGER,
            block4_max_candles_from_block INTEGER,
            block4_lookback_min_candles INTEGER,
            block4_lookback_max_candles INTEGER,
            block4_entry_surge_rate FLOAT,
            block4_entry_ma_period INTEGER,
            block4_entry_max_deviation_ratio FLOAT,
            block4_entry_min_trading_value FLOAT,
            block4_entry_volume_high_days INTEGER,
            block4_entry_volume_spike_ratio FLOAT,
            block4_entry_price_high_days INTEGER,
            block4_exit_condition_type VARCHAR(50),
            block4_exit_ma_period INTEGER,
            block4_min_start_interval_days INTEGER,
            block4_auto_exit_on_next_block BOOLEAN NOT NULL DEFAULT 0,
            block4_tolerance_pct FLOAT NOT NULL,
            block4_redetection_min_days_after_seed INTEGER NOT NULL DEFAULT 0,
            block4_redetection_max_days_after_seed INTEGER NOT NULL DEFAULT 1825,
            block5_volume_ratio FLOAT,
            block5_low_price_margin FLOAT,
            block5_min_candles_from_block INTEGER,
            block5_max_candles_from_block INTEGER,
            block5_lookback_min_candles INTEGER,
            block5_lookback_max_candles INTEGER,
            block5_entry_surge_rate FLOAT,
            block5_entry_ma_period INTEGER,
            block5_entry_max_deviation_ratio FLOAT,
            block5_entry_min_trading_value FLOAT,
            block5_entry_volume_high_days INTEGER,
            block5_entry_volume_spike_ratio FLOAT,
            block5_entry_price_high_days INTEGER,
            block5_exit_condition_type VARCHAR(50),
            block5_exit_ma_period INTEGER,
            block5_min_start_interval_days INTEGER,
            block5_auto_exit_on_next_block INTEGER DEFAULT 0 NOT NULL,
            block5_tolerance_pct FLOAT DEFAULT 25.0 NOT NULL,
            block5_redetection_min_days_after_seed INTEGER DEFAULT 0 NOT NULL,
            block5_redetection_max_days_after_seed INTEGER DEFAULT 1825 NOT NULL,
            block6_volume_ratio FLOAT,
            block6_low_price_margin FLOAT,
            block6_min_candles_from_block INTEGER,
            block6_max_candles_from_block INTEGER,
            block6_lookback_min_candles INTEGER,
            block6_lookback_max_candles INTEGER,
            block6_entry_surge_rate FLOAT,
            block6_entry_ma_period INTEGER,
            block6_entry_max_deviation_ratio FLOAT,
            block6_entry_min_trading_value FLOAT,
            block6_entry_volume_high_days INTEGER,
            block6_entry_volume_spike_ratio FLOAT,
            block6_entry_price_high_days INTEGER,
            block6_exit_condition_type VARCHAR(50),
            block6_exit_ma_period INTEGER,
            block6_min_start_interval_days INTEGER,
            block6_auto_exit_on_next_block INTEGER DEFAULT 0 NOT NULL,
            block6_tolerance_pct FLOAT DEFAULT 30.0 NOT NULL,
            block6_redetection_min_days_after_seed INTEGER DEFAULT 0 NOT NULL,
            block6_redetection_max_days_after_seed INTEGER DEFAULT 1825 NOT NULL,
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)

    # 데이터 복사 (기존 컬럼만 복사, 새 lookback 컬럼은 NULL)
    print("   - Copying data to new table...")
    if data:
        # 새 테이블의 컬럼 순서에 맞춰 기존 데이터를 매핑
        cursor.execute("SELECT * FROM redetection_condition_preset_new LIMIT 0")
        new_columns = [desc[0] for desc in cursor.description]

        # 기존 컬럼과 새 컬럼을 매핑
        for row in data:
            row_dict = dict(zip(columns, row))
            # 새 컬럼에 대해 기존 값이 있으면 사용, 없으면 NULL
            values = [row_dict.get(col, None) for col in new_columns]
            placeholders = ', '.join(['?' for _ in new_columns])
            insert_sql = f"INSERT INTO redetection_condition_preset_new ({', '.join(new_columns)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)

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
