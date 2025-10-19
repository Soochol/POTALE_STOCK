"""
아난티 데이터 수집 (패턴 테스트용)
"""
from datetime import date
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.collectors.naver.naver_hybrid_collector import NaverHybridCollector
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository


def main():
    print("=" * 70)
    print("아난티 데이터 수집 (패턴 테스트용)")
    print("=" * 70)

    # DB 연결
    db = DatabaseConnection("data/database/stock_data.db")
    db.create_tables()

    # 종목 정보 등록
    print("\n[1] 종목 정보 등록...")
    from src.infrastructure.database.models import StockInfo
    with db.session_scope() as session:
        existing = session.query(StockInfo).filter_by(ticker="025980").first()
        if not existing:
            stock_info = StockInfo(
                ticker="025980",
                name="아난티",
                market="KOSPI"
            )
            session.add(stock_info)
            session.commit()
            print("  아난티 종목 등록 완료")
        else:
            print("  아난티 종목 이미 존재")

    # 데이터 수집
    print("\n[2] 주가 데이터 수집 중...")
    collector = NaverHybridCollector()
    repo = SqliteStockRepository("data/database/stock_data.db")

    start_date = date(2015, 1, 1)
    end_date = date(2025, 10, 18)

    print(f"  기간: {start_date} ~ {end_date}")

    # 수집
    stocks = collector.collect(
        ticker="025980",
        start_date=start_date,
        end_date=end_date
    )

    print(f"  수집 완료: {len(stocks)}건")

    # 저장
    print("\n[3] DB 저장 중...")
    saved_count = 0
    for stock in stocks:
        repo.save(stock)
        saved_count += 1

    print(f"  저장 완료: {saved_count}건")

    # 검증
    print("\n[4] 검증...")
    loaded = repo.get_stock_data("025980", start_date, end_date)
    print(f"  DB 조회: {len(loaded)}건")
    if len(loaded) > 0:
        print(f"  기간: {loaded[0].date} ~ {loaded[-1].date}")

    print("\n" + "=" * 70)
    print("수집 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
