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
)

# Condition entities
from .conditions import (
    BaseEntryCondition,
    Block1ExitConditionType,
    Block1Condition,
    Block2Condition,
    Block3Condition,
    Block4Condition,
    SeedCondition,
    RedetectionCondition,
)

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

    # Conditions
    'BaseEntryCondition',
    'Block1ExitConditionType',
    'Block1Condition',
    'Block2Condition',
    'Block3Condition',
    'Block4Condition',
    'SeedCondition',
    'RedetectionCondition',

    # Patterns
    'BlockPattern',
]
