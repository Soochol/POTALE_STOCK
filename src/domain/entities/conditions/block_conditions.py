"""
Block Condition Entities - 블록1/2/3/4/5/6 조건 엔티티

각 블록의 진입/종료 조건을 정의하는 엔티티들을 하나의 파일로 통합
"""
from dataclasses import dataclass
from typing import Optional
from .base_entry_condition import BaseEntryCondition, Block1ExitConditionType

__all__ = [
    'Block1Condition',
    'Block2Condition',
    'Block3Condition',
    'Block4Condition',
    'Block5Condition',
    'Block6Condition',
    'Block1ExitConditionType',  # Re-export
]


@dataclass
class Block1Condition:
    """
    블록1 조건 엔티티

    블록1은 기본 진입/종료 조건만 사용 (추가 조건 없음)

    블록1 진입 조건 (5가지, 개별 판단):
    1. 등락률 조건: 전일 대비 N% 이상 (양수만)
    2. 이평선 조건 A: 당일 고가 >= 이동평균선 N
    3. 이평선 조건 B: 이동평균선 N 이격도 M% 이하
    4. 거래대금 조건: N억 이상
    5. 거래량 조건: N개월 신고거래량 (최근 N개월 최고)

    블록1 종료 조건 (3가지 중 택1):
    1. 이동평균선 이탈: 종가 < 이동평균선 N
    2. 삼선전환도: 첫 음봉 발생
    3. 블록1 캔들 몸통 중간: 종가 < (시가 + 종가) / 2

    중복 방지:
    - 최초 발생일 이후 N일(기본 120일)까지 동일 블록1 재탐지 제외
    """

    # 기본 진입/종료 조건
    base: BaseEntryCondition

    def validate(self) -> bool:
        """조건 유효성 검사"""
        return self.base.validate()

    def __repr__(self):
        return f"<Block1Condition(base={self.base})>"


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

    파라미터 독립성 (중요):
    - base: Block2 전용 값 (Block1과 다를 수 있음)
    - 예: Block1은 entry_surge_rate=8.0%, Block2는 entry_surge_rate=5.0% 사용 가능
    """

    # ===== 기본 진입/종료 조건 (Block2용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 전용 조건 =====
    block2_volume_ratio: Optional[float] = None  # 블록1 최고 거래량의 N% (단위: %)
    block2_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %)
    block2_min_candles_after_block1: Optional[int] = None  # 블록1 시작 후 최소 캔들 수
    block2_max_candles_after_block1: Optional[int] = None  # 블록1 시작 후 최대 캔들 수

    def validate(self) -> bool:
        """조건 유효성 검사"""
        if not self.base.validate():
            return False

        if self.block2_volume_ratio is not None and self.block2_volume_ratio <= 0:
            return False

        if self.block2_low_price_margin is not None and self.block2_low_price_margin < 0:
            return False

        if self.block2_min_candles_after_block1 is not None and self.block2_min_candles_after_block1 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.base.block1_entry_surge_rate:
            conditions.append(f"등락률>={self.base.block1_entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block2_low_price_margin:
            conditions.append(f"Block2저가마진={self.block2_low_price_margin}%")

        return f"<Block2Condition({', '.join(conditions)})>"


@dataclass
class Block3Condition:
    """
    블록3 조건 엔티티

    블록3 = 기본 진입/종료 조건 + Block2 조건 + Block3 전용 조건
    (단, 각 블록은 독립적인 조건 값을 가짐)

    추가 조건:
    1. Block2 거래량 조건: 당일_거래량 >= 블록1_최고_거래량 × N%
    2. Block2 저가 마진 조건: 당일_저가 × (1 + M%) > 블록1_peak_price
    3. Block3 거래량 조건: 당일_거래량 >= 블록2_최고_거래량 × N%
    4. Block3 저가 마진 조건: 당일_저가 × (1 + M%) > 블록2_peak_price

    파라미터 독립성:
    - base: Block3 전용 값 (Block1/2와 다를 수 있음)
    - 예: Block1=8.0%, Block2=5.0%, Block3=3.0% 처럼 단계별 최적화 가능
    """

    # ===== 기본 진입/종료 조건 (Block3용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 조건 (독립적인 값) =====
    block2_volume_ratio: Optional[float] = None
    block2_low_price_margin: Optional[float] = None
    block2_min_candles_after_block1: Optional[int] = None
    block2_max_candles_after_block1: Optional[int] = None

    # ===== Block3 전용 조건 =====
    block3_volume_ratio: Optional[float] = None
    block3_low_price_margin: Optional[float] = None
    block3_min_candles_after_block2: Optional[int] = None
    block3_max_candles_after_block2: Optional[int] = None

    def validate(self) -> bool:
        """조건 유효성 검사"""
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

        return True

    def __repr__(self):
        conditions = []
        if self.base.block1_entry_surge_rate:
            conditions.append(f"등락률>={self.base.block1_entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block3_volume_ratio:
            conditions.append(f"Block3거래량비율={self.block3_volume_ratio}%")

        return f"<Block3Condition({', '.join(conditions)})>"


@dataclass
class Block4Condition:
    """
    블록4 조건 엔티티

    블록4 = 기본 진입/종료 조건 + Block2 조건 + Block3 조건 + Block4 전용 조건
    (단, 각 블록은 독립적인 조건 값을 가짐)

    추가 조건:
    1. Block2 거래량/저가 마진 조건
    2. Block3 거래량/저가 마진 조건
    3. Block4 거래량 조건: 당일_거래량 >= 블록3_최고_거래량 × N%
    4. Block4 저가 마진 조건: 당일_저가 × (1 + M%) > 블록3_peak_price

    파라미터 독립성:
    - base: Block4 전용 값 (Block1/2/3과 다를 수 있음)
    - 예: Block1=8.0%, Block2=5.0%, Block3=3.0%, Block4=2.0% 처럼 단계별 최적화 가능
    """

    # ===== 기본 진입/종료 조건 (Block4용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 조건 (독립적인 값) =====
    block2_volume_ratio: Optional[float] = None
    block2_low_price_margin: Optional[float] = None
    block2_min_candles_after_block1: Optional[int] = None
    block2_max_candles_after_block1: Optional[int] = None

    # ===== Block3 조건 (독립적인 값) =====
    block3_volume_ratio: Optional[float] = None
    block3_low_price_margin: Optional[float] = None
    block3_min_candles_after_block2: Optional[int] = None
    block3_max_candles_after_block2: Optional[int] = None

    # ===== Block4 전용 조건 =====
    block4_volume_ratio: Optional[float] = None
    block4_low_price_margin: Optional[float] = None
    block4_min_candles_after_block3: Optional[int] = None
    block4_max_candles_after_block3: Optional[int] = None

    def validate(self) -> bool:
        """조건 유효성 검사"""
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

        # Block4 조건 검증
        if self.block4_volume_ratio is not None and self.block4_volume_ratio <= 0:
            return False
        if self.block4_low_price_margin is not None and self.block4_low_price_margin < 0:
            return False
        if self.block4_min_candles_after_block3 is not None and self.block4_min_candles_after_block3 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.base.block1_entry_surge_rate:
            conditions.append(f"등락률>={self.base.block1_entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block3_volume_ratio:
            conditions.append(f"Block3거래량비율={self.block3_volume_ratio}%")
        if self.block4_volume_ratio:
            conditions.append(f"Block4거래량비율={self.block4_volume_ratio}%")

        return f"<Block4Condition({', '.join(conditions)})>"


@dataclass
class Block5Condition:
    """
    블록5 조건 엔티티

    블록5 = 기본 진입/종료 조건 + Block2 조건 + Block3 조건 + Block4 조건 + Block5 전용 조건
    (단, 각 블록은 독립적인 조건 값을 가짐)

    추가 조건:
    1. Block2 거래량/저가 마진 조건
    2. Block3 거래량/저가 마진 조건
    3. Block4 거래량/저가 마진 조건
    4. Block5 거래량 조건: 당일_거래량 >= 블록4_최고_거래량 × N%
    5. Block5 저가 마진 조건: 당일_저가 × (1 + M%) > 블록4_peak_price

    파라미터 독립성:
    - base: Block5 전용 값 (Block1/2/3/4와 다를 수 있음)
    - 예: Block1=8.0%, Block2=5.0%, Block3=3.0%, Block4=2.0%, Block5=1.5% 처럼 단계별 최적화 가능
    """

    # ===== 기본 진입/종료 조건 (Block5용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 조건 (독립적인 값) =====
    block2_volume_ratio: Optional[float] = None
    block2_low_price_margin: Optional[float] = None
    block2_min_candles_after_block1: Optional[int] = None
    block2_max_candles_after_block1: Optional[int] = None

    # ===== Block3 조건 (독립적인 값) =====
    block3_volume_ratio: Optional[float] = None
    block3_low_price_margin: Optional[float] = None
    block3_min_candles_after_block2: Optional[int] = None
    block3_max_candles_after_block2: Optional[int] = None

    # ===== Block4 조건 (독립적인 값) =====
    block4_volume_ratio: Optional[float] = None
    block4_low_price_margin: Optional[float] = None
    block4_min_candles_after_block3: Optional[int] = None
    block4_max_candles_after_block3: Optional[int] = None

    # ===== Block5 전용 조건 =====
    block5_volume_ratio: Optional[float] = None
    block5_low_price_margin: Optional[float] = None
    block5_min_candles_after_block4: Optional[int] = None
    block5_max_candles_after_block4: Optional[int] = None

    def validate(self) -> bool:
        """조건 유효성 검사"""
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

        # Block4 조건 검증
        if self.block4_volume_ratio is not None and self.block4_volume_ratio <= 0:
            return False
        if self.block4_low_price_margin is not None and self.block4_low_price_margin < 0:
            return False
        if self.block4_min_candles_after_block3 is not None and self.block4_min_candles_after_block3 < 0:
            return False

        # Block5 조건 검증
        if self.block5_volume_ratio is not None and self.block5_volume_ratio <= 0:
            return False
        if self.block5_low_price_margin is not None and self.block5_low_price_margin < 0:
            return False
        if self.block5_min_candles_after_block4 is not None and self.block5_min_candles_after_block4 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.base.block1_entry_surge_rate:
            conditions.append(f"등락률>={self.base.block1_entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block3_volume_ratio:
            conditions.append(f"Block3거래량비율={self.block3_volume_ratio}%")
        if self.block4_volume_ratio:
            conditions.append(f"Block4거래량비율={self.block4_volume_ratio}%")
        if self.block5_volume_ratio:
            conditions.append(f"Block5거래량비율={self.block5_volume_ratio}%")

        return f"<Block5Condition({', '.join(conditions)})>"


@dataclass
class Block6Condition:
    """
    블록6 조건 엔티티

    블록6 = 기본 진입/종료 조건 + Block2~5 조건 + Block6 전용 조건
    (단, 각 블록은 독립적인 조건 값을 가짐)

    추가 조건:
    1. Block2 거래량/저가 마진 조건
    2. Block3 거래량/저가 마진 조건
    3. Block4 거래량/저가 마진 조건
    4. Block5 거래량/저가 마진 조건
    5. Block6 거래량 조건: 당일_거래량 >= 블록5_최고_거래량 × N%
    6. Block6 저가 마진 조건: 당일_저가 × (1 + M%) > 블록5_peak_price

    파라미터 독립성:
    - base: Block6 전용 값 (Block1/2/3/4/5와 다를 수 있음)
    - 예: Block1=8.0%, Block2=5.0%, Block3=3.0%, Block4=2.0%, Block5=1.5%, Block6=1.0% 처럼 단계별 최적화 가능
    """

    # ===== 기본 진입/종료 조건 (Block6용 독립적 값) =====
    base: BaseEntryCondition

    # ===== Block2 조건 (독립적인 값) =====
    block2_volume_ratio: Optional[float] = None
    block2_low_price_margin: Optional[float] = None
    block2_min_candles_after_block1: Optional[int] = None
    block2_max_candles_after_block1: Optional[int] = None

    # ===== Block3 조건 (독립적인 값) =====
    block3_volume_ratio: Optional[float] = None
    block3_low_price_margin: Optional[float] = None
    block3_min_candles_after_block2: Optional[int] = None
    block3_max_candles_after_block2: Optional[int] = None

    # ===== Block4 조건 (독립적인 값) =====
    block4_volume_ratio: Optional[float] = None
    block4_low_price_margin: Optional[float] = None
    block4_min_candles_after_block3: Optional[int] = None
    block4_max_candles_after_block3: Optional[int] = None

    # ===== Block5 조건 (독립적인 값) =====
    block5_volume_ratio: Optional[float] = None
    block5_low_price_margin: Optional[float] = None
    block5_min_candles_after_block4: Optional[int] = None
    block5_max_candles_after_block4: Optional[int] = None

    # ===== Block6 전용 조건 =====
    block6_volume_ratio: Optional[float] = None
    block6_low_price_margin: Optional[float] = None
    block6_min_candles_after_block5: Optional[int] = None
    block6_max_candles_after_block5: Optional[int] = None

    def validate(self) -> bool:
        """조건 유효성 검사"""
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

        # Block4 조건 검증
        if self.block4_volume_ratio is not None and self.block4_volume_ratio <= 0:
            return False
        if self.block4_low_price_margin is not None and self.block4_low_price_margin < 0:
            return False
        if self.block4_min_candles_after_block3 is not None and self.block4_min_candles_after_block3 < 0:
            return False

        # Block5 조건 검증
        if self.block5_volume_ratio is not None and self.block5_volume_ratio <= 0:
            return False
        if self.block5_low_price_margin is not None and self.block5_low_price_margin < 0:
            return False
        if self.block5_min_candles_after_block4 is not None and self.block5_min_candles_after_block4 < 0:
            return False

        # Block6 조건 검증
        if self.block6_volume_ratio is not None and self.block6_volume_ratio <= 0:
            return False
        if self.block6_low_price_margin is not None and self.block6_low_price_margin < 0:
            return False
        if self.block6_min_candles_after_block5 is not None and self.block6_min_candles_after_block5 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.base.block1_entry_surge_rate:
            conditions.append(f"등락률>={self.base.block1_entry_surge_rate}%")
        if self.block2_volume_ratio:
            conditions.append(f"Block2거래량비율={self.block2_volume_ratio}%")
        if self.block3_volume_ratio:
            conditions.append(f"Block3거래량비율={self.block3_volume_ratio}%")
        if self.block4_volume_ratio:
            conditions.append(f"Block4거래량비율={self.block4_volume_ratio}%")
        if self.block5_volume_ratio:
            conditions.append(f"Block5거래량비율={self.block5_volume_ratio}%")
        if self.block6_volume_ratio:
            conditions.append(f"Block6거래량비율={self.block6_volume_ratio}%")

        return f"<Block6Condition({', '.join(conditions)})>"
