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
        expression_engine: ExpressionEngine
    ):
        """
        Args:
            block_graph: 블록 그래프 정의
            expression_engine: 표현식 평가 엔진
        """
        self.block_graph = block_graph
        self.expression_engine = expression_engine

    def detect_blocks(
        self,
        ticker: str,
        stocks: List[Stock],
        condition_name: str = "seed",
        active_blocks: Optional[List[DynamicBlockDetection]] = None
    ) -> List[DynamicBlockDetection]:
        """
        주가 데이터에서 블록 감지

        Args:
            ticker: 종목 코드
            stocks: 주가 데이터 리스트 (시간순 정렬)
            condition_name: 조건 이름 ("seed" 또는 "redetection")
            active_blocks: 진행 중인 블록 리스트 (None이면 빈 리스트)

        Returns:
            감지된 블록 리스트 (신규 + 업데이트된 기존 블록)
        """
        if active_blocks is None:
            active_blocks = []

        # 블록을 block_id로 매핑 (모든 블록 포함, 완료된 블록도 추적)
        active_blocks_map = {b.block_id: b for b in active_blocks}

        # 주가 데이터 순회
        for i, current_stock in enumerate(stocks):
            # 이전 주가
            prev_stock = stocks[i - 1] if i > 0 else None

            # Context 구성
            context = self._build_context(
                current=current_stock,
                prev=prev_stock,
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
                active_blocks_map=active_blocks_map
            )

            # 2. 새로운 블록을 active_blocks_map에 추가
            for new_block in new_blocks:
                active_blocks_map[new_block.block_id] = new_block

            # 3. Context 재구성 (새로 추가된 블록 포함)
            if new_blocks:
                context = self._build_context(
                    current=current_stock,
                    prev=prev_stock,
                    all_stocks=stocks[:i + 1],
                    active_blocks=active_blocks_map
                )

            # 4. 진행 중인 블록 종료 조건 확인
            # 새 블록이 추가되었으므로 EXISTS() 조건이 올바르게 평가됨
            self._check_and_complete_blocks(
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

    def _build_context(
        self,
        current: Stock,
        prev: Optional[Stock],
        all_stocks: List[Stock],
        active_blocks: Dict[str, DynamicBlockDetection]
    ) -> dict:
        """
        표현식 평가를 위한 context 구성

        Args:
            current: 현재 주가
            prev: 이전 주가 (None 가능)
            all_stocks: 전체 주가 데이터
            active_blocks: 진행 중인 블록 맵 (block_id → DynamicBlockDetection)

        Returns:
            Context 딕셔너리
        """
        context = {
            'current': current,
            'prev': prev,
            'all_stocks': all_stocks,
        }

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
        context: dict
    ) -> None:
        """
        진행 중인 블록의 종료 조건 확인 및 완료 처리

        Peak 갱신은 하지 않고, 종료 조건만 체크합니다.
        새 블록이 감지된 후 호출되어 EXISTS() 조건을 올바르게 평가합니다.

        Args:
            active_blocks_map: 진행 중인 블록 맵
            current_date: 현재 날짜
            context: 평가 context
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
            if self._check_exit_conditions(node, context):
                blocks_to_complete.append(block_id)

        # 종료 조건을 만족한 블록들 완료 처리
        for block_id in blocks_to_complete:
            block = active_blocks_map[block_id]
            block.complete(current_date)

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
        active_blocks_map: Dict[str, DynamicBlockDetection]
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
            active_blocks_map: 진행 중인 블록 맵

        Returns:
            신규 감지된 블록 리스트
        """
        new_blocks = []

        # 모든 노드에 대해 진입 조건 확인
        for node_id, node in self.block_graph.nodes.items():
            # 이미 진행 중인 블록은 스킵
            if node_id in active_blocks_map:
                continue

            # 진입 조건 확인 (AND 조건)
            if self._check_entry_conditions(node, context):
                # 새 블록 생성
                new_block = DynamicBlockDetection(
                    block_id=node.block_id,
                    block_type=node.block_type,
                    ticker=ticker,
                    condition_name=condition_name
                )

                new_block.start(current_date)
                new_block.update_peak(current_date, current_price, current_volume)

                # 부모 블록 연결 (엣지 기반)
                parent_nodes = self.block_graph.get_parents(node_id)
                for parent_node in parent_nodes:
                    if parent_node.block_id in active_blocks_map:
                        parent_block = active_blocks_map[parent_node.block_id]
                        if parent_block.id is not None:
                            new_block.add_parent_block(parent_block.id)

                new_blocks.append(new_block)

        return new_blocks

    def _check_entry_conditions(
        self,
        node: BlockNode,
        context: dict
    ) -> bool:
        """
        진입 조건 확인 (AND 조건 - 모든 조건을 만족해야 함)

        Args:
            node: 블록 노드
            context: 평가 context

        Returns:
            모든 조건을 만족하면 True
        """
        if not node.entry_conditions:
            return False

        try:
            for condition_expr in node.entry_conditions:
                result = self.expression_engine.evaluate(condition_expr, context)

                # 결과가 False이면 즉시 False 반환
                if not result:
                    return False

            # 모든 조건이 True
            return True

        except Exception as e:
            # 평가 중 에러 발생 시 False
            print(f"  [ERROR] Entry condition evaluation failed for {node.block_id}: {e}")
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

        except Exception:
            # 평가 중 에러 발생 시 False
            return False

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
                except Exception:
                    return False

            # 조건부가 아니면 전이 가능
            return True

        # 해당 엣지가 없으면 전이 불가
        return False
