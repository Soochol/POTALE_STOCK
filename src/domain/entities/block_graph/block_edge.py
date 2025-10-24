"""
BlockEdge - 블록 간 관계 (그래프의 엣지)

블록 간의 전이(transition) 관계를 정의. 조건부 전이를 지원.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class EdgeType(Enum):
    """
    엣지 타입

    - SEQUENTIAL: 순차적 전이 (Block1 → Block2)
    - CONDITIONAL: 조건부 전이 (조건 만족 시 전이)
    - OPTIONAL: 선택적 전이 (스킵 가능)
    - BRANCHING: 분기 (하나의 블록에서 여러 블록으로 분기)
    """
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"
    BRANCHING = "branching"


@dataclass
class BlockEdge:
    """
    블록 간 관계 (엣지)

    하나의 블록에서 다른 블록으로의 전이를 나타냄.

    Attributes:
        from_block_id: 시작 블록 ID (예: "block1")
        to_block_id: 도착 블록 ID (예: "block2")
        edge_type: 엣지 타입 (순차, 조건부, 선택적, 분기)
        condition: 전이 조건 표현식 (조건부 엣지의 경우)
        priority: 우선순위 (낮을수록 먼저 평가, 분기 시 사용)
        metadata: 추가 메타데이터
    """

    from_block_id: str
    to_block_id: str
    edge_type: EdgeType = EdgeType.SEQUENTIAL
    condition: Optional[str] = None
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """엣지 검증"""
        if not self.from_block_id:
            raise ValueError("from_block_id는 필수입니다")

        if not self.to_block_id:
            raise ValueError("to_block_id는 필수입니다")

        if self.from_block_id == self.to_block_id:
            raise ValueError(f"자기 자신으로의 엣지는 허용되지 않습니다: {self.from_block_id}")

        # 조건부 엣지는 condition이 필수
        if self.edge_type == EdgeType.CONDITIONAL and not self.condition:
            raise ValueError(f"조건부 엣지는 condition이 필요합니다: {self.from_block_id} → {self.to_block_id}")

    def is_conditional(self) -> bool:
        """조건부 엣지인지 확인"""
        return self.edge_type == EdgeType.CONDITIONAL

    def is_branching(self) -> bool:
        """분기 엣지인지 확인"""
        return self.edge_type == EdgeType.BRANCHING

    def is_optional(self) -> bool:
        """선택적 엣지인지 확인"""
        return self.edge_type == EdgeType.OPTIONAL

    def validate(self) -> list[str]:
        """
        엣지 유효성 검증

        Returns:
            오류 메시지 리스트 (빈 리스트 = 검증 성공)
        """
        errors = []

        if not self.from_block_id:
            errors.append("from_block_id가 비어있습니다")

        if not self.to_block_id:
            errors.append("to_block_id가 비어있습니다")

        if self.from_block_id == self.to_block_id:
            errors.append(f"자기 자신으로의 엣지: {self.from_block_id}")

        # 조건부 엣지 검증
        if self.edge_type == EdgeType.CONDITIONAL and not self.condition:
            errors.append(f"조건부 엣지에 condition이 없습니다: {self.from_block_id} → {self.to_block_id}")

        return errors

    def __repr__(self) -> str:
        cond_str = f", condition='{self.condition}'" if self.condition else ""
        return (
            f"BlockEdge({self.from_block_id} → {self.to_block_id}, "
            f"type={self.edge_type.value}{cond_str}, priority={self.priority})"
        )
