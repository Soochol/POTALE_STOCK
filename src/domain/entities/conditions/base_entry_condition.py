"""
Base Entry Condition Entity - 기본 진입/종료 조건 엔티티

모든 블록(Block1/2/3/4)이 공통으로 사용하는 진입/종료 조건을 정의
각 블록은 이 조건을 포함(composition)하여 사용하며, 값은 블록별로 다를 수 있음
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Block1ExitConditionType(Enum):
    """블록1 종료 조건 타입"""
    MA_BREAK = "ma_break"                      # 이동평균선 이탈
    THREE_LINE_REVERSAL = "three_line_reversal"  # 삼선전환도 첫 음봉
    BODY_MIDDLE = "body_middle"                # 블록1 캔들 몸통 중간 가격 이탈


@dataclass
class BaseEntryCondition:
    """
    모든 블록이 공통으로 사용하는 진입/종료 조건

    각 블록은 이 조건의 인스턴스를 생성하여 사용하며,
    블록별로 다른 값을 설정할 수 있음

    예시:
        # Block1: 8% 급등률
        block1_base = BaseEntryCondition(block1_entry_surge_rate=8.0, block1_entry_ma_period=120)

        # Block2: 6% 급등률 (완화된 조건)
        block2_base = BaseEntryCondition(block1_entry_surge_rate=6.0, block1_entry_ma_period=90)

    진입 조건 (8가지):
    1. 등락률 조건: 전일 대비 N% 이상
    2. 이평선 조건 A: 당일 고가 >= 이동평균선 N
    3. 이평선 조건 B: 이동평균선 N 이격도 M% 이하
    4. 거래대금 조건: N억 이상
    5. 거래량 조건: N개월 신고거래량
    6. 전날 거래량 비율
    7. 신고가 조건

    종료 조건 (3가지 중 택1):
    1. 이동평균선 이탈
    2. 삼선전환도 첫 음봉
    3. 블록1 캔들 몸통 중간
    """

    # ===== 진입 조건 (8개) =====
    # 조건 1: 등락률
    block1_entry_surge_rate: Optional[float] = None  # 등락률 (%, 예: 5.0 = 5%)

    # 조건 2, 3: 이평선
    block1_entry_ma_period: Optional[int] = None  # 진입용 이동평균선 기간 (예: 5, 20, 120일). None이면 MA 조건 전체 skip, 값이 있으면 고가≥MA 체크
    block1_entry_max_deviation_ratio: Optional[float] = None  # 이격도 (MA를 100으로 봤을 때, 예: 115 = MA의 115%)

    # 조건 4: 거래대금
    block1_entry_min_trading_value: Optional[float] = None  # 거래대금 (억, 예: 100 = 100억)

    # 조건 5: 거래량
    block1_entry_volume_high_days: Optional[int] = None  # 신고거래량 기간 (달력 기준 일수, 예: 90일, 180일, 365일)

    # 조건 6: 전날 거래량 비율
    block1_entry_volume_spike_ratio: Optional[float] = None  # 전날 대비 비율 (%, 예: 400 = 400%, 즉 4배)

    # 조건 7: 신고가 조건
    block1_entry_price_high_days: Optional[int] = None  # N일 신고가 (달력 기준 일수, 예: 90일, 180일, 365일)

    # ===== 종료 조건 (2개) =====
    block1_exit_condition_type: Block1ExitConditionType = Block1ExitConditionType.MA_BREAK
    block1_exit_ma_period: Optional[int] = None  # 종료용 이동평균선 기간 (None이면 entry_ma_period 사용)

    # ===== 시스템 (1개) =====
    block1_min_start_interval_days: int = 120  # 같은 레벨 블록 중복 방지: 시작 후 N일간 새 블록 탐지 금지

    def validate(self) -> bool:
        """
        조건 유효성 검사

        Returns:
            유효하면 True, 아니면 False
        """
        # 최소 1개 이상의 진입 조건 필요
        has_condition = any([
            self.block1_entry_surge_rate is not None,
            self.block1_entry_ma_period is not None,
            self.block1_entry_min_trading_value is not None,
            self.block1_entry_volume_high_days is not None
        ])

        if not has_condition:
            return False

        # 값 범위 검증
        if self.block1_entry_surge_rate is not None and self.block1_entry_surge_rate <= 0:
            return False

        if self.block1_entry_ma_period is not None and self.block1_entry_ma_period <= 0:
            return False

        if self.block1_entry_max_deviation_ratio is not None and self.block1_entry_max_deviation_ratio <= 0:
            return False

        if self.block1_entry_min_trading_value is not None and self.block1_entry_min_trading_value <= 0:
            return False

        if self.block1_entry_volume_high_days is not None and self.block1_entry_volume_high_days <= 0:
            return False

        if self.block1_entry_volume_spike_ratio is not None and self.block1_entry_volume_spike_ratio < 0:
            return False

        if self.block1_entry_price_high_days is not None and self.block1_entry_price_high_days <= 0:
            return False

        if self.block1_min_start_interval_days <= 0:
            return False

        return True

    def __repr__(self):
        conditions = []
        if self.block1_entry_surge_rate:
            conditions.append(f"등락률>={self.block1_entry_surge_rate}%")
        if self.block1_entry_ma_period:
            conditions.append(f"진입MA{self.block1_entry_ma_period}")
        if self.block1_exit_ma_period:
            conditions.append(f"종료MA{self.block1_exit_ma_period}")
        if self.block1_entry_min_trading_value:
            conditions.append(f"거래대금>={self.block1_entry_min_trading_value}억")
        if self.block1_entry_volume_high_days:
            conditions.append(f"{self.block1_entry_volume_high_days}일신고거래량")
        if self.block1_entry_volume_spike_ratio:
            conditions.append(f"전날대비{self.block1_entry_volume_spike_ratio*100:.0f}%증가")

        return f"<BaseEntryCondition({', '.join(conditions)})>"
