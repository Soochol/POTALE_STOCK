"""
Seed Condition Entity - Seed 조건 엔티티

Seed 탐지를 위한 엄격한 조건
"""
from dataclasses import dataclass
from typing import Optional
from .base_entry_condition import BaseEntryCondition, Block1ExitConditionType


@dataclass
class SeedCondition:
    """
    Seed 조건 엔티티 (엄격한 조건)

    Block1/2/3/4 Seed를 찾기 위한 엄격한 조건 세트

    변수 순서 (블록별 완전 그룹핑):
    1. Block1: 기본 조건 (base)
    2. Block2: 추가 조건 (3개) + 전용 파라미터 (11개)
    3. Block3: 추가 조건 (3개) + 전용 파라미터 (11개)
    4. Block4: 추가 조건 (3개) + 전용 파라미터 (11개)

    각 블록의 모든 관련 변수들을 하나의 섹션으로 그룹핑하여
    가독성과 유지보수성을 향상
    """

    # ===== Block1 기본 조건 =====
    base: BaseEntryCondition

    # ===== Block2 조건 =====
    # Block2 추가 조건
    block2_volume_ratio: float = 15.0  # Block1 최고 거래량 대비 (%)
    block2_low_price_margin: float = 10.0  # Block1 최고가 저가 마진 (%)
    block2_min_candles_from_block: int = 4  # Block1 시작 후 최소 캔들 수
    block2_max_candles_from_block: Optional[int] = None  # Block1 시작 후 최대 캔들 수
    block2_lookback_min_candles: Optional[int] = None  # Lookback 최소 범위 (Block2 후보일 기준 과거 캔들)
    block2_lookback_max_candles: Optional[int] = None  # Lookback 최대 범위 (Block2 후보일 기준 과거 캔들)

    # Block2 전용 파라미터 (Optional, 없으면 Block1 값 사용)
    block2_entry_surge_rate: Optional[float] = None
    block2_entry_ma_period: Optional[int] = None
    block2_entry_max_deviation_ratio: Optional[float] = None
    block2_entry_min_trading_value: Optional[float] = None
    block2_entry_volume_high_days: Optional[int] = None  # 달력 기준 일수
    block2_entry_volume_spike_ratio: Optional[float] = None
    block2_entry_price_high_days: Optional[int] = None  # 달력 기준 일수
    block2_exit_condition_type: Optional[Block1ExitConditionType] = None
    block2_exit_ma_period: Optional[int] = None
    block2_min_start_interval_days: Optional[int] = None

    # ===== Block3 조건 =====
    # Block3 추가 조건
    block3_volume_ratio: float = 15.0  # Block2 최고 거래량 대비 (%)
    block3_low_price_margin: float = 10.0  # Block2 최고가 저가 마진 (%)
    block3_min_candles_from_block: int = 4  # Block2 시작 후 최소 캔들 수
    block3_max_candles_from_block: Optional[int] = None  # Block2 시작 후 최대 캔들 수
    block3_lookback_min_candles: Optional[int] = None  # Lookback 최소 범위 (Block3 후보일 기준 과거 캔들)
    block3_lookback_max_candles: Optional[int] = None  # Lookback 최대 범위 (Block3 후보일 기준 과거 캔들)

    # Block3 전용 파라미터 (Optional, 없으면 Block1 값 사용)
    block3_entry_surge_rate: Optional[float] = None
    block3_entry_ma_period: Optional[int] = None
    block3_entry_max_deviation_ratio: Optional[float] = None
    block3_entry_min_trading_value: Optional[float] = None
    block3_entry_volume_high_days: Optional[int] = None  # 달력 기준 일수
    block3_entry_volume_spike_ratio: Optional[float] = None
    block3_entry_price_high_days: Optional[int] = None  # 달력 기준 일수
    block3_exit_condition_type: Optional[Block1ExitConditionType] = None
    block3_exit_ma_period: Optional[int] = None
    block3_min_start_interval_days: Optional[int] = None

    # ===== Block4 조건 =====
    # Block4 추가 조건
    block4_volume_ratio: float = 20.0  # Block3 최고 거래량 대비 (%)
    block4_low_price_margin: float = 10.0  # Block3 최고가 저가 마진 (%)
    block4_min_candles_from_block: int = 4  # Block3 시작 후 최소 캔들 수
    block4_max_candles_from_block: Optional[int] = None  # Block3 시작 후 최대 캔들 수
    block4_lookback_min_candles: Optional[int] = None  # Lookback 최소 범위 (Block4 후보일 기준 과거 캔들)
    block4_lookback_max_candles: Optional[int] = None  # Lookback 최대 범위 (Block4 후보일 기준 과거 캔들)

    # Block4 전용 파라미터 (Optional, 없으면 Block1 값 사용)
    block4_entry_surge_rate: Optional[float] = None
    block4_entry_ma_period: Optional[int] = None
    block4_entry_max_deviation_ratio: Optional[float] = None
    block4_entry_min_trading_value: Optional[float] = None
    block4_entry_volume_high_days: Optional[int] = None  # 달력 기준 일수
    block4_entry_volume_spike_ratio: Optional[float] = None
    block4_entry_price_high_days: Optional[int] = None  # 달력 기준 일수
    block4_exit_condition_type: Optional[Block1ExitConditionType] = None
    block4_exit_ma_period: Optional[int] = None
    block4_min_start_interval_days: Optional[int] = None
