"""
System Health Check - 전체 시스템 무결성 검증

데이터베이스 스키마, 모델, 엔티티, 데이터 무결성을 종합적으로 검증합니다.

실행방법:
    python migrations/verify_system_health.py
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
from datetime import datetime


def verify_database_tables():
    """데이터베이스 테이블 존재 여부 확인"""
    print("\n" + "=" * 80)
    print("  [1/5] 데이터베이스 테이블 확인")
    print("=" * 80)

    db_path = project_root / "data" / "database" / "stock_data.db"

    expected_tables = [
        'seed_condition_preset',
        'redetection_condition_preset',
        'block_pattern',
        'block1_detection',
        'block2_detection',
        'block3_detection',
        'block4_detection',
        'stock_info',
        'stock_price',
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    existing_tables = [row[0] for row in cursor.fetchall()]

    all_ok = True
    for table in expected_tables:
        if table in existing_tables:
            print(f"  [OK] {table}")
        else:
            print(f"  [ERROR] {table} - 테이블 없음!")
            all_ok = False

    conn.close()
    return all_ok


def verify_preset_schema():
    """Preset 테이블 스키마 확인"""
    print("\n" + "=" * 80)
    print("  [2/5] Preset 스키마 확인")
    print("=" * 80)

    db_path = project_root / "data" / "database" / "stock_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # seed_condition_preset 확인
    print("\n  seed_condition_preset:")
    cursor.execute("PRAGMA table_info(seed_condition_preset);")
    seed_cols = [row[1] for row in cursor.fetchall()]

    required_seed_cols = [
        'block1_entry_volume_high_days',
        'block1_entry_price_high_days',
        'block1_min_start_interval_days',
        'block2_min_candles_after_block1',
        'block2_max_candles_after_block1',
    ]

    deprecated_cols = [
        'block1_entry_volume_high_months',
        'block1_entry_price_high_months',
        'block1_cooldown_days',
        'block1_entry_high_above_ma',
    ]

    seed_ok = True
    for col in required_seed_cols:
        if col in seed_cols:
            print(f"    [OK] {col} 존재")
        else:
            print(f"    [ERROR] {col} 없음!")
            seed_ok = False

    for col in deprecated_cols:
        if col not in seed_cols:
            print(f"    [OK] {col} 제거됨")
        else:
            print(f"    [WARN] {col} 아직 존재 (제거되어야 함)")

    # redetection_condition_preset 확인
    print("\n  redetection_condition_preset:")
    cursor.execute("PRAGMA table_info(redetection_condition_preset);")
    redetect_cols = [row[1] for row in cursor.fetchall()]

    required_redetect_cols = [
        'block1_entry_volume_high_days',
        'block1_entry_price_high_days',
        'block1_min_start_interval_days',
        'block2_min_candles_after_block1',
        'block2_max_candles_after_block1',
        'block1_tolerance_pct',
        'block1_redetection_min_days_after_seed',
        'block1_redetection_max_days_after_seed',
    ]

    redetect_ok = True
    for col in required_redetect_cols:
        if col in redetect_cols:
            print(f"    [OK] {col} 존재")
        else:
            print(f"    [ERROR] {col} 없음!")
            redetect_ok = False

    conn.close()
    return seed_ok and redetect_ok


def verify_preset_data():
    """Preset 데이터 로드 확인"""
    print("\n" + "=" * 80)
    print("  [3/5] Preset 데이터 로드 확인")
    print("=" * 80)

    try:
        from src.infrastructure.database.connection import DatabaseConnection
        from src.infrastructure.repositories.preset import (
            SeedConditionPresetRepository,
            RedetectionConditionPresetRepository
        )

        db = DatabaseConnection("data/database/stock_data.db")

        # Seed 프리셋 로드
        print("\n  Seed Condition Presets:")
        seed_repo = SeedConditionPresetRepository(db)
        try:
            seed_preset = seed_repo.load("default_seed")
            if seed_preset:
                print(f"    [OK] default_seed 로드 성공")
            else:
                print("    [WARN] default_seed 없음")
        except Exception as e:
            print(f"    [ERROR] default_seed 로드 실패: {e}")

        # Redetection 프리셋 로드
        print("\n  Redetection Condition Presets:")
        redetect_repo = RedetectionConditionPresetRepository(db)
        try:
            redetect_preset = redetect_repo.load("default_redetect")
            if redetect_preset:
                print(f"    [OK] default_redetect 로드 성공")
            else:
                print("    [WARN] default_redetect 없음")
        except Exception as e:
            print(f"    [ERROR] default_redetect 로드 실패: {e}")

        return True

    except Exception as e:
        print(f"    [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_detection_data():
    """Detection 데이터 무결성 확인"""
    print("\n" + "=" * 80)
    print("  [4/5] Detection 데이터 무결성 확인")
    print("=" * 80)

    db_path = project_root / "data" / "database" / "stock_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Pattern 수 확인
    cursor.execute("SELECT COUNT(*) FROM block_pattern")
    pattern_count = cursor.fetchone()[0]
    print(f"\n  [OK] block_pattern: {pattern_count}개")

    # Block 탐지 수 확인
    for block_num in [1, 2, 3, 4]:
        cursor.execute(f"SELECT COUNT(*) FROM block{block_num}_detection")
        count = cursor.fetchone()[0]
        print(f"  [OK] block{block_num}_detection: {count}개")

    # 무결성 검증
    cursor.execute("""
        SELECT COUNT(*)
        FROM block2_detection b2
        LEFT JOIN block1_detection b1 ON b2.pattern_id = b1.pattern_id
        WHERE b1.id IS NULL
    """)
    orphan_block2 = cursor.fetchone()[0]

    if orphan_block2 == 0:
        print(f"\n  [OK] Block2 무결성: 모든 Block2가 유효한 Block1 참조")
    else:
        print(f"\n  [WARN] Block2 무결성: {orphan_block2}개 고아 레코드 발견")

    conn.close()
    return orphan_block2 == 0


def verify_yaml_sync():
    """YAML preset과 DB 동기화 확인"""
    print("\n" + "=" * 80)
    print("  [5/5] YAML Preset 동기화 확인")
    print("=" * 80)

    try:
        import subprocess
        result = subprocess.run(
            ["python", "scripts/update_presets_from_yaml.py"],
            capture_output=True,
            timeout=30,
            cwd=str(project_root),
            errors='ignore'  # 인코딩 에러 무시
        )

        # returncode 0이면 성공
        if result.returncode == 0:
            print("  [OK] YAML preset 동기화 성공")
            return True
        else:
            print(f"  [ERROR] YAML preset 동기화 실패 (returncode: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print("  [ERROR] YAML preset 동기화 타임아웃")
        return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def main():
    """전체 시스템 건강도 검증"""
    print("=" * 80)
    print(f"  System Health Check")
    print(f"  시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = []

    # 1. 테이블 확인
    results.append(("테이블 확인", verify_database_tables()))

    # 2. 스키마 확인
    results.append(("스키마 확인", verify_preset_schema()))

    # 3. Preset 로드
    results.append(("Preset 로드", verify_preset_data()))

    # 4. Detection 데이터
    results.append(("Detection 무결성", verify_detection_data()))

    # 5. YAML 동기화
    results.append(("YAML 동기화", verify_yaml_sync()))

    # 결과 요약
    print("\n" + "=" * 80)
    print("  검증 결과 요약")
    print("=" * 80)

    all_passed = True
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("  [SUCCESS] 모든 검증 통과!")
        print("=" * 80)
        return True
    else:
        print("  [WARNING] 일부 검증 실패")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
