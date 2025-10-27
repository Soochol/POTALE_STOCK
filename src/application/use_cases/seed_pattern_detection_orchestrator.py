"""
Seed Pattern Detection Orchestrator

블록 탐지와 패턴 관리를 조율하는 최상위 Use Case
"""
from datetime import date
from typing import List, Optional, Dict

from loguru import logger

from src.application.services.seed_pattern_tree_manager import SeedPatternTreeManager
from src.application.services.redetection_detector import RedetectionDetector
from src.application.services.highlight_detector import HighlightDetector
from src.application.services.support_resistance_analyzer import SupportResistanceAnalyzer
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.application.use_cases.pattern_detection_state import PatternContext, PatternDetectionState
from src.domain.entities.block_graph import BlockGraph
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.patterns import SeedPatternTree, PatternId
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
        self.block_graph = block_graph
        self.expression_engine = expression_engine
        self.block_detector = DynamicBlockDetector(block_graph, expression_engine)
        self.pattern_manager = SeedPatternTreeManager()
        self.redetection_detector = RedetectionDetector(expression_engine)
        self.seed_pattern_repository = seed_pattern_repository
        self.yaml_config_path = ""  # 외부에서 설정

        # Shared Application Services (NEW - 2025-10-27 Phase 2)
        self.highlight_detector = HighlightDetector(expression_engine)
        self.support_resistance_analyzer = SupportResistanceAnalyzer(tolerance_pct=2.0)

        # Option D: 패턴 시퀀스 카운터 (ticker별)
        self.pattern_sequence_counter: Dict[str, int] = {}

    def detect_patterns(
        self,
        ticker: str,
        stocks: List[Stock],
        condition_name: str = "seed",
        save_to_db: bool = True,
        auto_archive: bool = True
    ) -> List[SeedPatternTree]:
        """
        시드 패턴 탐지 (Option D 리팩토링 버전)

        주요 개선사항:
        - 멀티패턴 동시 탐지 (패턴별 독립 평가)
        - 패턴 간 간섭 완전 차단
        - 데이터 1회 순회 (효율적)
        - pattern_id 자동 생성
        - 패턴 완료 자동 감지

        Args:
            ticker: 종목 코드
            stocks: 주가 데이터
            condition_name: 조건 이름 ("seed" 권장)
            save_to_db: DB 저장 여부
            auto_archive: 완료된 패턴 자동 보관 여부

        Returns:
            탐지된 모든 패턴 리스트 (active + completed)

        Example:
            >>> patterns = orchestrator.detect_patterns("025980", stocks)
            >>> len(patterns)
            26  # 26개 독립 패턴 (기존에는 1개만 탐지됨)
            >>> patterns[0].pattern_id
            PatternId('SEED_025980_20180307_001')

        Note:
            Option D 리팩토링으로 완전히 새로 작성된 메서드입니다.
            패턴별 독립 평가를 통해 멀티패턴 문제를 근본적으로 해결합니다.
        """
        logger.info(
            f"Starting seed pattern detection (Option D) for {ticker}",
            extra={
                'ticker': ticker,
                'num_candles': len(stocks),
                'period': f"{stocks[0].date} ~ {stocks[-1].date}" if stocks else "empty"
            }
        )

        # Forward fill 전처리
        from src.infrastructure.utils.stock_data_utils import forward_fill_prices
        stocks = forward_fill_prices(stocks)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 핵심: 패턴별 독립 탐지 (Single Pass)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        active_pattern_contexts: List[PatternContext] = []

        for i, current_stock in enumerate(stocks):
            # 이전 주가 찾기
            prev_stock = self._find_last_valid_day(stocks, i)

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 1. Block1 조건 체크 (패턴 무관)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if self._should_start_new_pattern(ticker, current_stock, prev_stock, stocks[:i+1]):
                new_pattern = self._create_pattern_context(ticker, current_stock, prev_stock, stocks[:i+1])
                active_pattern_contexts.append(new_pattern)

                logger.info(
                    f"Created new pattern: {new_pattern.pattern_id}",
                    extra={
                        'pattern_id': new_pattern.pattern_id,
                        'date': str(current_stock.date)
                    }
                )

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 2. 각 패턴마다 진행
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            for pattern_ctx in active_pattern_contexts:
                # 패턴별 컨텍스트 구축
                context = self._build_pattern_context(
                    pattern=pattern_ctx,
                    current=current_stock,
                    prev=prev_stock,
                    all_stocks=stocks[:i+1]
                )

                # 활성 블록 peak 갱신
                self._update_active_blocks(pattern_ctx, current_stock)

                # 다음 블록 진입 체크
                self._check_and_create_next_blocks(
                    pattern=pattern_ctx,
                    context=context,
                    condition_name=condition_name,
                    current_stock=current_stock,
                    prev_stock=prev_stock
                )

                # 종료 조건 체크
                self._check_and_complete_blocks(
                    pattern=pattern_ctx,
                    context=context,
                    condition_name=condition_name,
                    current_date=current_stock.date
                )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2.5. 데이터 순회 완료 후 남은 active 블록들 완료 처리
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        last_date = stocks[-1].date if stocks else date.today()
        auto_completed_count = 0

        for pattern_ctx in active_pattern_contexts:
            for block_id, block in pattern_ctx.blocks.items():
                if block.is_active():
                    block.complete(last_date)
                    auto_completed_count += 1
                    logger.debug(
                        f"Auto-completed remaining active block: {block_id}",
                        extra={
                            'pattern_id': pattern_ctx.pattern_id,
                            'block_id': block_id,
                            'end_date': str(last_date),
                            'reason': 'data_end'
                        }
                    )

        if auto_completed_count > 0:
            logger.info(
                f"Auto-completed {auto_completed_count} remaining active blocks",
                extra={
                    'ticker': ticker,
                    'last_date': str(last_date),
                    'auto_completed': auto_completed_count
                }
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. PatternContext → SeedPatternTree 변환
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self._convert_to_pattern_trees(ticker, active_pattern_contexts)

        logger.info(
            f"Pattern contexts created: {len(active_pattern_contexts)}",
            extra={
                'ticker': ticker,
                'total_patterns': len(active_pattern_contexts),
                'pattern_ids': [p.pattern_id for p in active_pattern_contexts]
            }
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3.5. 하이라이트 탐지 (NEW - 2025-10-27 Phase 2)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self._detect_highlights_for_patterns(ticker, stocks)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 재탐지 탐지
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self._detect_redetections_for_patterns(ticker, stocks)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 완료된 패턴 저장
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        completed_patterns = self.pattern_manager.check_and_complete_patterns()

        if save_to_db and self.seed_pattern_repository:
            for pattern in completed_patterns:
                self._save_pattern_to_db(pattern, auto_archive)

        # 최종 통계
        stats = self.pattern_manager.get_statistics()
        logger.info(
            "Pattern detection completed (Option D)",
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

        # 시작 날짜순 정렬 (Virtual Block System 개선)
        # CRITICAL FIX: Virtual blocks를 real blocks 뒤로 배치하여 패턴이 먼저 생성되도록 함
        # - Real blocks: (0, started_at, pattern_sequence)
        # - Virtual blocks: (1, date.max, pattern_sequence) → 가장 뒤로 배치
        # 이렇게 해야 Block1→Block2 순서로 패턴이 생성된 후 Virtual Block3가 추가됨
        sorted_blocks = sorted(
            blocks,
            key=lambda b: (
                1 if b.is_virtual else 0,  # Virtual blocks를 뒤로
                b.started_at or date.max,  # Virtual blocks는 date.max로
                b.pattern_sequence
            )
        )

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

                        # Virtual Block 전용 로깅 (중요!)
                        if block.is_virtual:
                            logger.info(
                                f"Added VIRTUAL {block.block_id} to pattern {pattern.pattern_id}",
                                extra={
                                    'pattern_id': str(pattern.pattern_id),
                                    'block_id': block.block_id,
                                    'is_virtual': True,
                                    'logical_level': block.logical_level,
                                    'yaml_type': block.yaml_type,
                                    'pattern_sequence': block.pattern_sequence
                                }
                            )
                        else:
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
            # 저장 전 archive 처리 (auto_archive=True인 경우)
            if auto_archive:
                pattern.archive()

            seed_pattern = pattern.to_seed_pattern(self.yaml_config_path)

            saved = self.seed_pattern_repository.save(seed_pattern)

            logger.info(
                f"Saved pattern to DB: {pattern.pattern_id}",
                extra={
                    'pattern_id': str(pattern.pattern_id),
                    'db_id': saved.id,
                    'status': seed_pattern.status.value
                }
            )

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Option D: 새로운 헬퍼 메서드들 (패턴별 독립 탐지용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _find_last_valid_day(
        self,
        stocks: List[Stock],
        current_index: int
    ) -> Optional[Stock]:
        """
        마지막 정상 거래일 찾기 (volume > 0)

        Args:
            stocks: 주가 데이터 리스트
            current_index: 현재 인덱스

        Returns:
            마지막 정상 거래일 주가, 없으면 None
        """
        for i in range(current_index - 1, -1, -1):
            if stocks[i].volume > 0:
                return stocks[i]
        return None

    def _should_start_new_pattern(
        self,
        ticker: str,
        current: Stock,
        prev: Optional[Stock],
        all_stocks: List[Stock]
    ) -> bool:
        """
        Block1 진입 조건 평가 (패턴 무관)

        Block1은 패턴 없이 독립적으로 평가합니다.

        Args:
            ticker: 종목 코드
            current: 현재 주가
            prev: 이전 주가
            all_stocks: 전체 주가 데이터

        Returns:
            Block1 조건 만족 여부
        """
        # Root node 가져오기
        if not self.block_graph.root_node_id:
            return False

        root_node = self.block_graph.get_node(self.block_graph.root_node_id)
        if not root_node:
            return False

        # 패턴 무관 기본 컨텍스트
        context = {
            'current': current,
            'prev': prev,
            'all_stocks': all_stocks
        }

        return self.block_detector.evaluate_entry_condition(
            node=root_node,
            context=context,
            condition_name="seed"
        )

    def _create_pattern_context(
        self,
        ticker: str,
        current_stock: Stock,
        prev_stock: Optional[Stock],
        all_stocks: List[Stock]
    ) -> PatternContext:
        """
        새 패턴 컨텍스트 생성 + Block1 추가

        Args:
            ticker: 종목 코드
            current_stock: 현재 주가
            prev_stock: 이전 주가
            all_stocks: 전체 주가 데이터

        Returns:
            새로 생성된 PatternContext
        """
        # pattern_id 생성
        sequence = self.pattern_sequence_counter.get(ticker, 0) + 1
        self.pattern_sequence_counter[ticker] = sequence
        pattern_id = PatternId.generate(ticker, current_stock.date, sequence)

        # Block1 생성
        block1 = DynamicBlockDetection(
            block_id='block1',
            block_type=1,
            ticker=ticker,
            pattern_id=str(pattern_id),
            condition_name='seed'
        )
        block1.start(current_stock.date)
        block1.update_peak(current_stock.date, current_stock.close, current_stock.volume)

        # 전일 종가 저장
        if prev_stock:
            block1.prev_close = prev_stock.close

        # spot1 자동 추가
        block1.add_spot(
            spot_date=current_stock.date,
            open_price=current_stock.open,
            close_price=current_stock.close,
            high_price=current_stock.high,
            low_price=current_stock.low,
            volume=current_stock.volume
        )

        # PatternContext 생성
        pattern_ctx = PatternContext(
            pattern_id=str(pattern_id),
            ticker=ticker,
            blocks={'block1': block1},
            block_graph=self.block_graph,
            created_at=current_stock.date,
            detection_state=PatternDetectionState()
        )

        return pattern_ctx

    def _build_pattern_context(
        self,
        pattern: PatternContext,
        current: Stock,
        prev: Optional[Stock],
        all_stocks: List[Stock]
    ) -> dict:
        """
        패턴별 평가 컨텍스트 구축

        핵심: pattern.blocks에서 block1, block2, ... 추출

        Args:
            pattern: 패턴 컨텍스트
            current: 현재 주가
            prev: 이전 주가
            all_stocks: 전체 주가 데이터

        Returns:
            평가 컨텍스트
        """
        context = {
            'current': current,
            'prev': prev,
            'all_stocks': all_stocks,
            'pattern_id': pattern.pattern_id,
            'active_blocks': pattern.blocks  # Spot 전략용
        }

        # 이 패턴의 블록들 추가
        for block_id, block in pattern.blocks.items():
            context[block_id] = block

        return context

    def _update_active_blocks(
        self,
        pattern: PatternContext,
        current_stock: Stock
    ) -> None:
        """
        활성 블록 peak 갱신

        Args:
            pattern: 패턴 컨텍스트
            current_stock: 현재 주가
        """
        for block in pattern.blocks.values():
            if block.is_active():
                block.update_peak(
                    current_stock.date,
                    current_stock.close,
                    current_stock.volume
                )

    def _check_and_create_next_blocks(
        self,
        pattern: PatternContext,
        context: dict,
        condition_name: str,
        current_stock: Stock,
        prev_stock: Optional[Stock]
    ) -> None:
        """
        다음 블록 진입 조건 체크 및 생성

        Args:
            pattern: 패턴 컨텍스트
            context: 평가 컨텍스트
            condition_name: 조건 이름
            current_stock: 현재 주가
            prev_stock: 이전 주가
        """
        next_nodes = pattern.get_next_target_nodes()

        for node in next_nodes:
            # 이미 존재하면 스킵
            if node.block_id in pattern.blocks and pattern.blocks[node.block_id].is_active():
                continue

            # 진입 조건 평가
            if self.block_detector.evaluate_entry_condition(node, context, condition_name):
                # Spot 체크
                spot_target = self.block_detector.evaluate_spot_strategy(node, context)

                if spot_target:
                    # spot 추가 로직
                    spot_target.add_spot(
                        spot_date=current_stock.date,
                        open_price=current_stock.open,
                        close_price=current_stock.close,
                        high_price=current_stock.high,
                        low_price=current_stock.low,
                        volume=current_stock.volume
                    )
                    logger.debug(
                        f"Added spot to {spot_target.block_id}",
                        extra={
                            'pattern_id': pattern.pattern_id,
                            'block_id': spot_target.block_id,
                            'spot_date': str(current_stock.date)
                        }
                    )
                else:
                    # 새 블록 생성
                    new_block = DynamicBlockDetection(
                        block_id=node.block_id,
                        block_type=node.block_type,
                        ticker=pattern.ticker,
                        pattern_id=pattern.pattern_id,
                        condition_name=condition_name
                    )
                    new_block.start(current_stock.date)
                    new_block.update_peak(
                        current_stock.date,
                        current_stock.close,
                        current_stock.volume
                    )

                    # 전일 종가 저장
                    if prev_stock:
                        new_block.prev_close = prev_stock.close

                    # spot1 자동 추가
                    new_block.add_spot(
                        spot_date=current_stock.date,
                        open_price=current_stock.open,
                        close_price=current_stock.close,
                        high_price=current_stock.high,
                        low_price=current_stock.low,
                        volume=current_stock.volume
                    )

                    # 패턴에 추가
                    pattern.blocks[node.block_id] = new_block

                    logger.debug(
                        f"Created new block: {node.block_id}",
                        extra={
                            'pattern_id': pattern.pattern_id,
                            'block_id': node.block_id,
                            'date': str(current_stock.date)
                        }
                    )

    def _check_and_complete_blocks(
        self,
        pattern: PatternContext,
        context: dict,
        condition_name: str,
        current_date: date
    ) -> None:
        """
        활성 블록 종료 조건 체크

        Args:
            pattern: 패턴 컨텍스트
            context: 평가 컨텍스트
            condition_name: 조건 이름
            current_date: 현재 날짜
        """
        for block_id, block in list(pattern.blocks.items()):
            if not block.is_active():
                continue

            node = self.block_graph.get_node(block_id)
            if not node:
                continue

            # 종료 조건 평가
            exit_reason = self.block_detector.evaluate_exit_condition(node, context, condition_name)

            if exit_reason:
                # EXISTS() 조건이면 전일 종료, 가격 조건이면 당일 종료
                if 'exists(' in exit_reason.lower():
                    # 시작일과 같은 날이면 당일 종료
                    if block.started_at == current_date:
                        end_date = current_date
                    else:
                        # 전일 종료 (정확한 날짜 필요 - 여기서는 단순화)
                        end_date = current_date
                else:
                    end_date = current_date

                block.complete(end_date)
                logger.debug(
                    f"Completed block: {block_id}",
                    extra={
                        'pattern_id': pattern.pattern_id,
                        'block_id': block_id,
                        'end_date': str(end_date),
                        'reason': exit_reason
                    }
                )

    def _convert_to_pattern_trees(
        self,
        ticker: str,
        pattern_contexts: List[PatternContext]
    ) -> None:
        """
        PatternContext → SeedPatternTree 변환

        PatternManager에 패턴을 등록합니다.

        Args:
            ticker: 종목 코드
            pattern_contexts: 패턴 컨텍스트 리스트
        """
        for pattern_ctx in pattern_contexts:
            # Block1 검증
            if 'block1' not in pattern_ctx.blocks:
                logger.warning(
                    f"Pattern {pattern_ctx.pattern_id} has no block1, skipping",
                    extra={'pattern_id': pattern_ctx.pattern_id}
                )
                continue

            block1 = pattern_ctx.blocks['block1']

            # SeedPatternTree 생성
            pattern = self.pattern_manager.create_new_pattern(
                ticker=ticker,
                root_block=block1,
                detection_date=pattern_ctx.created_at
            )

            # 나머지 블록들 추가
            for block_id, block in pattern_ctx.blocks.items():
                if block_id == 'block1':
                    continue  # block1은 이미 추가됨

                try:
                    self.pattern_manager.add_block_to_pattern(pattern, block)
                except ValueError as e:
                    logger.warning(
                        f"Failed to add {block_id} to pattern: {e}",
                        extra={
                            'pattern_id': pattern_ctx.pattern_id,
                            'block_id': block_id
                        }
                    )

    def set_yaml_config_path(self, path: str) -> None:
        """YAML 설정 파일 경로 설정"""
        self.yaml_config_path = path

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Phase 2: Highlight Detection Integration (NEW - 2025-10-27)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _detect_highlights_for_patterns(
        self,
        ticker: str,
        stocks: List[Stock]
    ) -> None:
        """
        모든 패턴에 대해 하이라이트 탐지 (NEW - 2025-10-27 Phase 2)

        각 패턴의 블록들을 검사하여 하이라이트 조건을 만족하는
        블록을 찾고, Primary highlight를 패턴에 저장합니다.

        프로세스:
        1. 모든 패턴 순회
        2. 각 패턴의 블록들에 대해 highlight_condition 확인
        3. HighlightDetector로 하이라이트 블록 찾기
        4. Primary highlight를 SeedPatternTree에 설정

        Args:
            ticker: 종목 코드
            stocks: 전체 주가 데이터

        Example:
            >>> self._detect_highlights_for_patterns('025980', stocks)
            # Pattern SEED_025980_20180307_001: Highlight detected on block1
        """
        all_patterns = self.pattern_manager.get_all_patterns()
        total_highlights = 0

        for pattern in all_patterns:
            # Block1의 highlight_condition 확인
            block1_node = self.block_graph.get_node('block1')
            if not block1_node or not block1_node.has_highlight_condition():
                continue  # 하이라이트 조건 없음

            highlight_condition = block1_node.highlight_condition

            # 패턴의 모든 블록 조회 (리스트로 변환)
            pattern_blocks = list(pattern.blocks.values())

            # 평가 컨텍스트 구성
            context = {
                'ticker': ticker,
                'all_stocks': stocks
            }

            # 하이라이트 탐지
            highlights = self.highlight_detector.find_highlights(
                blocks=pattern_blocks,
                highlight_condition=highlight_condition,
                context=context
            )

            if highlights:
                # Primary highlight 설정
                primary = self.highlight_detector.find_primary(highlights)

                if primary:
                    pattern.set_primary_highlight(
                        block_id=primary.block_id,
                        metadata={
                            'highlight_type': highlight_condition.type,
                            'spot_count': primary.get_spot_count(),
                            'priority': highlight_condition.priority,
                            'detected_at': primary.started_at.isoformat() if primary.started_at else None
                        }
                    )
                    total_highlights += 1

                    logger.info(
                        f"Highlight detected for pattern {pattern.pattern_id}",
                        extra={
                            'pattern_id': str(pattern.pattern_id),
                            'highlight_block_id': primary.block_id,
                            'highlight_type': highlight_condition.type,
                            'spot_count': primary.get_spot_count()
                        }
                    )

        if total_highlights > 0:
            logger.info(
                f"Highlight detection summary",
                extra={
                    'ticker': ticker,
                    'total_patterns': len(all_patterns),
                    'patterns_with_highlights': total_highlights,
                    'highlight_rate_pct': round(total_highlights / len(all_patterns) * 100, 2) if all_patterns else 0
                }
            )
