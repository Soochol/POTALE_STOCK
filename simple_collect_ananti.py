"""
아난티 데이터 간단 수집 (패턴 테스트용)
"""
import requests
from datetime import date, datetime
from bs4 import BeautifulSoup
from src.domain.entities.stock import Stock
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.database.connection import DatabaseConnection


def collect_naver_price(ticker: str, start_date: date, end_date: date):
    """네이버 금융에서 일별 시세 수집"""
    url = f"https://finance.naver.com/item/sise_day.naver?code={ticker}&page=1"

    stocks = []
    page = 1

    print(f"네이버 금융 데이터 수집 중...")

    while True:
        print(f"  페이지 {page} 수집 중...", end="\r")

        response = requests.get(f"https://finance.naver.com/item/sise_day.naver?code={ticker}&page={page}")
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'type2'})

        if not table:
            break

        rows = table.find('tbody').find_all('tr')

        found_data = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 7:
                continue

            # 날짜
            date_span = cols[0].find('span', {'class': 'tah'})
            if not date_span:
                continue

            date_str = date_span.text.strip()
            stock_date = datetime.strptime(date_str, "%Y.%m.%d").date()

            # 날짜 범위 체크
            if stock_date < start_date:
                return stocks  # 범위 벗어나면 종료

            if stock_date > end_date:
                continue

            found_data = True

            # 가격 데이터
            try:
                close = int(cols[1].text.strip().replace(',', ''))
                diff = cols[2].text.strip().replace(',', '')
                open_price = int(cols[3].text.strip().replace(',', ''))
                high = int(cols[4].text.strip().replace(',', ''))
                low = int(cols[5].text.strip().replace(',', ''))
                volume = int(cols[6].text.strip().replace(',', ''))

                stock = Stock(
                    ticker=ticker,
                    date=stock_date,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    trading_value=volume * close  # 거래대금 (원)
                )

                stocks.append(stock)

            except (ValueError, AttributeError) as e:
                continue

        if not found_data:
            break

        page += 1

        # 너무 많은 페이지 방지
        if page > 500:
            break

    print(f"\n  총 {len(stocks)}건 수집 완료")
    return sorted(stocks, key=lambda x: x.date)


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
    print("\n[2] 네이버 금융에서 데이터 수집...")
    start_date = date(2015, 1, 1)
    end_date = date(2025, 10, 18)

    stocks = collect_naver_price("025980", start_date, end_date)

    if not stocks:
        print("  데이터 수집 실패")
        return

    # 저장
    print("\n[3] DB 저장 중...")
    repo = SqliteStockRepository("data/database/stock_data.db")

    saved_count = 0
    for stock in stocks:
        try:
            repo.save(stock)
            saved_count += 1
        except Exception as e:
            print(f"  저장 오류: {stock.date} - {e}")

    print(f"  저장 완료: {saved_count}건")

    # 검증
    print("\n[4] 검증...")
    loaded = repo.get_stock_data("025980", start_date, end_date)
    print(f"  DB 조회: {len(loaded)}건")
    if len(loaded) > 0:
        print(f"  기간: {loaded[0].date} ~ {loaded[-1].date}")
        print(f"  첫 데이터: {loaded[0].date} 종가={loaded[0].close:,}원 거래량={loaded[0].volume:,}주")
        print(f"  마지막: {loaded[-1].date} 종가={loaded[-1].close:,}원 거래량={loaded[-1].volume:,}주")

    print("\n" + "=" * 70)
    print("수집 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
