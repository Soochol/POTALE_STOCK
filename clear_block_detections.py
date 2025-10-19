"""
기존 Block 탐지 데이터 초기화 스크립트

아난티(025980)의 모든 Block1/2/3 탐지 데이터를 삭제합니다.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseConnection


def main():
    """메인 함수"""
    ticker = "025980"
    db_path = "data/database/stock_data.db"

    print("="*70)
    print("Block 탐지 데이터 초기화")
    print("="*70)
    print()

    db_conn = DatabaseConnection(db_path)

    try:
        with db_conn.session_scope() as session:
            # Block3 먼저 삭제 (외래키 제약 때문)
            from src.infrastructure.database.models import Block3Detection

            result = session.query(Block3Detection).filter_by(ticker=ticker).delete()
            block3_deleted = result
            print(f"[1/3] Block3 삭제: {block3_deleted}건")

            # Block2 삭제
            from src.infrastructure.database.models import Block2Detection

            result = session.query(Block2Detection).filter_by(ticker=ticker).delete()
            block2_deleted = result
            print(f"[2/3] Block2 삭제: {block2_deleted}건")

            # Block1 삭제
            from src.infrastructure.database.models import Block1Detection

            result = session.query(Block1Detection).filter_by(ticker=ticker).delete()
            block1_deleted = result
            print(f"[3/3] Block1 삭제: {block1_deleted}건")

            print()
            print("="*70)
            print("완료!")
            print(f"총 {block1_deleted + block2_deleted + block3_deleted}건 삭제됨")
            print("="*70)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


if __name__ == "__main__":
    main()
