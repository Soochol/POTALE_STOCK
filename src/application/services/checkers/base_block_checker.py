"""
Base Block Checker - 공통 블록 조건 검사 베이스 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable, Tuple
from datetime import date

from src.domain.entities import Stock
from src.application.services.common.utils import get_previous_trading_day_stock


class ConditionCheck:
    """조건 검사 정의"""
    def __init__(
        self,
        name: str,
        field_name: str,
        check_fn: Callable,
        required: bool = False
    ):
        self.name = name
        self.field_name = field_name
        self.check_fn = check_fn
        self.required = required


class BaseBlockChecker(ABC):
    """
    블록 진입 조건 검사 베이스 클래스

    Block1/2/3/4 Checker가 공통으로 사용하는 진입 조건 검사 로직을 포함합니다.
    - 조건 1: 등락률
    - 조건 2: 고가 >= 이동평균선
    - 조건 3: 이격도
    - 조건 4: 거래대금
    - 조건 5: 신고거래량
    - 조건 6: 전날 거래량 비율
    - 조건 7: 신고가
    """

    def _check_surge_rate(
        self,
        stock: Stock,
        indicators: Dict,
        surge_rate: Optional[float]
    ) -> bool:
        """조건 1: 등락률 검사"""
        if surge_rate is None:
            return True

        rate = indicators.get('rate', 0)
        return rate >= surge_rate

    def _check_ma_high(
        self,
        stock: Stock,
        indicators: Dict,
        ma_period: Optional[int],
        high_above_ma: Optional[bool]
    ) -> bool:
        """조건 2: 고가 >= 이동평균선 검사"""
        if not (ma_period and high_above_ma):
            return True

        ma_key = f'MA_{ma_period}'
        ma_value = indicators.get(ma_key)
        if ma_value is None:
            return False

        return stock.high >= ma_value

    def _check_deviation(
        self,
        stock: Stock,
        indicators: Dict,
        max_deviation: Optional[float]
    ) -> bool:
        """조건 3: 이격도 검사"""
        if max_deviation is None:
            return True

        deviation = indicators.get('deviation', 100)
        return deviation <= max_deviation

    def _check_trading_value(
        self,
        stock: Stock,
        indicators: Dict,
        min_trading_value: Optional[float]
    ) -> bool:
        """조건 4: 거래대금 검사"""
        if min_trading_value is None:
            return True

        trading_value = indicators.get('trading_value_100m', 0)
        return trading_value >= min_trading_value

    def _check_volume_high(
        self,
        stock: Stock,
        indicators: Dict,
        volume_high_months: Optional[int]
    ) -> bool:
        """조건 5: 신고거래량 검사"""
        if volume_high_months is None:
            return True

        is_volume_high = indicators.get('is_volume_high', False)
        return is_volume_high

    def _check_volume_spike(
        self,
        stock: Stock,
        indicators: Dict,
        volume_spike_ratio: Optional[float],
        all_stocks: List[Stock]
    ) -> bool:
        """조건 6: 전날 거래량 비율 검사"""
        if volume_spike_ratio is None:
            return True

        prev_stock = get_previous_trading_day_stock(stock.date, all_stocks)

        if prev_stock is None or prev_stock.volume <= 0:
            return False

        ratio = volume_spike_ratio / 100.0
        required_volume = prev_stock.volume * ratio
        return stock.volume >= required_volume

    def _check_price_high(
        self,
        stock: Stock,
        indicators: Dict,
        price_high_months: Optional[int]
    ) -> bool:
        """조건 7: 신고가 검사"""
        if price_high_months is None:
            return True

        is_new_high = indicators.get('is_new_high', False)
        return is_new_high

    def check_common_entry_conditions(
        self,
        stock: Stock,
        base_condition,
        all_stocks: List[Stock]
    ) -> bool:
        """
        공통 진입 조건 검사 (7가지 조건)

        Args:
            stock: 주식 데이터 (지표 포함)
            base_condition: BaseEntryCondition 객체
            all_stocks: 전체 주식 데이터 리스트

        Returns:
            모든 조건 만족 여부
        """
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators

        # 조건 1: 등락률
        if not self._check_surge_rate(stock, indicators, base_condition.block1_entry_surge_rate):
            return False

        # 조건 2: 고가 >= 이동평균선
        if not self._check_ma_high(
            stock, indicators,
            base_condition.block1_entry_ma_period,
            base_condition.block1_entry_high_above_ma
        ):
            return False

        # 조건 3: 이격도
        if not self._check_deviation(stock, indicators, base_condition.block1_entry_max_deviation_ratio):
            return False

        # 조건 4: 거래대금
        if not self._check_trading_value(stock, indicators, base_condition.block1_entry_min_trading_value):
            return False

        # 조건 5: 신고거래량
        if not self._check_volume_high(stock, indicators, base_condition.block1_entry_volume_high_months):
            return False

        # 조건 6: 전날 거래량 비율
        if not self._check_volume_spike(stock, indicators, base_condition.block1_entry_volume_spike_ratio, all_stocks):
            return False

        # 조건 7: 신고가
        if not self._check_price_high(stock, indicators, base_condition.block1_entry_price_high_months):
            return False

        return True

    @abstractmethod
    def check_entry(self, condition, stock: Stock, all_stocks: List[Stock]) -> bool:
        """
        블록 진입 조건 검사 (서브클래스에서 구현)

        공통 조건 + 블록별 추가 조건을 검사합니다.
        """
        pass
