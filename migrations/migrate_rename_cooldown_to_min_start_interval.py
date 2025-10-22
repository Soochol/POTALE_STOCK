"""
Database Migration: Rename cooldown_days to min_start_interval_days

cooldown_days는 "종료 후 대기"를 의미하는 것으로 오해되었으나,
실제 구현은 "시작 후 간격"을 의미합니다.

이를 명확히 하기 위해 컬럼명을 변경합니다:
- cooldown_days → min_start_interval_days
- 의미: 같은 레벨 블록 시작 간 최소 간격 (시작일 기준)
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def migrate_rename_cooldown():
    """cooldown_days를 min_start_interval_days로 변경"""

    db_path = project_root / "data" / "database" / "stock_data.db"

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return False

    print(f"Database: {db_path}")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # ======================================================================
        # seed_condition_preset 테이블 컬럼 변경
        # ======================================================================
        print("\n[1] seed_condition_preset 테이블 마이그레이션...")

        seed_columns = [
            'block1_cooldown_days',
            'block2_cooldown_days',
            'block3_cooldown_days',
            'block4_cooldown_days'
        ]

        for old_col in seed_columns:
            new_col = old_col.replace('cooldown_days', 'min_start_interval_days')

            try:
                # SQLite 3.25.0+ 지원하는 RENAME COLUMN
                cursor.execute(f"""
                    ALTER TABLE seed_condition_preset
                    RENAME COLUMN {old_col} TO {new_col}
                """)
                print(f"  OK: {old_col} -> {new_col}")
            except sqlite3.OperationalError as e:
                if "no such column" in str(e).lower():
                    print(f"  WARN: {old_col} column already missing (skip)")
                elif "duplicate column name" in str(e).lower():
                    print(f"  WARN: {new_col} column already exists (skip)")
                else:
                    raise

        # ======================================================================
        # redetection_condition_preset 테이블 컬럼 변경
        # ======================================================================
        print("\n[2] redetection_condition_preset 테이블 마이그레이션...")

        redetect_columns = [
            'block1_cooldown_days',
            'block2_cooldown_days',
            'block3_cooldown_days',
            'block4_cooldown_days'
        ]

        for old_col in redetect_columns:
            new_col = old_col.replace('cooldown_days', 'min_start_interval_days')

            try:
                cursor.execute(f"""
                    ALTER TABLE redetection_condition_preset
                    RENAME COLUMN {old_col} TO {new_col}
                """)
                print(f"  OK: {old_col} -> {new_col}")
            except sqlite3.OperationalError as e:
                if "no such column" in str(e).lower():
                    print(f"  WARN: {old_col} column already missing (skip)")
                elif "duplicate column name" in str(e).lower():
                    print(f"  WARN: {new_col} column already exists (skip)")
                else:
                    raise

        # 변경사항 커밋
        conn.commit()

        # ======================================================================
        # 검증
        # ======================================================================
        print("\n[3] 변경사항 검증...")

        # seed_condition_preset 검증
        cursor.execute("PRAGMA table_info(seed_condition_preset)")
        seed_cols = [row[1] for row in cursor.fetchall()]

        for new_col in ['block1_min_start_interval_days', 'block2_min_start_interval_days',
                        'block3_min_start_interval_days', 'block4_min_start_interval_days']:
            if new_col in seed_cols:
                print(f"  OK: seed_condition_preset.{new_col} exists")
            else:
                print(f"  ERROR: seed_condition_preset.{new_col} missing")
                return False

        # redetection_condition_preset 검증
        cursor.execute("PRAGMA table_info(redetection_condition_preset)")
        redetect_cols = [row[1] for row in cursor.fetchall()]

        for new_col in ['block1_min_start_interval_days', 'block2_min_start_interval_days',
                        'block3_min_start_interval_days', 'block4_min_start_interval_days']:
            if new_col in redetect_cols:
                print(f"  OK: redetection_condition_preset.{new_col} exists")
            else:
                print(f"  ERROR: redetection_condition_preset.{new_col} missing")
                return False

        # 데이터 확인
        print("\n[4] 데이터 확인...")
        cursor.execute("""
            SELECT name,
                   block1_min_start_interval_days,
                   block2_min_start_interval_days,
                   block3_min_start_interval_days,
                   block4_min_start_interval_days
            FROM seed_condition_preset
        """)

        rows = cursor.fetchall()
        print(f"  seed_condition_preset: {len(rows)}개 레코드")
        for row in rows:
            print(f"    {row[0]}: B1={row[1]}, B2={row[2]}, B3={row[3]}, B4={row[4]}")

        cursor.execute("""
            SELECT name,
                   block1_min_start_interval_days,
                   block2_min_start_interval_days,
                   block3_min_start_interval_days,
                   block4_min_start_interval_days
            FROM redetection_condition_preset
        """)

        rows = cursor.fetchall()
        print(f"  redetection_condition_preset: {len(rows)}개 레코드")
        for row in rows:
            print(f"    {row[0]}: B1={row[1]}, B2={row[2]}, B3={row[3]}, B4={row[4]}")

        print("\n" + "=" * 80)
        print("SUCCESS: Migration completed!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate_rename_cooldown()
    sys.exit(0 if success else 1)
