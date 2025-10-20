"""
Detection Repositories
블록 탐지 결과 저장/조회 Repository
"""
from .block1_repository import Block1Repository
from .block2_repository import Block2Repository
from .block3_repository import Block3Repository
from .block4_repository import Block4Repository

__all__ = [
    'Block1Repository',
    'Block2Repository',
    'Block3Repository',
    'Block4Repository',
]
