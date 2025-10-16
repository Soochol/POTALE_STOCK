"""
Stock Price Collector - 주식 가격 데이터 수집기
"""
import time
from datetime import date, datetime, timedelta
from typing import List, Optional
from pykrx import stock as pykrx_stock
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..base_collector import BaseCollector, CollectionResult
from ...repositories.sqlite_stock_repository import SqliteStockRepository
from ....domain.entities.stock import Stock


class StockPriceCollector(BaseCollector):
    """주식 가격 데이터 수집기"""

    def __init__(
        self,
        repository: Optional[SqliteStockRepository] = None,
        delay: float = 0.1
    ):
        super().__init__(delay)
        self.repository = repository or SqliteStockRepository()

    def collect_single_stock(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        save: bool = True
    ) -> CollectionResult:
        """
        단일 종목 데이터 수집

        Args:
            ticker: 종목 코드
            start_date: 시작일
            end_date: 종료일
            save: DB 저장 여부

        Returns:
            CollectionResult
        """
        started_at = datetime.now()
        record_count = 0

        try:
            # 종목명 조회
            name = pykrx_stock.get_market_ticker_name(ticker)

            # OHLCV 데이터 조회
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            df = pykrx_stock.get_market_ohlcv(start_str, end_str, ticker)

            if df.empty:
                return CollectionResult(
                    success=False,
                    record_count=0,
                    error_message=f"{ticker}: 데이터가 없습니다",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

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
                    record_count += 1
                except Exception as e:
                    self._log_warning(f"데이터 변환 실패: {idx} - {str(e)}")

            # 저장
            if save and stocks:
                self.repository.save_stock_data(stocks)

            return CollectionResult(
                success=True,
                record_count=record_count,
                started_at=started_at,
                completed_at=datetime.now()
            )

        except Exception as e:
            return CollectionResult(
                success=False,
                record_count=record_count,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )

    def collect_multiple_stocks(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        save: bool = True
    ) -> CollectionResult:
        """
        여러 종목 데이터 일괄 수집

        Args:
            tickers: 종목 코드 리스트
            start_date: 시작일
            end_date: 종료일
            save: DB 저장 여부

        Returns:
            CollectionResult
        """
        self._log_start(f"{len(tickers)}개 종목 데이터 수집")

        started_at = datetime.now()
        total_records = 0
        success_count = 0
        failed_tickers = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"[cyan]데이터 수집 중...",
                total=len(tickers)
            )

            for ticker in tickers:
                result = self.collect_single_stock(ticker, start_date, end_date, save)

                if result.success:
                    total_records += result.record_count
                    success_count += 1
                else:
                    failed_tickers.append((ticker, result.error_message))

                # API 호출 제한 방지
                time.sleep(self.delay)
                progress.update(task, advance=1)

        completed_at = datetime.now()

        # 결과 출력
        self._log_success(f"성공: {success_count}/{len(tickers)} 종목")
        self._log_success(f"총 {total_records}개 레코드 수집")

        if failed_tickers:
            self._log_warning(f"실패: {len(failed_tickers)}개 종목")
            for ticker, error in failed_tickers[:5]:  # 처음 5개만 표시
                self._log_warning(f"  - {ticker}: {error}")

        return CollectionResult(
            success=len(failed_tickers) == 0,
            record_count=total_records,
            error_message=f"{len(failed_tickers)} 종목 실패" if failed_tickers else None,
            started_at=started_at,
            completed_at=completed_at
        )

    def collect_market(
        self,
        market: str = "KOSPI",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: Optional[int] = None
    ) -> CollectionResult:
        """
        시장 전체 또는 시가총액 상위 N개 종목 수집

        Args:
            market: 시장 구분 (KOSPI, KOSDAQ, ALL)
            start_date: 시작일 (기본: 1년 전)
            end_date: 종료일 (기본: 오늘)
            top_n: 시가총액 상위 N개 (None이면 전체)

        Returns:
            CollectionResult
        """
        # 기본 날짜 설정
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # 종목 코드 조회
        if top_n:
            # 시가총액 상위 N개
            date_str = end_date.strftime("%Y%m%d")
            if market == "ALL":
                kospi_df = pykrx_stock.get_market_cap(date_str, market="KOSPI")
                kosdaq_df = pykrx_stock.get_market_cap(date_str, market="KOSDAQ")
                import pandas as pd
                df = pd.concat([kospi_df, kosdaq_df])
            else:
                df = pykrx_stock.get_market_cap(date_str, market=market)

            df = df.sort_values('시가총액', ascending=False).head(top_n)
            tickers = df.index.tolist()
        else:
            # 전체 종목
            today_str = date.today().strftime("%Y%m%d")
            if market == "ALL":
                kospi = pykrx_stock.get_market_ticker_list(today_str, market="KOSPI")
                kosdaq = pykrx_stock.get_market_ticker_list(today_str, market="KOSDAQ")
                tickers = kospi + kosdaq
            else:
                tickers = pykrx_stock.get_market_ticker_list(today_str, market=market)

        # 데이터 수집
        return self.collect_multiple_stocks(tickers, start_date, end_date, save=True)

    def update_recent_data(
        self,
        tickers: Optional[List[str]] = None,
        days: int = 7
    ) -> CollectionResult:
        """
        최근 N일 데이터 업데이트

        Args:
            tickers: 종목 코드 리스트 (None이면 DB의 모든 종목)
            days: 최근 N일

        Returns:
            CollectionResult
        """
        if tickers is None:
            tickers = self.repository.get_all_tickers()

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        self._log_start(f"최근 {days}일 데이터 업데이트")
        return self.collect_multiple_stocks(tickers, start_date, end_date, save=True)

    def collect(
        self,
        tickers: Optional[List[str]] = None,
        market: str = "KOSPI",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        top_n: Optional[int] = None
    ) -> CollectionResult:
        """
        데이터 수집 실행 (메인 메서드)

        Args:
            tickers: 종목 코드 리스트 (우선순위 1)
            market: 시장 구분 (tickers가 None일 때 사용)
            start_date: 시작일
            end_date: 종료일
            top_n: 시가총액 상위 N개

        Returns:
            CollectionResult
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        if tickers:
            return self.collect_multiple_stocks(tickers, start_date, end_date, save=True)
        else:
            return self.collect_market(market, start_date, end_date, top_n)
