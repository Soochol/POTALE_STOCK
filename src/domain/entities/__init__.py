"""
Domain Entities Package
도메인 엔티티 패키지

모든 엔티티를 중앙에서 export하여 기존 import 경로 유지:
    from src.domain.entities import Stock, Block1Detection, Block1Condition, ...
"""

# Core entities
from .core import Stock, DetectionResult, Condition, Rule, RuleType

# Detection entities
from .detections import (
    BaseBlockDetection,
    Block1Detection,
    Block2Detection,
    Block3Detection,
    Block4Detection,
    Block5Detection,
    Block6Detection,
)

# Condition entities (Dynamic System)
from .conditions import (
    ExpressionEngine,
)

# Block Graph (Dynamic Block Relationships)
from .block_graph import (
    BlockNode,
    BlockEdge,
    EdgeType,
    BlockGraph,
)

# Old conditions (backed up to backup/old_system)
# BaseEntryCondition, Block1Condition, etc. are no longer used

# Pattern entities
from .patterns import BlockPattern

__all__ = [
    # Core
    'Stock',
    'DetectionResult',
    'Condition',
    'Rule',
    'RuleType',

    # Detections
    'BaseBlockDetection',
    'Block1Detection',
    'Block2Detection',
    'Block3Detection',
    'Block4Detection',
    'Block5Detection',
    'Block6Detection',

    # Conditions (Dynamic System)
    'ExpressionEngine',

    # Block Graph (Dynamic Block Relationships)
    'BlockNode',
    'BlockEdge',
    'EdgeType',
    'BlockGraph',

    # Patterns
    'BlockPattern',
]
