"""
Redetection Event Entity

재탐지 이벤트 도메인 엔티티
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .block_status import BlockStatus


@dataclass
class RedetectionEvent:
    """
    재탐지 이벤트

    원래 Seed Block의 고점 근처로 가격이 재진입한 이벤트를 나타냅니다.

    주요 특징:
    - 항상 parent Seed Block만 참조 (재탐지의 재탐지는 없음)
    - 한 블록당 한 번에 1개만 active 가능
    - Sequence 번호로 식별 (1, 2, 3, ...)
    - Pattern 완료 조건에는 영향 없음 (부가 정보)

    Lifecycle:
        ACTIVE → COMPLETED

    Example:
        >>> redetection = RedetectionEvent(
        ...     sequence=1,
        ...     parent_block_id='block1',
        ...     started_at=date(2018, 3, 20),
        ...     peak_price=7200.0,
        ...     peak_volume=4500000
        ... )
        >>> redetection.is_active()
        True
        >>> redetection.complete(date(2018, 3, 22))
        >>> redetection.is_completed()
        True
    """

    sequence: int
    """재탐지 순서 번호 (1, 2, 3, ...)"""

    parent_block_id: str
    """부모 Seed Block ID ('block1', 'block2', ...)"""

    started_at: date
    """재탐지 시작일"""

    ended_at: Optional[date] = None
    """재탐지 종료일 (None = 아직 진행 중)"""

    peak_price: float = 0.0
    """재탐지 기간 중 최고가"""

    peak_volume: int = 0
    """재탐지 기간 중 최대 거래량"""

    status: BlockStatus = field(default=BlockStatus.ACTIVE)
    """재탐지 상태 (active/completed)"""

    def is_active(self) -> bool:
        """
        Active 상태 여부

        Returns:
            True if status == ACTIVE
        """
        return self.status == BlockStatus.ACTIVE

    def is_completed(self) -> bool:
        """
        Completed 상태 여부

        Returns:
            True if status == COMPLETED
        """
        return self.status == BlockStatus.COMPLETED

    def complete(self, end_date: date) -> None:
        """
        재탐지 완료 처리

        Args:
            end_date: 종료일

        Raises:
            ValueError: 이미 completed 상태인 경우

        Example:
            >>> redetection.complete(date(2018, 3, 22))
        """
        if self.is_completed():
            raise ValueError(
                f"Redetection #{self.sequence} is already completed"
            )

        self.ended_at = end_date
        self.status = BlockStatus.COMPLETED

    def update_peak(self, price: float, volume: int) -> None:
        """
        Peak 가격/거래량 업데이트

        Args:
            price: 현재 고가
            volume: 현재 거래량

        Example:
            >>> redetection.update_peak(7300.0, 4800000)
        """
        if price > self.peak_price:
            self.peak_price = price

        if volume > self.peak_volume:
            self.peak_volume = volume

    def to_dict(self) -> dict:
        """
        JSON 직렬화

        Returns:
            Dictionary representation

        Example:
            >>> redet.to_dict()
            {
                'sequence': 1,
                'parent_block_id': 'block1',
                'started_at': '2018-03-20',
                'ended_at': '2018-03-22',
                'peak_price': 7200.0,
                'peak_volume': 4500000,
                'status': 'completed'
            }
        """
        return {
            'sequence': self.sequence,
            'parent_block_id': self.parent_block_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'peak_price': self.peak_price,
            'peak_volume': self.peak_volume,
            'status': self.status.value
        }

    @staticmethod
    def from_dict(data: dict) -> 'RedetectionEvent':
        """
        JSON 역직렬화

        Args:
            data: Dictionary data

        Returns:
            RedetectionEvent instance

        Example:
            >>> data = {'sequence': 1, 'parent_block_id': 'block1', ...}
            >>> redet = RedetectionEvent.from_dict(data)
        """
        return RedetectionEvent(
            sequence=data['sequence'],
            parent_block_id=data['parent_block_id'],
            started_at=date.fromisoformat(data['started_at']) if data.get('started_at') else date.today(),
            ended_at=date.fromisoformat(data['ended_at']) if data.get('ended_at') else None,
            peak_price=data.get('peak_price', 0.0),
            peak_volume=data.get('peak_volume', 0),
            status=BlockStatus(data.get('status', 'active'))
        )

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        status_symbol = "🔄" if self.is_active() else "✓"
        return (
            f"RedetectionEvent({status_symbol} #{self.sequence} "
            f"of {self.parent_block_id}, "
            f"{self.started_at} ~ {self.ended_at or 'active'})"
        )
