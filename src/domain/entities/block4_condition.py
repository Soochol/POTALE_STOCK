"""
Block4 Condition Entity - 블록4 조건 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from .base_entry_condition import BaseEntryCondition


@dataclass
class Block4Condition:
    """
    블록4 조건 엔티티

    블록4 = 기본 진입/종료 조건 + Block2 조건 + Block3 조건 + Block4 전용 조건
    (단, 각 블록은 독립적인 조건 값을 가짐)

    추가 조건:
    1. Block2 거래량 조건: 당일_거래량 >= 블록1_최고_거래량 × N%
    2. Block2 저가 마진 조건: 당일_저가 × (1 + M%) > 블록1_peak_price
    3. Block3 거래량 조건: 당일_거래량 >= 블록2_최고_거래량 × N%
    4. Block3 저가 마진 조건: 당일_저가 × (1 + M%) > 블록2_peak_price
    5. Block4 거래량 조건: 당일_거래량 >= 블록3_최고_거래량 × N%
    6. Block4 저가 마진 조건: 당일_저가 × (1 + M%) > 블록3_peak_price

    블록4 종료 조건:
    - 블록1/2/3과 동일한 3가지 종료 조건 중 택1

    직전 블록3 찾기:
    - 당일 기준으로 가장 최근에 완료된(completed) 블록3
    - 날짜 역순으로 검색하여 첫 번째 완료된 블록3 사용

    파라미터 독립성 (중요):
    - base: Block4 전용 값 (Block1/2/3과 다를 수 있음)
    - 예: Block1=8.0%, Block2=5.0%, Block3=3.0%, Block4=2.0% 처럼 단계별 최적화 가능
    - 이는 블록별 최적화를 위한 설계 (2025-10 리팩토링 완료)
    """

    # ===== 기본 진입/종료 조건 (Block4용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 조건 (독립적인 값) =====
    block2_volume_ratio: Optional[float] = None  # 블록1 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block2_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %, 예: 10 = 10%)
    block2_min_candles_after_block1: Optional[int] = None  # 블록1 시작 후 최소 캔들 수

    # ===== Block3 조건 (독립적인 값) =====
    block3_volume_ratio: Optional[float] = None  # 블록2 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block3_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %, 예: 10 = 10%)
    block3_min_candles_after_block2: Optional[int] = None  # 블록2 시작 후 최소 캔들 수

    # ===== Block4 전용 조건 =====
    block4_volume_ratio: Optional[float] = None  # 블록3 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block4_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %, 예: 10 = 10%)
    block4_min_candles_after_block3: Optional[int] = None  # 블록3 시작 후 최소 캔들 수

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # 기본 조건 검증
        if not self.base.validate():
            return False

        # Block2 조건 검증
        if self.block2_volume_ratio is not None and self.block2_volume_ratio <= 0:
            return False

        if self.block2_low_price_margin is not None and self.block2_low_price_margin < 0:
            return False

        if self.block2_min_candles_after_block1 is not None and self.block2_min_candles_after_block1 < 0:
            return False

        # Block3 조건 검증
        if self.block3_volume_ratio is not None and self.block3_volume_ratio <= 0:
            return False

        if self.block3_low_price_margin is not None and self.block3_low_price_margin < 0:
            return False

        if self.block3_min_candles_after_block2 is not None and self.block3_min_candles_after_block2 < 0:
            return False

        # Block4 전용 조건 검증
        if self.block4_volume_ratio is not None and self.block4_volume_ratio <= 0:
            return False

        if self.block4_low_price_margin is not None and self.block4_low_price_margin < 0:
            return False

        if self.block4_min_candles_after_block3 is not None and self.block4_min_candles_after_block3 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.base.entry_surge_rate:
            conditions.append(f"등락률>={self.base.entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block3_volume_ratio:
            conditions.append(f"Block3거래량비율={self.block3_volume_ratio}%")
        if self.block4_volume_ratio:
            conditions.append(f"Block4거래량비율={self.block4_volume_ratio}%")

        return f"<Block4Condition({', '.join(conditions)})>"
