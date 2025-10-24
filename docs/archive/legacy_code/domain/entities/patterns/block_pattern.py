"""
Block Pattern Entity - 블록 패턴 엔티티

재탐지 시스템의 패턴 단위
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class BlockPattern:
    """
    블록 패턴 엔티티

    각 Block1 Seed를 기준으로 한 독립적인 패턴
    - Seed: Block1/2/3 Seed 참조
    - 재탐지 기간: 5년
    """

    pattern_id: Optional[int]  # 패턴 ID (DB 저장 후 할당)
    ticker: str  # 종목 코드

    # Seed 참조
    seed_block1_id: str  # Block1 Seed의 block1_id
    seed_block2_id: str  # Block2 Seed의 block2_id
    seed_block3_id: str  # Block3 Seed의 block3_id

    # 재탐지 기간
    redetection_start: date  # 재탐지 시작일 (Block1 Seed 시작일)
    redetection_end: date  # 재탐지 종료일 (시작일 + 5년)

    # Block4/5/6 Seed (선택적) - Optional 필드는 맨 뒤로
    seed_block4_id: Optional[str] = None  # Block4 Seed의 block4_id (선택적)
    seed_block5_id: Optional[str] = None  # Block5 Seed의 block5_id (선택적)
    seed_block6_id: Optional[str] = None  # Block6 Seed의 block6_id (선택적)

    def __repr__(self):
        return (
            f"<BlockPattern("
            f"id={self.pattern_id}, "
            f"ticker={self.ticker}, "
            f"period={self.redetection_start}~{self.redetection_end}"
            f")>"
        )

    def get_redetection_days(self) -> int:
        """재탐지 기간 (일수) 반환"""
        return (self.redetection_end - self.redetection_start).days
