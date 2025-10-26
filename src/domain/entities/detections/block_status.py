"""
Block Status Enum

블록 상태를 나타내는 Enum
"""
from enum import Enum


class BlockStatus(Enum):
    """블록 상태"""
    ACTIVE = "active"  # 진행 중
    COMPLETED = "completed"  # 정상 완료
    FAILED = "failed"  # 조건 실패로 종료
    VIRTUAL_SKIPPED = "virtual_skipped"  # Spot으로 스킵된 가상 블록
