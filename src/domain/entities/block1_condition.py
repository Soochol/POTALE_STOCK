"""
Block1 Condition Entity - 블록1 조건 엔티티
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
class Block1Condition:
    """
    블록1 조건 엔티티

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

    def validate(self) -> bool:
        """조건 유효성 검사"""
        # 최소 1개 이상의 진입 조건 필요
        has_condition = any([
            self.entry_surge_rate is not None,
            self.entry_ma_period is not None,
            self.entry_min_trading_value is not None,
            self.entry_volume_high_months is not None
        ])

        if not has_condition:
            return False

        # 값 범위 검증
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

        if self.cooldown_days <= 0:
            return False

        if self.entry_price_high_months is not None and self.entry_price_high_months <= 0:
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
        if self.entry_min_trading_value:
            conditions.append(f"거래대금>={self.entry_min_trading_value}억")
        if self.entry_volume_high_months:
            conditions.append(f"{self.entry_volume_high_months}개월신고거래량")
        if self.entry_volume_spike_ratio:
            conditions.append(f"전날대비{self.entry_volume_spike_ratio*100:.0f}%증가")

        return f"<Block1Condition({', '.join(conditions)})>"
