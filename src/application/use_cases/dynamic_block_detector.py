"""
DynamicBlockDetector - 동적 블록 감지 Use Case

BlockGraph와 ExpressionEngine을 활용하여 주가 데이터에서 블록 패턴을 감지.
"""

from typing import List, Dict, Optional
from datetime import date

from src.domain.entities.core import Stock
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.domain.entities.block_graph import BlockGraph, BlockNode
from src.domain.entities.conditions import ExpressionEngine
from src.domain.exceptions import ExpressionEvaluationError
from src.application.services.spot_strategies import SpotStrategy, CompositeSpotStrategy
from src.application.use_cases.pattern_detection_state import PatternDetectionState
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class DynamicBlockDetector:
    """
    동적 블록 감지기

    BlockGraph 정의에 따라 주가 데이터에서 블록을 감지.

    Attributes:
        block_graph: 블록 그래프 정의
        expression_engine: 표현식 평가 엔진
    """

    def __init__(
        self,
        block_graph: BlockGraph,
        expression_engine: ExpressionEngine,
        spot_strategy: Optional[SpotStrategy] = None
    ):
        """
        Args:
            block_graph: 블록 그래프 정의
            expression_engine: 표현식 평가 엔진
            spot_strategy: Spot 판정 전략 (None이면 CompositeSpotStrategy 사용)
        """
        self.block_graph = block_graph
        self.expression_engine = expression_engine
        self.spot_strategy = spot_strategy or CompositeSpotStrategy(expression_engine)

    def detect_blocks(
        self,
        ticker: str,
        stocks: List[Stock],
        condition_name: str = "seed",
        active_blocks: Optional[List[DynamicBlockDetection]] = None
    ) -> List[DynamicBlockDetection]:
        """
        주가 데이터에서 블록 감지

        .. deprecated::
            이 메서드는 멀티패턴 지원을 위해 deprecated되었습니다.
            대신 SeedPatternDetectionOrchestrator를 사용하세요.

            내부적으로는 여전히 작동하지만, 패턴별 독립 평가가 필요한 경우
            evaluate_entry_condition(), evaluate_exit_condition()을 직접 사용하세요.

        Args:
            ticker: 종목 코드
            stocks: 주가 데이터 리스트 (시간순 정렬)
            condition_name: 조건 이름 ("seed" 또는 "redetection")
            active_blocks: 진행 중인 블록 리스트 (None이면 빈 리스트)

        Returns:
            감지된 블록 리스트 (신규 + 업데이트된 기존 블록)

        Note:
            이 메서드는 여전히 동작하지만, 멀티패턴 탐지를 제대로 지원하지 못합니다.
            새 코드에서는 SeedPatternDetectionOrchestrator.detect_patterns()를 사용하세요.
        """
        if active_blocks is None:
            active_blocks = []

        # 데이터 전처리: 거래 없는 날의 가격을 마지막 거래 종가로 채움
        from src.infrastructure.utils.stock_data_utils import forward_fill_prices
        stocks = forward_fill_prices(stocks)
        logger.info(
            "Applied forward-fill preprocessing",
            context={'ticker': ticker, 'total_records': len(stocks)}
        )

        # 블록을 block_id로 매핑 (모든 블록 포함, 완료된 블록도 추적)
        active_blocks_map = {b.block_id: b for b in active_blocks}

        # Virtual Block System 상태 관리
        pattern_state = PatternDetectionState()

        # 스킵된 블록 추적 (is_backward_spot으로 스킵된 블록을 다음에 재탐지)
        next_target_blocks = []

        # 주가 데이터 순회
        for i, current_stock in enumerate(stocks):
            # 이전 주가: 마지막 정상 거래일
            prev_stock = self._find_last_valid_day(stocks, i)
            prev_raw = stocks[i - 1] if i > 0 else None

            # Context 구성
            context = self._build_context(
                current=current_stock,
                prev=prev_stock,
                prev_raw=prev_raw,
                all_stocks=stocks[:i + 1],  # 현재까지의 주가
                active_blocks=active_blocks_map
            )

            # 1. 새로운 블록 감지 (peak 갱신 전에 먼저 체크!)
            # 이렇게 해야 "block1.peak_volume보다 큼" 조건이 제대로 작동함
            new_blocks = self._detect_new_blocks(
                ticker=ticker,
                condition_name=condition_name,
                current_date=current_stock.date,
                current_price=current_stock.high,
                current_volume=current_stock.volume,
                context=context,
                active_blocks_map=active_blocks_map,
                next_target_blocks=next_target_blocks,
                pattern_state=pattern_state
            )

            # 2. 새로운 블록을 active_blocks_map에 추가
            for new_block in new_blocks:
                active_blocks_map[new_block.block_id] = new_block

            # 3. Context 재구성 (새로 추가된 블록 포함)
            if new_blocks:
                context = self._build_context(
                    current=current_stock,
                    prev=prev_stock,
                    prev_raw=prev_raw,
                    all_stocks=stocks[:i + 1],
                    active_blocks=active_blocks_map
                )

            # 4. 진행 중인 블록 종료 조건 확인
            # 새 블록이 추가되었으므로 EXISTS() 조건이 올바르게 평가됨
            self._check_and_complete_blocks(
                active_blocks_map,
                current_stock.date,
                stocks[:i + 1],  # 현재까지의 주가 데이터
                context,
                condition_name
            )

            # 4.5. Forward Spot 체크 (NEW - 2025-10-26)
            # Active 블록의 D+1, D+2일에 spot 조건을 만족하면 spot 추가
            self._check_forward_spots(
                active_blocks_map,
                current_stock.date,
                context
            )

            # 5. 활성 블록들의 peak 갱신 (종료된 블록 제외)
            self._update_peaks(
                active_blocks_map,
                current_stock.date,
                context
            )

        # 모든 블록 반환 (active_blocks_map에 모든 블록이 포함됨)
        return list(active_blocks_map.values())

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Public API - Stateless 조건 평가 메서드 (Option D 리팩토링)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def evaluate_entry_condition(
        self,
        node: BlockNode,
        context: dict,
        condition_name: str = "seed"
    ) -> bool:
        """
        블록 진입 조건 평가 (stateless)

        상태 관리 없이 순수하게 조건만 평가합니다.
        패턴별 독립 평가를 위해 사용됩니다.

        Args:
            node: 평가할 블록 노드
            context: 평가 컨텍스트
                - current: 현재 주가
                - prev: 이전 주가
                - all_stocks: 전체 주가 데이터
                - block1, block2, ...: 활성 블록들 (패턴별)
            condition_name: 조건 이름 ("seed" 또는 "redetection")

        Returns:
            진입 조건 만족 여부

        Example:
            >>> detector = DynamicBlockDetector(graph, engine)
            >>> context = {
            ...     'current': stock,
            ...     'prev': prev_stock,
            ...     'all_stocks': all_stocks,
            ...     'block1': pattern.blocks['block1']
            ... }
            >>> detector.evaluate_entry_condition(block2_node, context)
            True

        Note:
            Option D 리팩토링의 핵심 메서드.
            Orchestrator가 패턴별로 컨텍스트를 구성하여 호출합니다.
        """
        return self._check_entry_conditions(node, context, condition_name)

    def evaluate_exit_condition(
        self,
        node: BlockNode,
        context: dict,
        condition_name: str = "seed"
    ) -> Optional[str]:
        """
        블록 종료 조건 평가 (stateless)

        상태 관리 없이 순수하게 조건만 평가합니다.

        Args:
            node: 평가할 블록 노드
            context: 평가 컨텍스트
            condition_name: 조건 이름

        Returns:
            만족된 종료 조건 표현식 (만족 안 하면 None)

        Example:
            >>> exit_expr = detector.evaluate_exit_condition(block1_node, context)
            >>> if exit_expr:
            ...     print(f"Exit condition met: {exit_expr}")

        Note:
            EXISTS() 조건 vs 가격 조건을 구분하여 반환합니다.
            Orchestrator는 이를 통해 종료일을 결정합니다.
        """
        return self._check_exit_conditions_with_reason(node, context, condition_name)

    def evaluate_spot_strategy(
        self,
        current_node: BlockNode,
        context: dict
    ) -> Optional[DynamicBlockDetection]:
        """
        Spot 전략 평가 (stateless)

        현재 노드가 spot으로 추가되어야 하는지 판단합니다.

        Args:
            current_node: 현재 평가 중인 노드
            context: 평가 컨텍스트
                - active_blocks: 패턴의 활성 블록 맵

        Returns:
            spot 추가 대상 블록 (추가하지 않으면 None)

        Example:
            >>> target_block = detector.evaluate_spot_strategy(block2_node, context)
            >>> if target_block:
            ...     target_block.add_spot(...)

        Note:
            SpotStrategy 패턴을 내부적으로 사용합니다.
        """
        active_blocks = context.get('active_blocks', {})
        return self.spot_strategy.should_add_spot(
            current_node=current_node,
            context=context,
            active_blocks=active_blocks
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Private Helper Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _find_last_valid_day(
        self,
        stocks: List[Stock],
        current_index: int
    ) -> Optional[Stock]:
        """
        마지막 정상 거래일 찾기

        현재 인덱스 이전의 가장 최근 정상 거래일(`volume > 0`) 주가를 반환합니다.

        Args:
            stocks: 주가 데이터 리스트
            current_index: 현재 인덱스

        Returns:
            마지막 정상 거래일 주가, 없으면 None

        Example:
            stocks = [day1(vol=100), day2(vol=0), day3(vol=0), day4(vol=200)]
            _find_last_valid_day(stocks, 3) → day1
        """
        for i in range(current_index - 1, -1, -1):
            if stocks[i].volume > 0:
                logger.debug(
                    "Found last valid trading day",
                    context={
                        'current_index': current_index,
                        'valid_index': i,
                        'days_back': current_index - i
                    }
                )
                return stocks[i]

        logger.debug(
            "No valid trading day found",
            context={'current_index': current_index}
        )
        return None

    def _build_context(
        self,
        current: Stock,
        prev: Optional[Stock],
        all_stocks: List[Stock],
        active_blocks: Dict[str, DynamicBlockDetection],
        prev_raw: Optional[Stock] = None
    ) -> dict:
        """
        표현식 평가를 위한 context 구성

        Args:
            current: 현재 주가
            prev: 마지막 정상 거래일 주가 (volume > 0)
            all_stocks: 전체 주가 데이터 (forward-fill 적용됨)
            active_blocks: 진행 중인 블록 맵 (block_id → DynamicBlockDetection)
            prev_raw: 무조건 바로 전날 (거래 없어도 반환, None 가능)

        Returns:
            Context 딕셔너리
                - current: 현재 주가
                - prev: 마지막 정상 거래일 주가
                - prev_raw: 바로 전날 주가 (원본)
                - days_since_prev: 마지막 정상 거래일로부터 경과일
                - all_stocks: 전체 주가 데이터
                - block1, block2, ... : 활성 블록들
        """
        context = {
            'current': current,
            'prev': prev,
            'prev_raw': prev_raw,
            'all_stocks': all_stocks,
        }

        # days_since_prev 계산
        if prev and current:
            context['days_since_prev'] = (current.date - prev.date).days
        else:
            context['days_since_prev'] = 0

        # 진행 중인 블록들을 context에 추가
        # block1, block2, block3, ... 형태로 추가
        for block_id, block in active_blocks.items():
            # block_id가 "block1" 형태라면 그대로 사용
            # 아니면 "blockN" 형태로 변환
            if block_id.startswith('block'):
                context[block_id] = block
            else:
                # 커스텀 block_id인 경우 (예: "my_custom_block")
                context[block_id] = block

        return context

    def _check_and_complete_blocks(
        self,
        active_blocks_map: Dict[str, DynamicBlockDetection],
        current_date: date,
        all_stocks: List[Stock],
        context: dict,
        condition_name: str = "seed"
    ) -> None:
        """
        진행 중인 블록의 종료 조건 확인 및 완료 처리

        Peak 갱신은 하지 않고, 종료 조건만 체크합니다.
        새 블록이 감지된 후 호출되어 EXISTS() 조건을 올바르게 평가합니다.

        종료일 결정 규칙:
        1. EXISTS() 조건으로 종료 (예: exists('block2'))
           a) 블록이 시작일과 같은 날 종료: **당일**로 종료
              → 이유: 블록이 당일에 시작하고 즉시 종료되는 경우 (started_at < ended_at 방지)
           b) 블록이 최소 하루 이상 진행: **전 거래일**로 종료
              → 이유: 새 블록이 시작된 당일은 이미 새 블록의 시작일이므로
                      이전 블록은 그 전날 종료된 것으로 간주

        2. 가격/지표 조건으로 종료 (예: current.low < ma(60))
           → 조건을 만족한 **당일**로 종료
           → 이유: 저가가 MA60 아래로 터치한 바로 그날 종료된 것으로 간주

        Args:
            active_blocks_map: 진행 중인 블록 맵
            current_date: 현재 날짜
            all_stocks: 현재까지의 주가 데이터
            context: 평가 context
            condition_name: 조건 이름 ("seed" 또는 "reentry")
        """
        blocks_to_complete = []

        for block_id, block in active_blocks_map.items():
            if not block.is_active():
                continue

            # 블록 정의 조회
            node = self.block_graph.get_node(block_id)
            if not node:
                continue

            # 종료 조건 확인 (OR 조건)
            # 어떤 조건이 만족되었는지도 반환받음
            satisfied_condition = self._check_exit_conditions_with_reason(node, context, condition_name)
            if satisfied_condition:
                blocks_to_complete.append((block_id, satisfied_condition))

        # 종료 조건을 만족한 블록들 완료 처리
        for block_id, condition_expr in blocks_to_complete:
            block = active_blocks_map[block_id]

            # Virtual Block은 complete() 불필요 (이미 VIRTUAL_SKIPPED 상태)
            if block.is_virtual:
                continue

            # 종료 조건이 EXISTS() 함수를 사용하는지 확인
            is_exists_condition = 'exists(' in condition_expr.lower()

            if is_exists_condition:
                # EXISTS() 조건: 새 블록 시작으로 인한 종료
                # 단, 시작일과 종료일이 같은 경우는 당일로 종료 (블록이 당일에 시작+종료)
                if block.started_at == current_date:
                    end_date = current_date  # 시작일과 같은 날 종료되면 당일로
                else:
                    # 블록이 최소 하루 이상 진행된 경우 → 전 거래일로 종료
                    end_date = self._find_last_trading_day_before(current_date, all_stocks)
            else:
                # 가격/지표 조건: 조건 만족 당일로 종료
                end_date = current_date

            block.complete(end_date)

    def _update_peaks(
        self,
        active_blocks_map: Dict[str, DynamicBlockDetection],
        current_date: date,
        context: dict
    ) -> None:
        """
        활성 블록들의 peak 갱신

        종료된 블록은 제외하고, 진행 중인 블록만 peak를 갱신합니다.

        Args:
            active_blocks_map: 진행 중인 블록 맵
            current_date: 현재 날짜
            context: 평가 context
        """
        current = context['current']

        for block_id, block in active_blocks_map.items():
            if not block.is_active():
                continue

            # Peak 갱신
            block.update_peak(current_date, current.high, current.volume)

    def _detect_new_blocks(
        self,
        ticker: str,
        condition_name: str,
        current_date: date,
        current_price: float,
        current_volume: int,
        context: dict,
        active_blocks_map: Dict[str, DynamicBlockDetection],
        next_target_blocks: List[str],
        pattern_state: PatternDetectionState
    ) -> List[DynamicBlockDetection]:
        """
        새로운 블록 감지

        Args:
            ticker: 종목 코드
            condition_name: 조건 이름
            current_date: 현재 날짜
            current_price: 현재 가격
            current_volume: 현재 거래량
            context: 평가 context
            active_blocks_map: 활성 + 완료된 블록 맵 (context 참조용, 최신 블록만 유지)
            next_target_blocks: 스킵된 블록 리스트 (is_backward_spot으로 스킵된 블록을 재탐지)
            pattern_state: Virtual Block System 상태 관리 객체

        Returns:
            신규 감지된 블록 리스트 (real + virtual 블록 포함)
        """
        new_blocks = []
        current = context.get('current')

        # 스킵된 블록이 있으면 해당 블록들을 우선적으로 체크
        nodes_to_check = []
        if next_target_blocks:
            # 스킵된 블록들만 체크
            nodes_to_check = [
                (node_id, node) for node_id, node in self.block_graph.nodes.items()
                if node_id in next_target_blocks
            ]
        else:
            # 모든 블록 체크
            nodes_to_check = list(self.block_graph.nodes.items())

        # 노드에 대해 진입 조건 확인
        for node_id, node in nodes_to_check:
            # 이미 활성 상태인 블록은 스킵 (중복 방지)
            # 완료된 블록은 덮어쓰기 가능 (새로운 패턴 시작)
            if node_id in active_blocks_map and active_blocks_map[node_id].is_active():
                continue

            # 진입 조건 확인 (AND 조건)
            if self._check_entry_conditions(node, context, condition_name):
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # Spot 체크: SpotStrategy 패턴 사용
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                target_prev_block = self.spot_strategy.should_add_spot(
                    current_node=node,
                    context=context,
                    active_blocks=active_blocks_map
                )

                # spot 추가 시도
                if target_prev_block:
                    success = target_prev_block.add_spot(
                        spot_date=current_date,
                        open_price=current.open,
                        close_price=current.close,
                        high_price=current.high,
                        low_price=current.low,
                        volume=current.volume
                    )

                    if success:
                        logger.info(
                            f"Added spot{target_prev_block.get_spot_count()} to {target_prev_block.block_id}",
                            context={
                                'block_id': target_prev_block.block_id,
                                'block_type': target_prev_block.block_type,
                                'ticker': ticker,
                                'spot_date': current_date,
                                'spot_count': target_prev_block.get_spot_count(),
                                'skipped_block': node.block_id
                            }
                        )

                        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        # Virtual Block 생성 (Spot으로 스킵된 블록)
                        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        # Virtual Block System: spot으로 스킵되더라도 exists() 체크를 위해
                        # virtual block을 즉시 생성하여 active_blocks_map에 추가

                        logical_level, pattern_sequence = pattern_state.create_virtual_block()

                        virtual_block = DynamicBlockDetection(
                            block_id=node.block_id,
                            block_type=node.block_type,
                            ticker=ticker,
                            condition_name=condition_name,
                            # Virtual Block 전용 필드
                            yaml_type=node.block_type,  # 원래 YAML 정의값
                            logical_level=logical_level,  # 현재 level (증가 안 함)
                            pattern_sequence=0,  # Virtual = 0
                            is_virtual=True,  # Virtual 표시
                            status=BlockStatus.VIRTUAL_SKIPPED  # 스킵 상태
                        )

                        # Virtual block은 시작/종료 없이 바로 VIRTUAL_SKIPPED 상태
                        # started_at, ended_at은 None으로 남음

                        new_blocks.append(virtual_block)
                        active_blocks_map[node.block_id] = virtual_block

                        logger.info(
                            f"Created virtual block: {node.block_id}",
                            context={
                                'block_id': node.block_id,
                                'block_type': node.block_type,
                                'ticker': ticker,
                                'logical_level': logical_level,
                                'yaml_type': node.block_type,
                                'reason': 'spot_skip'
                            }
                        )

                        # Virtual 블록은 재탐지하지 않음 (next_target_blocks에 추가 안 함)
                        # spot 추가 성공 → 새 real 블록 생성하지 않고 계속 진행
                        continue
                    else:
                        # spot 추가 실패 (max_spots 초과 등)
                        logger.debug(
                            f"Spot addition failed, will create new block",
                            context={
                                'block_id': node.block_id,
                                'block_type': node.block_type,
                                'ticker': ticker,
                                'date': str(current_date),
                                'prev_block_id': target_prev_block.block_id,
                                'prev_block_spot_count': target_prev_block.get_spot_count()
                            }
                        )

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 새 블록 생성 (spot 조건 불만족 또는 spot 추가 실패)
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                # Early Start Spot 확인
                early_start_info = context.get('_early_start_info')

                logger.debug(
                    f"Creating new block: {node.block_id}",
                    context={
                        'block_id': node.block_id,
                        'block_type': node.block_type,
                        'ticker': ticker,
                        'date': str(current_date),
                        'spot_added': target_prev_block is not None,
                        'has_spot_condition': node.spot_condition is not None,
                        'has_early_start_info': early_start_info is not None
                    }
                )

                # Virtual Block System: Real 블록 생성 시 logical_level, pattern_sequence 할당
                logical_level, pattern_sequence = pattern_state.create_real_block()

                new_block = DynamicBlockDetection(
                    block_id=node.block_id,
                    block_type=node.block_type,
                    ticker=ticker,
                    condition_name=condition_name,
                    # Virtual Block System 필드
                    yaml_type=node.block_type,  # 원래 YAML 정의값
                    logical_level=logical_level,  # 실제 급등 순서 (증가됨)
                    pattern_sequence=pattern_sequence,  # 패턴 내 생성 순서 (증가됨)
                    is_virtual=False  # Real 블록
                )

                # Early Start 처리
                if early_start_info:
                    # 조기 시작일로 블록 시작
                    new_block.start(early_start_info.early_start_date)

                    # spot1 추가 (early start date)
                    new_block.add_spot(
                        spot_date=early_start_info.spot1_date,
                        open_price=early_start_info.spot1_data['open'],
                        close_price=early_start_info.spot1_data['close'],
                        high_price=early_start_info.spot1_data['high'],
                        low_price=early_start_info.spot1_data['low'],
                        volume=early_start_info.spot1_data['volume']
                    )

                    # spot2 추가 (current date)
                    new_block.add_spot(
                        spot_date=early_start_info.spot2_date,
                        open_price=early_start_info.spot2_data['open'],
                        close_price=early_start_info.spot2_data['close'],
                        high_price=early_start_info.spot2_data['high'],
                        low_price=early_start_info.spot2_data['low'],
                        volume=early_start_info.spot2_data['volume']
                    )

                    # Peak 업데이트 (early start date부터 계산)
                    # spot1 날짜부터 peak 계산
                    all_stocks = context.get('all_stocks', [])
                    for stock in all_stocks:
                        if stock.date >= early_start_info.early_start_date and stock.date <= current_date:
                            new_block.update_peak(stock.date, stock.close, stock.volume)

                    # 이전 블록 종료 (spot1 - 1일)
                    prev_block_id = early_start_info.prev_block_id
                    if prev_block_id in active_blocks_map:
                        prev_block = active_blocks_map[prev_block_id]
                        if prev_block.is_active():
                            # spot1 이전의 마지막 거래일 찾기
                            actual_end_date = self._find_last_trading_day_before(
                                early_start_info.spot1_date,
                                all_stocks
                            )
                            prev_block.complete(actual_end_date)
                            logger.info(
                                f"Terminated {prev_block_id} at {actual_end_date} (day before spot1)",
                                context={
                                    'prev_block_id': prev_block_id,
                                    'end_date': str(actual_end_date),
                                    'new_block_spot1': str(early_start_info.spot1_date)
                                }
                            )

                    logger.info(
                        f"Created block with early start: {node.block_id}",
                        context={
                            'block_id': node.block_id,
                            'early_start_date': str(early_start_info.early_start_date),
                            'spot1_date': str(early_start_info.spot1_date),
                            'spot2_date': str(early_start_info.spot2_date),
                            'prev_block_id': prev_block_id
                        }
                    )

                    # Early start info 클리어 (다음 노드에 영향 안 주도록)
                    context.pop('_early_start_info', None)

                else:
                    # 일반 블록 생성
                    new_block.start(current_date)
                    new_block.update_peak(current_date, current_price, current_volume)

                    # 자동 spot1 추가 (시작일 = spot1)
                    new_block.add_spot(
                        spot_date=current_date,
                        open_price=current.open,
                        close_price=current.close,
                        high_price=current.high,
                        low_price=current.low,
                        volume=current.volume
                    )

                # 전일 종가 저장 (상승폭 계산용)
                prev_stock = context.get('prev')
                if prev_stock and hasattr(prev_stock, 'close') and prev_stock.close:
                    new_block.prev_close = prev_stock.close

                # 부모 블록 연결 (엣지 기반)
                parent_nodes = self.block_graph.get_parents(node_id)
                for parent_node in parent_nodes:
                    if parent_node.block_id in active_blocks_map:
                        parent_block = active_blocks_map[parent_node.block_id]
                        if parent_block.id is not None:
                            new_block.add_parent_block(parent_block.id)

                new_blocks.append(new_block)

                # 블록 생성 성공 → next_target_blocks에서 제거
                if node.block_id in next_target_blocks:
                    next_target_blocks.remove(node.block_id)
                    logger.debug(
                        f"Block {node.block_id} created successfully, removed from next_target_blocks",
                        context={
                            'created_block': node.block_id,
                            'remaining_targets': next_target_blocks
                        }
                    )

        return new_blocks

    def _check_entry_conditions(
        self,
        node: BlockNode,
        context: dict,
        condition_name: str = "seed"
    ) -> bool:
        """
        진입 조건 확인 (AND 조건 - 모든 조건을 만족해야 함)

        Args:
            node: 블록 노드
            context: 평가 context
            condition_name: 조건 이름 ("seed" 또는 "reentry")

        Returns:
            모든 조건을 만족하면 True

        Note:
            - condition_name="seed": node.entry_conditions 사용
            - condition_name="reentry": node.reentry_entry_conditions 사용
            - 디버깅을 위해 각 조건의 평가 결과를 DEBUG 레벨로 로깅합니다.
        """
        # condition_name에 따라 조건 선택
        if condition_name == "reentry":
            conditions = node.reentry_entry_conditions
        else:
            conditions = node.entry_conditions

        if not conditions:
            return False

        current_date = context.get('current').date if context.get('current') else None

        try:
            for condition in conditions:
                # Condition 객체의 evaluate() 메서드 사용
                result = condition.evaluate(self.expression_engine, context)

                # 각 조건의 평가 결과를 DEBUG 레벨로 로깅
                logger.debug(
                    f"Entry condition evaluated: {condition.name}",
                    context={
                        'block_id': node.block_id,
                        'block_type': node.block_type,
                        'date': str(current_date) if current_date else 'unknown',
                        'condition_name': condition.name,
                        'expression': condition.expression[:100] if len(condition.expression) > 100 else condition.expression,
                        'result': result
                    }
                )

                # 결과가 False이면 즉시 False 반환
                if not result:
                    logger.debug(
                        f"Entry condition FAILED: {condition.name}",
                        context={
                            'block_id': node.block_id,
                            'block_type': node.block_type,
                            'date': str(current_date) if current_date else 'unknown',
                            'condition_name': condition.name,
                            'expression': condition.expression[:100] if len(condition.expression) > 100 else condition.expression
                        }
                    )
                    return False

            # 모든 조건이 True
            logger.debug(
                f"All entry conditions passed for {node.block_id}",
                context={
                    'block_id': node.block_id,
                    'block_type': node.block_type,
                    'date': str(current_date) if current_date else 'unknown',
                    'num_conditions': len(node.entry_conditions)
                }
            )
            return True

        except Exception as e:
            # 평가 중 에러 발생 시 False
            logger.error(
                "Entry condition evaluation failed",
                context={
                    'block_id': node.block_id,
                    'block_type': node.block_type,
                    'num_conditions': len(node.entry_conditions),
                    'ticker': context.get('ticker', 'unknown') if isinstance(context, dict) else 'unknown',
                    'date': str(current_date) if current_date else 'unknown'
                },
                exc=e
            )
            return False

    def _check_exit_conditions(
        self,
        node: BlockNode,
        context: dict
    ) -> bool:
        """
        종료 조건 확인 (OR 조건 - 하나라도 만족하면 종료)

        Args:
            node: 블록 노드
            context: 평가 context

        Returns:
            하나라도 조건을 만족하면 True
        """
        if not node.exit_conditions:
            return False

        try:
            for condition_expr in node.exit_conditions:
                result = self.expression_engine.evaluate(condition_expr, context)

                # 결과가 True이면 즉시 True 반환
                if result:
                    return True

            # 모든 조건이 False
            return False

        except Exception as e:
            # 평가 중 에러 발생 시 False
            logger.error(
                "Exit condition evaluation failed",
                context={
                    'block_id': node.block_id,
                    'block_type': node.block_type,
                    'num_conditions': len(node.exit_conditions),
                    'ticker': context.get('ticker', 'unknown') if isinstance(context, dict) else 'unknown'
                },
                exc=e
            )
            return False

    def _check_exit_conditions_with_reason(
        self,
        node: BlockNode,
        context: dict,
        condition_name: str = "seed"
    ) -> Optional[str]:
        """
        종료 조건 확인 및 만족된 조건 반환 (OR 조건 - 하나라도 만족하면 종료)

        Args:
            node: 블록 노드
            context: 평가 context
            condition_name: 조건 이름 ("seed" 또는 "reentry")

        Returns:
            만족된 조건의 expression (만족된 조건이 없으면 None)

        Note:
            - condition_name="seed": node.exit_conditions 사용
            - condition_name="reentry": node.reentry_exit_conditions 사용
            - 디버깅을 위해 각 종료 조건의 평가 결과를 DEBUG 레벨로 로깅합니다.
            - 종료 조건은 OR 조건으로, 하나라도 만족하면 블록이 종료됩니다.
        """
        # condition_name에 따라 조건 선택
        if condition_name == "reentry":
            conditions = node.reentry_exit_conditions
        else:
            conditions = node.exit_conditions

        if not conditions:
            return None

        current_date = context.get('current').date if context.get('current') else None

        try:
            for condition in conditions:
                # Condition 객체의 evaluate() 메서드 사용
                result = condition.evaluate(self.expression_engine, context)

                # 각 종료 조건의 평가 결과를 DEBUG 레벨로 로깅
                logger.debug(
                    f"Exit condition evaluated: {condition.name}",
                    context={
                        'block_id': node.block_id,
                        'block_type': node.block_type,
                        'date': str(current_date) if current_date else 'unknown',
                        'condition_name': condition.name,
                        'expression': condition.expression[:100] if len(condition.expression) > 100 else condition.expression,
                        'result': result
                    }
                )

                # 결과가 True이면 해당 조건 expression 반환
                if result:
                    logger.debug(
                        f"Exit condition SATISFIED: {condition.name} - Block will terminate",
                        context={
                            'block_id': node.block_id,
                            'block_type': node.block_type,
                            'date': str(current_date) if current_date else 'unknown',
                            'condition_name': condition.name,
                            'expression': condition.expression[:100] if len(condition.expression) > 100 else condition.expression
                        }
                    )
                    return condition.expression

            # 모든 조건이 False
            logger.debug(
                f"No exit conditions satisfied for {node.block_id}",
                context={
                    'block_id': node.block_id,
                    'block_type': node.block_type,
                    'date': str(current_date) if current_date else 'unknown',
                    'num_conditions': len(node.exit_conditions)
                }
            )
            return None

        except Exception as e:
            # 평가 중 에러 발생 시 None
            logger.error(
                "Exit condition evaluation failed",
                context={
                    'block_id': node.block_id,
                    'block_type': node.block_type,
                    'num_conditions': len(node.exit_conditions),
                    'ticker': context.get('ticker', 'unknown') if isinstance(context, dict) else 'unknown'
                },
                exc=e
            )
            return None

    def can_transition(
        self,
        from_block_id: str,
        to_block_id: str,
        context: dict
    ) -> bool:
        """
        블록 전이 가능 여부 확인

        Args:
            from_block_id: 시작 블록 ID
            to_block_id: 도착 블록 ID
            context: 평가 context

        Returns:
            전이 가능하면 True
        """
        edges = self.block_graph.get_edges_from(from_block_id)

        for edge in edges:
            if edge.to_block_id != to_block_id:
                continue

            # 조건부 엣지인 경우 조건 확인
            if edge.is_conditional():
                if not edge.condition:
                    return False

                try:
                    result = self.expression_engine.evaluate(edge.condition, context)
                    return bool(result)
                except Exception as e:
                    logger.error(
                        "Edge condition evaluation failed",
                        context={
                            'from_block': from_block_id,
                            'to_block': to_block_id,
                            'edge_condition': edge.condition,
                            'ticker': context.get('ticker', 'unknown') if isinstance(context, dict) else 'unknown'
                        },
                        exc=e
                    )
                    return False

            # 조건부가 아니면 전이 가능
            return True

        # 해당 엣지가 없으면 전이 불가
        return False

    def _find_last_trading_day_before(
        self,
        target_date: date,
        all_stocks: List[Stock]
    ) -> date:
        """
        현재 날짜 이전의 마지막 정상 거래일 찾기

        Args:
            target_date: 기준 날짜
            all_stocks: 주가 데이터 리스트

        Returns:
            마지막 정상 거래일 (찾지 못하면 target_date)
        """
        for stock in reversed(all_stocks):
            if stock.date < target_date and stock.volume > 0:
                return stock.date
        return target_date

    def _find_previous_block_for_spot(
        self,
        current_block_type: int,
        current_date: date,
        active_blocks_map: Dict[str, DynamicBlockDetection],
        context: dict
    ) -> Optional[DynamicBlockDetection]:
        """
        spot 추가 대상 블록 찾기

        현재 블록 타입(N)에 대해, 직전 블록 타입(N-1)을 찾아서
        D-1일 또는 D-2일에 시작했는지 확인.

        Args:
            current_block_type: 현재 블록 타입 (예: 2 for Block2)
            current_date: 현재 날짜 (D)
            active_blocks_map: 활성 블록 맵
            context: 평가 컨텍스트

        Returns:
            spot 추가 대상 블록 (조건 불만족 시 None)

        조건:
        1. 직전 블록(N-1)이 존재하고 active 상태
        2. spot2가 아직 없음 (최대 2개 제한)
        3. 직전 블록 시작일이 D-1일 또는 D-2일
           → candles_between(prev_block.started_at, current_date) == 2 또는 3
        """
        # 직전 블록 타입 (Block2 → Block1)
        prev_block_type = current_block_type - 1

        if prev_block_type < 1:
            # Block1보다 이전은 없음
            return None

        # 직전 타입의 블록 찾기
        prev_block = None
        for block_id, block in active_blocks_map.items():
            if block.block_type == prev_block_type and block.is_active():
                prev_block = block
                break

        if prev_block is None:
            # 직전 블록이 없거나 active가 아님
            return None

        # spot2가 이미 있으면 제외
        if prev_block.has_spot2():
            return None

        # D-1, D-2 체크: candles_between 사용
        # candles_between은 시작일과 종료일을 포함하여 계산
        # prev_block.started_at = Day 10
        # current_date = Day 11 → candles_between = 2 (Day 10, Day 11)
        # current_date = Day 12 → candles_between = 3 (Day 10, Day 11, Day 12)
        from src.domain.entities.conditions.builtin_functions import candles_between

        try:
            days_diff = candles_between(prev_block.started_at, current_date, context)

            # D+1 또는 D+2 (candles_between = 2 또는 3)
            if days_diff == 2 or days_diff == 3:
                logger.debug(
                    f"Found previous block for spot",
                    context={
                        'prev_block_id': prev_block.block_id,
                        'prev_block_type': prev_block.block_type,
                        'prev_block_started_at': prev_block.started_at,
                        'current_date': current_date,
                        'days_diff': days_diff
                    }
                )
                return prev_block

        except Exception as e:
            logger.error(
                "candles_between calculation failed in spot check",
                context={
                    'prev_block_id': prev_block.block_id,
                    'prev_block_started_at': prev_block.started_at,
                    'current_date': current_date
                },
                exc=e
            )

        return None

    def _get_previous_block_from_context(
        self,
        node: BlockNode,
        context: dict,
        active_blocks_map: Dict[str, DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        spot_condition에서 참조한 이전 블록을 context에서 추출

        spot_condition 예: "is_spot_candidate('block1', 1, 2)"
        → 'block1'을 추출하여 context['block1'] 반환

        Args:
            node: 현재 블록 노드
            context: 평가 컨텍스트
            active_blocks_map: 활성 블록 맵

        Returns:
            이전 블록 객체 (없으면 None)
        """
        if not node.spot_condition:
            return None

        # spot_condition expression에서 block_id 추출
        # 예: "is_spot_candidate('block1', 1, 2)" → 'block1'
        # 예: "is_continuation_spot('block1', 1, 2)" → 'block1'
        import re
        # 일반화된 패턴 (함수명 관계없이 첫 번째 문자열 인자 추출)
        match = re.search(r"\(['\"](\w+)['\"]", node.spot_condition.expression)

        if not match:
            logger.warning(
                "Failed to extract prev_block_id from spot_condition",
                context={
                    'node_id': node.block_id,
                    'spot_condition': node.spot_condition.expression
                }
            )
            return None

        prev_block_id = match.group(1)

        # context에서 블록 조회
        prev_block = context.get(prev_block_id)

        if prev_block is None:
            logger.warning(
                "Previous block not found in context",
                context={
                    'node_id': node.block_id,
                    'prev_block_id': prev_block_id
                }
            )
            return None

        return prev_block

    def _check_forward_spots(
        self,
        active_blocks_map: Dict[str, DynamicBlockDetection],
        current_date: date,
        context: dict
    ) -> None:
        """
        Forward Spot 체크 (NEW - 2025-10-26)

        Active 블록의 forward_spot_condition을 평가하여
        D+1, D+2일에 spot 조건을 만족하면 spot을 추가합니다.

        Args:
            active_blocks_map: 활성 블록 맵 (block_id -> DynamicBlockDetection)
            current_date: 현재 날짜
            context: 평가 컨텍스트
        """
        for block_id, block in active_blocks_map.items():
            # Active 블록만 체크
            if block.status != BlockStatus.ACTIVE:
                continue

            # BlockNode 조회
            node = self.block_graph.get_node(block_id)
            if not node:
                continue

            # forward_spot_condition이 정의되어 있는가?
            if not node.forward_spot_condition:
                continue

            # spot_entry_conditions가 정의되어 있는가?
            if not node.spot_entry_conditions:
                logger.debug(
                    "forward_spot_condition defined but spot_entry_conditions missing",
                    context={
                        'block_id': block_id,
                        'date': current_date
                    }
                )
                continue

            # check_day를 Block 시작일 데이터로 설정
            # spot_entry_conditions에서 check_day.high를 사용할 수 있도록
            all_stocks = context.get('all_stocks', [])
            started_at_stock = None
            for stock in all_stocks:
                if stock.date == block.started_at:
                    started_at_stock = stock
                    break

            if not started_at_stock:
                logger.debug(
                    "Started at stock not found for forward spot check",
                    context={
                        'block_id': block_id,
                        'started_at': block.started_at,
                        'current_date': current_date
                    }
                )
                continue

            # check_day 설정
            context['check_day'] = started_at_stock

            # forward_spot_condition 평가
            try:
                forward_condition_met = self._evaluate_condition(
                    node.forward_spot_condition,
                    context
                )
            except Exception as e:
                logger.error(
                    "Forward spot condition evaluation failed",
                    context={
                        'block_id': block_id,
                        'date': current_date,
                        'expression': node.forward_spot_condition.expression,
                        'error': str(e)
                    }
                )
                continue

            if not forward_condition_met:
                continue

            # spot_entry_conditions 평가
            try:
                all_spot_conditions_met = self._evaluate_all_conditions(
                    node.spot_entry_conditions,
                    context
                )
            except Exception as e:
                logger.error(
                    "Spot entry conditions evaluation failed",
                    context={
                        'block_id': block_id,
                        'date': current_date,
                        'error': str(e)
                    }
                )
                continue

            if not all_spot_conditions_met:
                logger.debug(
                    "Forward spot condition met but spot_entry_conditions not satisfied",
                    context={
                        'block_id': block_id,
                        'date': current_date
                    }
                )
                continue

            # Spot 추가 (중복 방지)
            if block.spot1_date is None:
                block.set_spot1(current_date)
                logger.info(
                    "Forward spot1 added",
                    context={
                        'block_id': block_id,
                        'block_type': block.block_type,
                        'started_at': block.started_at,
                        'spot1_date': current_date
                    }
                )
            elif block.spot2_date is None:
                block.set_spot2(current_date)
                logger.info(
                    "Forward spot2 added",
                    context={
                        'block_id': block_id,
                        'block_type': block.block_type,
                        'started_at': block.started_at,
                        'spot2_date': current_date
                    }
                )
            else:
                logger.debug(
                    "Forward spot already full (spot1 and spot2)",
                    context={
                        'block_id': block_id,
                        'spot1_date': block.spot1_date,
                        'spot2_date': block.spot2_date,
                        'current_date': current_date
                    }
                )
