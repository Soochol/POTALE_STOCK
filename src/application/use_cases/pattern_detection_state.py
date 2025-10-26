"""
Pattern Detection State - 패턴 탐지 상태 관리

Virtual Block System을 위한 상태 추적 클래스.
패턴 탐지 중 logical_level과 pattern_sequence를 일관성 있게 관리합니다.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.detections import DynamicBlockDetection
    from src.domain.entities.block_graph import BlockGraph, BlockNode


class PatternDetectionState:
    """
    패턴 탐지 상태 추적

    Virtual Block System에서 logical_level과 pattern_sequence를
    일관성 있게 관리하기 위한 상태 객체.

    Attributes:
        logical_level: 현재 논리적 레벨 (실제 급등 순서: 1, 2, 3, ...)
        physical_sequence: 물리적 생성 순서 (패턴 내 블록 번호: 1, 2, 3, ...)

    Example:
        >>> state = PatternDetectionState()
        >>> level, seq = state.create_real_block()  # (1, 1)
        >>> level, seq = state.create_real_block()  # (2, 2)
        >>> level, seq = state.create_virtual_block()  # (3, 0) - virtual이므로 sequence=0
        >>> level, seq = state.create_real_block()  # (4, 3) - level은 계속 증가
    """

    def __init__(self):
        """상태 초기화"""
        self.logical_level = 1
        self.physical_sequence = 1

    def get_current_level(self) -> int:
        """
        현재 logical_level 반환 (증가하지 않음)

        Virtual 블록 생성 시 현재 level을 확인할 때 사용.

        Returns:
            현재 logical_level

        Example:
            >>> state = PatternDetectionState()
            >>> state.get_current_level()  # 1
            >>> state.create_real_block()
            >>> state.get_current_level()  # 2
        """
        return self.logical_level

    def create_virtual_block(self) -> tuple[int, int]:
        """
        Virtual 블록 생성 (logical_level 증가 안 함, sequence=0)

        Spot으로 스킵된 블록을 생성할 때 사용.
        logical_level은 증가시키지 않고 현재 값 반환,
        pattern_sequence는 0으로 반환 (virtual 표시).

        Returns:
            (logical_level, pattern_sequence) 튜플
            - logical_level: 현재 level (증가 안 함)
            - pattern_sequence: 0 (virtual 표시)

        Example:
            >>> state = PatternDetectionState()
            >>> state.create_real_block()  # (1, 1)
            >>> state.create_virtual_block()  # (2, 0) - level 2에 virtual 블록
            >>> state.create_real_block()  # (2, 2) - 같은 level 2에 real 블록
        """
        # Virtual 블록: level 증가 안 함, sequence=0
        return self.logical_level, 0

    def create_real_block(self) -> tuple[int, int]:
        """
        Real 블록 생성 (logical_level 증가, sequence 증가)

        실제 블록이 감지되었을 때 사용.
        현재 logical_level과 sequence를 반환한 후,
        다음 블록을 위해 둘 다 1씩 증가.

        Returns:
            (logical_level, pattern_sequence) 튜플
            - logical_level: 현재 level (반환 후 증가)
            - pattern_sequence: 현재 sequence (반환 후 증가)

        Example:
            >>> state = PatternDetectionState()
            >>> state.create_real_block()  # (1, 1)
            >>> state.create_real_block()  # (2, 2)
            >>> state.create_real_block()  # (3, 3)
        """
        level = self.logical_level
        seq = self.physical_sequence

        # 다음 블록을 위해 증가
        self.logical_level += 1
        self.physical_sequence += 1

        return level, seq

    def reset(self):
        """
        상태 초기화 (새 패턴 시작 시 사용)

        Example:
            >>> state = PatternDetectionState()
            >>> state.create_real_block()
            >>> state.reset()
            >>> state.get_current_level()  # 1 (초기화됨)
        """
        self.logical_level = 1
        self.physical_sequence = 1

    def __repr__(self) -> str:
        return f"PatternDetectionState(level={self.logical_level}, seq={self.physical_sequence})"


@dataclass
class PatternContext:
    """
    단일 패턴의 실행 컨텍스트

    Option D 리팩토링의 핵심 클래스.
    각 패턴의 블록들을 독립적으로 관리하여 패턴 간 간섭을 방지합니다.

    책임:
    1. 패턴 ID 관리
    2. 패턴 내 블록 관리 (block_id → DynamicBlockDetection)
    3. 다음 탐지 대상 블록 추적
    4. 패턴 완료 여부 판단

    Example:
        >>> pattern_ctx = PatternContext(
        ...     pattern_id="SEED_025980_20180307_001",
        ...     ticker="025980",
        ...     blocks={'block1': block1},
        ...     block_graph=graph,
        ...     created_at=date(2018, 3, 7),
        ...     detection_state=PatternDetectionState()
        ... )
        >>> next_nodes = pattern_ctx.get_next_target_nodes()
        >>> is_done = pattern_ctx.is_completed()
    """

    # 식별 정보
    pattern_id: str  # "SEED_025980_20180307_001"
    ticker: str

    # 블록 관리
    blocks: Dict[str, 'DynamicBlockDetection']  # block_id → block
    block_graph: 'BlockGraph'

    # 시간 정보
    created_at: date

    # Virtual Block System 상태
    detection_state: PatternDetectionState = field(default_factory=PatternDetectionState)

    def get_active_block_ids(self) -> List[str]:
        """
        활성 상태인 블록 ID 목록 반환

        Returns:
            활성 블록 ID 리스트

        Example:
            >>> pattern_ctx.get_active_block_ids()
            ['block1', 'block2']
        """
        return [block_id for block_id, block in self.blocks.items() if block.is_active()]

    def get_next_target_nodes(self) -> List['BlockNode']:
        """
        다음에 탐지할 노드 목록 반환 (엣지 기반)

        활성 블록의 자식 노드들을 반환합니다.
        이미 활성 상태인 노드는 제외됩니다.

        Returns:
            다음 탐지 대상 노드 리스트

        Example:
            >>> nodes = pattern_ctx.get_next_target_nodes()
            >>> [node.block_id for node in nodes]
            ['block2', 'block3']
        """
        active_ids = self.get_active_block_ids()
        next_nodes = []

        for parent_id in active_ids:
            children = self.block_graph.get_children(parent_id)
            for child in children:
                # 이미 활성 상태인 블록은 제외
                if child.block_id not in self.blocks or not self.blocks[child.block_id].is_active():
                    next_nodes.append(child)

        return next_nodes

    def is_completed(self) -> bool:
        """
        패턴 완료 여부 확인

        모든 블록이 completed 상태여야 완료로 간주합니다.

        Returns:
            완료 여부

        Example:
            >>> pattern_ctx.is_completed()
            False
        """
        if not self.blocks:
            return False

        return all(block.is_completed() for block in self.blocks.values())

    def has_block(self, block_id: str) -> bool:
        """
        특정 블록 존재 여부 확인

        Args:
            block_id: 블록 ID

        Returns:
            존재 여부

        Example:
            >>> pattern_ctx.has_block('block1')
            True
        """
        return block_id in self.blocks

    def is_block_active(self, block_id: str) -> bool:
        """
        특정 블록이 활성 상태인지 확인

        Args:
            block_id: 블록 ID

        Returns:
            활성 상태 여부 (블록이 없으면 False)

        Example:
            >>> pattern_ctx.is_block_active('block1')
            True
        """
        return block_id in self.blocks and self.blocks[block_id].is_active()

    def __repr__(self) -> str:
        return (
            f"PatternContext(pattern_id='{self.pattern_id}', "
            f"ticker='{self.ticker}', "
            f"blocks={len(self.blocks)}, "
            f"created_at={self.created_at})"
        )
