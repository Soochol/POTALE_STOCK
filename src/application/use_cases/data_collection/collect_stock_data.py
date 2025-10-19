"""
Collect Stock Data Use Case - 주식 데이터 수집 유스케이스
"""
from datetime import date
from typing import List
from src.domain.entities.stock import Stock
from src.domain.repositories.stock_repository import IStockRepository


class CollectStockDataUseCase:
    """주식 데이터 수집 유스케이스"""

    def __init__(self, stock_repository: IStockRepository):
        self.stock_repository = stock_repository

    def execute(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        save: bool = True
    ) -> List[Stock]:
        """
        주식 데이터 수집 실행

        Args:
            tickers: 종목 코드 리스트
            start_date: 시작일
            end_date: 종료일
            save: 수집 후 저장 여부

        Returns:
            수집된 주식 데이터 리스트
        """
        # 데이터 수집
        stocks = self.stock_repository.get_multiple_stocks_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date
        )

        # 저장 옵션이 활성화된 경우
        if save and stocks:
            self.stock_repository.save_stock_data(stocks)

        return stocks

    def execute_all_market(
        self,
        market: str,
        start_date: date,
        end_date: date,
        top_n: int = None
    ) -> List[Stock]:
        """
        시장 전체 또는 시가총액 상위 N개 종목 수집

        Args:
            market: 시장 구분 (KOSPI, KOSDAQ, ALL)
            start_date: 시작일
            end_date: 종료일
            top_n: 상위 N개 (None이면 전체)

        Returns:
            수집된 주식 데이터 리스트
        """
        # 시가총액 기준으로 종목 선정
        if top_n:
            market_cap_data = self.stock_repository.get_market_cap(
                date=end_date,
                market=market,
                top_n=top_n
            )
            tickers = [ticker for ticker, _ in market_cap_data]
        else:
            tickers = self.stock_repository.get_all_tickers(market=market)

        # 데이터 수집
        return self.execute(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            save=True
        )
