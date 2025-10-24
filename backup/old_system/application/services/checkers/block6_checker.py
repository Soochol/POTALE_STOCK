"""
Block6 Checker Service - 블록6 진입/종료 조건 검사 서비스
"""
from datetime import date, timedelta
from typing import List, Optional

from src.domain.entities import (
    Block1Condition,
    Block1Detection,
    Block2Detection,
    Block3Detection,
    Block4Detection,
    Block5Detection,
    Block6Condition,
    Block6Detection,
    Stock,
)

from ..common.utils import get_previous_trading_day_stock
from .block1_checker import Block1Checker
from .block2_checker import Block2Checker
from .block3_checker import Block3Checker
from .block4_checker import Block4Checker
from .block5_checker import Block5Checker

class Block6Checker:
    """블록6 진입 및 종료 조건 검사 서비스"""

    def __init__(self) -> None:
        """Block6Checker 초기화"""
        self.block5_checker = Block5Checker()
        self.block4_checker = Block4Checker()
        self.block3_checker = Block3Checker()
        self.block2_checker = Block2Checker()
        self.block1_checker = Block1Checker()

    def check_entry(
        self,
        condition: Block6Condition,
        stock: Stock,
        all_stocks: List[Stock],
        prev_seed_block1: Optional[Block1Detection] = None,
        prev_seed_block2: Optional[Block2Detection] = None,
        prev_seed_block3: Optional[Block3Detection] = None,
        prev_seed_block4: Optional[Block4Detection] = None,
        prev_seed_block5: Optional[Block5Detection] = None
    ) -> bool:
        """
        블록6 진입 조건 검사
        = 블록5의 모든 조건 + 블록6 추가 조건

        Args:
            condition: 블록6 조건
            stock: 주식 데이터 (지표 포함)
            all_stocks: 전체 주식 데이터 리스트
            prev_seed_block1: Block1 Seed
            prev_seed_block2: Block2 Seed
            prev_seed_block3: Block3 Seed
            prev_seed_block4: Block4 Seed
            prev_seed_block5: Block5 Seed (Block6 조건의 volume_ratio, low_price_margin 비교 기준)

        Returns:
            모든 조건 만족 여부
        """
        # 1. Block1~Block5 기본 조건 검사
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators

        # Block1 조건
        if condition.base.block1_entry_surge_rate is not None:
            rate = indicators.get('rate', 0)
            if rate < condition.base.block1_entry_surge_rate:
                return False

        if condition.base.block1_entry_ma_period:
            ma_key = f'MA_{condition.base.block1_entry_ma_period}'
            ma_value = indicators.get(ma_key)
            if ma_value is None or stock.high < ma_value:
                return False

        if condition.base.block1_entry_max_deviation_ratio is not None:
            deviation_field = f'deviation_{condition.base.block1_entry_ma_period}'
            deviation = indicators.get(deviation_field, 100)
            if deviation > condition.base.block1_entry_max_deviation_ratio:
                return False

        if condition.base.block1_entry_min_trading_value is not None:
            trading_value = indicators.get('trading_value_100m', 0)
            if trading_value < condition.base.block1_entry_min_trading_value:
                return False

        if condition.base.block1_entry_volume_high_days is not None:
            field_name = f'is_volume_high_{condition.base.block1_entry_volume_high_days}d'
            is_volume_high = indicators.get(field_name, False)
            if not is_volume_high:
                return False

        if condition.base.block1_entry_volume_spike_ratio is not None:
            prev_stock = get_previous_trading_day_stock(stock.date, all_stocks)
            if prev_stock is None or prev_stock.volume <= 0:
                return False

            ratio = condition.base.block1_entry_volume_spike_ratio / 100.0
            required_volume = prev_stock.volume * ratio
            if stock.volume < required_volume:
                return False

        if condition.base.block1_entry_price_high_days is not None:
            field_name = f'is_new_high_{condition.base.block1_entry_price_high_days}d'
            is_new_high = indicators.get(field_name, False)
            if not is_new_high:
                return False

        # Block2 추가 조건
        if prev_seed_block1 is not None:
            if condition.block2_volume_ratio is not None and prev_seed_block1.peak_volume is not None:
                ratio = condition.block2_volume_ratio / 100.0
                required_volume = prev_seed_block1.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

            if condition.block2_low_price_margin is not None and prev_seed_block1.peak_price is not None:
                margin = condition.block2_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)

                # OR 조건: DB peak_price OR 실제 range_high
                meets_db_peak = threshold_price > prev_seed_block1.peak_price
                range_high = self._get_range_high(
                    prev_seed_block1.started_at,
                    stock.date,
                    stock.ticker,
                    all_stocks
                )
                meets_range_high = range_high is not None and threshold_price > range_high

                if not (meets_db_peak or meets_range_high):
                    return False

        # Block3 추가 조건
        if prev_seed_block2 is not None:
            if condition.block3_volume_ratio is not None and prev_seed_block2.peak_volume is not None:
                ratio = condition.block3_volume_ratio / 100.0
                required_volume = prev_seed_block2.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

            if condition.block3_low_price_margin is not None and prev_seed_block2.peak_price is not None:
                margin = condition.block3_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)

                # OR 조건: DB peak_price OR 실제 range_high
                meets_db_peak = threshold_price > prev_seed_block2.peak_price
                range_high = self._get_range_high(
                    prev_seed_block2.started_at,
                    stock.date,
                    stock.ticker,
                    all_stocks
                )
                meets_range_high = range_high is not None and threshold_price > range_high

                if not (meets_db_peak or meets_range_high):
                    return False

        # Block4 추가 조건
        if prev_seed_block3 is not None:
            if condition.block4_volume_ratio is not None and prev_seed_block3.peak_volume is not None:
                ratio = condition.block4_volume_ratio / 100.0
                required_volume = prev_seed_block3.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

            if condition.block4_low_price_margin is not None and prev_seed_block3.peak_price is not None:
                margin = condition.block4_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)

                # OR 조건: DB peak_price OR 실제 range_high
                meets_db_peak = threshold_price > prev_seed_block3.peak_price
                range_high = self._get_range_high(
                    prev_seed_block3.started_at,
                    stock.date,
                    stock.ticker,
                    all_stocks
                )
                meets_range_high = range_high is not None and threshold_price > range_high

                if not (meets_db_peak or meets_range_high):
                    return False

        # Block5 추가 조건
        if prev_seed_block4 is not None:
            if condition.block5_volume_ratio is not None and prev_seed_block4.peak_volume is not None:
                ratio = condition.block5_volume_ratio / 100.0
                required_volume = prev_seed_block4.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

            if condition.block5_low_price_margin is not None and prev_seed_block4.peak_price is not None:
                margin = condition.block5_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)

                # OR 조건: DB peak_price OR 실제 range_high
                meets_db_peak = threshold_price > prev_seed_block4.peak_price
                range_high = self._get_range_high(
                    prev_seed_block4.started_at,
                    stock.date,
                    stock.ticker,
                    all_stocks
                )
                meets_range_high = range_high is not None and threshold_price > range_high

                if not (meets_db_peak or meets_range_high):
                    return False

        # 2. 블록6 추가 조건 검사
        if condition.block6_volume_ratio is not None:
            if prev_seed_block5 is not None and prev_seed_block5.peak_volume is not None:
                ratio = condition.block6_volume_ratio / 100.0
                required_volume = prev_seed_block5.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

        if condition.block6_low_price_margin is not None:
            if prev_seed_block5 is not None and prev_seed_block5.peak_price is not None:
                margin = condition.block6_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)

                # OR 조건: DB peak_price OR 실제 range_high
                meets_db_peak = threshold_price > prev_seed_block5.peak_price
                range_high = self._get_range_high(
                    prev_seed_block5.started_at,
                    stock.date,
                    stock.ticker,
                    all_stocks
                )
                meets_range_high = range_high is not None and threshold_price > range_high

                if not (meets_db_peak or meets_range_high):
                    return False

        # 모든 조건 만족
        return True

    def check_exit(
        self,
        condition: Block6Condition,
        detection: Block6Detection,
        current_stock: Stock,
        all_stocks: list
    ) -> Optional[str]:
        """블록6 종료 조건 검사"""
        temp_block1_condition = Block1Condition(base=condition.base)

        temp_block1 = Block1Detection(
            ticker=detection.ticker,
            condition_name=detection.condition_name,
            started_at=detection.started_at,
            entry_open=detection.entry_close,
            entry_high=detection.entry_close,
            entry_low=detection.entry_close,
            entry_close=detection.entry_close,
            entry_volume=0,
            peak_price=detection.peak_price
        )

        return self.block1_checker.check_exit(
            temp_block1_condition,
            temp_block1,
            current_stock,
            all_stocks
        )

    def create_detection(
        self,
        condition_name: str,
        stock: Stock,
        prev_block5: Optional[Block5Detection] = None
    ) -> Block6Detection:
        """블록6 탐지 결과 생성"""
        indicators = stock.indicators if hasattr(stock, 'indicators') else {}

        detection = Block6Detection(
            ticker=stock.ticker,
            condition_name=condition_name,
            started_at=stock.date,
            status="active",
            entry_close=stock.close,
            entry_rate=indicators.get('rate'),
        )

        if prev_block5:
            detection.prev_block5_id = prev_block5.id
            detection.prev_block5_peak_price = prev_block5.peak_price
            detection.prev_block5_peak_volume = prev_block5.peak_volume

        return detection

    def check_cooldown(
        self,
        ticker: str,
        current_date: date,
        existing_detections: List[Block6Detection],
        min_start_interval_days: int
    ) -> bool:
        """중복 방지 기간 확인"""
        for detection in existing_detections:
            if detection.ticker != ticker:
                continue

            if detection.status == "active":
                return False

            if detection.ended_at:
                interval_end = detection.started_at + timedelta(days=min_start_interval_days)
                if detection.started_at <= current_date < interval_end:
                    return False

        return True

    def check_min_candles(
        self,
        current_date: date,
        prev_block5: Optional[Block5Detection],
        min_candles: int,
        all_stocks: List[Stock]
    ) -> bool:
        """이전 Seed Block 시작 후 최소 캔들 수 확인"""
        if prev_block5 is None:
            return True

        candles_count = self._count_candles_between(
            prev_block5.started_at,
            current_date,
            all_stocks
        )

        return candles_count > min_candles

    def check_max_candles(
        self,
        current_date: date,
        prev_block5: Optional[Block5Detection],
        max_candles: int,
        all_stocks: List[Stock]
    ) -> bool:
        """블록5 시작 후 최대 캔들 수 확인"""
        if prev_block5 is None or max_candles is None:
            return True

        candles_count = self._count_candles_between(
            prev_block5.started_at,
            current_date,
            all_stocks
        )

        return candles_count <= max_candles

    def check_lookback_window(
        self,
        current_date: date,
        prev_seed_block5: Optional[Block5Detection],
        lookback_min_candles: Optional[int],
        lookback_max_candles: Optional[int],
        all_stocks: List[Stock],
    ) -> bool:
        """
        Lookback 검증: Block6 후보일 기준 과거에 Block5가 적절한 범위 내에 존재하는지 확인

        Args:
            current_date: Block6 후보일
            prev_seed_block5: 이전 Seed Block5 탐지 결과
            lookback_min_candles: 과거 최소 캔들 범위 (None=체크 안함)
            lookback_max_candles: 과거 최대 캔들 범위 (None=체크 안함)
            all_stocks: 전체 주식 데이터 (날짜순 정렬)

        Returns:
            조건 만족 여부 (True: Block5가 적절한 범위에 있음, False: 범위 밖)
        """
        # 조건이 없으면 스킵
        if lookback_min_candles is None and lookback_max_candles is None:
            return True

        # 이전 Block5가 없으면 스킵
        if prev_seed_block5 is None:
            return True

        # 후보일에서 Block5 시작일까지의 캔들 수 계산
        candles_count = self._count_candles_between(
            prev_seed_block5.started_at,
            current_date,
            all_stocks
        )

        # 최소 범위 체크
        if lookback_min_candles is not None:
            if candles_count < lookback_min_candles:
                return False

        # 최대 범위 체크
        if lookback_max_candles is not None:
            if candles_count > lookback_max_candles:
                return False

        return True

    def _count_candles_between(
        self,
        start_date: date,
        end_date: date,
        all_stocks: List[Stock]
    ) -> int:
        """두 날짜 사이의 실제 거래일 캔들 수 계산"""
        count = 0
        for stock in all_stocks:
            if start_date <= stock.date <= end_date:
                count += 1
        return count

    def _get_range_high(
        self,
        start_date: date,
        end_date: date,
        ticker: str,
        all_stocks: List[Stock]
    ) -> Optional[float]:
        """지정된 기간의 실제 최고가(range_high) 계산"""
        max_high = None
        for stock in all_stocks:
            if (stock.ticker == ticker and
                start_date <= stock.date <= end_date):
                if max_high is None or stock.high > max_high:
                    max_high = stock.high
        return max_high
