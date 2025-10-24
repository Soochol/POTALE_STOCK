"""
Domain Entities Package
도메인 엔티티 패키지

모든 엔티티를 중앙에서 export하여 기존 import 경로 유지:
    from src.domain.entities import Stock, DynamicBlockDetection, ...
"""

# Core entities
from .core import Stock, DetectionResult

# Detection entities
from .detections import (
    BaseBlockDetection,
    DynamicBlockDetection,
    BlockStatus,
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

# Pattern entities
from .patterns import (
    SeedPattern,
    SeedPatternStatus,
    BlockFeatures,
    RedetectionConfig,
    ToleranceConfig,
    MatchingWeights,
)

__all__ = [
    # Core
    'Stock',
    'DetectionResult',

    # Detections
    'BaseBlockDetection',
    'DynamicBlockDetection',
    'BlockStatus',

    # Conditions (Dynamic System)
    'ExpressionEngine',

    # Block Graph (Dynamic Block Relationships)
    'BlockNode',
    'BlockEdge',
    'EdgeType',
    'BlockGraph',

    # Patterns
    'SeedPattern',
    'SeedPatternStatus',
    'BlockFeatures',
    'RedetectionConfig',
    'ToleranceConfig',
    'MatchingWeights',
]
