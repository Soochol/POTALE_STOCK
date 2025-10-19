"""
아난티(025980) 데이터 수집 스크립트 (간단 버전)
2015-01-01 ~ 오늘까지
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.collectors.naver.naver_hybrid_collector import NaverHybridCollector
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import StockInfo

def collect_ananti():
    """아난티 데이터 수집"""

    ticker = "025980"
    name = "아난티"
    start_date = date(2015, 1, 1)
    end_date = date.today()

    print(f"\n{'='*60}")
    print(f"아난티({ticker}) 데이터 수집")
    print(f"기간: {start_date} ~ {end_date}")
    print(f"{'='*60}\n")

    # DB 연결
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    # 1. 종목 정보 등록
    print("[1/2] 종목 정보 등록...")

    try:
        session = db_conn.get_session()

        # 기존 종목 확인
        existing = session.query(StockInfo).filter(StockInfo.ticker == ticker).first()

        if existing:
            print(f"종목 정보 이미 존재: {existing.ticker} {existing.name}")
        else:
            stock_info = StockInfo(
                ticker=ticker,
                name=name,
                market="KOSDAQ"
            )
            session.add(stock_info)
            session.commit()
            print(f"종목 정보 등록 완료: {ticker} {name}")

        session.close()

    except Exception as e:
        print(f"[ERROR] 종목 정보 등록 실패: {e}")
        return False

    # 2. 주가 데이터 수집
    print("\n[2/2] 주가 데이터 수집 (NaverHybridCollector)...")
    print("진행 중... (최대 5분 소요)")

    try:
        collector = NaverHybridCollector(db_connection=db_conn, delay=0.05)

        result = collector.collect(
            ticker=ticker,
            fromdate=start_date,
            todate=end_date
        )

        if result.success:
            print(f"\n[SUCCESS] 수집 완료!")
            print(f"- 저장된 데이터: {result.record_count}건")
            if result.error_message:
                print(f"- 메시지: {result.error_message}")
            return True
        else:
            print(f"\n[ERROR] 수집 실패")
            print(f"- 오류: {result.error_message}")
            return False

    except Exception as e:
        print(f"\n[ERROR] 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = collect_ananti()

    print(f"\n{'='*60}")
    if success:
        print("[SUCCESS] 아난티 데이터 수집 완료!")
    else:
        print("[FAILED] 아난티 데이터 수집 실패")
    print(f"{'='*60}\n")

    sys.exit(0 if success else 1)
