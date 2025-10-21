"""
DB Migration: Add Block2/3/4 specific parameters for all Block1 base conditions

Block1의 11개 기본 파라미터를 Block2/3/4용으로 복제하여 블록별 독립 설정 가능하게 함
- seed_condition_preset: 33개 컬럼 추가
- redetection_condition_preset: 33개 컬럼 추가
"""
import sqlite3
from pathlib import Path


def add_columns_to_table(cursor, table_name: str, columns: list):
    """테이블에 컬럼 추가 (이미 존재하면 스킵)"""
    print(f"\n[{table_name}] 컬럼 추가 중...")

    # 기존 컬럼 목록 가져오기
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    added_count = 0
    skipped_count = 0

    for col_name, col_type, default_value in columns:
        if col_name in existing_columns:
            print(f"  [SKIP] {col_name} - already exists")
            skipped_count += 1
            continue

        # 컬럼 추가
        sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
        if default_value is not None:
            if isinstance(default_value, str):
                sql += f" DEFAULT '{default_value}'"
            elif isinstance(default_value, bool):
                sql += f" DEFAULT {1 if default_value else 0}"
            else:
                sql += f" DEFAULT {default_value}"
        else:
            sql += " DEFAULT NULL"

        cursor.execute(sql)
        print(f"  [OK] {col_name} {col_type} (default: {default_value})")
        added_count += 1

    print(f"  완료: {added_count}개 추가, {skipped_count}개 스킵")
    return added_count, skipped_count


def main():
    db_path = Path("data/database/stock_data.db")

    if not db_path.exists():
        print(f"[ERROR] Database file not found: {db_path}")
        return

    print("=" * 70)
    print("Block2/3/4 파라미터 컬럼 추가 마이그레이션")
    print("=" * 70)
    print(f"DB 경로: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Block1 기본 조건 11개 파라미터
        base_params = [
            # (컬럼명, 타입, 기본값)
            ('entry_surge_rate', 'REAL', None),
            ('entry_ma_period', 'INTEGER', None),
            ('entry_high_above_ma', 'INTEGER', None),  # 0/1 for bool
            ('entry_max_deviation_ratio', 'REAL', None),
            ('entry_min_trading_value', 'REAL', None),
            ('entry_volume_high_months', 'INTEGER', None),
            ('entry_volume_spike_ratio', 'REAL', None),
            ('entry_price_high_months', 'INTEGER', None),
            ('exit_condition_type', 'TEXT', None),
            ('exit_ma_period', 'INTEGER', None),
            ('cooldown_days', 'INTEGER', None),
        ]

        # Block2/3/4용 컬럼 생성
        block2_columns = [(f'block2_{name}', dtype, default) for name, dtype, default in base_params]
        block3_columns = [(f'block3_{name}', dtype, default) for name, dtype, default in base_params]
        block4_columns = [(f'block4_{name}', dtype, default) for name, dtype, default in base_params]

        all_new_columns = block2_columns + block3_columns + block4_columns

        print(f"\n추가할 컬럼 수: {len(all_new_columns)}개")
        print(f"  - Block2용: {len(block2_columns)}개")
        print(f"  - Block3용: {len(block3_columns)}개")
        print(f"  - Block4용: {len(block4_columns)}개")

        # 1. seed_condition_preset 테이블 수정
        added, skipped = add_columns_to_table(cursor, 'seed_condition_preset', all_new_columns)

        # 2. redetection_condition_preset 테이블 수정
        added2, skipped2 = add_columns_to_table(cursor, 'redetection_condition_preset', all_new_columns)

        # 커밋
        conn.commit()

        print("\n" + "=" * 70)
        print("마이그레이션 완료!")
        print("=" * 70)
        print(f"seed_condition_preset: {added}개 추가, {skipped}개 스킵")
        print(f"redetection_condition_preset: {added2}개 추가, {skipped2}개 스킵")
        print(f"총 {added + added2}개 컬럼 추가됨")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
