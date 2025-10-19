"""
Block2 Condition Entity - 블록2 조건 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from .block1_condition import Block1Condition


@dataclass
class Block2Condition:
    """
    블록2 조건 엔티티

    블록2 = 블록1의 모든 조건 + 추가 조건 2가지

    추가 조건:
    1. 블록 거래량 조건: 당일_거래량 >= 블록1_최고_거래량 × N%
    2. 저가 마진 조건: 당일_저가 × (1 + M%) > 블록1_peak_price

    블록2 종료 조건:
    - 블록1과 동일한 3가지 종료 조건 중 택1
    - 또는 블록3 시작 시 자동 종료 (블록3 시작일 전날)

    직전 블록1 찾기:
    - 당일 기준으로 가장 최근에 완료된(completed) 블록1
    - 날짜 역순으로 검색하여 첫 번째 완료된 블록1 사용
    """

    # 블록1 조건 (상속)
    block1_condition: Block1Condition

    # 블록2 추가 조건
    block2_volume_ratio: Optional[float] = None  # 블록1 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block2_low_price_margin: Optional[float] = None     # 저가 마진 (단위: %, 예: 10 = 10%)

    # 중복 방지
    cooldown_days: Optional[int] = None  # 재탐지 제외 기간 (예: 120 = 120일)

    # 블록 전환 대기 기간
    block2_min_candles_after_block1: Optional[int] = None  # 블록1 시작 후 최소 캔들 수 (예: 4 = 5번째 캔들부터 블록2 가능)

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # 블록1 조건 검증
        if not self.block1_condition.validate():
            return False

        # 블록2 추가 조건 검증
        if self.block2_volume_ratio is not None and self.block2_volume_ratio <= 0:
            return False

        if self.block2_low_price_margin is not None and self.block2_low_price_margin < 0:
            return False

        if self.cooldown_days is not None and self.cooldown_days <= 0:
            return False

        if self.block2_min_candles_after_block1 is not None and self.block2_min_candles_after_block1 < 0:
            return False

        return True

    def __repr__(self):
        return (
            f"<Block2Condition("
            f"Block1={self.block1_condition}, "
            f"거래량비율={self.block2_volume_ratio:.0f}%, "
            f"저가마진={self.block2_low_price_margin:.0f}%"
            f")>"
        )
