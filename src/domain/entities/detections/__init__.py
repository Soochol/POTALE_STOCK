"""
Detection Result Entities
블록 탐지 결과 엔티티
"""
from .base_detection import BaseBlockDetection
from .dynamic_block_detection import DynamicBlockDetection, BlockStatus

__all__ = [
    'BaseBlockDetection',
    'DynamicBlockDetection',
    'BlockStatus',
]
