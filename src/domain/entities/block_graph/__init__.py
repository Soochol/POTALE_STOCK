"""
Block Graph Package - Dynamic Block Relationships

블록 간의 동적 관계를 정의하고 관리하는 그래프 시스템.

지원 기능:
- 분기 (Branching): Block1 → [Block2A, Block2B]
- 건너뛰기 (Skipping): Block1 → Block3
- 조건부 관계 (Conditional): 조건에 따라 다음 블록 선택
- 다중 부모 (Multi-parent): Block3이 Block2A, Block2B 모두의 자식
"""

from .block_node import BlockNode
from .block_edge import BlockEdge, EdgeType
from .block_graph import BlockGraph

__all__ = [
    'BlockNode',
    'BlockEdge',
    'EdgeType',
    'BlockGraph',
]
