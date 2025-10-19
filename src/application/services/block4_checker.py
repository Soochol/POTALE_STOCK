"""
Block4 Checker Service - 블록4 진입/종료 조건 검사 서비스
"""
from typing import Optional
from ...domain.entities.stock import Stock
from ...domain.entities.block4_condition import Block4Condition
from ...domain.entities.block4_detection import Block4Detection
from ...domain.entities.block3_detection import Block3Detection
from ...domain.entities.block2_detection import Block2Detection
from ...domain.entities.block1_detection import Block1Detection
from ...domain.entities.block1_condition import Block1Condition
from .block3_checker import Block3Checker
from .block2_checker import Block2Checker
from .block1_checker import Block1Checker


class Block4Checker:
    """블록4 진입 및 종료 조건 검사 서비스"""

    def __init__(self):
        self.block3_checker = Block3Checker()
        self.block2_checker = Block2Checker()
        self.block1_checker = Block1Checker()

    def check_entry(
        self,
        condition: Block4Condition,
        stock: Stock,
        prev_stock: Optional[Stock] = None,
        prev_block1: Optional[Block1Detection] = None,
        prev_block2: Optional[Block2Detection] = None,
        prev_block3: Optional[Block3Detection] = None
    ) -> bool:
        """
        블록4 진입 조건 검사
        = 블록3의 모든 조건 + 블록4 추가 조건 3가지

        Args:
            condition: 블록4 조건
            stock: 주식 데이터 (지표 포함)
            prev_stock: 전일 주식 데이터 (전날 거래량 조건용, 선택적)
            prev_block1: 직전 블록1 탐지 결과 (블록2 조건용, 선택적)
            prev_block2: 직전 블록2 탐지 결과 (블록3 조건용, 선택적)
            prev_block3: 직전 블록3 탐지 결과 (추가 조건용, 선택적)

        Returns:
            모든 조건 만족 여부
        """
        # 1. Block1+Block2+Block3 기본 조건 검사
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators

        # Block1 조건
        if condition.entry_surge_rate is not None:
            rate = indicators.get('rate', 0)
            if rate < condition.entry_surge_rate:
                return False

        if condition.entry_ma_period and condition.entry_high_above_ma:
            ma_key = f'MA_{condition.entry_ma_period}'
            ma_value = indicators.get(ma_key)
            if ma_value is None or stock.high < ma_value:
                return False

        if condition.entry_max_deviation_ratio is not None:
            deviation = indicators.get('deviation', 100)
            if deviation > condition.entry_max_deviation_ratio:
                return False

        if condition.entry_min_trading_value is not None:
            trading_value = indicators.get('trading_value_100m', 0)
            if trading_value < condition.entry_min_trading_value:
                return False

        if condition.entry_volume_high_months is not None:
            is_volume_high = indicators.get('is_volume_high', False)
            if not is_volume_high:
                return False

        if condition.entry_volume_spike_ratio is not None:
            if prev_stock is None:
                return False

            ratio = condition.entry_volume_spike_ratio / 100.0
            required_volume = prev_stock.volume * ratio
            if stock.volume < required_volume:
                return False

        if condition.entry_price_high_months is not None:
            is_new_high = indicators.get('is_new_high', False)
            if not is_new_high:
                return False

        # Block2 추가 조건
        if prev_block1 is not None:
            if condition.block2_volume_ratio is not None and prev_block1.peak_volume is not None:
                ratio = condition.block2_volume_ratio / 100.0
                required_volume = prev_block1.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

            if condition.block2_low_price_margin is not None and prev_block1.peak_price is not None:
                margin = condition.block2_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)
                if threshold_price <= prev_block1.peak_price:
                    return False

        # Block3 추가 조건
        if prev_block2 is not None:
            if condition.block3_volume_ratio is not None and prev_block2.peak_volume is not None:
                ratio = condition.block3_volume_ratio / 100.0
                required_volume = prev_block2.peak_volume * ratio
                if stock.volume < required_volume:
                    return False

            if condition.block3_low_price_margin is not None and prev_block2.peak_price is not None:
                margin = condition.block3_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)
                if threshold_price <= prev_block2.peak_price:
                    return False

        # 2. 블록4 추가 조건 검사
        # 추가 조건을 위해서는 prev_block3가 필요 (독립적으로 시작하는 경우 prev_block3가 없을 수 있음)
        if prev_block3 is None:
            # 독립적으로 시작하는 경우: 블록3 조건만 만족하면 OK
            # (실제로는 직전 블록3를 찾아서 전달해야 하지만, 없으면 추가 조건 스킵)
            return True

        # 추가 조건 1: 블록 거래량 조건 (선택적)
        # 당일_거래량 >= 블록3_최고_거래량 × (block4_volume_ratio/100)
        # block4_volume_ratio는 % 단위 (예: 20 = 20%)
        if condition.block4_volume_ratio is not None and prev_block3.peak_volume is not None:
            ratio = condition.block4_volume_ratio / 100.0
            required_volume = prev_block3.peak_volume * ratio
            if stock.volume < required_volume:
                return False

        # 추가 조건 2: 저가 마진 조건 (선택적)
        # 당일_저가 × (1 + block4_low_price_margin/100) > 블록3_peak_price
        # block4_low_price_margin은 % 단위 (예: 10 = 10%)
        if condition.block4_low_price_margin is not None and prev_block3.peak_price is not None:
            margin = condition.block4_low_price_margin / 100.0
            threshold_price = stock.low * (1 + margin)
            if threshold_price <= prev_block3.peak_price:
                return False

        # 모든 조건 만족
        return True

    def check_exit(
        self,
        condition: Block4Condition,
        detection: Block4Detection,
        current_stock: Stock,
        all_stocks: list
    ) -> Optional[str]:
        """
        블록4 종료 조건 검사 (블록1/2/3과 동일)

        Args:
            condition: 블록4 조건
            detection: 블록4 탐지 결과
            current_stock: 현재 주식 데이터
            all_stocks: 전체 주식 데이터 (삼선전환도 계산용)

        Returns:
            종료 사유 또는 None
        """
        # Block4Condition에서 Block1Condition 임시 생성
        temp_block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            entry_high_above_ma=condition.entry_high_above_ma,
            entry_max_deviation_ratio=condition.entry_max_deviation_ratio,
            entry_min_trading_value=condition.entry_min_trading_value,
            entry_volume_high_months=condition.entry_volume_high_months,
            entry_volume_spike_ratio=condition.entry_volume_spike_ratio,
            entry_price_high_months=condition.entry_price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block1Detection 형태로 변환하여 전달
        temp_block1 = Block1Detection(
            ticker=detection.ticker,
            condition_name=detection.condition_name,
            started_at=detection.started_at,
            entry_close=detection.entry_close,
            peak_price=detection.peak_price
        )

        return self.block1_checker.check_exit(
            temp_block1_condition,
            temp_block1,
            current_stock,
            all_stocks
        )
