"""
DB 마이그레이션: Block1 진입 조건 파라미터 이름 통일

변경 사항:
  high_above_ma        → entry_high_above_ma
  max_deviation_ratio  → entry_max_deviation_ratio
  min_trading_value    → entry_min_trading_value
  volume_high_months   → entry_volume_high_months
  volume_spike_ratio   → entry_volume_spike_ratio
  price_high_months    → entry_price_high_months

영향 받는 테이블:
  - seed_condition_preset
  - redetection_condition_preset
  - block1_condition_preset
  - block2_condition_preset
  - block3_condition_preset
"""
import sqlite3

def migrate_database(db_path: str):
    """데이터베이스 마이그레이션 실행"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 70)
    print("DB 마이그레이션 시작: Block1 진입 조건 파라미터 이름 통일")
    print("=" * 70)

    tables = [
        'seed_condition_preset',
        'redetection_condition_preset',
        'block1_condition_preset',
        'block2_condition_preset',
        'block3_condition_preset'
    ]

    rename_mapping = {
        'high_above_ma': 'entry_high_above_ma',
        'max_deviation_ratio': 'entry_max_deviation_ratio',
        'min_trading_value': 'entry_min_trading_value',
        'volume_high_months': 'entry_volume_high_months',
        'volume_spike_ratio': 'entry_volume_spike_ratio',
        'price_high_months': 'entry_price_high_months'
    }

    for table in tables:
        print(f"\n[{table}]")

        # 테이블 존재 확인
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cursor.fetchone():
            print(f"  [!] 테이블이 존재하지 않음 - 건너뜀")
            continue

        # 테이블 스키마 가져오기
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {row[1]: row for row in cursor.fetchall()}

        # 각 컬럼 이름 변경
        renamed_count = 0
        for old_name, new_name in rename_mapping.items():
            if old_name in columns:
                try:
                    cursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}")
                    print(f"  [OK] {old_name} → {new_name}")
                    renamed_count += 1
                except sqlite3.OperationalError as e:
                    # 이미 변경되었거나 다른 오류
                    if "duplicate column name" in str(e).lower():
                        print(f"  [!] {new_name} 이미 존재 - 건너뜀")
                    elif "no such column" in str(e).lower():
                        print(f"  [!] {old_name} 컬럼 없음 - 건너뜀")
                    else:
                        print(f"  [!] 오류: {e}")
            else:
                print(f"  [!] {old_name} 컬럼 없음 - 건너뜀")

        if renamed_count == 0:
            print(f"  [!] 변경된 컬럼 없음")

    # 변경사항 커밋
    conn.commit()
    conn.close()

    print("\n" + "=" * 70)
    print("[OK] 마이그레이션 완료!")
    print("=" * 70)


if __name__ == "__main__":
    import sys

    db_path = "data/database/stock_data.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print(f"\nDB 경로: {db_path}\n")

    # 확인
    response = input("마이그레이션을 실행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("취소되었습니다.")
        sys.exit(0)

    migrate_database(db_path)
