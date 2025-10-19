"""
Redetection Condition Entity - 재탐지 조건 엔티티

재탐지를 위한 완화된 조건 + 가격 범위 필터
"""
from dataclasses import dataclass
from typing import Optional
from src.domain.entities.block1_condition import Block1ExitConditionType


@dataclass
class RedetectionCondition:
    """
    재탐지 조건 엔티티 (완화된 조건 + 가격 범위)

    5년 재탐지를 위한 조건 세트
    - Block1 기본 조건 (완화)
    - 가격 범위 Tolerance (block1/2/3/4)
    - Block2 추가 조건
    - Block3 추가 조건
    - Block4 추가 조건
    - Cooldown (재탐지 간 최소 간격)
    """

    # ===== Block1 조건 (완화) =====
    # 진입 조건
    entry_surge_rate: float  # 등락률 (%, 완화, 예: 5.0 = 5%)
    entry_ma_period: int  # 진입용 이동평균선 기간
    entry_high_above_ma: bool = True  # 고가 >= 이평선 검사
    entry_max_deviation_ratio: float = 120.0  # 이격도 (%)
    entry_min_trading_value: float = 300.0  # 거래대금 (억)
    entry_volume_high_months: int = 6  # 신고거래량 기간 (개월, 완화)
    entry_volume_spike_ratio: float = 300.0  # 전날 대비 비율 (%, 완화)
    entry_price_high_months: int = 1  # N개월 신고가 (완화)

    # 종료 조건
    exit_condition_type: Block1ExitConditionType = Block1ExitConditionType.MA_BREAK
    exit_ma_period: Optional[int] = None  # 종료용 이동평균선 기간

    # ===== 재탐지 전용: 가격 범위 Tolerance =====
    block1_tolerance_pct: float = 10.0  # Block1 재탐지 가격 범위 (±%)
    block2_tolerance_pct: float = 15.0  # Block2 재탐지 가격 범위 (±%)
    block3_tolerance_pct: float = 20.0  # Block3 재탐지 가격 범위 (±%)
    block4_tolerance_pct: float = 25.0  # Block4 재탐지 가격 범위 (±%)

    # 재탐지 간 최소 간격
    cooldown_days: int = 20  # 기본 20일

    # ===== Block2 추가 조건 =====
    block2_volume_ratio: float = 15.0  # Block1 최고 거래량 대비 (%)
    block2_low_price_margin: float = 10.0  # Block1 최고가 저가 마진 (%)
    block2_min_candles_after_block1: int = 4  # Block1 시작 후 최소 캔들 수

    # ===== Block3 추가 조건 =====
    block3_volume_ratio: float = 15.0  # Block2 최고 거래량 대비 (%)
    block3_low_price_margin: float = 10.0  # Block2 최고가 저가 마진 (%)
    block3_min_candles_after_block2: int = 4  # Block2 시작 후 최소 캔들 수

    # ===== Block4 추가 조건 =====
    block4_volume_ratio: float = 20.0  # Block3 최고 거래량 대비 (%)
    block4_low_price_margin: float = 10.0  # Block3 최고가 저가 마진 (%)
    block4_min_candles_after_block3: int = 4  # Block3 시작 후 최소 캔들 수

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # Block1 조건
        if self.entry_surge_rate <= 0:
            return False
        if self.entry_ma_period <= 0:
            return False
        if self.entry_max_deviation_ratio <= 0:
            return False
        if self.entry_min_trading_value <= 0:
            return False
        if self.entry_volume_high_months <= 0:
            return False
        if self.entry_volume_spike_ratio < 0:
            return False
        if self.entry_price_high_months <= 0:
            return False
        if self.cooldown_days <= 0:
            return False

        # Tolerance
        if self.block1_tolerance_pct <= 0 or self.block1_tolerance_pct > 100:
            return False
        if self.block2_tolerance_pct <= 0 or self.block2_tolerance_pct > 100:
            return False
        if self.block3_tolerance_pct <= 0 or self.block3_tolerance_pct > 100:
            return False
        if self.block4_tolerance_pct <= 0 or self.block4_tolerance_pct > 100:
            return False

        # Block2 조건
        if self.block2_volume_ratio <= 0:
            return False
        if self.block2_low_price_margin < 0:
            return False
        if self.block2_min_candles_after_block1 < 0:
            return False

        # Block3 조건
        if self.block3_volume_ratio <= 0:
            return False
        if self.block3_low_price_margin < 0:
            return False
        if self.block3_min_candles_after_block2 < 0:
            return False

        # Block4 조건
        if self.block4_volume_ratio <= 0:
            return False
        if self.block4_low_price_margin < 0:
            return False
        if self.block4_min_candles_after_block3 < 0:
            return False

        return True

    def __repr__(self):
        return (
            f"<RedetectionCondition("
            f"surge={self.entry_surge_rate}%, "
            f"MA{self.entry_ma_period}, "
            f"vol={self.entry_volume_high_months}mo, "
            f"tol=[{self.block1_tolerance_pct}/{self.block2_tolerance_pct}/{self.block3_tolerance_pct}/{self.block4_tolerance_pct}]%, "
            f"cooldown={self.cooldown_days}d"
            f")>"
        )
