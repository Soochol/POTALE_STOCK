"""
Seed Pattern Tree - Aggregate Root

하나의 독립적인 시드 패턴 트리를 나타내는 Aggregate Root
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Optional, List, Any

from .pattern_id import PatternId
from .pattern_status import PatternStatus
from .seed_pattern import SeedPattern, BlockFeatures


@dataclass
class SeedPatternTree:
    """
    시드 패턴 트리 (Aggregate Root)

    하나의 독립적인 시드 패턴을 나타내는 tree 구조.
    Block1(root) → Block2 → Block3 → ... → BlockN

    이 클래스는 Aggregate Root로서 다음을 보장합니다:
    1. 불변 조건 (Invariants) 유지
    2. 상태 전이 규칙 강제
    3. 비즈니스 로직 캡슐화

    Invariants (불변 조건):
        1. 항상 Block1(root)을 가져야 함
        2. 상태 전이는 FSM 규칙을 따름
        3. COMPLETED 상태에서는 블록 추가 불가
        4. 각 block_id는 tree 내에서 최대 1개만 존재

    Attributes:
        pattern_id: 패턴 고유 ID
        ticker: 종목 코드
        root_block: Block1 (필수, tree의 root)
        blocks: block_id → DynamicBlockDetection 매핑
        status: 패턴 상태 (FSM)
        created_at: 패턴 생성 시각
        completed_at: 패턴 완료 시각 (COMPLETED 상태)

    Example:
        >>> root = DynamicBlockDetection(block_id='block1', ...)
        >>> pattern_id = PatternId.generate("025980", date(2018, 3, 7), 1)
        >>> tree = SeedPatternTree(
        ...     pattern_id=pattern_id,
        ...     ticker="025980",
        ...     root_block=root,
        ...     blocks={},
        ...     status=PatternStatus.ACTIVE,
        ...     created_at=datetime.now()
        ... )
        >>> tree.add_block(block2)
        >>> tree.check_completion()
    """

    # Identity
    pattern_id: PatternId
    ticker: str

    # Tree structure
    root_block: 'DynamicBlockDetection'  # Forward reference
    blocks: Dict[str, 'DynamicBlockDetection'] = field(default_factory=dict)

    # State
    status: PatternStatus = PatternStatus.ACTIVE

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """
        불변 조건 검증

        Raises:
            ValueError: 불변 조건 위반 시
        """
        # Invariant 1: root_block은 반드시 block1이어야 함
        if self.root_block.block_id != 'block1':
            raise ValueError(
                f"Root block must be 'block1', got '{self.root_block.block_id}'"
            )

        # root_block을 blocks에도 추가 (중복 방지)
        if 'block1' not in self.blocks:
            self.blocks['block1'] = self.root_block

    def add_block(self, block: 'DynamicBlockDetection') -> None:
        """
        블록 추가 (트리에 자식 추가)

        Args:
            block: 추가할 블록

        Raises:
            ValueError: 상태가 ACTIVE가 아니거나 이미 존재하는 block_id

        Example:
            >>> tree.add_block(block2)
            >>> tree.blocks
            {'block1': <Block1>, 'block2': <Block2>}
        """
        # Invariant 2: ACTIVE 상태에서만 블록 추가 가능
        if not self.status.can_add_block():
            raise ValueError(
                f"Cannot add block in {self.status} state. "
                f"Blocks can only be added in ACTIVE state."
            )

        # Invariant 4: 각 block_id는 tree 내에서 유일해야 함
        if block.block_id in self.blocks:
            raise ValueError(
                f"Block '{block.block_id}' already exists in pattern {self.pattern_id}"
            )

        self.blocks[block.block_id] = block

    def get_block(self, block_id: str) -> Optional['DynamicBlockDetection']:
        """
        블록 조회

        Args:
            block_id: 블록 ID (예: "block1")

        Returns:
            DynamicBlockDetection 또는 None

        Example:
            >>> block1 = tree.get_block('block1')
        """
        return self.blocks.get(block_id)

    def has_block(self, block_id: str) -> bool:
        """
        블록 존재 여부 확인

        Args:
            block_id: 블록 ID

        Returns:
            존재하면 True

        Example:
            >>> tree.has_block('block2')
            True
        """
        return block_id in self.blocks

    def get_block_count(self) -> int:
        """블록 개수"""
        return len(self.blocks)

    def check_completion(self) -> bool:
        """
        완료 조건 확인

        완료 조건: 모든 블록이 'completed' 상태

        Returns:
            모든 블록이 completed 상태면 True

        Example:
            >>> tree.check_completion()
            False  # 일부 블록이 아직 active
        """
        # ACTIVE 상태에서만 완료 가능
        if not self.status.can_complete():
            return False

        # 모든 블록이 completed 상태인지 확인
        return all(block.is_completed() for block in self.blocks.values())

    def complete(self) -> None:
        """
        패턴 완료 처리

        Raises:
            ValueError: 완료 조건을 만족하지 않음

        Example:
            >>> tree.complete()
            >>> tree.status
            PatternStatus.COMPLETED
        """
        if not self.check_completion():
            active_blocks = [
                bid for bid, b in self.blocks.items()
                if not b.is_completed()
            ]
            raise ValueError(
                f"Cannot complete pattern {self.pattern_id}: "
                f"Following blocks are not completed: {active_blocks}"
            )

        # Invariant 2: 상태 전이 검증
        if not self.status.validate_transition(PatternStatus.COMPLETED):
            raise ValueError(
                f"Invalid state transition: {self.status} → COMPLETED"
            )

        self.status = PatternStatus.COMPLETED
        self.completed_at = datetime.now()

    def archive(self) -> None:
        """
        패턴 보관 처리 (DB 저장 후 메모리 해제 예정)

        Raises:
            ValueError: COMPLETED 상태가 아님

        Example:
            >>> tree.archive()
            >>> tree.status
            PatternStatus.ARCHIVED
        """
        if not self.status.can_archive():
            raise ValueError(
                f"Cannot archive from {self.status} state. "
                f"Pattern must be COMPLETED first."
            )

        # Invariant 2: 상태 전이 검증
        if not self.status.validate_transition(PatternStatus.ARCHIVED):
            raise ValueError(
                f"Invalid state transition: {self.status} → ARCHIVED"
            )

        self.status = PatternStatus.ARCHIVED

    def to_seed_pattern(self, yaml_config_path: str = "") -> SeedPattern:
        """
        SeedPattern 엔티티로 변환 (DB 저장용)

        Args:
            yaml_config_path: YAML 설정 파일 경로

        Returns:
            SeedPattern: DB 저장용 엔티티

        Example:
            >>> seed_pattern = tree.to_seed_pattern("presets/examples/test1_alt.yaml")
            >>> seed_pattern.pattern_name
            'SEED_025980_20180307_001'
        """
        block_features = []
        prices = []
        volumes = []

        # 블록 정렬 (block_type 순서대로)
        sorted_blocks = sorted(self.blocks.values(), key=lambda b: b.block_type)

        for block in sorted_blocks:
            # Duration 계산
            duration = 0
            if block.started_at and block.ended_at:
                duration = (block.ended_at - block.started_at).days + 1

            # BlockFeatures 생성
            feature = BlockFeatures(
                block_id=block.block_id,
                block_type=block.block_type,
                started_at=block.started_at,
                ended_at=block.ended_at,
                duration_candles=duration,
                low_price=block.peak_price or 0.0,
                high_price=block.peak_price or 0.0,
                peak_price=block.peak_price or 0.0,
                peak_date=block.peak_date or block.started_at,
                min_volume=block.peak_volume or 0,
                max_volume=block.peak_volume or 0,
                peak_volume=block.peak_volume or 0,
                avg_volume=block.peak_volume or 0
            )
            block_features.append(feature)

            # Shape 데이터 수집
            if block.peak_price:
                prices.append(block.peak_price)
            if block.peak_volume:
                volumes.append(float(block.peak_volume))

        # 정규화
        price_shape = SeedPattern.normalize_sequence(prices) if prices else []
        volume_shape = SeedPattern.normalize_sequence(volumes) if volumes else []

        # SeedPattern 생성
        return SeedPattern(
            pattern_name=str(self.pattern_id),
            ticker=self.ticker,
            yaml_config_path=yaml_config_path,
            detection_date=self.root_block.started_at or date.today(),
            block_features=block_features,
            price_shape=price_shape,
            volume_shape=volume_shape
        )

    def get_metadata(self) -> Dict[str, Any]:
        """
        패턴 메타데이터 반환

        Returns:
            메타데이터 딕셔너리

        Example:
            >>> metadata = tree.get_metadata()
            >>> metadata['num_blocks']
            3
        """
        duration_seconds = None
        if self.completed_at:
            duration_seconds = (self.completed_at - self.created_at).total_seconds()

        return {
            'pattern_id': str(self.pattern_id),
            'ticker': self.ticker,
            'num_blocks': len(self.blocks),
            'block_ids': list(self.blocks.keys()),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': duration_seconds,
            'root_block_date': self.root_block.started_at.isoformat() if self.root_block.started_at else None
        }

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"SeedPatternTree("
            f"pattern_id={self.pattern_id}, "
            f"ticker='{self.ticker}', "
            f"blocks={len(self.blocks)}, "
            f"status={self.status})"
        )

    def __str__(self) -> str:
        """사용자용 문자열 표현"""
        return f"Pattern {self.pattern_id} ({self.status}): {len(self.blocks)} blocks"


# Forward reference resolution을 위한 TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.domain.entities.detections import DynamicBlockDetection
