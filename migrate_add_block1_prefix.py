"""
DB Migration: Add block1_ prefix to common parameters
Common 필드에 block1_ prefix 추가 (네이밍 일관성)

변경 내용:
- entry_surge_rate -> block1_entry_surge_rate
- entry_ma_period -> block1_entry_ma_period
- entry_high_above_ma -> block1_entry_high_above_ma
- entry_max_deviation_ratio -> block1_entry_max_deviation_ratio
- entry_min_trading_value -> block1_entry_min_trading_value
- entry_volume_high_months -> block1_entry_volume_high_months
- entry_volume_spike_ratio -> block1_entry_volume_spike_ratio
- entry_price_high_months -> block1_entry_price_high_months
- exit_condition_type -> block1_exit_condition_type
- exit_ma_period -> block1_exit_ma_period
- cooldown_days -> block1_cooldown_days

대상 테이블:
- seed_condition_preset
- redetection_condition_preset
"""

import sqlite3
from pathlib import Path


def migrate():
    """컬럼명 변경 마이그레이션"""

    db_path = Path("data/database/stock_data.db")

    if not db_path.exists():
        print(f"[ERROR] Database file not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 80)
    print("DB Migration: Add block1_ prefix to common parameters")
    print("=" * 80)

    # 변경할 컬럼 목록
    column_mappings = [
        ('entry_surge_rate', 'block1_entry_surge_rate'),
        ('entry_ma_period', 'block1_entry_ma_period'),
        ('entry_high_above_ma', 'block1_entry_high_above_ma'),
        ('entry_max_deviation_ratio', 'block1_entry_max_deviation_ratio'),
        ('entry_min_trading_value', 'block1_entry_min_trading_value'),
        ('entry_volume_high_months', 'block1_entry_volume_high_months'),
        ('entry_volume_spike_ratio', 'block1_entry_volume_spike_ratio'),
        ('entry_price_high_months', 'block1_entry_price_high_months'),
        ('exit_condition_type', 'block1_exit_condition_type'),
        ('exit_ma_period', 'block1_exit_ma_period'),
        ('cooldown_days', 'block1_cooldown_days'),
    ]

    # 변경할 테이블 목록
    tables = ['seed_condition_preset', 'redetection_condition_preset']

    try:
        for table in tables:
            print(f"\n[{table}] 컬럼명 변경 중...")

            # 1. 기존 데이터 조회
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            cursor.execute(f"PRAGMA table_info({table})")
            old_columns = [col[1] for col in cursor.fetchall()]

            print(f"  - 기존 데이터: {len(rows)}건")
            print(f"  - 기존 컬럼: {len(old_columns)}개")

            # 2. 새 테이블 생성 (임시)
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()

            # 컬럼 정의 생성 (이름 변경 적용)
            new_columns_def = []
            for col in columns_info:
                col_id, name, type_, notnull, default, pk = col

                # 컬럼명 변경 적용
                new_name = name
                for old_name, new_col_name in column_mappings:
                    if name == old_name:
                        new_name = new_col_name
                        print(f"  [OK] {old_name} -> {new_name}")
                        break

                # 컬럼 정의 구성
                col_def = f"{new_name} {type_}"
                if pk:
                    col_def += " PRIMARY KEY"
                if notnull and not pk:
                    col_def += " NOT NULL"
                if default is not None:
                    col_def += f" DEFAULT {default}"

                new_columns_def.append(col_def)

            # 3. 임시 테이블 생성
            temp_table = f"{table}_new"
            create_sql = f"CREATE TABLE {temp_table} ({', '.join(new_columns_def)})"
            cursor.execute(create_sql)

            # 4. 데이터 복사 (컬럼 순서 유지)
            if rows:
                old_col_names = [col[1] for col in columns_info]
                new_col_names = []
                for old_name in old_col_names:
                    new_name = old_name
                    for old_n, new_n in column_mappings:
                        if old_name == old_n:
                            new_name = new_n
                            break
                    new_col_names.append(new_name)

                placeholders = ','.join(['?'] * len(old_col_names))
                insert_sql = f"INSERT INTO {temp_table} ({','.join(new_col_names)}) VALUES ({placeholders})"

                cursor.executemany(insert_sql, rows)
                print(f"  - 데이터 복사 완료: {len(rows)}건")

            # 5. 기존 테이블 삭제 및 임시 테이블 이름 변경
            cursor.execute(f"DROP TABLE {table}")
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table}")

            print(f"  [SUCCESS] {table} migration completed")

        # 커밋
        conn.commit()

        print("\n" + "=" * 80)
        print("[SUCCESS] Migration completed!")
        print("=" * 80)

        # 검증
        print("\n[검증] 변경된 컬럼명 확인:")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"\n{table}:")
            block1_cols = [col for col in columns if col.startswith('block1_')]
            print(f"  - block1_ prefix 컬럼: {len(block1_cols)}개")
            for col in sorted(block1_cols)[:5]:  # 처음 5개만 출력
                print(f"    - {col}")
            if len(block1_cols) > 5:
                print(f"    ... 외 {len(block1_cols) - 5}개")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
