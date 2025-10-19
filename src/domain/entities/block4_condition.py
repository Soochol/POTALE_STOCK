"""
Block4 Condition Entity - 블록4 조건 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from .block3_condition import Block3Condition


@dataclass
class Block4Condition:
    """
    블록4 조건 엔티티

    블록4 = 블록3의 모든 조건 + 추가 조건 3가지

    추가 조건:
    1. 블록 거래량 조건: 당일_거래량 >= 블록3_최고_거래량 × N%
    2. 저가 마진 조건: 당일_저가 × (1 + M%) > 블록3_peak_price
    3. 블록3 시작 후 최소 캔들 수

    블록4 종료 조건:
    - 블록1/2/3과 동일한 3가지 종료 조건 중 택1
    - 블록4가 최종 단계 (블록5 없음)

    직전 블록3 찾기:
    - 당일 기준으로 가장 최근에 완료된(completed) 블록3
    - 날짜 역순으로 검색하여 첫 번째 완료된 블록3 사용
    """

    # 블록3 조건 (상속)
    block3_condition: Block3Condition

    # 블록4 추가 조건 (블록3과 동일한 구조, 대상만 블록3)
    block4_volume_ratio: Optional[float] = None  # 블록3 최고 거래량의 N% (단위: %, 예: 20 = 20%)
    block4_low_price_margin: Optional[float] = None     # 저가 마진 (단위: %, 예: 10 = 10%)

    # 블록 전환 대기 기간
    block4_min_candles_after_block3: Optional[int] = None  # 블록3 시작 후 최소 캔들 수 (예: 4 = 5번째 캔들부터 블록4 가능)

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # 블록3 조건 검증
        if not self.block3_condition.validate():
            return False

        # 블록4 추가 조건 검증
        if self.block4_volume_ratio is not None and self.block4_volume_ratio <= 0:
            return False

        if self.block4_low_price_margin is not None and self.block4_low_price_margin < 0:
            return False

        if self.block4_min_candles_after_block3 is not None and self.block4_min_candles_after_block3 < 0:
            return False

        return True

    def __repr__(self):
        return (
            f"<Block4Condition("
            f"Block3={self.block3_condition}, "
            f"거래량비율={self.block4_volume_ratio:.0f}%, "
            f"저가마진={self.block4_low_price_margin:.0f}%"
            f")>"
        )
