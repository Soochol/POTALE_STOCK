"""
Detection Result Entities
블록 탐지 결과 엔티티
"""
from .base_detection import BaseBlockDetection
from .block1_detection import Block1Detection
from .block2_detection import Block2Detection
from .block3_detection import Block3Detection
from .block4_detection import Block4Detection

__all__ = [
    'BaseBlockDetection',
    'Block1Detection',
    'Block2Detection',
    'Block3Detection',
    'Block4Detection',
]
