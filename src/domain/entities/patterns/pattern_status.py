"""
Pattern Status - Finite State Machine

시드 패턴의 상태를 관리하는 FSM
"""
from enum import Enum


class PatternStatus(str, Enum):
    """
    패턴 상태 (Finite State Machine)

    상태 전이 규칙:
        ACTIVE → COMPLETED → ARCHIVED

    States:
        ACTIVE: 진행 중 (블록 추가 가능)
        COMPLETED: 완료됨 (모든 블록 completed)
        ARCHIVED: 보관됨 (DB 저장 완료, 메모리 해제 가능)

    Features:
        - 불변 상태 전이 규칙 강제
        - 각 상태에서 허용되는 작업 명시
    """
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    def can_add_block(self) -> bool:
        """
        블록 추가 가능 여부

        Returns:
            ACTIVE 상태에서만 True

        Example:
            >>> status = PatternStatus.ACTIVE
            >>> status.can_add_block()
            True
            >>> status = PatternStatus.COMPLETED
            >>> status.can_add_block()
            False
        """
        return self == PatternStatus.ACTIVE

    def can_complete(self) -> bool:
        """
        완료 처리 가능 여부

        Returns:
            ACTIVE 상태에서만 True

        Example:
            >>> status = PatternStatus.ACTIVE
            >>> status.can_complete()
            True
        """
        return self == PatternStatus.ACTIVE

    def can_archive(self) -> bool:
        """
        보관 처리 가능 여부

        Returns:
            COMPLETED 상태에서만 True

        Example:
            >>> status = PatternStatus.COMPLETED
            >>> status.can_archive()
            True
        """
        return self == PatternStatus.COMPLETED

    def validate_transition(self, new_status: 'PatternStatus') -> bool:
        """
        상태 전이 유효성 검증

        허용되는 전이:
            ACTIVE → COMPLETED
            COMPLETED → ARCHIVED

        Args:
            new_status: 전이하려는 새 상태

        Returns:
            전이 가능하면 True

        Example:
            >>> current = PatternStatus.ACTIVE
            >>> current.validate_transition(PatternStatus.COMPLETED)
            True
            >>> current.validate_transition(PatternStatus.ARCHIVED)
            False
        """
        allowed_transitions = {
            PatternStatus.ACTIVE: [PatternStatus.COMPLETED],
            PatternStatus.COMPLETED: [PatternStatus.ARCHIVED],
            PatternStatus.ARCHIVED: []  # 최종 상태
        }

        return new_status in allowed_transitions.get(self, [])

    def __str__(self) -> str:
        """문자열 표현"""
        return self.value

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"PatternStatus.{self.name}"
