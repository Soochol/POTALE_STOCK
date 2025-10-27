"""
HighlightDetector - 하이라이트 블록 탐지 Application Service

패턴의 앵커 포인트가 되는 하이라이트 블록을 탐지하는 재사용 가능한 서비스.
Sequential 및 Highlight-Centric 시스템 모두에서 사용.
"""
from typing import List, Optional, Dict, Any
from datetime import date

from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.highlights import HighlightCondition
from src.domain.entities.conditions import ExpressionEngine
from src.common.logging import get_logger

logger = get_logger(__name__)


class HighlightDetector:
    """
    하이라이트 블록 탐지 Application Service

    Responsibilities:
        - 블록 리스트에서 하이라이트 조건을 만족하는 블록 식별
        - Primary vs Secondary 하이라이트 분류
        - 다양한 하이라이트 타입 지원 (forward_spot, backward_spot, etc.)

    이 서비스는 Application Layer의 재사용 가능한 모듈로,
    여러 Use Case에서 공유됨 (Clean Architecture 원칙 준수).

    Example:
        >>> detector = HighlightDetector(expression_engine)
        >>> highlights = detector.find_highlights(
        ...     blocks=[block1, block2],
        ...     highlight_condition=condition,
        ...     context={'ticker': '025980'}
        ... )
        >>> primary = detector.find_primary(highlights)
    """

    def __init__(self, expression_engine: ExpressionEngine):
        """
        Args:
            expression_engine: ExpressionEngine 인스턴스
        """
        self.expression_engine = expression_engine
        logger.debug("HighlightDetector initialized")

    def find_highlights(
        self,
        blocks: List[DynamicBlockDetection],
        highlight_condition: HighlightCondition,
        context: Dict[str, Any]
    ) -> List[DynamicBlockDetection]:
        """
        하이라이트 조건을 만족하는 블록 찾기

        Args:
            blocks: 검사할 블록 리스트
            highlight_condition: 하이라이트 조건
            context: 평가 컨텍스트 (ticker, all_stocks, etc.)

        Returns:
            하이라이트 조건을 만족하는 블록 리스트 (시작일 기준 오름차순)

        Example:
            >>> condition = HighlightCondition(
            ...     type="forward_spot",
            ...     parameters={"required_spot_count": 2}
            ... )
            >>> highlights = detector.find_highlights(blocks, condition, context)
        """
        if not highlight_condition.is_enabled():
            logger.debug("Highlight condition is disabled")
            return []

        if not blocks:
            logger.debug("No blocks to evaluate")
            return []

        logger.debug(
            f"Finding highlights with condition type: {highlight_condition.type}",
            context={
                'num_blocks': len(blocks),
                'condition_type': highlight_condition.type
            }
        )

        highlights = []

        for block in blocks:
            if self._is_highlight(block, highlight_condition, context):
                highlights.append(block)
                logger.debug(
                    f"Block identified as highlight",
                    context={
                        'block_id': block.block_id,
                        'started_at': block.started_at
                    }
                )

        # 시작일 기준 오름차순 정렬 (가장 먼저 발생한 하이라이트가 Primary)
        highlights.sort(key=lambda b: b.started_at if b.started_at else date.min)

        logger.info(
            f"Found {len(highlights)} highlight(s)",
            context={'num_highlights': len(highlights)}
        )

        return highlights

    def find_primary(
        self,
        highlights: List[DynamicBlockDetection]
    ) -> Optional[DynamicBlockDetection]:
        """
        Primary 하이라이트 반환 (가장 먼저 발생한 것)

        Args:
            highlights: 하이라이트 블록 리스트

        Returns:
            Primary 하이라이트 (없으면 None)

        Example:
            >>> primary = detector.find_primary(highlights)
            >>> if primary:
            ...     print(f"Primary highlight: {primary.block_id}")
        """
        if not highlights:
            logger.debug("No highlights to classify")
            return None

        # 첫 번째 하이라이트가 Primary (find_highlights에서 이미 정렬됨)
        primary = highlights[0]

        logger.info(
            f"Primary highlight identified",
            context={
                'block_id': primary.block_id,
                'started_at': primary.started_at
            }
        )

        return primary

    def classify_highlights(
        self,
        highlights: List[DynamicBlockDetection]
    ) -> Dict[str, List[DynamicBlockDetection]]:
        """
        하이라이트를 Primary/Secondary로 분류

        Args:
            highlights: 하이라이트 블록 리스트

        Returns:
            {'primary': [block], 'secondary': [block1, block2, ...]}

        Example:
            >>> classified = detector.classify_highlights(highlights)
            >>> primary_block = classified['primary'][0] if classified['primary'] else None
            >>> secondary_blocks = classified['secondary']
        """
        if not highlights:
            return {'primary': [], 'secondary': []}

        primary = highlights[0]
        secondary = highlights[1:] if len(highlights) > 1 else []

        logger.info(
            f"Classified highlights",
            context={
                'num_primary': 1,
                'num_secondary': len(secondary)
            }
        )

        return {
            'primary': [primary],
            'secondary': secondary
        }

    def _is_highlight(
        self,
        block: DynamicBlockDetection,
        highlight_condition: HighlightCondition,
        context: Dict[str, Any]
    ) -> bool:
        """
        블록이 하이라이트 조건을 만족하는지 확인 (내부 메서드)

        Args:
            block: 검사할 블록
            highlight_condition: 하이라이트 조건
            context: 평가 컨텍스트

        Returns:
            하이라이트 조건 만족 시 True
        """
        condition_type = highlight_condition.type

        # forward_spot 타입: spot2가 있는지 확인
        if condition_type == "forward_spot":
            required_spot_count = highlight_condition.get_parameter(
                "required_spot_count", 2
            )
            actual_spot_count = block.get_spot_count()

            logger.debug(
                f"Checking forward_spot highlight",
                context={
                    'block_id': block.block_id,
                    'required_spots': required_spot_count,
                    'actual_spots': actual_spot_count
                }
            )

            return actual_spot_count >= required_spot_count

        # backward_spot 타입: metadata의 'is_backward_spot' 플래그 확인
        elif condition_type == "backward_spot":
            is_backward = block.get_metadata('is_backward_spot', False)

            logger.debug(
                f"Checking backward_spot highlight",
                context={
                    'block_id': block.block_id,
                    'is_backward_spot': is_backward
                }
            )

            return is_backward

        # custom 타입: expression 평가
        elif condition_type == "custom":
            # TODO: custom expression 평가 로직 구현
            # 현재는 항상 False 반환 (추후 확장)
            logger.warning(
                f"Custom highlight type not yet implemented",
                context={'block_id': block.block_id}
            )
            return False

        else:
            logger.warning(
                f"Unknown highlight condition type: {condition_type}",
                context={'condition_type': condition_type}
            )
            return False

    def count_highlights(
        self,
        blocks: List[DynamicBlockDetection],
        highlight_condition: HighlightCondition,
        context: Dict[str, Any]
    ) -> int:
        """
        하이라이트 개수 반환 (블록 리스트를 반환하지 않고 개수만)

        Args:
            blocks: 검사할 블록 리스트
            highlight_condition: 하이라이트 조건
            context: 평가 컨텍스트

        Returns:
            하이라이트 개수

        Example:
            >>> count = detector.count_highlights(blocks, condition, context)
            >>> print(f"Found {count} highlights")
        """
        highlights = self.find_highlights(blocks, highlight_condition, context)
        return len(highlights)

    def has_highlight(
        self,
        blocks: List[DynamicBlockDetection],
        highlight_condition: HighlightCondition,
        context: Dict[str, Any]
    ) -> bool:
        """
        하이라이트가 존재하는지 여부만 확인 (빠른 체크)

        Args:
            blocks: 검사할 블록 리스트
            highlight_condition: 하이라이트 조건
            context: 평가 컨텍스트

        Returns:
            하이라이트가 1개 이상 존재하면 True

        Example:
            >>> if detector.has_highlight(blocks, condition, context):
            ...     print("Highlight detected!")
        """
        return self.count_highlights(blocks, highlight_condition, context) > 0
