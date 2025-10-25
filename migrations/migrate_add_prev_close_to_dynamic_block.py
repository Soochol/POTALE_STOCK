"""
데이터베이스 마이그레이션: prev_close 필드 추가

블록 시작 전일 종가를 저장하여 상승폭 계산 가능하게 함
- is_price_doubling_surge() 함수에서 사용
- Block2 진입 조건: Block1 상승폭 반복 감지

변경 사항:
- dynamic_block_detection 테이블에 prev_close 추가
- FLOAT NULL (기존 블록은 NULL 허용)

사용법:
    python migrations/migrate_add_prev_close_to_dynamic_block.py
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
        # dynamic_block_detection 테이블 수정
        print("\n[1/1] dynamic_block_detection 테이블 수정 중...")

        # 컬럼 존재 여부 확인
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'prev_close' not in columns:
            print("  ✓ prev_close 컬럼 추가 중...")
            cursor.execute("""
                ALTER TABLE dynamic_block_detection
                ADD COLUMN prev_close FLOAT NULL
            """)
            conn.commit()
            print("  ✅ prev_close 컬럼 추가 완료")
        else:
            print("  ⊘ prev_close 이미 존재 (스킵)")

        # 추가된 컬럼 확인
        cursor.execute("PRAGMA table_info(dynamic_block_detection)")
        columns_info = cursor.fetchall()
        print("\n📋 dynamic_block_detection 테이블 스키마:")
        for col in columns_info:
            col_id, name, type_, notnull, default, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            pk_marker = " (PK)" if pk else ""
            default_str = f" DEFAULT {default}" if default is not None else ""
            print(f"  - {name}: {type_} {nullable}{default_str}{pk_marker}")

        print("\n" + "=" * 80)
        print("✅ 마이그레이션 완료!")
        print("\n📌 다음 단계:")
        print("  1. 기존 블록의 prev_close는 NULL (신규 블록부터 자동 저장)")
        print("  2. test1_alt.yaml 설정 확인 (Block2 진입 조건에 is_price_doubling_surge 추가)")
        print("  3. 테스트 실행: python -m pytest tests/unit/entities/test_builtin_functions_price_surge.py -v")

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
