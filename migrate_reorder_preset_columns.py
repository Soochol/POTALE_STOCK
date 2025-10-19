"""
DB Preset 테이블 컬럼 순서 재정렬 마이그레이션

목적:
- seed_condition_preset, redetection_condition_preset 테이블의 컬럼 순서를
  논리적이고 합리적인 순서로 재정렬

순서:
1. 메타데이터 (id, name, description)
2. Block1 (entry_* 8개 + exit_* 2개 + cooldown + tolerance)
3. Block2 (추가조건 3개 + entry_* 8개 + exit_* 2개 + cooldown + tolerance)
4. Block3 (추가조건 3개 + entry_* 8개 + exit_* 2개 + cooldown + tolerance)
5. Block4 (추가조건 3개 + entry_* 8개 + exit_* 2개 + cooldown + tolerance)
6. 시스템 메타데이터 (is_active, created_at, updated_at)
"""
import sqlite3
from pathlib import Path


def reorder_seed_condition_preset(db_path: str):
    """seed_condition_preset 테이블 컬럼 순서 재정렬"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("seed_condition_preset 테이블 재정렬 시작")
    print("=" * 80)

    # 1. 기존 데이터 백업
    cursor.execute("SELECT COUNT(*) FROM seed_condition_preset")
    row_count = cursor.fetchone()[0]
    print(f"\n기존 데이터: {row_count}건")

    # 2. 새로운 테이블 생성 (컬럼 순서 재정렬)
    cursor.execute("""
        CREATE TABLE seed_condition_preset_new (
            -- [메타데이터]
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(500),

            -- [Block1 - 기본 조건]
            block1_entry_surge_rate FLOAT NOT NULL,
            block1_entry_ma_period INTEGER NOT NULL,
            block1_entry_high_above_ma INTEGER,
            block1_entry_max_deviation_ratio FLOAT NOT NULL,
            block1_entry_min_trading_value FLOAT NOT NULL,
            block1_entry_volume_high_months INTEGER NOT NULL,
            block1_entry_volume_spike_ratio FLOAT NOT NULL,
            block1_entry_price_high_months INTEGER NOT NULL,
            block1_exit_condition_type VARCHAR(50) NOT NULL,
            block1_exit_ma_period INTEGER,
            block1_cooldown_days INTEGER NOT NULL,

            -- [Block2 - 추가조건 + 전용파라미터]
            block2_volume_ratio FLOAT,
            block2_low_price_margin FLOAT,
            block2_min_candles_after_block1 INTEGER,
            block2_entry_surge_rate REAL,
            block2_entry_ma_period INTEGER,
            block2_entry_high_above_ma INTEGER,
            block2_entry_max_deviation_ratio REAL,
            block2_entry_min_trading_value REAL,
            block2_entry_volume_high_months INTEGER,
            block2_entry_volume_spike_ratio REAL,
            block2_entry_price_high_months INTEGER,
            block2_exit_condition_type TEXT,
            block2_exit_ma_period INTEGER,
            block2_cooldown_days INTEGER,

            -- [Block3 - 추가조건 + 전용파라미터]
            block3_volume_ratio FLOAT,
            block3_low_price_margin FLOAT,
            block3_min_candles_after_block2 INTEGER,
            block3_entry_surge_rate REAL,
            block3_entry_ma_period INTEGER,
            block3_entry_high_above_ma INTEGER,
            block3_entry_max_deviation_ratio REAL,
            block3_entry_min_trading_value REAL,
            block3_entry_volume_high_months INTEGER,
            block3_entry_volume_spike_ratio REAL,
            block3_entry_price_high_months INTEGER,
            block3_exit_condition_type TEXT,
            block3_exit_ma_period INTEGER,
            block3_cooldown_days INTEGER,

            -- [Block4 - 추가조건 + 전용파라미터]
            block4_volume_ratio REAL DEFAULT 0.3,
            block4_low_price_margin REAL DEFAULT 10.0,
            block4_min_candles_after_block3 INTEGER DEFAULT 1,
            block4_entry_surge_rate REAL,
            block4_entry_ma_period INTEGER,
            block4_entry_high_above_ma INTEGER,
            block4_entry_max_deviation_ratio REAL,
            block4_entry_min_trading_value REAL,
            block4_entry_volume_high_months INTEGER,
            block4_entry_volume_spike_ratio REAL,
            block4_entry_price_high_months INTEGER,
            block4_exit_condition_type TEXT,
            block4_exit_ma_period INTEGER,
            block4_cooldown_days INTEGER,

            -- [시스템 메타데이터]
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)
    print("\n새 테이블 생성 완료 (컬럼 순서 재정렬)")

    # 3. 데이터 복사 (모든 컬럼 명시적으로 나열)
    cursor.execute("""
        INSERT INTO seed_condition_preset_new (
            id, name, description,
            block1_entry_surge_rate, block1_entry_ma_period, block1_entry_high_above_ma,
            block1_entry_max_deviation_ratio, block1_entry_min_trading_value,
            block1_entry_volume_high_months, block1_entry_volume_spike_ratio,
            block1_entry_price_high_months, block1_exit_condition_type,
            block1_exit_ma_period, block1_cooldown_days,
            block2_volume_ratio, block2_low_price_margin, block2_min_candles_after_block1,
            block2_entry_surge_rate, block2_entry_ma_period, block2_entry_high_above_ma,
            block2_entry_max_deviation_ratio, block2_entry_min_trading_value,
            block2_entry_volume_high_months, block2_entry_volume_spike_ratio,
            block2_entry_price_high_months, block2_exit_condition_type,
            block2_exit_ma_period, block2_cooldown_days,
            block3_volume_ratio, block3_low_price_margin, block3_min_candles_after_block2,
            block3_entry_surge_rate, block3_entry_ma_period, block3_entry_high_above_ma,
            block3_entry_max_deviation_ratio, block3_entry_min_trading_value,
            block3_entry_volume_high_months, block3_entry_volume_spike_ratio,
            block3_entry_price_high_months, block3_exit_condition_type,
            block3_exit_ma_period, block3_cooldown_days,
            block4_volume_ratio, block4_low_price_margin, block4_min_candles_after_block3,
            block4_entry_surge_rate, block4_entry_ma_period, block4_entry_high_above_ma,
            block4_entry_max_deviation_ratio, block4_entry_min_trading_value,
            block4_entry_volume_high_months, block4_entry_volume_spike_ratio,
            block4_entry_price_high_months, block4_exit_condition_type,
            block4_exit_ma_period, block4_cooldown_days,
            is_active, created_at, updated_at
        )
        SELECT
            id, name, description,
            block1_entry_surge_rate, block1_entry_ma_period, block1_entry_high_above_ma,
            block1_entry_max_deviation_ratio, block1_entry_min_trading_value,
            block1_entry_volume_high_months, block1_entry_volume_spike_ratio,
            block1_entry_price_high_months, block1_exit_condition_type,
            block1_exit_ma_period, block1_cooldown_days,
            block2_volume_ratio, block2_low_price_margin, block2_min_candles_after_block1,
            block2_entry_surge_rate, block2_entry_ma_period, block2_entry_high_above_ma,
            block2_entry_max_deviation_ratio, block2_entry_min_trading_value,
            block2_entry_volume_high_months, block2_entry_volume_spike_ratio,
            block2_entry_price_high_months, block2_exit_condition_type,
            block2_exit_ma_period, block2_cooldown_days,
            block3_volume_ratio, block3_low_price_margin, block3_min_candles_after_block2,
            block3_entry_surge_rate, block3_entry_ma_period, block3_entry_high_above_ma,
            block3_entry_max_deviation_ratio, block3_entry_min_trading_value,
            block3_entry_volume_high_months, block3_entry_volume_spike_ratio,
            block3_entry_price_high_months, block3_exit_condition_type,
            block3_exit_ma_period, block3_cooldown_days,
            block4_volume_ratio, block4_low_price_margin, block4_min_candles_after_block3,
            block4_entry_surge_rate, block4_entry_ma_period, block4_entry_high_above_ma,
            block4_entry_max_deviation_ratio, block4_entry_min_trading_value,
            block4_entry_volume_high_months, block4_entry_volume_spike_ratio,
            block4_entry_price_high_months, block4_exit_condition_type,
            block4_exit_ma_period, block4_cooldown_days,
            is_active, created_at, updated_at
        FROM seed_condition_preset
    """)
    print(f"데이터 복사 완료: {cursor.rowcount}건")

    # 4. 기존 테이블 삭제
    cursor.execute("DROP TABLE seed_condition_preset")
    print("기존 테이블 삭제 완료")

    # 5. 새 테이블 이름 변경
    cursor.execute("ALTER TABLE seed_condition_preset_new RENAME TO seed_condition_preset")
    print("새 테이블 이름 변경 완료")

    # 6. 검증
    cursor.execute("SELECT COUNT(*) FROM seed_condition_preset")
    new_row_count = cursor.fetchone()[0]
    match_status = "[OK]" if new_row_count == row_count else "[ERROR]"
    print(f"\n검증: {new_row_count}건 (기존 {row_count}건과 일치: {match_status})")

    conn.commit()
    conn.close()
    print("\n[OK] seed_condition_preset 재정렬 완료!\n")


