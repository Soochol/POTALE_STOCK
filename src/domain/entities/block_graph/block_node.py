"""
BlockNode - 블록 그래프의 노드

각 블록을 표현하는 노드. 블록의 정의(조건, 파라미터)와 연결 정보를 포함.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class BlockNode:
    """
    블록 그래프의 노드

    하나의 블록 정의를 나타냄 (예: Block1, Block2, Block3, ...)

    Attributes:
        block_id: 블록 ID (예: "block1", "block2a", "block3")
        block_type: 블록 타입 번호 (1, 2, 3, 4, 5, ...)
        name: 블록 이름 (예: "Initial Surge", "Continuation Phase")
        description: 블록 설명
        entry_conditions: 진입 조건 표현식 리스트
        exit_conditions: 종료 조건 표현식 리스트
        parameters: 블록별 파라미터 (예: min_candles, max_candles, ...)
        metadata: 추가 메타데이터 (선택적)
    """

    block_id: str
    block_type: int
    name: str
    description: str = ""
    entry_conditions: List[str] = field(default_factory=list)
    exit_conditions: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """블록 ID와 타입 검증"""
        if not self.block_id:
            raise ValueError("block_id는 필수입니다")

        if self.block_type < 1:
            raise ValueError(f"block_type은 1 이상이어야 합니다: {self.block_type}")

    def add_entry_condition(self, condition_expression: str) -> None:
        """
        진입 조건 추가

        Args:
            condition_expression: 조건 표현식 (예: "current.close >= ma(120)")
        """
        if condition_expression not in self.entry_conditions:
            self.entry_conditions.append(condition_expression)

    def add_exit_condition(self, condition_expression: str) -> None:
        """
        종료 조건 추가

        Args:
            condition_expression: 조건 표현식
        """
        if condition_expression not in self.exit_conditions:
            self.exit_conditions.append(condition_expression)

    def set_parameter(self, key: str, value: Any) -> None:
        """
        파라미터 설정

        Args:
            key: 파라미터 키 (예: "min_candles_from_previous")
            value: 파라미터 값
        """
        self.parameters[key] = value

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        파라미터 조회

        Args:
            key: 파라미터 키
            default: 기본값 (파라미터가 없을 때)

        Returns:
            파라미터 값 또는 기본값
        """
        return self.parameters.get(key, default)

    def validate(self) -> List[str]:
        """
        블록 노드 유효성 검증

        Returns:
            오류 메시지 리스트 (빈 리스트 = 검증 성공)
        """
        errors = []

        # 필수 필드 검증
        if not self.block_id:
            errors.append("block_id가 비어있습니다")

        if not self.name:
            errors.append("name이 비어있습니다")

        if self.block_type < 1:
            errors.append(f"block_type이 유효하지 않습니다: {self.block_type}")

        # 조건 검증 (최소 1개의 진입 조건 필요)
        if not self.entry_conditions:
            errors.append("최소 1개의 entry_condition이 필요합니다")

        return errors

    def __repr__(self) -> str:
        return (
            f"BlockNode(id='{self.block_id}', type={self.block_type}, "
            f"name='{self.name}', entry_conds={len(self.entry_conditions)}, "
            f"exit_conds={len(self.exit_conditions)})"
        )
