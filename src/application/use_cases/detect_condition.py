"""
Detect Condition Use Case - 조건 탐지 유스케이스
"""
from datetime import datetime
from typing import List
from ...domain.entities.stock import Stock
from ...domain.entities.condition import Condition
from ...domain.entities.detection_result import DetectionResult
from ...domain.repositories.condition_repository import IConditionRepository
from ..services.indicator_calculator import IndicatorCalculator
from ..services.condition_checker import ConditionChecker


class DetectConditionUseCase:
    """조건 탐지 유스케이스"""

    def __init__(
        self,
        condition_repository: IConditionRepository,
        indicator_calculator: IndicatorCalculator,
        condition_checker: ConditionChecker
    ):
        self.condition_repository = condition_repository
        self.indicator_calculator = indicator_calculator
        self.condition_checker = condition_checker

    def execute(
        self,
        condition_name: str,
        stocks: List[Stock]
    ) -> DetectionResult:
        """
        조건 탐지 실행

        Args:
            condition_name: 조건 이름
            stocks: 검사할 주식 데이터 리스트

        Returns:
            탐지 결과
        """
        # 조건 조회
        condition = self.condition_repository.get_by_name(condition_name)
        if not condition:
            raise ValueError(f"조건을 찾을 수 없습니다: {condition_name}")

        # 조건 유효성 검사
        if not condition.validate():
            raise ValueError(f"유효하지 않은 조건입니다: {condition_name}")

        # 종목별로 그룹화
        stocks_by_ticker = self._group_by_ticker(stocks)

        # 결과 객체 생성
        result = DetectionResult(
            condition_name=condition_name,
            detected_at=datetime.now()
        )

        # 각 종목에 대해 조건 검사
        for ticker, ticker_stocks in stocks_by_ticker.items():
            # 지표 계산
            stocks_with_indicators = self.indicator_calculator.calculate(
                ticker_stocks
            )

            # 조건 검사
            detected_stocks = self.condition_checker.check(
                condition=condition,
                stocks=stocks_with_indicators
            )

            # 결과에 추가
            for stock in detected_stocks:
                result.add_stock(stock)

        return result

    def _group_by_ticker(self, stocks: List[Stock]) -> dict:
        """종목별로 그룹화"""
        grouped = {}
        for stock in stocks:
            if stock.ticker not in grouped:
                grouped[stock.ticker] = []
            grouped[stock.ticker].append(stock)
        return grouped
