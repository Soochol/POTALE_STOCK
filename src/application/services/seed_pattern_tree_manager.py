"""
Seed Pattern Tree Manager

시드 패턴 트리의 생명주기를 관리하는 서비스
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from loguru import logger

from src.domain.entities.patterns import PatternId, PatternStatus, SeedPatternTree
from src.domain.entities.detections import DynamicBlockDetection


class SeedPatternTreeManager:
    """
    시드 패턴 트리 생명주기 관리자

    책임:
    1. 여러 시드 패턴 동시 관리 (무제한)
    2. 새 Block1 탐지 시 → 새 패턴 생성
    3. 자식 블록 추가 → 부모 패턴 찾기
    4. 패턴 완료 감지 및 처리
    5. pattern_id 자동 생성

    Features:
    - 무제한 동시 패턴 관리
    - 자동 pattern_id 생성 (ticker + date + sequence)
    - 패턴 완료 자동 감지
    - 메모리 기반 관리 (처리 속도 우선)

    Example:
        >>> manager = SeedPatternTreeManager()
        >>> pattern = manager.create_new_pattern("025980", block1, date(2018, 3, 7))
        >>> manager.add_block_to_pattern(pattern, block2)
        >>> completed = manager.check_and_complete_patterns()
    """

    def __init__(self):
        """초기화"""
        self.active_patterns: List[SeedPatternTree] = []
        self.completed_patterns: List[SeedPatternTree] = []
        self.pattern_sequence: Dict[str, int] = {}  # ticker → sequence

    def create_new_pattern(
        self,
        ticker: str,
        root_block: DynamicBlockDetection,
        detection_date: date
    ) -> SeedPatternTree:
        """
        새 시드 패턴 생성

        Args:
            ticker: 종목 코드
            root_block: Block1 (root)
            detection_date: 탐지 날짜

        Returns:
            새로 생성된 SeedPatternTree

        Raises:
            ValueError: root_block이 block1이 아닌 경우

        Example:
            >>> pattern = manager.create_new_pattern("025980", block1, date(2018, 3, 7))
            >>> pattern.pattern_id
            PatternId('SEED_025980_20180307_001')
        """
        # pattern_id 자동 생성
        sequence = self.pattern_sequence.get(ticker, 0) + 1
        self.pattern_sequence[ticker] = sequence

        pattern_id = PatternId.generate(ticker, detection_date, sequence)

        # 패턴 생성
        pattern = SeedPatternTree(
            pattern_id=pattern_id,
            ticker=ticker,
            root_block=root_block,
            blocks={},  # __post_init__에서 root_block 추가됨
            status=PatternStatus.ACTIVE,
            created_at=datetime.now()
        )

        self.active_patterns.append(pattern)

        logger.info(
            f"Created new seed pattern: {pattern_id}",
            extra={
                'pattern_id': str(pattern_id),
                'ticker': ticker,
                'root_block_date': str(root_block.started_at) if root_block.started_at else None,
                'sequence': sequence
            }
        )

        return pattern

    def find_active_pattern_for_block(
        self,
        block: DynamicBlockDetection
    ) -> Optional[SeedPatternTree]:
        """
        블록이 추가될 활성 패턴 찾기

        로직:
        1. block_id가 'block1'이면 → None (새 패턴 생성 필요)
        2. 시간 기반: 현재 블록보다 먼저 시작된 활성 패턴 중 가장 최근 것

        Args:
            block: 추가할 블록

        Returns:
            찾은 패턴, 없으면 None

        Example:
            >>> pattern = manager.find_active_pattern_for_block(block2)
        """
        # Block1은 항상 새 패턴
        if block.block_id == 'block1':
            return None

        # Virtual Block 처리: started_at이 None이므로 시간 기반 매칭 불가
        # 대신 ticker만 매칭하여 가장 최근 활성 패턴에 할당
        if block.is_virtual:
            candidate_patterns = [
                p for p in self.active_patterns
                if p.ticker == block.ticker
            ]
        else:
            # Real Block: 시간 기반 현재 블록보다 먼저 시작된 활성 패턴 중 가장 최근 것
            candidate_patterns = [
                p for p in self.active_patterns
                if p.ticker == block.ticker
                and p.root_block.started_at
                and block.started_at
                and p.root_block.started_at <= block.started_at
            ]

        if not candidate_patterns:
            logger.warning(
                f"No active pattern found for {block.block_id}",
                extra={
                    'block_id': block.block_id,
                    'block_type': block.block_type,
                    'ticker': block.ticker,
                    'date': str(block.started_at) if block.started_at else None,
                    'active_patterns_count': len(self.active_patterns)
                }
            )
            return None

        # 가장 최근에 시작된 패턴
        pattern = max(candidate_patterns, key=lambda p: p.root_block.started_at)

        logger.debug(
            f"Found parent pattern {pattern.pattern_id} for {block.block_id}",
            extra={
                'pattern_id': str(pattern.pattern_id),
                'block_id': block.block_id,
                'block_date': str(block.started_at) if block.started_at else None
            }
        )

        return pattern

    def add_block_to_pattern(
        self,
        pattern: SeedPatternTree,
        block: DynamicBlockDetection
    ) -> None:
        """
        패턴에 블록 추가

        Args:
            pattern: 대상 패턴
            block: 추가할 블록

        Raises:
            ValueError: 패턴에 블록 추가 불가능한 경우

        Example:
            >>> manager.add_block_to_pattern(pattern, block2)
        """
        pattern.add_block(block)

        logger.info(
            f"Added {block.block_id} to pattern {pattern.pattern_id}",
            extra={
                'pattern_id': str(pattern.pattern_id),
                'block_id': block.block_id,
                'block_date': str(block.started_at) if block.started_at else None,
                'pattern_block_count': pattern.get_block_count()
            }
        )

    def check_and_complete_patterns(self) -> List[SeedPatternTree]:
        """
        완료 가능한 패턴들 확인 및 완료 처리

        Returns:
            완료된 패턴 리스트

        Example:
            >>> completed = manager.check_and_complete_patterns()
            >>> len(completed)
            2
        """
        completed = []

        for pattern in self.active_patterns[:]:  # 복사본 순회 (원본 수정 안전)
            if pattern.check_completion():
                try:
                    pattern.complete()

                    # active → completed로 이동
                    self.active_patterns.remove(pattern)
                    self.completed_patterns.append(pattern)

                    completed.append(pattern)

                    duration = (pattern.completed_at - pattern.created_at).total_seconds()

                    logger.info(
                        f"Pattern completed: {pattern.pattern_id}",
                        extra={
                            'pattern_id': str(pattern.pattern_id),
                            'num_blocks': len(pattern.blocks),
                            'duration_seconds': duration
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to complete pattern {pattern.pattern_id}",
                        extra={
                            'pattern_id': str(pattern.pattern_id),
                            'error': str(e)
                        },
                        exc_info=True
                    )

        return completed

    def get_all_patterns(self) -> List[SeedPatternTree]:
        """
        모든 패턴 반환 (active + completed)

        Returns:
            모든 패턴 리스트

        Example:
            >>> all_patterns = manager.get_all_patterns()
        """
        return self.active_patterns + self.completed_patterns

    def get_active_patterns(self) -> List[SeedPatternTree]:
        """활성 패턴만 반환"""
        return self.active_patterns.copy()

    def get_completed_patterns(self) -> List[SeedPatternTree]:
        """완료된 패턴만 반환"""
        return self.completed_patterns.copy()

    def get_patterns_by_ticker(self, ticker: str) -> List[SeedPatternTree]:
        """
        특정 종목의 패턴들 반환

        Args:
            ticker: 종목 코드

        Returns:
            해당 종목의 패턴 리스트
        """
        return [p for p in self.get_all_patterns() if p.ticker == ticker]

    def get_statistics(self) -> Dict[str, Any]:
        """
        통계 정보

        Returns:
            통계 딕셔너리

        Example:
            >>> stats = manager.get_statistics()
            >>> stats['total_patterns']
            10
        """
        return {
            'active_patterns': len(self.active_patterns),
            'completed_patterns': len(self.completed_patterns),
            'total_patterns': len(self.active_patterns) + len(self.completed_patterns),
            'patterns_by_ticker': self._count_by_ticker()
        }

    def _count_by_ticker(self) -> Dict[str, Dict[str, int]]:
        """
        종목별 패턴 개수

        Returns:
            {ticker: {'active': N, 'completed': M}}
        """
        result: Dict[str, Dict[str, int]] = {}
        all_patterns = self.get_all_patterns()

        for pattern in all_patterns:
            if pattern.ticker not in result:
                result[pattern.ticker] = {'active': 0, 'completed': 0}

            if pattern.status == PatternStatus.ACTIVE:
                result[pattern.ticker]['active'] += 1
            elif pattern.status == PatternStatus.COMPLETED:
                result[pattern.ticker]['completed'] += 1

        return result

    def clear_completed_patterns(self) -> int:
        """
        완료된 패턴 메모리에서 제거 (메모리 관리)

        Returns:
            제거된 패턴 개수

        Example:
            >>> count = manager.clear_completed_patterns()
            >>> print(f"Cleared {count} patterns")
        """
        count = len(self.completed_patterns)
        self.completed_patterns.clear()

        if count > 0:
            logger.info(
                f"Cleared {count} completed patterns from memory",
                extra={'cleared_count': count}
            )

        return count

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"SeedPatternTreeManager("
            f"active={len(self.active_patterns)}, "
            f"completed={len(self.completed_patterns)})"
        )
