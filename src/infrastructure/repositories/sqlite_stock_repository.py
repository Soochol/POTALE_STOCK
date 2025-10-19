"""
SQLite Stock Repository - SQLite를 사용한 주식 데이터 저장소 구현
"""
from datetime import date
from typing import List, Optional
from sqlalchemy import and_, func
from sqlalchemy.dialects.sqlite import insert
from rich.console import Console

from ...domain.entities.stock import Stock
from ...domain.repositories.stock_repository import IStockRepository
from ..database.connection import DatabaseConnection, get_db_session
from ..database.models import StockInfo, StockPrice, MarketData

console = Console()


class SqliteStockRepository(IStockRepository):
    """SQLite를 사용한 주식 데이터 저장소"""

    def __init__(self, db_path: str = "data/database/stock_data.db"):
        self.db_path = db_path
        self.console = Console()

    def get_all_tickers(self, market: str = "ALL") -> List[str]:
        """전체 종목 코드 조회"""
        with get_db_session(self.db_path) as session:
            query = session.query(StockInfo.ticker)

            if market != "ALL":
                query = query.filter(StockInfo.market == market)

            tickers = [row[0] for row in query.all()]

            console.print(f"[green]✓[/green] {len(tickers)}개 종목 코드 조회 완료")
            return tickers

    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """특정 종목의 데이터 조회"""
        with get_db_session(self.db_path) as session:
            # StockInfo와 StockPrice 조인
            query = session.query(
                StockPrice, StockInfo.name
            ).join(
                StockInfo, StockPrice.ticker == StockInfo.ticker
            ).filter(
                and_(
                    StockPrice.ticker == ticker,
                    StockPrice.date >= start_date,
                    StockPrice.date <= end_date
                )
            ).order_by(StockPrice.date)

            results = query.all()

            stocks = []
            for price, name in results:
                try:
                    # 거래대금 계산 (종가 * 거래량)
                    trading_value = price.close * price.volume if price.close and price.volume else None

                    stock = Stock(
                        ticker=price.ticker,
                        name=name,
                        date=price.date,
                        open=price.open,
                        high=price.high,
                        low=price.low,
                        close=price.close,
                        volume=price.volume,
                        trading_value=trading_value
                    )
                    stocks.append(stock)
                except Exception as e:
                    console.print(f"[yellow]![/yellow] 데이터 변환 실패: {price.id} - {str(e)}")

            return stocks

    def get_multiple_stocks_data(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """여러 종목의 데이터 일괄 조회"""
        all_stocks = []

        for ticker in tickers:
            stocks = self.get_stock_data(ticker, start_date, end_date)
            all_stocks.extend(stocks)

        console.print(f"[green]✓[/green] 총 {len(all_stocks)}개 데이터 조회 완료")
        return all_stocks

    def save_stock_data(self, stocks: List[Stock]) -> bool:
        """주식 데이터 저장 (upsert)"""
        if not stocks:
            return True

        try:
            with get_db_session(self.db_path) as session:
                saved_count = 0

                for stock in stocks:
                    # StockInfo 저장 (없으면 생성)
                    stock_info = session.query(StockInfo).filter(
                        StockInfo.ticker == stock.ticker
                    ).first()

                    if not stock_info:
                        stock_info = StockInfo(
                            ticker=stock.ticker,
                            name=stock.name,
                            market="UNKNOWN"  # 나중에 업데이트 필요
                        )
                        session.add(stock_info)

                    # StockPrice upsert (중복 시 업데이트)
                    stmt = insert(StockPrice).values(
                        ticker=stock.ticker,
                        date=stock.date,
                        open=stock.open,
                        high=stock.high,
                        low=stock.low,
                        close=stock.close,
                        volume=stock.volume
                    )

                    stmt = stmt.on_conflict_do_update(
                        index_elements=['ticker', 'date'],
                        set_={
                            'open': stock.open,
                            'high': stock.high,
                            'low': stock.low,
                            'close': stock.close,
                            'volume': stock.volume
                        }
                    )

                    session.execute(stmt)
                    saved_count += 1

                session.commit()
                console.print(f"[green]✓[/green] {saved_count}개 데이터 저장 완료")
                return True

        except Exception as e:
            console.print(f"[red]✗[/red] 데이터 저장 실패: {str(e)}")
            return False

    def save_stock_info(
        self,
        ticker: str,
        name: str,
        market: str,
        sector: Optional[str] = None
    ) -> bool:
        """종목 정보 저장"""
        try:
            with get_db_session(self.db_path) as session:
                stock_info = session.query(StockInfo).filter(
                    StockInfo.ticker == ticker
                ).first()

                if stock_info:
                    # 업데이트
                    stock_info.name = name
                    stock_info.market = market
                    if sector:
                        stock_info.sector = sector
                else:
                    # 생성
                    stock_info = StockInfo(
                        ticker=ticker,
                        name=name,
                        market=market,
                        sector=sector
                    )
                    session.add(stock_info)

                session.commit()
                return True

        except Exception as e:
            console.print(f"[red]✗[/red] 종목 정보 저장 실패: {str(e)}")
            return False

    def get_market_cap(
        self,
        date: date,
        market: str = "ALL",
        top_n: Optional[int] = None
    ) -> List[tuple]:
        """시가총액 순위 조회"""
        with get_db_session(self.db_path) as session:
            query = session.query(
                MarketData.ticker,
                MarketData.market_cap
            ).filter(
                MarketData.date == date
            )

            if market != "ALL":
                query = query.join(StockInfo).filter(StockInfo.market == market)

            query = query.order_by(MarketData.market_cap.desc())

            if top_n:
                query = query.limit(top_n)

            results = [(row.ticker, row.market_cap) for row in query.all()]

            console.print(f"[green]✓[/green] 시가총액 데이터 {len(results)}개 조회 완료")
            return results

    def save_market_data(
        self,
        ticker: str,
        date: date,
        market_cap: Optional[int] = None,
        per: Optional[float] = None,
        pbr: Optional[float] = None,
        eps: Optional[float] = None,
        div: Optional[float] = None
    ) -> bool:
        """시장 데이터 저장"""
        try:
            with get_db_session(self.db_path) as session:
                # Upsert
                stmt = insert(MarketData).values(
                    ticker=ticker,
                    date=date,
                    market_cap=market_cap,
                    per=per,
                    pbr=pbr,
                    eps=eps,
                    div=div
                )

                stmt = stmt.on_conflict_do_update(
                    index_elements=['ticker', 'date'],
                    set_={
                        'market_cap': market_cap,
                        'per': per,
                        'pbr': pbr,
                        'eps': eps,
                        'div': div
                    }
                )

                session.execute(stmt)
                session.commit()
                return True

        except Exception as e:
            console.print(f"[red]✗[/red] 시장 데이터 저장 실패: {str(e)}")
            return False

    def get_date_range(self, ticker: str) -> Optional[tuple]:
        """특정 종목의 데이터 날짜 범위 조회"""
        with get_db_session(self.db_path) as session:
            result = session.query(
                func.min(StockPrice.date),
                func.max(StockPrice.date)
            ).filter(
                StockPrice.ticker == ticker
            ).first()

            return result if result[0] else None

    def count_records(self, ticker: Optional[str] = None) -> int:
        """레코드 수 조회"""
        with get_db_session(self.db_path) as session:
            query = session.query(func.count(StockPrice.id))

            if ticker:
                query = query.filter(StockPrice.ticker == ticker)

            return query.scalar()

    def delete_stock_data(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """주식 데이터 삭제"""
        try:
            with get_db_session(self.db_path) as session:
                query = session.query(StockPrice).filter(
                    StockPrice.ticker == ticker
                )

                if start_date:
                    query = query.filter(StockPrice.date >= start_date)
                if end_date:
                    query = query.filter(StockPrice.date <= end_date)

                count = query.delete()
                session.commit()

                console.print(f"[green]✓[/green] {count}개 데이터 삭제 완료")
                return count

        except Exception as e:
            console.print(f"[red]✗[/red] 데이터 삭제 실패: {str(e)}")
            return 0
