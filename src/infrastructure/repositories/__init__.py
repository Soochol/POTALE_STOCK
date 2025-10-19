"""
Infrastructure Repositories
데이터 저장/조회를 위한 Repository 클래스들
"""
# Common utilities
from .common import (
    BaseDetectionRepository,
    BaseConditionPresetRepository,
    bool_to_int,
    int_to_bool,
)

# Stock & Condition repositories
from .sqlite_stock_repository import SqliteStockRepository
from .yaml_condition_repository import YamlConditionRepository

# Block Detection repositories
from .block1_repository import Block1Repository
from .block2_repository import Block2Repository
from .block3_repository import Block3Repository

# Condition Preset repositories (통합된 Seed/Redetection 방식 사용)
from .seed_condition_preset_repository import SeedConditionPresetRepository
from .redetection_condition_preset_repository import RedetectionConditionPresetRepository
from .block_pattern_repository import BlockPatternRepository

__all__ = [
    # Common
    'BaseDetectionRepository',
    'BaseConditionPresetRepository',
    'bool_to_int',
    'int_to_bool',
    # Stock & Condition
    'SqliteStockRepository',
    'YamlConditionRepository',
    # Block Detection
    'Block1Repository',
    'Block2Repository',
    'Block3Repository',
    # Condition Preset (통합)
    'SeedConditionPresetRepository',
    'RedetectionConditionPresetRepository',
    # Pattern
    'BlockPatternRepository',
]
