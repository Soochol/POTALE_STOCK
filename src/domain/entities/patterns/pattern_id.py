"""
Pattern ID Value Object

시드 패턴의 고유 식별자
"""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PatternId:
    """
    패턴 고유 ID (Value Object)

    불변(immutable) 객체로, 패턴의 고유성을 보장합니다.

    Format: SEED_{TICKER}_{YYYYMMDD}_{SEQUENCE}
    Example: SEED_025980_20180307_001

    Attributes:
        value: 패턴 ID 문자열

    Features:
        - Immutable (frozen=True)
        - Auto-generated from ticker, date, sequence
        - Guaranteed uniqueness within same ticker+date
    """
    value: str

    def __post_init__(self):
        """검증"""
        if not self.value:
            raise ValueError("PatternId value cannot be empty")

        if not isinstance(self.value, str):
            raise ValueError("PatternId value must be a string")

    @staticmethod
    def generate(ticker: str, detection_date: date, sequence: int) -> 'PatternId':
        """
        패턴 ID 자동 생성

        Args:
            ticker: 종목 코드 (예: "025980")
            detection_date: 탐지 날짜
            sequence: 시퀀스 번호 (같은 날짜에 여러 패턴이 있을 수 있음)

        Returns:
            PatternId: 생성된 패턴 ID

        Raises:
            ValueError: 입력값이 유효하지 않은 경우

        Example:
            >>> pattern_id = PatternId.generate("025980", date(2018, 3, 7), 1)
            >>> str(pattern_id)
            'SEED_025980_20180307_001'
        """
        if not ticker:
            raise ValueError("ticker cannot be empty")

        if sequence < 1:
            raise ValueError("sequence must be >= 1")

        date_str = detection_date.strftime('%Y%m%d')
        value = f"SEED_{ticker}_{date_str}_{sequence:03d}"

        return PatternId(value)

    @staticmethod
    def from_string(value: str) -> 'PatternId':
        """
        문자열로부터 PatternId 생성

        Args:
            value: 패턴 ID 문자열

        Returns:
            PatternId: 생성된 패턴 ID

        Example:
            >>> pattern_id = PatternId.from_string("SEED_025980_20180307_001")
        """
        return PatternId(value)

    def __str__(self) -> str:
        """문자열 표현"""
        return self.value

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"PatternId('{self.value}')"

    def __hash__(self) -> int:
        """해시 값 (딕셔너리 키로 사용 가능)"""
        return hash(self.value)

    def __eq__(self, other) -> bool:
        """동등성 비교"""
        if not isinstance(other, PatternId):
            return False
        return self.value == other.value
