"""
Block3 Condition Entity - 블록3 조건 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from .block2_condition import Block2Condition


@dataclass
class Block3Condition:
    """
    블록3 조건 엔티티

    블록3 = 블록2의 모든 조건 + 추가 조건 2가지

    추가 조건:
    1. 블록 거래량 조건: 당일_거래량 >= 블록2_최고_거래량 × N%
    2. 저가 마진 조건: 당일_저가 × (1 + M%) > 블록2_peak_price

    블록3 종료 조건:
    - 블록1/2와 동일한 3가지 종료 조건 중 택1

    직전 블록2 찾기:
    - 당일 기준으로 가장 최근에 완료된(completed) 블록2
    - 날짜 역순으로 검색하여 첫 번째 완료된 블록2 사용
    """

    # 블록2 조건 (상속)
    block2_condition: Block2Condition

    # 블록3 추가 조건 (블록2와 동일한 구조, 대상만 블록2)
    block_volume_ratio: Optional[float] = None  # 블록2 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    low_price_margin: Optional[float] = None     # 저가 마진 (단위: %, 예: 10 = 10%)

    # 블록 전환 대기 기간
    min_candles_after_block2: Optional[int] = None  # 블록2 시작 후 최소 캔들 수 (예: 4 = 5번째 캔들부터 블록3 가능)

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # 블록2 조건 검증
        if not self.block2_condition.validate():
            return False

        # 블록3 추가 조건 검증
        if self.block_volume_ratio is not None and self.block_volume_ratio <= 0:
            return False

        if self.low_price_margin is not None and self.low_price_margin < 0:
            return False

        if self.min_candles_after_block2 is not None and self.min_candles_after_block2 < 0:
            return False

        return True

    def __repr__(self):
        return (
            f"<Block3Condition("
            f"Block2={self.block2_condition}, "
            f"거래량비율={self.block_volume_ratio:.0f}%, "
            f"저가마진={self.low_price_margin:.0f}%"
            f")>"
        )
