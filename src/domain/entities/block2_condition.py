"""
Block2 Condition Entity - 블록2 조건 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from .base_entry_condition import BaseEntryCondition


@dataclass
class Block2Condition:
    """
    블록2 조건 엔티티

    블록2 = 기본 진입/종료 조건 + Block2 전용 조건 3가지
    (단, 각 블록은 독립적인 조건 값을 가짐)

    추가 조건:
    1. 블록 거래량 조건: 당일_거래량 >= 블록1_최고_거래량 × N%
    2. 저가 마진 조건: 당일_저가 × (1 + M%) > 블록1_peak_price
    3. 최소 캔들 조건: 블록1 시작 후 최소 N개 캔들 경과

    블록2 종료 조건:
    - 블록1과 동일한 3가지 종료 조건 중 택1
    - 또는 블록3 시작 시 자동 종료 (블록3 시작일 전날)

    직전 블록1 찾기:
    - 당일 기준으로 가장 최근에 완료된(completed) 블록1
    - 날짜 역순으로 검색하여 첫 번째 완료된 블록1 사용

    파라미터 독립성 (중요):
    - base: Block2 전용 값 (Block1과 다를 수 있음)
    - 예: Block1은 entry_surge_rate=8.0%, Block2는 entry_surge_rate=5.0% 사용 가능
    - 이는 블록별 최적화를 위한 설계 (2025-10 리팩토링 완료)
    """

    # ===== 기본 진입/종료 조건 (Block2용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 전용 조건 =====
    block2_volume_ratio: Optional[float] = None  # 블록1 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block2_low_price_margin: Optional[float] = None     # 저가 마진 (단위: %, 예: 10 = 10%)

    # 블록 전환 대기 기간
    block2_min_candles_after_block1: Optional[int] = None  # 블록1 시작 후 최소 캔들 수 (예: 4 = 5번째 캔들부터 블록2 가능)

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # 기본 조건 검증
        if not self.base.validate():
            return False

        # Block2 전용 조건 검증
        if self.block2_volume_ratio is not None and self.block2_volume_ratio <= 0:
            return False

        if self.block2_low_price_margin is not None and self.block2_low_price_margin < 0:
            return False

        if self.block2_min_candles_after_block1 is not None and self.block2_min_candles_after_block1 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.base.entry_surge_rate:
            conditions.append(f"등락률>={self.base.entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block2_low_price_margin:
            conditions.append(f"Block2저가마진={self.block2_low_price_margin}%")

        return f"<Block2Condition({', '.join(conditions)})>"
