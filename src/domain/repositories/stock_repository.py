"""
Stock Repository Interface - 주식 데이터 저장소 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from ..entities.stock import Stock


class IStockRepository(ABC):
    """주식 데이터 저장소 인터페이스"""

    @abstractmethod
    def get_all_tickers(self, market: str = "ALL") -> List[str]:
        """
        전체 종목 코드 조회

        Args:
            market: 시장 구분 (KOSPI, KOSDAQ, ALL)

        Returns:
            종목 코드 리스트
        """
        pass

    @abstractmethod
    def get_stock_data(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """
        특정 종목의 데이터 조회

        Args:
            ticker: 종목 코드
            start_date: 시작일
            end_date: 종료일

        Returns:
            주식 데이터 리스트
        """
        pass

    @abstractmethod
    def get_multiple_stocks_data(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """
        여러 종목의 데이터 일괄 조회

        Args:
            tickers: 종목 코드 리스트
            start_date: 시작일
            end_date: 종료일

        Returns:
            주식 데이터 리스트
        """
        pass

    @abstractmethod
    def save_stock_data(self, stocks: List[Stock]) -> bool:
        """
        주식 데이터 저장

        Args:
            stocks: 주식 데이터 리스트

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    def get_market_cap(
        self,
        date: date,
        market: str = "ALL",
        top_n: Optional[int] = None
    ) -> List[tuple]:
        """
        시가총액 순위 조회

        Args:
            date: 조회 날짜
            market: 시장 구분
            top_n: 상위 N개 (None이면 전체)

        Returns:
            (ticker, market_cap) 튜플 리스트
        """
        pass
