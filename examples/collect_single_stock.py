"""
단일 종목 데이터 수집 예제
"""
import sys
from pathlib import Path
from datetime import date

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.collectors.naver.naver_hybrid_collector import NaverHybridCollector
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import Base


def collect_single_stock(ticker: str, fromdate: date, todate: date):
    """
    단일 종목 데이터 수집

    Args:
        ticker: 종목코드 (예: "005930", "035720")
        fromdate: 시작일
        todate: 종료일
    """
    print(f"=" * 80)
    print(f"종목 데이터 수집: {ticker}")
    print(f"기간: {fromdate} ~ {todate}")
    print(f"=" * 80)

    # 1. DB 초기화
    db_path = "stock_data.db"
    db = DatabaseConnection(db_path)
    Base.metadata.create_all(db.engine)

    # 2. 수집기 생성
    collector = NaverHybridCollector(db_connection=db)

    # 3. 데이터 수집
    result = collector.collect(ticker, fromdate, todate)

    # 4. 결과 출력
    print(f"\n{'=' * 80}")
    print("수집 결과")
    print(f"{'=' * 80}")

    if result.success:
        print(f"[성공] {result.record_count}건 수집 완료")
        print(f"소요 시간: {result.duration_seconds:.1f}초")
    else:
        print(f"[실패] {result.error_message}")

    return result


if __name__ == "__main__":
    # 예제: 삼성전자 2024년 데이터 수집
    collect_single_stock(
        ticker="005930",  # 삼성전자
        fromdate=date(2024, 1, 1),
        todate=date(2024, 12, 31)
    )

    # 다른 예제들 (주석 해제하여 사용)

    # 카카오 2023-2024년 데이터
    # collect_single_stock("035720", date(2023, 1, 1), date(2024, 12, 31))

    # 네이버 최근 1년 데이터
    # collect_single_stock("035420", date(2024, 1, 1), date(2024, 12, 31))

    # 아난티 전체 데이터 (2015~)
    # collect_single_stock("025980", date(2015, 1, 1), date(2024, 12, 31))
