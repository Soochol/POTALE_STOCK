"""
DynamicBlockDetection - 동적 블록 감지 엔티티

YAML 정의를 기반으로 동적으로 블록을 감지하고 관리하는 범용 엔티티.
기존의 Block1Detection, Block2Detection 등을 대체하는 통합 엔티티.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Dict, Any, List
from enum import Enum


class BlockStatus(Enum):
    """블록 상태"""
    ACTIVE = "active"  # 진행 중
    COMPLETED = "completed"  # 정상 완료
    FAILED = "failed"  # 조건 실패로 종료


@dataclass
class DynamicBlockDetection:
    """
    동적 블록 감지 엔티티

    YAML에서 정의한 블록을 런타임에 감지하고 관리.
    블록 타입(1, 2, 3, ..., N)에 관계없이 동일한 구조 사용.

    Attributes:
        id: DB 레코드 ID (None이면 아직 저장되지 않음)
        block_id: 블록 정의 ID (예: "block1", "block2a", "block3")
        block_type: 블록 타입 번호 (1, 2, 3, 4, ...)
        ticker: 종목 코드
        pattern_id: 패턴 ID (이 블록이 속한 패턴)
        condition_name: 조건 이름 ("seed" 또는 "redetection")

        started_at: 블록 시작 날짜
        ended_at: 블록 종료 날짜 (None이면 진행 중)
        status: 블록 상태 (active, completed, failed)

        peak_price: 블록 내 최고가
        peak_volume: 블록 내 최대 거래량
        peak_date: 최고가/최대거래량 발생 날짜

        parent_blocks: 부모 블록 ID 리스트 (다중 부모 지원)
        metadata: 추가 메타데이터 (블록별 커스텀 데이터)
    """

    # 식별 정보
    block_id: str
    block_type: int
    ticker: str
    condition_name: str

    # 패턴 연결
    pattern_id: Optional[int] = None

    # 시간 정보
    started_at: Optional[date] = None
    ended_at: Optional[date] = None
    status: BlockStatus = BlockStatus.ACTIVE

    # 가격/거래량 정보
    peak_price: Optional[float] = None
    peak_volume: Optional[int] = None
    peak_date: Optional[date] = None

    # 관계 정보
    parent_blocks: List[int] = field(default_factory=list)  # 부모 블록 DB ID 리스트

    # 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    # DB ID (저장 후 할당)
    id: Optional[int] = None

    def __post_init__(self):
        """엔티티 검증"""
        if not self.block_id:
            raise ValueError("block_id는 필수입니다")

        if self.block_type < 1:
            raise ValueError(f"block_type은 1 이상이어야 합니다: {self.block_type}")

        if not self.ticker:
            raise ValueError("ticker는 필수입니다")

        if not self.condition_name:
            raise ValueError("condition_name은 필수입니다")

    def start(self, start_date: date) -> None:
        """
        블록 시작

        Args:
            start_date: 시작 날짜
        """
        if self.started_at is not None:
            raise ValueError(f"블록이 이미 시작되었습니다: {self.started_at}")

        self.started_at = start_date
        self.status = BlockStatus.ACTIVE

    def update_peak(self, current_date: date, price: float, volume: int) -> None:
        """
        최고가/최대거래량 갱신

        Args:
            current_date: 현재 날짜
            price: 현재 가격
            volume: 현재 거래량
        """
        # 최고가 갱신
        if self.peak_price is None or price > self.peak_price:
            self.peak_price = price
            self.peak_date = current_date

        # 최대 거래량 갱신
        if self.peak_volume is None or volume > self.peak_volume:
            self.peak_volume = volume

    def complete(self, end_date: date) -> None:
        """
        블록 정상 완료

        Args:
            end_date: 종료 날짜
        """
        if self.started_at is None:
            raise ValueError("블록이 아직 시작되지 않았습니다")

        if self.status != BlockStatus.ACTIVE:
            raise ValueError(f"진행 중인 블록만 완료할 수 있습니다. 현재 상태: {self.status}")

        self.ended_at = end_date
        self.status = BlockStatus.COMPLETED

    def fail(self, end_date: date) -> None:
        """
        블록 실패 (조건 이탈)

        Args:
            end_date: 종료 날짜
        """
        if self.started_at is None:
            raise ValueError("블록이 아직 시작되지 않았습니다")

        if self.status != BlockStatus.ACTIVE:
            raise ValueError(f"진행 중인 블록만 실패 처리할 수 있습니다. 현재 상태: {self.status}")

        self.ended_at = end_date
        self.status = BlockStatus.FAILED

    def is_active(self) -> bool:
        """블록이 진행 중인지 확인"""
        return self.status == BlockStatus.ACTIVE

    def is_completed(self) -> bool:
        """블록이 정상 완료되었는지 확인"""
        return self.status == BlockStatus.COMPLETED

    def is_failed(self) -> bool:
        """블록이 실패했는지 확인"""
        return self.status == BlockStatus.FAILED

    def add_parent_block(self, parent_block_id: int) -> None:
        """
        부모 블록 추가

        Args:
            parent_block_id: 부모 블록 DB ID
        """
        if parent_block_id not in self.parent_blocks:
            self.parent_blocks.append(parent_block_id)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        메타데이터 설정

        Args:
            key: 키
            value: 값
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        메타데이터 조회

        Args:
            key: 키
            default: 기본값

        Returns:
            메타데이터 값 또는 기본값
        """
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (DB 저장용)"""
        return {
            'id': self.id,
            'block_id': self.block_id,
            'block_type': self.block_type,
            'ticker': self.ticker,
            'pattern_id': self.pattern_id,
            'condition_name': self.condition_name,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'status': self.status.value,
            'peak_price': self.peak_price,
            'peak_volume': self.peak_volume,
            'peak_date': self.peak_date,
            'parent_blocks': self.parent_blocks,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DynamicBlockDetection':
        """딕셔너리에서 생성 (DB 조회용)"""
        status = BlockStatus(data['status']) if isinstance(data['status'], str) else data['status']

        return cls(
            id=data.get('id'),
            block_id=data['block_id'],
            block_type=data['block_type'],
            ticker=data['ticker'],
            pattern_id=data.get('pattern_id'),
            condition_name=data['condition_name'],
            started_at=data.get('started_at'),
            ended_at=data.get('ended_at'),
            status=status,
            peak_price=data.get('peak_price'),
            peak_volume=data.get('peak_volume'),
            peak_date=data.get('peak_date'),
            parent_blocks=data.get('parent_blocks', []),
            metadata=data.get('metadata', {}),
        )

    def __repr__(self) -> str:
        return (
            f"DynamicBlockDetection(id={self.id}, block_id='{self.block_id}', "
            f"type={self.block_type}, ticker='{self.ticker}', "
            f"started={self.started_at}, status={self.status.value})"
        )
