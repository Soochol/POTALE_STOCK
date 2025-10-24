"""
마이그레이션: min/max_candles 파라미터 이름 변경

배경:
- 기존: blockN_min_candles_after_blockM (예: block2_min_candles_after_block1)
- "after"라는 용어가 혼란을 야기 (Block1 시작일 포함 여부 불명확)
- 실제 구현은 Block1 시작일부터 카운트 (포함)

변경사항:
- blockN_min_candles_after_blockM → blockN_min_candles_from_block
- blockN_max_candles_after_blockM → blockN_max_candles_from_block
- Block2~6의 모든 파라미터에 적용
- SeedConditionPreset 및 RedetectionConditionPreset 양쪽 모두

의미:
- "from_block": 이전 블록 시작일부터 카운트한다는 명확한 의미
- 예: block2_min_candles_from_block=2 → Block1 시작일 포함하여 2개 캔들 이후부터

실행방법:
    # 백업 필수!
    copy data\\database\\stock_data.db data\\database\\stock_data_backup_candles_rename.db
    python migrations/migrate_rename_candles_from_block.py
"""

import sqlite3
from pathlib import Path


def migrate():
    db_path = Path("data/database/stock_data.db")

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        return

    print(f"=== Renaming candles parameters in {db_path} ===\n")

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
    """SeedConditionPreset 테이블에서 candles 파라미터 이름 변경"""

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM seed_condition_preset")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    # 변경할 컬럼 매핑
    column_rename_map = {
        'block2_min_candles_after_block1': 'block2_min_candles_from_block',
        'block2_max_candles_after_block1': 'block2_max_candles_from_block',
        'block3_min_candles_after_block2': 'block3_min_candles_from_block',
        'block3_max_candles_after_block2': 'block3_max_candles_from_block',
        'block4_min_candles_after_block3': 'block4_min_candles_from_block',
        'block4_max_candles_after_block3': 'block4_max_candles_from_block',
        'block5_min_candles_after_block4': 'block5_min_candles_from_block',
        'block5_max_candles_after_block4': 'block5_max_candles_from_block',
        'block6_min_candles_after_block5': 'block6_min_candles_from_block',
        'block6_max_candles_after_block5': 'block6_max_candles_from_block',
    }

    # 새 컬럼 리스트
    new_columns = [column_rename_map.get(col, col) for col in columns]

    # 임시 테이블 생성
    print("   - Creating new table with renamed columns...")
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
    """RedetectionConditionPreset 테이블에서 candles 파라미터 이름 변경"""

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM redetection_condition_preset")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    # 변경할 컬럼 매핑
    column_rename_map = {
        'block2_min_candles_after_block1': 'block2_min_candles_from_block',
        'block2_max_candles_after_block1': 'block2_max_candles_from_block',
        'block3_min_candles_after_block2': 'block3_min_candles_from_block',
        'block3_max_candles_after_block2': 'block3_max_candles_from_block',
        'block4_min_candles_after_block3': 'block4_min_candles_from_block',
        'block4_max_candles_after_block3': 'block4_max_candles_from_block',
        'block5_min_candles_after_block4': 'block5_min_candles_from_block',
        'block5_max_candles_after_block4': 'block5_max_candles_from_block',
        'block6_min_candles_after_block5': 'block6_min_candles_from_block',
        'block6_max_candles_after_block5': 'block6_max_candles_from_block',
    }

    # 새 컬럼 리스트
    new_columns = [column_rename_map.get(col, col) for col in columns]

    # 임시 테이블 생성
    print("   - Creating new table with renamed columns...")
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
