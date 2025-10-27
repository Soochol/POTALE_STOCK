"""
SpotStrategy - Spot 판정 전략 패턴

블록 진입 조건이 만족되었을 때, 새 블록을 생성할지 아니면
기존 블록에 spot을 추가할지 결정하는 전략 인터페이스.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import date
import re

from src.domain.entities.block_graph import BlockNode
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.conditions import ExpressionEngine
from src.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EarlyStartInfo:
    """
    Early Start Spot 정보

    Block2 조건이 D일에 만족되었지만, D-1 또는 D-2일부터
    조건이 만족되어 시작일을 앞당기는 경우의 정보.
    """
    early_start_date: date  # 조기 시작일 (D-1 또는 D-2)
    spot1_date: date  # spot1 날짜 (= early_start_date)
    spot2_date: date  # spot2 날짜 (= D, 원래 감지된 날짜)
    spot1_data: dict  # spot1의 OHLCV 데이터
    spot2_data: dict  # spot2의 OHLCV 데이터
    prev_block_id: str  # 이전 블록 ID (종료 처리용)


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
    is_backward_spot, is_levelup_spot 등 모든 함수 지원.
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
            >>> _extract_prev_block_id("is_backward_spot('block1', -1, -2)")
            'block1'
            >>> _extract_prev_block_id("is_levelup_spot('block2', 1, 2)")
            'block2'

        Args:
            expression: spot_condition expression

        Returns:
            이전 블록 ID (추출 실패 시 None)
        """
        # 첫 번째 문자열 인자 추출 (함수명 무관)
        match = re.search(r"\(['\"](\w+)['\"]", expression)
        return match.group(1) if match else None


