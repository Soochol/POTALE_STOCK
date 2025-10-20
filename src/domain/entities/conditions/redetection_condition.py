"""
Redetection Condition Entity - 재탐지 조건 엔티티

재탐지를 위한 완화된 조건 + 가격 범위 필터
"""
from dataclasses import dataclass
from typing import Optional
from .base_entry_condition import BaseEntryCondition, Block1ExitConditionType


@dataclass
class RedetectionCondition:
    """
    재탐지 조건 엔티티 (완화된 조건 + 가격 범위)

    5년 재탐지를 위한 조건 세트
    - Block1 기본 조건 (완화, base)
    - 가격 범위 Tolerance (block1/2/3/4)
    - Block2/3/4 전용 파라미터 (Optional, 없으면 Block1 값 사용)
    - Block2/3/4 추가 조건
    - Cooldown (재탐지 간 최소 간격)
    """

    # ===== Block1 기본 조건 (완화) =====
    base: BaseEntryCondition

    # ===== 재탐지 전용: 가격 범위 Tolerance =====
    block1_tolerance_pct: float = 10.0  # Block1 재탐지 가격 범위 (±%)
    block2_tolerance_pct: float = 15.0  # Block2 재탐지 가격 범위 (±%)
    block3_tolerance_pct: float = 20.0  # Block3 재탐지 가격 범위 (±%)
    block4_tolerance_pct: float = 25.0  # Block4 재탐지 가격 범위 (±%)

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

    # ===== Block2 전용 파라미터 (Optional, 없으면 Block1 값 사용) =====
    block2_entry_surge_rate: Optional[float] = None
    block2_entry_ma_period: Optional[int] = None
    block2_entry_high_above_ma: Optional[bool] = None
    block2_entry_max_deviation_ratio: Optional[float] = None
    block2_entry_min_trading_value: Optional[float] = None
    block2_entry_volume_high_months: Optional[int] = None
    block2_entry_volume_spike_ratio: Optional[float] = None
    block2_entry_price_high_months: Optional[int] = None
    block2_exit_condition_type: Optional[Block1ExitConditionType] = None
    block2_exit_ma_period: Optional[int] = None
    block2_cooldown_days: Optional[int] = None

    # ===== Block3 전용 파라미터 (Optional, 없으면 Block1 값 사용) =====
    block3_entry_surge_rate: Optional[float] = None
    block3_entry_ma_period: Optional[int] = None
    block3_entry_high_above_ma: Optional[bool] = None
    block3_entry_max_deviation_ratio: Optional[float] = None
    block3_entry_min_trading_value: Optional[float] = None
    block3_entry_volume_high_months: Optional[int] = None
    block3_entry_volume_spike_ratio: Optional[float] = None
    block3_entry_price_high_months: Optional[int] = None
    block3_exit_condition_type: Optional[Block1ExitConditionType] = None
    block3_exit_ma_period: Optional[int] = None
    block3_cooldown_days: Optional[int] = None

    # ===== Block4 전용 파라미터 (Optional, 없으면 Block1 값 사용) =====
    block4_entry_surge_rate: Optional[float] = None
    block4_entry_ma_period: Optional[int] = None
    block4_entry_high_above_ma: Optional[bool] = None
    block4_entry_max_deviation_ratio: Optional[float] = None
    block4_entry_min_trading_value: Optional[float] = None
    block4_entry_volume_high_months: Optional[int] = None
    block4_entry_volume_spike_ratio: Optional[float] = None
    block4_entry_price_high_months: Optional[int] = None
    block4_exit_condition_type: Optional[Block1ExitConditionType] = None
    block4_exit_ma_period: Optional[int] = None
    block4_cooldown_days: Optional[int] = None
