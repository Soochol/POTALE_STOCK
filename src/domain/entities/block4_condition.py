"""
Block4 Condition Entity - 블록4 조건 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from .block1_condition import Block1ExitConditionType


@dataclass
class Block4Condition:
    """
    블록4 조건 엔티티

    블록4 = 블록1의 모든 조건 항목 + Block2 추가 조건 + Block3 추가 조건 + Block4 추가 조건
    (단, 각 블록은 독립적인 조건 값을 가짐)

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

    # ===== Block1 기본 조건 (독립적인 값) =====
    # 진입 조건 1: 등락률
    entry_surge_rate: Optional[float] = None  # 등락률 (%, 예: 5.0 = 5%)

    # 진입 조건 2, 3: 이평선
    entry_ma_period: Optional[int] = None  # 진입용 이동평균선 기간 (예: 5, 20, 120일)
    entry_high_above_ma: Optional[bool] = None  # 고가 >= 이평선 검사 여부
    entry_max_deviation_ratio: Optional[float] = None  # 이격도 (MA를 100으로 봤을 때, 예: 115 = MA의 115%)

    # 진입 조건 4: 거래대금
    entry_min_trading_value: Optional[float] = None  # 거래대금 (억, 예: 100 = 100억)

    # 진입 조건 5: 거래량
    entry_volume_high_months: Optional[int] = None  # 신고거래량 기간 (개월, 예: 3, 6개월)

    # 진입 조건 6: 전날 거래량 비율
    entry_volume_spike_ratio: Optional[float] = None  # 전날 대비 비율 (%, 예: 400 = 400%, 즉 4배)

    # 진입 조건 7: 신고가 조건
    entry_price_high_months: Optional[int] = None  # N개월 신고가 (개월, 예: 2 = 2개월 신고가)

    # 종료 조건
    exit_condition_type: Block1ExitConditionType = Block1ExitConditionType.MA_BREAK
    exit_ma_period: Optional[int] = None  # 종료용 이동평균선 기간 (None이면 ma_period 사용)

    # 중복 방지
    cooldown_days: int = 120  # 재탐지 제외 기간 (기본 120일)

    # ===== Block2 추가 조건 (독립적인 값) =====
    block2_volume_ratio: Optional[float] = None  # 블록1 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block2_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %, 예: 10 = 10%)
    block2_min_candles_after_block1: Optional[int] = None  # 블록1 시작 후 최소 캔들 수

    # ===== Block3 추가 조건 (독립적인 값) =====
    block3_volume_ratio: Optional[float] = None  # 블록2 최고 거래량의 N% (단위: %, 예: 15 = 15%)
    block3_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %, 예: 10 = 10%)
    block3_min_candles_after_block2: Optional[int] = None  # 블록2 시작 후 최소 캔들 수

    # ===== Block4 추가 조건 =====
    block4_volume_ratio: Optional[float] = None  # 블록3 최고 거래량의 N% (단위: %, 예: 20 = 20%)
    block4_low_price_margin: Optional[float] = None  # 저가 마진 (단위: %, 예: 10 = 10%)
    block4_min_candles_after_block3: Optional[int] = None  # 블록3 시작 후 최소 캔들 수

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # Block1 기본 조건 검증 (최소 1개 이상 필요)
        has_condition = any([
            self.entry_surge_rate is not None,
            self.entry_ma_period is not None,
            self.entry_min_trading_value is not None,
            self.entry_volume_high_months is not None
        ])

        if not has_condition:
            return False

        # Block1 조건 값 범위 검증
        if self.entry_surge_rate is not None and self.entry_surge_rate <= 0:
            return False

        if self.entry_ma_period is not None and self.entry_ma_period <= 0:
            return False

        if self.entry_max_deviation_ratio is not None and self.entry_max_deviation_ratio <= 0:
            return False

        if self.entry_min_trading_value is not None and self.entry_min_trading_value <= 0:
            return False

        if self.entry_volume_high_months is not None and self.entry_volume_high_months <= 0:
            return False

        if self.entry_volume_spike_ratio is not None and self.entry_volume_spike_ratio < 0:
            return False

        if self.entry_price_high_months is not None and self.entry_price_high_months <= 0:
            return False

        if self.cooldown_days <= 0:
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

        # Block4 추가 조건 검증
        if self.block4_volume_ratio is not None and self.block4_volume_ratio <= 0:
            return False

        if self.block4_low_price_margin is not None and self.block4_low_price_margin < 0:
            return False

        if self.block4_min_candles_after_block3 is not None and self.block4_min_candles_after_block3 < 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.entry_surge_rate:
            conditions.append(f"등락률>={self.entry_surge_rate}%")
        if self.entry_ma_period:
            conditions.append(f"진입MA{self.entry_ma_period}")
        if self.exit_ma_period:
            conditions.append(f"종료MA{self.exit_ma_period}")
        if self.block4_volume_ratio:
            conditions.append(f"Block4거래량비율={self.block4_volume_ratio}%")
        if self.block4_low_price_margin:
            conditions.append(f"Block4저가마진={self.block4_low_price_margin}%")

        return f"<Block4Condition({', '.join(conditions)})>"
