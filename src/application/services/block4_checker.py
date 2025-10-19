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
        # 1. 블록3 조건 검사 (상속)
        if not self.block3_checker.check_entry(condition.block3_condition, stock, prev_stock, prev_block1, prev_block2):
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
        # Block1 checker를 사용하여 종료 조건 검사
        # (Block1/2/3/4 모두 동일한 종료 조건 사용)
        block1_cond = condition.block3_condition.block2_condition.block1_condition

        # Block1Detection 형태로 변환하여 전달
        temp_block1 = Block1Detection(
            ticker=detection.ticker,
            condition_name=detection.condition_name,
            started_at=detection.started_at,
            entry_close=detection.entry_close,
            peak_price=detection.peak_price
        )

        return self.block1_checker.check_exit(
            block1_cond,
            temp_block1,
            current_stock,
            all_stocks
        )
