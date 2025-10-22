"""
Unified Database Migration: Rename months columns to days

이 스크립트는 preset 테이블들의 *_months 컬럼을 *_days로 변경합니다.

배경:
  - 기존에는 개월 단위로 신고거래량/신고가 기간을 설정했지만,
    더 정확한 계산을 위해 달력 기준 일수로 변경
  - 예: 3개월 → 90일, 6개월 → 180일, 12개월 → 365일

변경사항:
  seed_condition_preset:
    - *_volume_high_months → *_volume_high_days (block1/2/3/4)
    - *_price_high_months → *_price_high_days (block1/2/3/4)

  redetection_condition_preset:
    - *_volume_high_months → *_volume_high_days (block1/2/3/4)
    - *_price_high_months → *_price_high_days (block1/2/3/4)

참고:
  - high_above_ma 제거와 cooldown→min_start_interval 변경은 이미 완료됨

실행방법:
    python migrations/migrate_unified_schema_update.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def migrate():
    db_path = Path("data/database/stock_data.db")

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        return False

    print("=" * 80)
    print(f"  Unified Schema Migration")
    print(f"  Database: {db_path}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 1. seed_condition_preset 마이그레이션
            print("\n[1/2] Migrating seed_condition_preset table...")
            migrate_seed_condition_preset(cursor)

            # 2. redetection_condition_preset 마이그레이션
            print("\n[2/2] Migrating redetection_condition_preset table...")
            migrate_redetection_condition_preset(cursor)

            conn.commit()

            # 검증
            print("\n" + "=" * 80)
            print("  Verification")
            print("=" * 80)
            verify_migration(cursor)

            print("\n" + "=" * 80)
            print("  [SUCCESS] Migration completed successfully!")
            print("=" * 80)
            return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_seed_condition_preset(cursor):
    """
    seed_condition_preset 테이블 마이그레이션
    - months → days
    (high_above_ma와 cooldown_days는 이미 처리됨)
    """

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM seed_condition_preset")
    old_columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    print(f"     Found {len(data)} rows")

    # 컬럼 이름 매핑 (months → days만)
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

    # 새 컬럼 리스트 생성 (이름 변경 적용)
    new_columns = [column_rename_map.get(col, col) for col in old_columns]

    # 임시 테이블 생성
    print("   - Creating new table with updated schema...")
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
            block2_min_start_interval_days INTEGER,
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
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)

    # 데이터 복사 (컬럼 매핑 적용)
    print("   - Copying data with column mapping...")
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
    """
    redetection_condition_preset 테이블 마이그레이션
    - months → days (min_start_interval_days는 이미 존재)
    """

    # 기존 데이터 백업
    print("   - Backing up existing data...")
    cursor.execute("SELECT * FROM redetection_condition_preset")
    old_columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    print(f"     Found {len(data)} rows")

    # 컬럼 이름 매핑 (cooldown은 이미 min_start_interval_days로 되어 있음)
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

    # 새 컬럼 리스트 생성
    new_columns = [column_rename_map.get(col, col) for col in old_columns]

    # 임시 테이블 생성
    print("   - Creating new table with updated schema...")
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
            block1_min_start_interval_days INTEGER NOT NULL,
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
            block2_min_start_interval_days INTEGER,
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
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            UNIQUE (name)
        )
    """)

    # 데이터 복사
    print("   - Copying data with column mapping...")
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


def verify_migration(cursor):
    """마이그레이션 검증"""

    # seed_condition_preset 검증
    print("\n1. seed_condition_preset verification:")
    cursor.execute("PRAGMA table_info(seed_condition_preset)")
    seed_cols = [row[1] for row in cursor.fetchall()]

    # 제거되어야 할 컬럼들 (months)
    removed_cols = ['block1_entry_volume_high_months', 'block1_entry_price_high_months',
                    'block2_entry_volume_high_months', 'block2_entry_price_high_months',
                    'block3_entry_volume_high_months', 'block3_entry_price_high_months',
                    'block4_entry_volume_high_months', 'block4_entry_price_high_months']
    for col in removed_cols:
        if col not in seed_cols:
            print(f"   [OK] {col} removed")
        else:
            print(f"   [ERROR] {col} still exists!")

    # 새로 생성되어야 할 컬럼들 (days)
    new_cols = ['block1_entry_volume_high_days', 'block1_entry_price_high_days',
                'block2_entry_volume_high_days', 'block2_entry_price_high_days',
                'block3_entry_volume_high_days', 'block3_entry_price_high_days',
                'block4_entry_volume_high_days', 'block4_entry_price_high_days']
    for col in new_cols:
        if col in seed_cols:
            print(f"   [OK] {col} exists")
        else:
            print(f"   [ERROR] {col} missing!")

    # redetection_condition_preset 검증
    print("\n2. redetection_condition_preset verification:")
    cursor.execute("PRAGMA table_info(redetection_condition_preset)")
    redetect_cols = [row[1] for row in cursor.fetchall()]

    # 제거되어야 할 컬럼들
    removed_cols = ['block1_entry_volume_high_months', 'block1_entry_price_high_months',
                    'block2_entry_volume_high_months', 'block2_entry_price_high_months',
                    'block3_entry_volume_high_months', 'block3_entry_price_high_months',
                    'block4_entry_volume_high_months', 'block4_entry_price_high_months']
    for col in removed_cols:
        if col not in redetect_cols:
            print(f"   [OK] {col} removed")
        else:
            print(f"   [ERROR] {col} still exists!")

    # 새로 생성되어야 할 컬럼들
    new_cols = ['block1_entry_volume_high_days', 'block1_entry_price_high_days',
                'block2_entry_volume_high_days', 'block2_entry_price_high_days',
                'block3_entry_volume_high_days', 'block3_entry_price_high_days',
                'block4_entry_volume_high_days', 'block4_entry_price_high_days']
    for col in new_cols:
        if col in redetect_cols:
            print(f"   [OK] {col} exists")
        else:
            print(f"   [ERROR] {col} missing!")

    # 데이터 확인
    print("\n3. Data integrity:")
    cursor.execute("SELECT COUNT(*) FROM seed_condition_preset")
    seed_count = cursor.fetchone()[0]
    print(f"   seed_condition_preset: {seed_count} rows")

    cursor.execute("SELECT COUNT(*) FROM redetection_condition_preset")
    redetect_count = cursor.fetchone()[0]
    print(f"   redetection_condition_preset: {redetect_count} rows")


if __name__ == "__main__":
    import sys
    success = migrate()
    sys.exit(0 if success else 1)
