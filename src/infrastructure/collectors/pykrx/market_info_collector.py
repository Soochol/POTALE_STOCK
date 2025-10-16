"""
Market Info Collector - 시장 정보 및 종목 메타데이터 수집기
"""
import time
from datetime import date, datetime
from typing import List, Optional
from pykrx import stock as pykrx_stock
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..base_collector import BaseCollector, CollectionResult
from ...repositories.sqlite_stock_repository import SqliteStockRepository


class MarketInfoCollector(BaseCollector):
    """시장 정보 수집기"""

    def __init__(
        self,
        repository: Optional[SqliteStockRepository] = None,
        delay: float = 0.1
    ):
        super().__init__(delay)
        self.repository = repository or SqliteStockRepository()

    def collect_stock_info(
        self,
        market: str = "ALL"
    ) -> CollectionResult:
        """
        종목 기본 정보 수집 (종목코드, 종목명, 시장구분)

        Args:
            market: 시장 구분 (KOSPI, KOSDAQ, ALL)

        Returns:
            CollectionResult
        """
        self._log_start(f"{market} 종목 정보 수집")

        started_at = datetime.now()
        record_count = 0

        try:
            today = date.today().strftime("%Y%m%d")

            # 시장별 종목 조회
            if market == "ALL":
                kospi_tickers = pykrx_stock.get_market_ticker_list(today, market="KOSPI")
                kosdaq_tickers = pykrx_stock.get_market_ticker_list(today, market="KOSDAQ")
                market_tickers = [
                    (ticker, "KOSPI") for ticker in kospi_tickers
                ] + [
                    (ticker, "KOSDAQ") for ticker in kosdaq_tickers
                ]
            else:
                tickers = pykrx_stock.get_market_ticker_list(today, market=market)
                market_tickers = [(ticker, market) for ticker in tickers]

            # 종목 정보 저장
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]종목 정보 수집 중...",
                    total=len(market_tickers)
                )

                for ticker, mkt in market_tickers:
                    try:
                        name = pykrx_stock.get_market_ticker_name(ticker)
                        self.repository.save_stock_info(
                            ticker=ticker,
                            name=name,
                            market=mkt
                        )
                        record_count += 1
                    except Exception as e:
                        self._log_warning(f"{ticker} 정보 수집 실패: {str(e)}")

                    time.sleep(self.delay)
                    progress.update(task, advance=1)

            self._log_success(f"{record_count}개 종목 정보 저장 완료")

            return CollectionResult(
                success=True,
                record_count=record_count,
                started_at=started_at,
                completed_at=datetime.now()
            )

        except Exception as e:
            self._log_error(f"종목 정보 수집 실패: {str(e)}")
            return CollectionResult(
                success=False,
                record_count=record_count,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )

    def collect_market_cap(
        self,
        target_date: Optional[date] = None,
        market: str = "ALL"
    ) -> CollectionResult:
        """
        시가총액 및 기본적 분석 데이터 수집

        Args:
            target_date: 조회 날짜 (기본: 오늘)
            market: 시장 구분

        Returns:
            CollectionResult
        """
        if target_date is None:
            target_date = date.today()

        self._log_start(f"{target_date} 시가총액 데이터 수집")

        started_at = datetime.now()
        record_count = 0

        try:
            date_str = target_date.strftime("%Y%m%d")

            # 시가총액 데이터 조회
            if market == "ALL":
                kospi_cap = pykrx_stock.get_market_cap(date_str, market="KOSPI")
                kosdaq_cap = pykrx_stock.get_market_cap(date_str, market="KOSDAQ")
                import pandas as pd
                cap_df = pd.concat([kospi_cap, kosdaq_cap])
            else:
                cap_df = pykrx_stock.get_market_cap(date_str, market=market)

            # 기본적 분석 데이터 조회
            if market == "ALL":
                kospi_fundamental = pykrx_stock.get_market_fundamental(date_str, market="KOSPI")
                kosdaq_fundamental = pykrx_stock.get_market_fundamental(date_str, market="KOSDAQ")
                fundamental_df = pd.concat([kospi_fundamental, kosdaq_fundamental])
            else:
                fundamental_df = pykrx_stock.get_market_fundamental(date_str, market=market)

            # 데이터 병합 및 저장
            for ticker in cap_df.index:
                try:
                    market_cap = int(cap_df.loc[ticker, '시가총액'])

                    # 기본적 분석 데이터
                    per = None
                    pbr = None
                    eps = None
                    div = None

                    if ticker in fundamental_df.index:
                        per = float(fundamental_df.loc[ticker, 'PER']) if 'PER' in fundamental_df.columns else None
                        pbr = float(fundamental_df.loc[ticker, 'PBR']) if 'PBR' in fundamental_df.columns else None
                        eps = float(fundamental_df.loc[ticker, 'EPS']) if 'EPS' in fundamental_df.columns else None
                        div = float(fundamental_df.loc[ticker, 'DIV']) if 'DIV' in fundamental_df.columns else None

                    self.repository.save_market_data(
                        ticker=ticker,
                        date=target_date,
                        market_cap=market_cap,
                        per=per,
                        pbr=pbr,
                        eps=eps,
                        div=div
                    )
                    record_count += 1

                except Exception as e:
                    self._log_warning(f"{ticker} 시장 데이터 저장 실패: {str(e)}")

            self._log_success(f"{record_count}개 시가총액 데이터 저장 완료")

            return CollectionResult(
                success=True,
                record_count=record_count,
                started_at=started_at,
                completed_at=datetime.now()
            )

        except Exception as e:
            self._log_error(f"시가총액 데이터 수집 실패: {str(e)}")
            return CollectionResult(
                success=False,
                record_count=record_count,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )

    def collect(
        self,
        market: str = "ALL",
        target_date: Optional[date] = None,
        include_market_cap: bool = True
    ) -> CollectionResult:
        """
        시장 정보 수집 실행 (메인 메서드)

        Args:
            market: 시장 구분
            target_date: 조회 날짜
            include_market_cap: 시가총액 데이터 포함 여부

        Returns:
            CollectionResult
        """
        # 종목 정보 수집
        info_result = self.collect_stock_info(market)

        # 시가총액 수집
        if include_market_cap:
            cap_result = self.collect_market_cap(target_date, market)

            return CollectionResult(
                success=info_result.success and cap_result.success,
                record_count=info_result.record_count + cap_result.record_count,
                error_message=cap_result.error_message if not cap_result.success else info_result.error_message,
                started_at=info_result.started_at,
                completed_at=cap_result.completed_at
            )

        return info_result
