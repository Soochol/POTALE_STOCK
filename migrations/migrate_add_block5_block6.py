"""
마이그레이션: Block5, Block6 테이블 및 preset 컬럼 추가

Block5Detection, Block6Detection 테이블 생성 및
SeedConditionPreset, RedetectionConditionPreset에 block5, block6 관련 컬럼 추가
"""
import sys
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def migrate():
    """마이그레이션 실행"""
    db = DatabaseConnection()

    with db.session_scope() as session:
        print("=== Block5, Block6 마이그레이션 시작 ===\n")

        # ===== 1. Block5Detection 테이블 생성 =====
        print("1. Block5Detection 테이블 생성...")
        session.execute(text("""
        CREATE TABLE IF NOT EXISTS block5_detection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block5_id VARCHAR(50) UNIQUE NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            started_at DATE NOT NULL,
            ended_at DATE,
            entry_close FLOAT NOT NULL,
            entry_rate FLOAT,
            prev_block4_id INTEGER,
            prev_block4_peak_price FLOAT,
            prev_block4_peak_volume BIGINT,
            peak_price FLOAT,
            peak_date DATE,
            peak_gain_ratio FLOAT,
            peak_volume BIGINT,
            duration_days INTEGER,
            exit_reason VARCHAR(50),
            condition_name VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            pattern_id INTEGER,
            detection_type VARCHAR(20),
            FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
            FOREIGN KEY (prev_block4_id) REFERENCES block4_detection(id),
            FOREIGN KEY (pattern_id) REFERENCES block_pattern(pattern_id),
            CHECK (entry_close > 0),
            CHECK (ended_at IS NULL OR started_at <= ended_at),
            CHECK (peak_price IS NULL OR peak_price >= entry_close)
        )
        """))
        print("   [OK] Block5Detection 테이블 생성 완료\n")

        # Block5 인덱스 생성
        print("2. Block5Detection 인덱스 생성...")
        indexes_block5 = [
            "CREATE INDEX IF NOT EXISTS ix_block5_ticker_started ON block5_detection(ticker, started_at)",
            "CREATE INDEX IF NOT EXISTS ix_block5_status ON block5_detection(status)",
            "CREATE INDEX IF NOT EXISTS ix_block5_started ON block5_detection(started_at)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_block5_id ON block5_detection(block5_id)",
            "CREATE INDEX IF NOT EXISTS ix_block5_prev_block4 ON block5_detection(prev_block4_id)",
            "CREATE INDEX IF NOT EXISTS ix_block5_pattern ON block5_detection(pattern_id)",
            "CREATE INDEX IF NOT EXISTS ix_block5_detection_type ON block5_detection(detection_type)",
            "CREATE INDEX IF NOT EXISTS ix_block5_pattern_condition ON block5_detection(pattern_id, condition_name)",
            "CREATE INDEX IF NOT EXISTS ix_block5_status_started ON block5_detection(status, started_at)",
        ]
        for idx_sql in indexes_block5:
            session.execute(text(idx_sql))
        print("   [OK] Block5 인덱스 생성 완료\n")

        # ===== 3. Block6Detection 테이블 생성 =====
        print("3. Block6Detection 테이블 생성...")
        session.execute(text("""
        CREATE TABLE IF NOT EXISTS block6_detection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block6_id VARCHAR(50) UNIQUE NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            started_at DATE NOT NULL,
            ended_at DATE,
            entry_close FLOAT NOT NULL,
            entry_rate FLOAT,
            prev_block5_id INTEGER,
            prev_block5_peak_price FLOAT,
            prev_block5_peak_volume BIGINT,
            peak_price FLOAT,
            peak_date DATE,
            peak_gain_ratio FLOAT,
            peak_volume BIGINT,
            duration_days INTEGER,
            exit_reason VARCHAR(50),
            condition_name VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            pattern_id INTEGER,
            detection_type VARCHAR(20),
            FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
            FOREIGN KEY (prev_block5_id) REFERENCES block5_detection(id),
            FOREIGN KEY (pattern_id) REFERENCES block_pattern(pattern_id),
            CHECK (entry_close > 0),
            CHECK (ended_at IS NULL OR started_at <= ended_at),
            CHECK (peak_price IS NULL OR peak_price >= entry_close)
        )
        """))
        print("   [OK] Block6Detection 테이블 생성 완료\n")

        # Block6 인덱스 생성
        print("4. Block6Detection 인덱스 생성...")
        indexes_block6 = [
            "CREATE INDEX IF NOT EXISTS ix_block6_ticker_started ON block6_detection(ticker, started_at)",
            "CREATE INDEX IF NOT EXISTS ix_block6_status ON block6_detection(status)",
            "CREATE INDEX IF NOT EXISTS ix_block6_started ON block6_detection(started_at)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_block6_id ON block6_detection(block6_id)",
            "CREATE INDEX IF NOT EXISTS ix_block6_prev_block5 ON block6_detection(prev_block5_id)",
            "CREATE INDEX IF NOT EXISTS ix_block6_pattern ON block6_detection(pattern_id)",
            "CREATE INDEX IF NOT EXISTS ix_block6_detection_type ON block6_detection(detection_type)",
            "CREATE INDEX IF NOT EXISTS ix_block6_pattern_condition ON block6_detection(pattern_id, condition_name)",
            "CREATE INDEX IF NOT EXISTS ix_block6_status_started ON block6_detection(status, started_at)",
        ]
        for idx_sql in indexes_block6:
            session.execute(text(idx_sql))
        print("   [OK] Block6 인덱스 생성 완료\n")

        # ===== 5. SeedConditionPreset 컬럼 추가 =====
        print("5. SeedConditionPreset에 Block5, Block6 컬럼 추가...")
        seed_columns = [
            # Block5 진입 조건
            "block5_entry_surge_rate FLOAT",
            "block5_entry_ma_period INTEGER",
            "block5_entry_max_deviation_ratio FLOAT",
            "block5_entry_min_trading_value FLOAT",
            "block5_entry_volume_high_days INTEGER",
            "block5_entry_volume_spike_ratio FLOAT",
            "block5_entry_price_high_days INTEGER",
            "block5_exit_condition_type VARCHAR(50)",
            "block5_exit_ma_period INTEGER",
            "block5_auto_exit_on_next_block INTEGER DEFAULT 0 NOT NULL",
            "block5_min_start_interval_days INTEGER",
            # Block5 추가 조건
            "block5_volume_ratio FLOAT",
            "block5_low_price_margin FLOAT",
            "block5_min_candles_after_block4 INTEGER",
            "block5_max_candles_after_block4 INTEGER",
            # Block6 진입 조건
            "block6_entry_surge_rate FLOAT",
            "block6_entry_ma_period INTEGER",
            "block6_entry_max_deviation_ratio FLOAT",
            "block6_entry_min_trading_value FLOAT",
            "block6_entry_volume_high_days INTEGER",
            "block6_entry_volume_spike_ratio FLOAT",
            "block6_entry_price_high_days INTEGER",
            "block6_exit_condition_type VARCHAR(50)",
            "block6_exit_ma_period INTEGER",
            "block6_auto_exit_on_next_block INTEGER DEFAULT 0 NOT NULL",
            "block6_min_start_interval_days INTEGER",
            # Block6 추가 조건
            "block6_volume_ratio FLOAT",
            "block6_low_price_margin FLOAT",
            "block6_min_candles_after_block5 INTEGER",
            "block6_max_candles_after_block5 INTEGER",
        ]

        for col in seed_columns:
            col_name = col.split()[0]
            try:
                session.execute(text(f"ALTER TABLE seed_condition_preset ADD COLUMN {col}"))
                print(f"   [OK] 추가: {col_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   - 이미 존재: {col_name}")
                else:
                    print(f"   [ERROR] 실패: {col_name} - {e}")

        print("\n6. RedetectionConditionPreset에 Block5, Block6 컬럼 추가...")
        redetect_columns = seed_columns + [
            # Block5 재탐지 전용
            "block5_tolerance_pct FLOAT DEFAULT 25.0 NOT NULL",
            "block5_redetection_min_days_after_seed INTEGER DEFAULT 0 NOT NULL",
            "block5_redetection_max_days_after_seed INTEGER DEFAULT 1825 NOT NULL",
            # Block6 재탐지 전용
            "block6_tolerance_pct FLOAT DEFAULT 30.0 NOT NULL",
            "block6_redetection_min_days_after_seed INTEGER DEFAULT 0 NOT NULL",
            "block6_redetection_max_days_after_seed INTEGER DEFAULT 1825 NOT NULL",
        ]

        for col in redetect_columns:
            col_name = col.split()[0]
            try:
                session.execute(text(f"ALTER TABLE redetection_condition_preset ADD COLUMN {col}"))
                print(f"   [OK] 추가: {col_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   - 이미 존재: {col_name}")
                else:
                    print(f"   [ERROR] 실패: {col_name} - {e}")

        session.commit()
        print("\n=== 마이그레이션 완료 ===")
        print("\n다음 단계:")
        print("1. python scripts/preset_management/update_presets_from_yaml.py  # YAML → DB 동기화")
        print("2. Block5, Block6 통합 탐지 로직 업데이트")


if __name__ == "__main__":
    migrate()