def reorder_redetection_condition_preset(db_path: str):
    """redetection_condition_preset 테이블 컬럼 순서 재정렬"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("redetection_condition_preset 테이블 재정렬 시작")
    print("=" * 80)

    # 1. 기존 데이터 백업
    cursor.execute("SELECT COUNT(*) FROM redetection_condition_preset")
    row_count = cursor.fetchone()[0]
    print(f"\n기존 데이터: {row_count}건")

    # 2. 새로운 테이블 생성 (컬럼 순서 재정렬)
    cursor.execute("""
        CREATE TABLE redetection_condition_preset_new (
            -- [메타데이터]
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(500),

            -- [Block1 - 기본 조건]
            block1_entry_surge_rate FLOAT NOT NULL,
            block1_entry_ma_period INTEGER NOT NULL,
            block1_entry_high_above_ma INTEGER,
            block1_entry_max_deviation_ratio FLOAT NOT NULL,
            block1_entry_min_trading_value FLOAT NOT NULL,
            block1_entry_volume_high_months INTEGER NOT NULL,
            block1_entry_volume_spike_ratio FLOAT NOT NULL,
            block1_entry_price_high_months INTEGER NOT NULL,
            block1_exit_condition_type VARCHAR(50) NOT NULL,
            block1_exit_ma_period INTEGER,
            block1_cooldown_days INTEGER NOT NULL,
            block1_tolerance_pct FLOAT NOT NULL,

            -- [Block2 - 추가조건 + 전용파라미터]
            block2_volume_ratio FLOAT,
            block2_low_price_margin FLOAT,
            block2_min_candles_after_block1 INTEGER,
            block2_entry_surge_rate REAL,
            block2_entry_ma_period INTEGER,
            block2_entry_high_above_ma INTEGER,
            block2_entry_max_deviation_ratio REAL,
            block2_entry_min_trading_value REAL,
            block2_entry_volume_high_months INTEGER,
            block2_entry_volume_spike_ratio REAL,
            block2_entry_price_high_months INTEGER,
            block2_exit_condition_type TEXT,
            block2_exit_ma_period INTEGER,
            block2_cooldown_days INTEGER,
            block2_tolerance_pct FLOAT NOT NULL,

            -- [Block3 - 추가조건 + 전용파라미터]
            block3_volume_ratio FLOAT,
            block3_low_price_margin FLOAT,
            block3_min_candles_after_block2 INTEGER,
            block3_entry_surge_rate REAL,
            block3_entry_ma_period INTEGER,
            block3_entry_high_above_ma INTEGER,
            block3_entry_max_deviation_ratio REAL,
            block3_entry_min_trading_value REAL,
            block3_entry_volume_high_months INTEGER,
            block3_entry_volume_spike_ratio REAL,
            block3_entry_price_high_months INTEGER,
            block3_exit_condition_type TEXT,
            block3_exit_ma_period INTEGER,
            block3_cooldown_days INTEGER,
            block3_tolerance_pct FLOAT NOT NULL,

            -- [Block4 - 추가조건 + 전용파라미터]
            block4_volume_ratio REAL DEFAULT 0.3,
            block4_low_price_margin REAL DEFAULT 10.0,
            block4_min_candles_after_block3 INTEGER DEFAULT 1,
            block4_entry_surge_rate REAL,
            block4_entry_ma_period INTEGER,
            block4_entry_high_above_ma INTEGER,
            block4_entry_max_deviation_ratio REAL,
            block4_entry_min_trading_value REAL,
            block4_entry_volume_high_months INTEGER,
            block4_entry_volume_spike_ratio REAL,
            block4_entry_price_high_months INTEGER,
            block4_exit_condition_type TEXT,
            block4_exit_ma_period INTEGER,
            block4_cooldown_days INTEGER,
            block4_tolerance_pct REAL DEFAULT 25.0,

            -- [시스템 메타데이터]
            is_active INTEGER,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)
    print("\n새 테이블 생성 완료 (컬럼 순서 재정렬)")

    # 3. 데이터 복사
    cursor.execute("""
        INSERT INTO redetection_condition_preset_new (
            id, name, description,
            block1_entry_surge_rate, block1_entry_ma_period, block1_entry_high_above_ma,
            block1_entry_max_deviation_ratio, block1_entry_min_trading_value,
            block1_entry_volume_high_months, block1_entry_volume_spike_ratio,
            block1_entry_price_high_months, block1_exit_condition_type,
            block1_exit_ma_period, block1_cooldown_days, block1_tolerance_pct,
            block2_volume_ratio, block2_low_price_margin, block2_min_candles_after_block1,
            block2_entry_surge_rate, block2_entry_ma_period, block2_entry_high_above_ma,
            block2_entry_max_deviation_ratio, block2_entry_min_trading_value,
            block2_entry_volume_high_months, block2_entry_volume_spike_ratio,
            block2_entry_price_high_months, block2_exit_condition_type,
            block2_exit_ma_period, block2_cooldown_days, block2_tolerance_pct,
            block3_volume_ratio, block3_low_price_margin, block3_min_candles_after_block2,
            block3_entry_surge_rate, block3_entry_ma_period, block3_entry_high_above_ma,
            block3_entry_max_deviation_ratio, block3_entry_min_trading_value,
            block3_entry_volume_high_months, block3_entry_volume_spike_ratio,
            block3_entry_price_high_months, block3_exit_condition_type,
            block3_exit_ma_period, block3_cooldown_days, block3_tolerance_pct,
            block4_volume_ratio, block4_low_price_margin, block4_min_candles_after_block3,
            block4_entry_surge_rate, block4_entry_ma_period, block4_entry_high_above_ma,
            block4_entry_max_deviation_ratio, block4_entry_min_trading_value,
            block4_entry_volume_high_months, block4_entry_volume_spike_ratio,
            block4_entry_price_high_months, block4_exit_condition_type,
            block4_exit_ma_period, block4_cooldown_days, block4_tolerance_pct,
            is_active, created_at, updated_at
        )
        SELECT
            id, name, description,
            block1_entry_surge_rate, block1_entry_ma_period, block1_entry_high_above_ma,
            block1_entry_max_deviation_ratio, block1_entry_min_trading_value,
            block1_entry_volume_high_months, block1_entry_volume_spike_ratio,
            block1_entry_price_high_months, block1_exit_condition_type,
            block1_exit_ma_period, block1_cooldown_days, block1_tolerance_pct,
            block2_volume_ratio, block2_low_price_margin, block2_min_candles_after_block1,
            block2_entry_surge_rate, block2_entry_ma_period, block2_entry_high_above_ma,
            block2_entry_max_deviation_ratio, block2_entry_min_trading_value,
            block2_entry_volume_high_months, block2_entry_volume_spike_ratio,
            block2_entry_price_high_months, block2_exit_condition_type,
            block2_exit_ma_period, block2_cooldown_days, block2_tolerance_pct,
            block3_volume_ratio, block3_low_price_margin, block3_min_candles_after_block2,
            block3_entry_surge_rate, block3_entry_ma_period, block3_entry_high_above_ma,
            block3_entry_max_deviation_ratio, block3_entry_min_trading_value,
            block3_entry_volume_high_months, block3_entry_volume_spike_ratio,
            block3_entry_price_high_months, block3_exit_condition_type,
            block3_exit_ma_period, block3_cooldown_days, block3_tolerance_pct,
            block4_volume_ratio, block4_low_price_margin, block4_min_candles_after_block3,
            block4_entry_surge_rate, block4_entry_ma_period, block4_entry_high_above_ma,
            block4_entry_max_deviation_ratio, block4_entry_min_trading_value,
            block4_entry_volume_high_months, block4_entry_volume_spike_ratio,
            block4_entry_price_high_months, block4_exit_condition_type,
            block4_exit_ma_period, block4_cooldown_days, block4_tolerance_pct,
            is_active, created_at, updated_at
        FROM redetection_condition_preset
    """)
    print(f"데이터 복사 완료: {cursor.rowcount}건")

    # 4. 기존 테이블 삭제
    cursor.execute("DROP TABLE redetection_condition_preset")
    print("기존 테이블 삭제 완료")

    # 5. 새 테이블 이름 변경
    cursor.execute("ALTER TABLE redetection_condition_preset_new RENAME TO redetection_condition_preset")
    print("새 테이블 이름 변경 완료")

    # 6. 검증
    cursor.execute("SELECT COUNT(*) FROM redetection_condition_preset")
    new_row_count = cursor.fetchone()[0]
    match_status = "[OK]" if new_row_count == row_count else "[ERROR]"
    print(f"\n검증: {new_row_count}건 (기존 {row_count}건과 일치: {match_status})")

    conn.commit()
    conn.close()
    print("\n[OK] redetection_condition_preset 재정렬 완료!\n")


def main():
    """메인 실행"""
    db_path = "data/database/stock_data.db"

    if not Path(db_path).exists():
        print(f"[ERROR] DB 파일을 찾을 수 없습니다: {db_path}")
        return

    print("\n" + "=" * 80)
    print("DB Preset 테이블 컬럼 순서 재정렬 마이그레이션")
    print("=" * 80)
    print(f"\nDB: {db_path}\n")

    # 1. seed_condition_preset 재정렬
    reorder_seed_condition_preset(db_path)

    # 2. redetection_condition_preset 재정렬
    reorder_redetection_condition_preset(db_path)

    print("=" * 80)
    print("[OK] 모든 테이블 재정렬 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
