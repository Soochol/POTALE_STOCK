"""
Seed Condition Entity - Seed 조건 엔티티

Seed 탐지를 위한 엄격한 조건
"""
from dataclasses import dataclass
from typing import Optional
from src.domain.entities.block1_condition import Block1ExitConditionType


@dataclass
class SeedCondition:
    """
    Seed 조건 엔티티 (엄격한 조건)

    Block1/2/3 Seed를 찾기 위한 엄격한 조건 세트
    - Block1 기본 조건
    - Block2 추가 조건
    - Block3 추가 조건
    - Cooldown (Seed 간 최소 간격)
    """

    # ===== Block1 조건 =====
    # 진입 조건
    entry_surge_rate: float  # 등락률 (%, 예: 8.0 = 8%)
    entry_ma_period: int  # 진입용 이동평균선 기간
    entry_high_above_ma: bool = True  # 고가 >= 이평선 검사
    entry_max_deviation_ratio: float = 120.0  # 이격도 (%)
    entry_min_trading_value: float = 300.0  # 거래대금 (억)
    entry_volume_high_months: int = 12  # 신고거래량 기간 (개월)
    entry_volume_spike_ratio: float = 400.0  # 전날 대비 비율 (%)
    entry_price_high_months: int = 2  # N개월 신고가

    # 종료 조건
    exit_condition_type: Block1ExitConditionType = Block1ExitConditionType.MA_BREAK
    exit_ma_period: Optional[int] = None  # 종료용 이동평균선 기간

    # Seed 간 최소 간격
    cooldown_days: int = 20  # 기본 20일

    # ===== Block2 추가 조건 =====
    block2_volume_ratio: float = 15.0  # Block1 최고 거래량 대비 (%)
    block2_low_price_margin: float = 10.0  # Block1 최고가 저가 마진 (%)
    block2_min_candles_after_block1: int = 4  # Block1 시작 후 최소 캔들 수

    # ===== Block3 추가 조건 =====
    block3_volume_ratio: float = 15.0  # Block2 최고 거래량 대비 (%)
    block3_low_price_margin: float = 10.0  # Block2 최고가 저가 마진 (%)
    block3_min_candles_after_block2: int = 4  # Block2 시작 후 최소 캔들 수

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

        return True

    def __repr__(self):
        return (
            f"<SeedCondition("
            f"surge={self.entry_surge_rate}%, "
            f"MA{self.entry_ma_period}, "
            f"vol={self.entry_volume_high_months}mo, "
            f"cooldown={self.cooldown_days}d"
            f")>"
        )
