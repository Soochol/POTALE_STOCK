"""
아난티 데이터 수집 (FinanceDataReader 사용)
"""
import FinanceDataReader as fdr
from datetime import date
from src.domain.entities.stock import Stock
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.database.connection import DatabaseConnection


def main():
    print("=" * 70)
    print("아난티 데이터 수집 (FinanceDataReader)")
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
    print("\n[2] FinanceDataReader로 데이터 수집...")
    start_date = '2015-01-01'
    end_date = '2025-10-18'

    print(f"  기간: {start_date} ~ {end_date}")

    # FDR로 데이터 수집
    df = fdr.DataReader('025980', start_date, end_date)

    print(f"  수집 완료: {len(df)}건")

    # Stock 엔티티로 변환
    print("\n[3] Stock 엔티티 변환 중...")
    stocks = []
    for idx, row in df.iterrows():
        try:
            stock = Stock(
                ticker="025980",
                name="아난티",
                date=idx.date(),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                trading_value=int(row['Volume'] * row['Close'])  # 거래대금
            )
            stocks.append(stock)
        except ValueError as e:
            print(f"  오류 ({idx.date()}): {e}")
            print(f"    Open={row['Open']}, High={row['High']}, Low={row['Low']}, Close={row['Close']}")
            continue

    print(f"  변환 완료: {len(stocks)}건")

    # DB 저장
    print("\n[4] DB 저장 중...")
    repo = SqliteStockRepository("data/database/stock_data.db")

    try:
        result = repo.save_stock_data(stocks)
        print(f"  저장 완료: {len(stocks)}건")
    except Exception as e:
        print(f"  저장 오류: {e}")

    # 검증
    print("\n[5] 검증...")
    loaded = repo.get_stock_data(
        "025980",
        date(2015, 1, 1),
        date(2025, 10, 18)
    )

    print(f"  DB 조회: {len(loaded)}건")
    if len(loaded) > 0:
        print(f"  기간: {loaded[0].date} ~ {loaded[-1].date}")
        print(f"\n  첫 데이터:")
        print(f"    날짜: {loaded[0].date}")
        print(f"    시가: {loaded[0].open:,}원")
        print(f"    고가: {loaded[0].high:,}원")
        print(f"    저가: {loaded[0].low:,}원")
        print(f"    종가: {loaded[0].close:,}원")
        print(f"    거래량: {loaded[0].volume:,}주")

        print(f"\n  마지막 데이터:")
        print(f"    날짜: {loaded[-1].date}")
        print(f"    시가: {loaded[-1].open:,}원")
        print(f"    고가: {loaded[-1].high:,}원")
        print(f"    저가: {loaded[-1].low:,}원")
        print(f"    종가: {loaded[-1].close:,}원")
        print(f"    거래량: {loaded[-1].volume:,}주")

    print("\n" + "=" * 70)
    print("수집 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
