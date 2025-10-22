"""
데이터베이스 마이그레이션: auto_exit_on_next_block 필드 추가

다음 블록 시작 시 이전 블록을 자동 종료하는 기능 추가
- Block2 시작 → Block1 종료 (M-1일)
- Block3 시작 → Block2 종료 (M-1일)
- Block4 시작 → Block3 종료 (M-1일)

종료 조건:
- 기존 3가지 타입 (MA_BREAK, THREE_LINE_REVERSAL, BODY_MIDDLE) OR
- 다음 블록 시작 시 자동 종료

변경 사항:
- seed_condition_preset 테이블에 block1~4_auto_exit_on_next_block 추가
- redetection_condition_preset 테이블에 block1~4_auto_exit_on_next_block 추가
- BOOLEAN NOT NULL DEFAULT 0 (false)
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent


def migrate():
    """마이그레이션 실행"""
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    db_path = project_root / "data" / "database" / "stock_data.db"

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return False

    print(f"🔧 마이그레이션 시작: {db_path}")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. seed_condition_preset 테이블 수정
        print("\n[1/2] seed_condition_preset 테이블 수정 중...")

        # Block1~4에 대해 auto_exit_on_next_block 컬럼 추가
        for block_num in range(1, 5):
            column_name = f"block{block_num}_auto_exit_on_next_block"

            # 컬럼 존재 여부 확인
            cursor.execute(
                f"PRAGMA table_info(seed_condition_preset)"
            )
            columns = [row[1] for row in cursor.fetchall()]

            if column_name not in columns:
                print(f"  ✓ {column_name} 추가 중...")
                cursor.execute(
                    f"""
                    ALTER TABLE seed_condition_preset
                    ADD COLUMN {column_name} BOOLEAN NOT NULL DEFAULT 0
                    """
                )
            else:
                print(f"  ⊘ {column_name} 이미 존재 (스킵)")

        # 2. redetection_condition_preset 테이블 수정
        print("\n[2/2] redetection_condition_preset 테이블 수정 중...")

        # Block1~4에 대해 auto_exit_on_next_block 컬럼 추가
        for block_num in range(1, 5):
            column_name = f"block{block_num}_auto_exit_on_next_block"

            # 컬럼 존재 여부 확인
            cursor.execute(
                f"PRAGMA table_info(redetection_condition_preset)"
            )
            columns = [row[1] for row in cursor.fetchall()]

            if column_name not in columns:
                print(f"  ✓ {column_name} 추가 중...")
                cursor.execute(
                    f"""
                    ALTER TABLE redetection_condition_preset
                    ADD COLUMN {column_name} BOOLEAN NOT NULL DEFAULT 0
                    """
                )
            else:
                print(f"  ⊘ {column_name} 이미 존재 (스킵)")

        # 커밋
        conn.commit()

        print("\n" + "=" * 80)
        print("✅ 마이그레이션 완료!")
        print("\n📌 다음 단계:")
        print("  1. YAML 프리셋 파일 수정 (presets/seed_conditions.yaml)")
        print("  2. YAML 프리셋 파일 수정 (presets/redetection_conditions.yaml)")
        print("  3. 프리셋 업데이트: uv run python scripts/update_presets_from_yaml.py")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate()