class StaySpotStrategy(SpotStrategy):
    """
    Stay Spot 전략 (회고적 Spot 추가, 블록 유지)

    다음 블록 조건 만족 시 D-1, D-2일을 회고적으로 검사하여
    spot_entry_conditions 만족 여부 확인 후 현재 블록에 spot1, spot2 추가.
    다음 블록으로 전환하지 않고 현재 블록 유지.

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
            # spot_condition 평가 (is_backward_spot 함수)
            should_stay = current_node.spot_condition.evaluate(
                self.expression_engine,
                context
            )

            if not should_stay:
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
            detection_day_stock = context.get('current')  # D일 데이터
            current_date = detection_day_stock.date

            # 현재 날짜의 인덱스 찾기
            current_index = None
            for i, stock in enumerate(all_stocks):
                if stock.date == current_date:
                    current_index = i
                    break

            # 파라미터 기반 동적 범위 추출 (음수 오프셋)
            offset_start, offset_end = self._extract_days_range(
                current_node.spot_condition.expression
            )

            # 데이터 부족 체크 (최소 abs(offset_start)만큼 필요)
            if current_index is None or current_index < abs(offset_start):
                return None

            # 동적 범위 체크 (D+offset_start ~ D+offset_end)
            # 우선순위: D-1 > D-2 > D-3 > ... (먼저 만족하는 날짜 선택)
            # offset_start=-1, offset_end=-2 → range(-1, -3, -1) → [-1, -2]
            spot1_index = None
            for offset in range(offset_start, offset_end - 1, -1):
                check_index = current_index + offset  # offset이 음수이므로 +

                # 인덱스 범위 체크
                if check_index < 0 or check_index >= len(all_stocks):
                    continue

                # spot_entry_conditions 평가
                if self._check_spot_entry_conditions(
                    current_node,
                    all_stocks,
                    check_index,
                    detection_day_stock
                ):
                    spot1_index = check_index
                    break  # 첫 번째 만족하는 날짜 선택

            # 어떤 날짜도 조건 만족 안 함
            if spot1_index is None:
                return None

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

            # spot1이 D일로부터 며칠 전인지 계산
            days_offset = current_index - spot1_index

            logger.info(
                f"Added retrospective spots to {prev_block.block_id}",
                context={
                    'prev_block_id': prev_block.block_id,
                    'spot1_date': spot1_stock.date,
                    'spot2_date': current_stock.date,
                    'spot1_offset': f'D{days_offset}',  # D-1, D-2, ...
                    'offset_range': f'{offset_start}~{offset_end}'
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

    def _extract_days_range(self, expression: str) -> tuple[int, int]:
        """
        Expression에서 offset_start, offset_end 추출 (음수 오프셋)

        Args:
            expression: spot_condition 표현식
                예: "is_backward_spot('block1', -1, -2)"  # D-1, D-2 체크
                예: "is_backward_spot('block1', -1, -5)"  # D-1~D-5 체크

        Returns:
            (offset_start, offset_end) 튜플 (음수)
            예: (-1, -2) → D-1, D-2 체크
            예: (-1, -5) → D-1~D-5 체크

        Note:
            파싱 실패 시 기본값 (-1, -2) 반환
        """
        # 정규식: is_xxx_spot('block_id', offset_start, offset_end)
        # 음수를 포함한 정수 파싱
        match = re.search(r"is_\w+_spot\(['\"](\w+)['\"]\s*,\s*(-?\d+)\s*,\s*(-?\d+)\)", expression)
        if match:
            offset_start = int(match.group(2))
            offset_end = int(match.group(3))
            return offset_start, offset_end

        # 기본값: D-1, D-2
        return -1, -2

    def _check_spot_entry_conditions(
        self,
        node: BlockNode,
        all_stocks: list,
        stock_index: int,
        detection_day_stock=None
    ) -> bool:
        """
        특정 날짜의 데이터로 spot_entry_conditions 평가

        Args:
            node: BlockNode
            all_stocks: 전체 주가 데이터
            stock_index: 평가할 날짜의 인덱스 (D-1 또는 D-2)
            detection_day_stock: 원래 탐지일(D일) 데이터

        Returns:
            모든 spot_entry_conditions 만족 시 True
        """
        if stock_index < 0 or stock_index >= len(all_stocks):
            return False

        check_day_stock = all_stocks[stock_index]  # D-1 또는 D-2 (검사일)

        # Context 구성 (직관적인 변수명)
        # current: D일 (탐지일), check_day: 검사일, check_day_prev: 검사일 전날
        check_day_prev_stock = all_stocks[stock_index - 1] if stock_index > 0 else None
        temp_context = {
            'current': detection_day_stock,  # D일 (탐지일)
            'check_day': check_day_stock,  # D-1 또는 D-2 (검사일)
            'check_day_prev': check_day_prev_stock,  # D-2 또는 D-3 (검사일 전날)
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


class LevelupSpotStrategy(SpotStrategy):
    """
    Levelup Spot 전략 (블록 전환, 조기 시작)

    다음 블록 조건 만족 시 D-1, D-2일을 회고적으로 검사하여
    조건 만족 시 다음 블록을 생성하되 시작일을 앞당깁니다.
    (Block1 → Block2 전환, "레벨업")

    StaySpot과의 차이:
    - StaySpot: Block1에 spot 추가, Block2 생성 안 함 (블록 유지)
    - LevelupSpot: Block2 생성하되 started_at을 D-1 또는 D-2로 조정 (블록 전환)

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
        Early start 평가 (항상 None 반환, context에 early_start_info 저장)

        Returns:
            항상 None (새 블록 생성 허용)
            Side effect: context['_early_start_info'] = EarlyStartInfo(...)
        """
        # spot_condition이 없으면 None
        if not current_node.spot_condition:
            return None

        # spot_entry_conditions가 없으면 None (필수)
        if not current_node.spot_entry_conditions:
            logger.warning(
                "spot_entry_conditions not defined for early start spot",
                context={
                    'node_id': current_node.block_id,
                    'spot_condition': current_node.spot_condition.expression
                }
            )
            return None

        try:
            # spot_condition 평가 (is_levelup_spot 함수)
            should_levelup = current_node.spot_condition.evaluate(
                self.expression_engine,
                context
            )

            if not should_levelup:
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
            detection_day_stock = context.get('current')  # D일 데이터
            current_date = detection_day_stock.date

            # 현재 날짜의 인덱스 찾기
            current_index = None
            for i, stock in enumerate(all_stocks):
                if stock.date == current_date:
                    current_index = i
                    break

            # 파라미터 기반 동적 범위 추출 (음수 오프셋)
            offset_start, offset_end = self._extract_days_range(
                current_node.spot_condition.expression
            )

            # 데이터 부족 체크 (최소 abs(offset_start)만큼 필요)
            if current_index is None or current_index < abs(offset_start):
                return None

            # 동적 범위 체크 (D+offset_start ~ D+offset_end)
            # 우선순위: D-1 > D-2 > D-3 > ... (먼저 만족하는 날짜 선택)
            # offset_start=-1, offset_end=-2 → range(-1, -3, -1) → [-1, -2]
            early_index = None
            for offset in range(offset_start, offset_end - 1, -1):
                check_index = current_index + offset  # offset이 음수이므로 +

                # 인덱스 범위 체크
                if check_index < 0 or check_index >= len(all_stocks):
                    continue

                # spot_entry_conditions 평가 (exclude_conditions 필터링)
                if self._check_spot_entry_conditions(
                    current_node,
                    all_stocks,
                    check_index,
                    current_node.exclude_conditions,
                    detection_day_stock
                ):
                    early_index = check_index
                    break  # 첫 번째 만족하는 날짜 선택

            # 어떤 날짜도 조건 만족 안 함
            if early_index is None:
                return None

            early_stock = all_stocks[early_index]
            current_stock = context.get('current')

            early_start_info = EarlyStartInfo(
                early_start_date=early_stock.date,
                spot1_date=early_stock.date,
                spot2_date=current_stock.date,
                spot1_data={
                    'open': early_stock.open,
                    'close': early_stock.close,
                    'high': early_stock.high,
                    'low': early_stock.low,
                    'volume': early_stock.volume
                },
                spot2_data={
                    'open': current_stock.open,
                    'close': current_stock.close,
                    'high': current_stock.high,
                    'low': current_stock.low,
                    'volume': current_stock.volume
                },
                prev_block_id=prev_block_id
            )

            # Context에 저장 (DynamicBlockDetector에서 읽어서 사용)
            context['_early_start_info'] = early_start_info

            # early_start가 D일로부터 며칠 전인지 계산
            days_offset = current_index - early_index

            logger.info(
                f"Early start spot detected for {current_node.block_id}",
                context={
                    'current_node_id': current_node.block_id,
                    'early_start_date': early_stock.date,
                    'spot1_date': early_stock.date,
                    'spot2_date': current_stock.date,
                    'prev_block_id': prev_block_id,
                    'early_start_offset': f'D{days_offset}',  # D-1, D-2, ...
                    'offset_range': f'{offset_start}~{offset_end}'
                }
            )

            # None 반환 (새 블록 생성 허용, 하지만 DynamicBlockDetector가 early_start_info 사용)
            return None

        except Exception as e:
            logger.error(
                "EarlyStartSpotStrategy evaluation failed",
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

    def _extract_days_range(self, expression: str) -> tuple[int, int]:
        """
        Expression에서 offset_start, offset_end 추출 (음수 오프셋)

        Args:
            expression: spot_condition 표현식
                예: "is_levelup_spot('block1', -1, -2)"  # D-1, D-2 체크
                예: "is_levelup_spot('block1', -1, -5)"  # D-1~D-5 체크

        Returns:
            (offset_start, offset_end) 튜플 (음수)
            예: (-1, -2) → D-1, D-2 체크
            예: (-1, -5) → D-1~D-5 체크

        Note:
            파싱 실패 시 기본값 (-1, -2) 반환
        """
        # 정규식: is_xxx_spot('block_id', offset_start, offset_end)
        # 음수를 포함한 정수 파싱
        match = re.search(r"is_\w+_spot\(['\"](\w+)['\"]\s*,\s*(-?\d+)\s*,\s*(-?\d+)\)", expression)
        if match:
            offset_start = int(match.group(2))
            offset_end = int(match.group(3))
            return offset_start, offset_end

        # 기본값: D-1, D-2
        return -1, -2

    def _check_spot_entry_conditions(
        self,
        node: BlockNode,
        all_stocks: list,
        stock_index: int,
        exclude_conditions: Optional[List[str]] = None,
        detection_day_stock=None
    ) -> bool:
        """
        특정 날짜의 데이터로 spot_entry_conditions 평가

        exclude_conditions에 지정된 조건은 제외하고 평가합니다.

        Args:
            node: BlockNode
            all_stocks: 전체 주가 데이터
            stock_index: 평가할 날짜의 인덱스 (D-1 또는 D-2)
            exclude_conditions: 제외할 조건 이름 리스트 (선택적)
            detection_day_stock: 원래 탐지일(D일) 데이터

        Returns:
            필터링된 spot_entry_conditions 모두 만족 시 True
        """
        if stock_index < 0 or stock_index >= len(all_stocks):
            return False

        check_day_stock = all_stocks[stock_index]  # D-1 또는 D-2 (검사일)

        # Context 구성 (직관적인 변수명)
        # current: D일 (탐지일), check_day: 검사일, check_day_prev: 검사일 전날
        check_day_prev_stock = all_stocks[stock_index - 1] if stock_index > 0 else None
        temp_context = {
            'current': detection_day_stock,  # D일 (탐지일)
            'check_day': check_day_stock,  # D-1 또는 D-2 (검사일)
            'check_day_prev': check_day_prev_stock,  # D-2 또는 D-3 (검사일 전날)
            'all_stocks': all_stocks[:stock_index + 1]
        }

        # exclude_conditions 필터링
        conditions_to_check = node.spot_entry_conditions
        if exclude_conditions:
            # 제외할 조건 이름 세트 생성
            exclude_set = set(exclude_conditions)
            # 제외되지 않은 조건만 선택
            conditions_to_check = [
                cond for cond in node.spot_entry_conditions
                if cond.name not in exclude_set
            ]

        # 필터링된 조건 평가 (AND 조건)
        try:
            for condition in conditions_to_check:
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
                    'stock_index': stock_index,
                    'exclude_conditions': exclude_conditions
                },
                exc=e
            )
            return False


class CompositeSpotStrategy(SpotStrategy):
    """
    Composite Spot 전략 (Chain of Responsibility)

    여러 SpotStrategy를 순서대로 시도하여 첫 번째로 성공하는 전략 사용.
    LevelupSpotStrategy → StaySpotStrategy → ExpressionBasedSpotStrategy → FallbackSpotStrategy 순서로 시도.
    """

    def __init__(self, expression_engine: ExpressionEngine):
        """
        Args:
            expression_engine: ExpressionEngine 인스턴스
        """
        self.strategies = [
            LevelupSpotStrategy(expression_engine),
            StaySpotStrategy(expression_engine),
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
