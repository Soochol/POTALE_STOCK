"""
Block1 Condition Entity - 블록1 조건 엔티티
"""
from dataclasses import dataclass
from .base_entry_condition import BaseEntryCondition
from .base_entry_condition import Block1ExitConditionType  # Re-export for backward compatibility

__all__ = ['Block1Condition', 'Block1ExitConditionType']


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
