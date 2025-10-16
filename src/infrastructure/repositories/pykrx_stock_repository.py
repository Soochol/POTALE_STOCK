"""
PyKrx Stock Repository - pykrx를 사용한 주식 데이터 저장소 구현
"""
from datetime import date
from typing import List, Optional
import time
from pykrx import stock as pykrx_stock
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...domain.entities.stock import Stock
from ...domain.repositories.stock_repository import IStockRepository

console = Console()


class PyKrxStockRepository(IStockRepository):
    """pykrx를 사용한 주식 데이터 저장소"""

    def __init__(self, delay: float = 0.1):
        """
        Args:
            delay: API 호출 간 대기 시간 (초)
        """
        self.delay = delay
        self.console = Console()

    def get_all_tickers(self, market: str = "ALL") -> List[str]:
        """전체 종목 코드 조회"""
        try:
            today = date.today().strftime("%Y%m%d")

            if market == "ALL":
                kospi = pykrx_stock.get_market_ticker_list(today, market="KOSPI")
                kosdaq = pykrx_stock.get_market_ticker_list(today, market="KOSDAQ")
                tickers = kospi + kosdaq
            else:
                tickers = pykrx_stock.get_market_ticker_list(today, market=market)

            console.print(f"[green]✓[/green] {len(tickers)}개 종목 코드 조회 완료")
            return tickers

        except Exception as e:
            console.print(f"[red]✗[/red] 종목 코드 조회 실패: {str(e)}")
            return []

    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """특정 종목의 데이터 조회"""
        try:
            # 날짜 형식 변환
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")

            # 종목명 조회
            name = pykrx_stock.get_market_ticker_name(ticker)

            # OHLCV 데이터 조회
            df = pykrx_stock.get_market_ohlcv(start_str, end_str, ticker)

            if df.empty:
                return []

            # Stock 엔티티로 변환
            stocks = []
            for idx, row in df.iterrows():
                try:
                    stock = Stock(
                        ticker=ticker,
                        name=name,
                        date=idx.date(),
                        open=float(row['시가']),
                        high=float(row['고가']),
                        low=float(row['저가']),
                        close=float(row['종가']),
                        volume=int(row['거래량'])
                    )
                    stocks.append(stock)
                except Exception as e:
                    # 잘못된 데이터는 건너뜀
                    continue

            return stocks

        except Exception as e:
            console.print(f"[red]✗[/red] {ticker} 데이터 조회 실패: {str(e)}")
            return []

    def get_multiple_stocks_data(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """여러 종목의 데이터 일괄 조회"""
        all_stocks = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]{len(tickers)}개 종목 데이터 수집 중...",
                total=len(tickers)
            )

            for ticker in tickers:
                stocks = self.get_stock_data(ticker, start_date, end_date)
                all_stocks.extend(stocks)

                # API 호출 제한 방지
                time.sleep(self.delay)
                progress.update(task, advance=1)

        console.print(f"[green]✓[/green] 총 {len(all_stocks)}개 데이터 수집 완료")
        return all_stocks

    def save_stock_data(self, stocks: List[Stock]) -> bool:
        """
        주식 데이터 저장
        (현재는 파일 시스템에 저장하지 않고 메모리에만 보관)
        추후 SQLite 또는 다른 DB로 확장 가능
        """
        # TODO: 실제 저장 로직 구현
        console.print(f"[yellow]![/yellow] 저장 기능은 아직 구현되지 않았습니다.")
        return True

    def get_market_cap(
        self,
        date: date,
        market: str = "ALL",
        top_n: Optional[int] = None
    ) -> List[tuple]:
        """시가총액 순위 조회"""
        try:
            date_str = date.strftime("%Y%m%d")

            if market == "ALL":
                kospi_df = pykrx_stock.get_market_cap(date_str, market="KOSPI")
                kosdaq_df = pykrx_stock.get_market_cap(date_str, market="KOSDAQ")
                import pandas as pd
                df = pd.concat([kospi_df, kosdaq_df])
            else:
                df = pykrx_stock.get_market_cap(date_str, market=market)

            # 시가총액 기준 정렬
            df = df.sort_values('시가총액', ascending=False)

            # 상위 N개 선택
            if top_n:
                df = df.head(top_n)

            # (ticker, market_cap) 튜플 리스트로 변환
            result = [(ticker, row['시가총액']) for ticker, row in df.iterrows()]

            console.print(f"[green]✓[/green] 시가총액 데이터 {len(result)}개 조회 완료")
            return result

        except Exception as e:
            console.print(f"[red]✗[/red] 시가총액 조회 실패: {str(e)}")
            return []
