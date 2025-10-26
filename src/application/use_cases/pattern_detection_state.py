"""
Pattern Detection State - 패턴 탐지 상태 관리

Virtual Block System을 위한 상태 추적 클래스.
패턴 탐지 중 logical_level과 pattern_sequence를 일관성 있게 관리합니다.
"""


class PatternDetectionState:
    """
    패턴 탐지 상태 추적

    Virtual Block System에서 logical_level과 pattern_sequence를
    일관성 있게 관리하기 위한 상태 객체.

    Attributes:
        logical_level: 현재 논리적 레벨 (실제 급등 순서: 1, 2, 3, ...)
        physical_sequence: 물리적 생성 순서 (패턴 내 블록 번호: 1, 2, 3, ...)

    Example:
        >>> state = PatternDetectionState()
        >>> level, seq = state.create_real_block()  # (1, 1)
        >>> level, seq = state.create_real_block()  # (2, 2)
        >>> level, seq = state.create_virtual_block()  # (3, 0) - virtual이므로 sequence=0
        >>> level, seq = state.create_real_block()  # (4, 3) - level은 계속 증가
    """

    def __init__(self):
        """상태 초기화"""
        self.logical_level = 1
        self.physical_sequence = 1

    def get_current_level(self) -> int:
        """
        현재 logical_level 반환 (증가하지 않음)

        Virtual 블록 생성 시 현재 level을 확인할 때 사용.

        Returns:
            현재 logical_level

        Example:
            >>> state = PatternDetectionState()
            >>> state.get_current_level()  # 1
            >>> state.create_real_block()
            >>> state.get_current_level()  # 2
        """
        return self.logical_level

    def create_virtual_block(self) -> tuple[int, int]:
        """
        Virtual 블록 생성 (logical_level 증가 안 함, sequence=0)

        Spot으로 스킵된 블록을 생성할 때 사용.
        logical_level은 증가시키지 않고 현재 값 반환,
        pattern_sequence는 0으로 반환 (virtual 표시).

        Returns:
            (logical_level, pattern_sequence) 튜플
            - logical_level: 현재 level (증가 안 함)
            - pattern_sequence: 0 (virtual 표시)

        Example:
            >>> state = PatternDetectionState()
            >>> state.create_real_block()  # (1, 1)
            >>> state.create_virtual_block()  # (2, 0) - level 2에 virtual 블록
            >>> state.create_real_block()  # (2, 2) - 같은 level 2에 real 블록
        """
        # Virtual 블록: level 증가 안 함, sequence=0
        return self.logical_level, 0

    def create_real_block(self) -> tuple[int, int]:
        """
        Real 블록 생성 (logical_level 증가, sequence 증가)

        실제 블록이 감지되었을 때 사용.
        현재 logical_level과 sequence를 반환한 후,
        다음 블록을 위해 둘 다 1씩 증가.

        Returns:
            (logical_level, pattern_sequence) 튜플
            - logical_level: 현재 level (반환 후 증가)
            - pattern_sequence: 현재 sequence (반환 후 증가)

        Example:
            >>> state = PatternDetectionState()
            >>> state.create_real_block()  # (1, 1)
            >>> state.create_real_block()  # (2, 2)
            >>> state.create_real_block()  # (3, 3)
        """
        level = self.logical_level
        seq = self.physical_sequence

        # 다음 블록을 위해 증가
        self.logical_level += 1
        self.physical_sequence += 1

        return level, seq

    def reset(self):
        """
        상태 초기화 (새 패턴 시작 시 사용)

        Example:
            >>> state = PatternDetectionState()
            >>> state.create_real_block()
            >>> state.reset()
            >>> state.get_current_level()  # 1 (초기화됨)
        """
        self.logical_level = 1
        self.physical_sequence = 1

    def __repr__(self) -> str:
        return f"PatternDetectionState(level={self.logical_level}, seq={self.physical_sequence})"
