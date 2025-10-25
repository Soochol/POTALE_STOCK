"""
SpotStrategy - Spot 판정 전략 패턴

블록 진입 조건이 만족되었을 때, 새 블록을 생성할지 아니면
기존 블록에 spot을 추가할지 결정하는 전략 인터페이스.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
import re

from src.domain.entities.block_graph import BlockNode
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.conditions import ExpressionEngine
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class SpotStrategy(ABC):
    """
    Spot 판정 전략 인터페이스

    새 블록 생성 대신 기존 블록에 spot을 추가할지 결정하는 전략.
    """

    @abstractmethod
    def should_add_spot(
        self,
        current_node: BlockNode,
        context: dict,
        active_blocks: Dict[str, DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        Spot 추가 여부 판정

        Args:
            current_node: 현재 블록 노드 (진입 조건 만족)
            context: 평가 컨텍스트
            active_blocks: 활성 블록 맵 (block_id → DynamicBlockDetection)

        Returns:
            Spot을 추가할 대상 블록 (없으면 None)
            None 반환 시 새 블록 생성
        """
        pass


class ExpressionBasedSpotStrategy(SpotStrategy):
    """
    Expression 기반 Spot 전략

    spot_condition을 평가하여 spot 추가 여부 결정.
    is_spot_candidate, is_continuation_spot 등 모든 함수 지원.
    """

    def __init__(self, expression_engine: ExpressionEngine):
        """
        Args:
            expression_engine: ExpressionEngine 인스턴스
        """
        self.expression_engine = expression_engine

    def should_add_spot(
        self,
        current_node: BlockNode,
        context: dict,
        active_blocks: Dict[str, DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        spot_condition 평가하여 spot 추가 대상 블록 반환

        Returns:
            Spot 추가 대상 블록 (조건 불만족 시 None)
        """
        # spot_condition이 없으면 None
        if not current_node.spot_condition:
            return None

        try:
            # Condition 객체의 evaluate() 사용
            is_spot = current_node.spot_condition.evaluate(
                self.expression_engine,
                context
            )

            if not is_spot:
                return None

            # spot_condition expression에서 이전 블록 ID 추출
            prev_block_id = self._extract_prev_block_id(
                current_node.spot_condition.expression
            )

            if not prev_block_id:
                logger.warning(
                    "Failed to extract prev_block_id from spot_condition",
                    context={
                        'node_id': current_node.block_id,
                        'spot_condition': current_node.spot_condition.expression
                    }
                )
                return None

            # Context에서 이전 블록 조회
            prev_block = context.get(prev_block_id)

            if not prev_block:
                logger.warning(
                    "Previous block not found in context",
                    context={
                        'node_id': current_node.block_id,
                        'prev_block_id': prev_block_id
                    }
                )
                return None

            return prev_block

        except Exception as e:
            logger.error(
                "spot_condition evaluation failed",
                context={
                    'node_id': current_node.block_id,
                    'spot_condition': current_node.spot_condition.expression
                },
                exc=e
            )
            return None

    def _extract_prev_block_id(self, expression: str) -> Optional[str]:
        """
        Expression에서 이전 블록 ID 추출

        일반화된 패턴으로 함수명에 관계없이 첫 번째 문자열 인자 추출.

        Examples:
            >>> _extract_prev_block_id("is_spot_candidate('block1', 1, 2)")
            'block1'
            >>> _extract_prev_block_id("is_continuation_spot('block2', 1, 2)")
            'block2'

        Args:
            expression: spot_condition expression

        Returns:
            이전 블록 ID (추출 실패 시 None)
        """
        # 첫 번째 문자열 인자 추출 (함수명 무관)
        match = re.search(r"\(['\"](\w+)['\"]", expression)
        return match.group(1) if match else None


class ContinuationSpotStrategy(SpotStrategy):
    """
    Continuation Spot 전략 (회고적 Spot 추가)

    Block2 조건 만족 시 D-1, D-2일을 회고적으로 검사하여
    spot_entry_conditions 만족 여부 확인 후 spot1, spot2 추가.

    D-1, D-2 둘 다 만족 시 D-1 우선.
    """

    def __init__(self, expression_engine: ExpressionEngine):
        """
        Args:
            expression_engine: ExpressionEngine 인스턴스
        """
        self.expression_engine = expression_engine

    def should_add_spot(
        self,
        current_node: BlockNode,
        context: dict,
        active_blocks: Dict[str, DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        회고적 spot 평가하여 대상 블록 반환

        Returns:
            Spot 추가 대상 블록 (조건 불만족 시 None)
        """
        # spot_condition이 없으면 None
        if not current_node.spot_condition:
            return None

        # spot_entry_conditions가 없으면 None (필수)
        if not current_node.spot_entry_conditions:
            logger.warning(
                "spot_entry_conditions not defined for continuation spot",
                context={
                    'node_id': current_node.block_id,
                    'spot_condition': current_node.spot_condition.expression
                }
            )
            return None

        try:
            # spot_condition 평가 (is_continuation_spot 함수)
            is_continuation = current_node.spot_condition.evaluate(
                self.expression_engine,
                context
            )

            if not is_continuation:
                return None

            # 이전 블록 ID 추출
            prev_block_id = self._extract_prev_block_id(
                current_node.spot_condition.expression
            )

            if not prev_block_id:
                return None

            # Context에서 이전 블록 조회
            prev_block = context.get(prev_block_id)

            if not prev_block or not prev_block.is_active():
                return None

            # D-1, D-2일 데이터로 spot_entry_conditions 평가
            all_stocks = context.get('all_stocks', [])
            current_date = context.get('current').date

            # 현재 날짜의 인덱스 찾기
            current_index = None
            for i, stock in enumerate(all_stocks):
                if stock.date == current_date:
                    current_index = i
                    break

            if current_index is None or current_index < 2:
                # 데이터 부족
                return None

            # D-1, D-2일 체크
            d_minus_1_satisfied = self._check_spot_entry_conditions(
                current_node,
                all_stocks,
                current_index - 1
            )

            d_minus_2_satisfied = self._check_spot_entry_conditions(
                current_node,
                all_stocks,
                current_index - 2
            )

            if not (d_minus_1_satisfied or d_minus_2_satisfied):
                # 조건 불만족
                return None

            # Spot 추가 (D-1 우선)
            spot1_index = current_index - 1 if d_minus_1_satisfied else current_index - 2
            spot1_stock = all_stocks[spot1_index]

            # spot1 추가
            prev_block.add_spot(
                spot_date=spot1_stock.date,
                open_price=spot1_stock.open,
                close_price=spot1_stock.close,
                high_price=spot1_stock.high,
                low_price=spot1_stock.low,
                volume=spot1_stock.volume
            )

            # spot2 추가 (D일 = 현재)
            current_stock = context.get('current')
            prev_block.add_spot(
                spot_date=current_stock.date,
                open_price=current_stock.open,
                close_price=current_stock.close,
                high_price=current_stock.high,
                low_price=current_stock.low,
                volume=current_stock.volume
            )

            logger.info(
                f"Added retrospective spots to {prev_block.block_id}",
                context={
                    'prev_block_id': prev_block.block_id,
                    'spot1_date': spot1_stock.date,
                    'spot2_date': current_stock.date,
                    'd_minus_1_satisfied': d_minus_1_satisfied,
                    'd_minus_2_satisfied': d_minus_2_satisfied
                }
            )

            return prev_block

        except Exception as e:
            logger.error(
                "ContinuationSpotStrategy evaluation failed",
                context={
                    'node_id': current_node.block_id,
                    'spot_condition': current_node.spot_condition.expression
                },
                exc=e
            )
            return None

    def _extract_prev_block_id(self, expression: str) -> Optional[str]:
        """Expression에서 이전 블록 ID 추출"""
        match = re.search(r"\(['\"](\w+)['\"]", expression)
        return match.group(1) if match else None

    def _check_spot_entry_conditions(
        self,
        node: BlockNode,
        all_stocks: list,
        stock_index: int
    ) -> bool:
        """
        특정 날짜의 데이터로 spot_entry_conditions 평가

        Args:
            node: BlockNode
            all_stocks: 전체 주가 데이터
            stock_index: 평가할 날짜의 인덱스

        Returns:
            모든 spot_entry_conditions 만족 시 True
        """
        if stock_index < 0 or stock_index >= len(all_stocks):
            return False

        stock = all_stocks[stock_index]

        # Context 구성 (해당 날짜 기준)
        prev_stock = all_stocks[stock_index - 1] if stock_index > 0 else None
        temp_context = {
            'current': stock,
            'prev': prev_stock,
            'all_stocks': all_stocks[:stock_index + 1]
        }

        # 모든 spot_entry_conditions 평가 (AND 조건)
        try:
            for condition in node.spot_entry_conditions:
                result = condition.evaluate(self.expression_engine, temp_context)
                if not result:
                    return False
            return True
        except Exception as e:
            logger.error(
                "spot_entry_conditions evaluation failed",
                context={
                    'node_id': node.block_id,
                    'stock_date': stock.date,
                    'stock_index': stock_index
                },
                exc=e
            )
            return False


class CompositeSpotStrategy(SpotStrategy):
    """
    Composite Spot 전략 (Chain of Responsibility)

    여러 SpotStrategy를 순서대로 시도하여 첫 번째로 성공하는 전략 사용.
    ContinuationSpotStrategy → ExpressionBasedSpotStrategy → FallbackSpotStrategy 순서로 시도.
    """

    def __init__(self, expression_engine: ExpressionEngine):
        """
        Args:
            expression_engine: ExpressionEngine 인스턴스
        """
        self.strategies = [
            ContinuationSpotStrategy(expression_engine),
            ExpressionBasedSpotStrategy(expression_engine),
            FallbackSpotStrategy()
        ]

    def should_add_spot(
        self,
        current_node: BlockNode,
        context: dict,
        active_blocks: Dict[str, DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        순서대로 전략 시도하여 첫 번째 성공한 결과 반환

        Returns:
            Spot 추가 대상 블록 (모든 전략 실패 시 None)
        """
        for strategy in self.strategies:
            result = strategy.should_add_spot(current_node, context, active_blocks)
            if result is not None:
                return result

        return None


class FallbackSpotStrategy(SpotStrategy):
    """
    Fallback Spot 전략

    spot_condition이 없을 때 사용하는 기본 전략.
    block_type - 1 기반으로 직전 블록 찾기.
    """

    def should_add_spot(
        self,
        current_node: BlockNode,
        context: dict,
        active_blocks: Dict[str, DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        block_type 기반으로 직전 블록에 spot 추가

        Returns:
            Spot 추가 대상 블록 (조건 불만족 시 None)
        """
        # 직전 블록 타입 (Block2 → Block1)
        prev_block_type = current_node.block_type - 1

        if prev_block_type < 1:
            # Block1보다 이전은 없음
            return None

        # 직전 타입의 활성 블록 찾기
        for block in active_blocks.values():
            if block.block_type == prev_block_type and block.is_active():
                # spot2가 이미 있으면 제외
                if not block.has_spot2():
                    return block

        return None
