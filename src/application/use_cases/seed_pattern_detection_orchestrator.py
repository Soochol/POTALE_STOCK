"""
Seed Pattern Detection Orchestrator

블록 탐지와 패턴 관리를 조율하는 최상위 Use Case
"""
from datetime import date
from typing import List, Optional

from loguru import logger

from src.application.services.seed_pattern_tree_manager import SeedPatternTreeManager
from src.application.services.redetection_detector import RedetectionDetector
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.block_graph import BlockGraph
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.patterns import SeedPatternTree
from src.domain.repositories.seed_pattern_repository import SeedPatternRepository


class SeedPatternDetectionOrchestrator:
    """
    시드 패턴 탐지 오케스트레이터

    책임:
    1. DynamicBlockDetector와 SeedPatternTreeManager 조율
    2. 블록 탐지 → 패턴 관리 → DB 저장 전체 흐름 제어
    3. 여러 독립적인 시드 패턴 동시 관리

    Architecture:
        User Request
            ↓
        Orchestrator (이 클래스)
            ├→ DynamicBlockDetector (블록 탐지)
            ├→ SeedPatternTreeManager (패턴 관리)
            └→ SeedPatternRepository (DB 저장)

    Example:
        >>> orchestrator = SeedPatternDetectionOrchestrator(
        ...     block_graph=graph,
        ...     expression_engine=engine,
        ...     seed_pattern_repository=repo
        ... )
        >>> patterns = orchestrator.detect_patterns(
        ...     ticker="025980",
        ...     stocks=stocks
        ... )
    """

    def __init__(
        self,
        block_graph: BlockGraph,
        expression_engine: ExpressionEngine,
        seed_pattern_repository: Optional[SeedPatternRepository] = None
    ):
        """
        초기화

        Args:
            block_graph: 블록 그래프 정의
            expression_engine: 표현식 엔진
            seed_pattern_repository: 시드 패턴 저장소 (선택사항)
        """
        self.block_detector = DynamicBlockDetector(block_graph, expression_engine)
        self.pattern_manager = SeedPatternTreeManager()
        self.redetection_detector = RedetectionDetector(expression_engine)  # NEW
        self.seed_pattern_repository = seed_pattern_repository
        self.yaml_config_path = ""  # 외부에서 설정

    def detect_patterns(
        self,
        ticker: str,
        stocks: List[Stock],
        condition_name: str = "seed",
        save_to_db: bool = True,
        auto_archive: bool = True
    ) -> List[SeedPatternTree]:
        """
        시드 패턴 탐지 (전체 흐름)

        주요 개선사항:
        - 여러 시드 패턴 동시 관리 (덮어씌움 방지)
        - pattern_id 자동 생성
        - 패턴 완료 자동 감지
        - DB 자동 저장

        Args:
            ticker: 종목 코드
            stocks: 주가 데이터
            condition_name: 조건 이름
            save_to_db: DB 저장 여부
            auto_archive: 완료된 패턴 자동 보관 여부

        Returns:
            탐지된 모든 패턴 리스트 (active + completed)

        Example:
            >>> patterns = orchestrator.detect_patterns("025980", stocks)
            >>> len(patterns)
            5
            >>> patterns[0].pattern_id
            PatternId('SEED_025980_20180307_001')
        """
        logger.info(
            f"Starting seed pattern detection for {ticker}",
            extra={
                'ticker': ticker,
                'num_candles': len(stocks),
                'period': f"{stocks[0].date} ~ {stocks[-1].date}" if stocks else "empty"
            }
        )

        # Forward fill 전처리
        from src.infrastructure.utils.stock_data_utils import forward_fill_prices
        stocks = forward_fill_prices(stocks)

        # 기존 DynamicBlockDetector를 사용하여 블록 탐지
        # NOTE: 현재는 기존 방식을 사용하며, 반환된 블록들을 후처리로 패턴에 재할당
        # TODO: 향후 DynamicBlockDetector를 리팩토링하여 스트리밍 방식으로 개선
        detected_blocks = self.block_detector.detect_blocks(
            ticker=ticker,
            stocks=stocks,
            condition_name=condition_name
        )

        logger.info(
            f"Block detection completed",
            extra={
                'ticker': ticker,
                'num_blocks': len(detected_blocks)
            }
        )

        # 탐지된 블록들을 패턴으로 그룹화
        self._organize_blocks_into_patterns(ticker, detected_blocks)

        # 재탐지 탐지 (NEW - 2025-10-25)
        self._detect_redetections_for_patterns(ticker, stocks)

        # 완료된 패턴 처리
        completed_patterns = self.pattern_manager.check_and_complete_patterns()

        # DB 저장
        if save_to_db and self.seed_pattern_repository:
            for pattern in completed_patterns:
                self._save_pattern_to_db(pattern, auto_archive)

        # 최종 통계
        stats = self.pattern_manager.get_statistics()
        logger.info(
            "Pattern detection completed",
            extra={
                'ticker': ticker,
                **stats
            }
        )

        return self.pattern_manager.get_all_patterns()

    def _organize_blocks_into_patterns(
        self,
        ticker: str,
        blocks: List
    ) -> None:
        """
        탐지된 블록들을 패턴으로 구조화

        로직:
        1. 블록을 시작 날짜순으로 정렬
        2. Block1이 나타나면 새 패턴 시작
        3. 다른 블록들은 가장 최근 활성 패턴에 추가

        Args:
            ticker: 종목 코드
            blocks: 탐지된 블록 리스트

        Note:
            현재는 단순한 시간 기반 그룹화를 사용합니다.
            향후 parent_blocks 정보를 활용하여 더 정확한 그룹화 가능.
        """
        if not blocks:
            return

        # 시작 날짜순 정렬
        sorted_blocks = sorted(blocks, key=lambda b: b.started_at or date.min)

        # DEBUG: 블록 분포 확인
        block1_count = sum(1 for b in sorted_blocks if b.block_id == 'block1')
        logger.debug(
            f"Organizing {len(sorted_blocks)} blocks into patterns",
            extra={
                'ticker': ticker,
                'total_blocks': len(sorted_blocks),
                'block1_count': block1_count,
                'block_distribution': {
                    bid: sum(1 for b in sorted_blocks if b.block_id == bid)
                    for bid in set(b.block_id for b in sorted_blocks)
                }
            }
        )

        for block in sorted_blocks:
            if block.block_id == 'block1':
                # 새 패턴 시작
                pattern = self.pattern_manager.create_new_pattern(
                    ticker=ticker,
                    root_block=block,
                    detection_date=block.started_at or date.today()
                )
                logger.debug(
                    f"Created new pattern: {pattern.pattern_id}",
                    extra={
                        'pattern_id': str(pattern.pattern_id),
                        'block1_date': str(block.started_at)
                    }
                )
            else:
                # 기존 패턴에 추가
                pattern = self.pattern_manager.find_active_pattern_for_block(block)

                if pattern:
                    try:
                        self.pattern_manager.add_block_to_pattern(pattern, block)
                        logger.debug(
                            f"Added {block.block_id} to pattern {pattern.pattern_id}",
                            extra={
                                'pattern_id': str(pattern.pattern_id),
                                'block_id': block.block_id,
                                'block_date': str(block.started_at)
                            }
                        )
                    except ValueError as e:
                        logger.warning(
                            f"Failed to add block to pattern: {e}",
                            extra={
                                'block_id': block.block_id,
                                'ticker': ticker,
                                'date': str(block.started_at) if block.started_at else None
                            }
                        )

    def _detect_redetections_for_patterns(
        self,
        ticker: str,
        stocks: List[Stock]
    ) -> None:
        """
        모든 패턴의 모든 블록에 대해 재탐지 탐지 (NEW - 2025-10-25)

        프로세스:
        1. 모든 패턴 순회
        2. 각 패턴의 각 블록 순회
        3. 재탐지 지원 블록만 처리
        4. 해당 블록 종료 이후 캔들들에 대해 재탐지 탐지

        Args:
            ticker: 종목 코드
            stocks: 전체 주가 데이터

        Note:
            재탐지는 Seed Block이 completed 상태여야 시작 가능.
            한 블록당 한 번에 1개 재탐지만 active 가능.
        """
        all_patterns = self.pattern_manager.get_all_patterns()

        for pattern in all_patterns:
            for block_id, block in pattern.blocks.items():
                # 재진입 가능 여부 확인
                block_node = self.block_detector.block_graph.get_node(block_id)
                if not block_node or not block_node.has_reentry():
                    continue  # 재진입 설정 없음

                if not block.is_completed():
                    continue  # 아직 완료 안된 블록은 재탐지 불가

                # 해당 블록 종료 이후 캔들들 순회
                for stock in stocks:
                    if not block.ended_at or stock.date <= block.ended_at:
                        continue  # 블록 종료 전 캔들은 스킵

                    # 평가 컨텍스트 구성
                    context = self._build_redetection_context(
                        ticker=ticker,
                        current=stock,
                        all_stocks=stocks,
                        pattern=pattern
                    )

                    # 재탐지 탐지
                    self.redetection_detector.detect_redetections(
                        block=block,
                        block_node=block_node,
                        current=stock,
                        context=context
                    )

        # 재탐지 통계 로깅
        total_redetections = sum(
            block.get_redetection_count()
            for pattern in all_patterns
            for block in pattern.blocks.values()
        )

        if total_redetections > 0:
            logger.info(
                f"Redetection summary",
                extra={
                    'ticker': ticker,
                    'total_redetections': total_redetections,
                    'patterns_count': len(all_patterns)
                }
            )

    def _build_redetection_context(
        self,
        ticker: str,
        current: Stock,
        all_stocks: List[Stock],
        pattern: SeedPatternTree
    ) -> dict:
        """
        재탐지 평가를 위한 컨텍스트 구성

        Args:
            ticker: 종목 코드
            current: 현재 캔들
            all_stocks: 전체 주가 데이터
            pattern: 현재 패턴

        Returns:
            평가 컨텍스트 딕셔너리
        """
        # 이전 캔들 찾기
        current_idx = next(
            (i for i, s in enumerate(all_stocks) if s.date == current.date),
            None
        )
        prev = all_stocks[current_idx - 1] if current_idx and current_idx > 0 else None

        # 기본 컨텍스트
        context = {
            'ticker': ticker,
            'current': current,
            'prev': prev,
            'all_stocks': all_stocks,
        }

        # 패턴의 각 블록을 컨텍스트에 추가 (block1, block2, ...)
        for block_id, block in pattern.blocks.items():
            context[block_id] = block

        return context

    def _save_pattern_to_db(
        self,
        pattern: SeedPatternTree,
        auto_archive: bool = True
    ) -> None:
        """
        패턴을 DB에 저장

        Args:
            pattern: 저장할 패턴
            auto_archive: 저장 후 자동 보관 여부

        Example:
            >>> orchestrator._save_pattern_to_db(pattern)
        """
        try:
            seed_pattern = pattern.to_seed_pattern(self.yaml_config_path)

            saved = self.seed_pattern_repository.save(seed_pattern)

            logger.info(
                f"Saved pattern to DB: {pattern.pattern_id}",
                extra={
                    'pattern_id': str(pattern.pattern_id),
                    'db_id': saved.id
                }
            )

            # 저장 후 archive 처리
            if auto_archive:
                pattern.archive()

        except Exception as e:
            logger.error(
                f"Failed to save pattern {pattern.pattern_id}",
                extra={
                    'pattern_id': str(pattern.pattern_id),
                    'error': str(e)
                },
                exc_info=True
            )

    def get_all_patterns(self) -> List[SeedPatternTree]:
        """모든 패턴 조회"""
        return self.pattern_manager.get_all_patterns()

    def get_statistics(self) -> dict:
        """통계 정보 조회"""
        return self.pattern_manager.get_statistics()

    def set_yaml_config_path(self, path: str) -> None:
        """YAML 설정 파일 경로 설정"""
        self.yaml_config_path = path
