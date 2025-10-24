# Old imports removed (backed up to backup/old_system/)
# - DetectConditionUseCase, CreateConditionUseCase, etc.
# - DetectBlock1-3UseCase, DetectBlocksIntegratedUseCase, DetectPatternsUseCase

# New dynamic system
from .dynamic_block_detector import DynamicBlockDetector

__all__ = [
    'DynamicBlockDetector',
]
