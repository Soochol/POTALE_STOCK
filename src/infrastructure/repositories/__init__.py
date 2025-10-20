"""
Infrastructure Repositories
데이터 저장/조회를 위한 Repository 클래스들

새로운 구조:
- detection/: 블록 탐지 결과 Repository (Block1/2/3/4)
- preset/: 조건 프리셋 Repository (Seed/Redetection)
- pattern/: 블록 패턴 Repository
- stock/: 주식 데이터 Repository
- condition/: 조건 Repository (Legacy)
- common/: 공통 베이스 클래스 및 유틸리티
"""

# Common utilities (직접 export)
from .common import (
    BaseDetectionRepository,
    BaseConditionPresetRepository,
    UUIDMixin,
    DurationCalculatorMixin,
    ConditionPresetMapperMixin,
    DetectionQueryBuilder,
    with_session,
    bool_to_int,
    int_to_bool,
)

# Detection Repositories (새 구조에서 import, backward compatibility 유지)
from .detection import (
    Block1Repository,
    Block2Repository,
    Block3Repository,
    Block4Repository,
)

# Preset Repositories
from .preset import (
    SeedConditionPresetRepository,
    RedetectionConditionPresetRepository,
)

# Pattern Repositories
from .pattern import BlockPatternRepository

# Stock Repositories
from .stock import SqliteStockRepository

# Condition Repositories (Legacy)
from .condition import YamlConditionRepository

__all__ = [
    # Common - Base Classes
    'BaseDetectionRepository',
    'BaseConditionPresetRepository',
    # Common - Mixins
    'UUIDMixin',
    'DurationCalculatorMixin',
    'ConditionPresetMapperMixin',
    # Common - Query Builders
    'DetectionQueryBuilder',
    # Common - Decorators
    'with_session',
    # Common - Converters
    'bool_to_int',
    'int_to_bool',
    # Detection
    'Block1Repository',
    'Block2Repository',
    'Block3Repository',
    'Block4Repository',
    # Preset
    'SeedConditionPresetRepository',
    'RedetectionConditionPresetRepository',
    # Pattern
    'BlockPatternRepository',
    # Stock
    'SqliteStockRepository',
    # Condition (Legacy)
    'YamlConditionRepository',
]
