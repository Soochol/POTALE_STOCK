"""
Redetection Detector Service

재탐지 이벤트 탐지 서비스
"""
from datetime import date
from typing import Optional, Dict, Any

from loguru import logger

from src.domain.entities.block_graph import BlockNode
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock
from src.domain.entities.detections import DynamicBlockDetection, RedetectionEvent, BlockStatus


class RedetectionDetector:
    """
    재탐지 이벤트 탐지 서비스

    책임:
    1. 각 Seed Block의 재탐지 진입/종료 감지
    2. 한 번에 1개 재탐지만 active 보장
    3. Expression 기반 조건 평가

    아키텍처:
        - Domain Service (Application Layer)
        - ExpressionEngine 사용하여 동적 조건 평가
        - DynamicBlockDetection에 RedetectionEvent 추가

    Example:
        >>> detector = RedetectionDetector(expression_engine)
        >>> redetection = detector.detect_redetections(
        ...     block=block1,
        ...     block_node=block_node,
        ...     current=stock,
        ...     context={...}
        ... )
    """

    def __init__(self, expression_engine: ExpressionEngine):
        """
        초기화

        Args:
            expression_engine: 조건 평가 엔진
        """
        self.expression_engine = expression_engine

    def detect_redetections(
        self,
        block: DynamicBlockDetection,
        block_node: BlockNode,
        current: Stock,
        context: dict
    ) -> Optional[RedetectionEvent]:
        """
        현재 캔들에서 재탐지 이벤트 감지

        프로세스:
        1. 재탐지 설정 확인
        2. Active 재탐지 있으면 → 종료 조건 체크
        3. Active 재탐지 없으면 → 진입 조건 체크 → 새 재탐지 시작

        Args:
            block: 대상 Seed Block
            block_node: 블록 노드 정의 (YAML)
            current: 현재 주가 데이터
            context: 평가 컨텍스트

        Returns:
            새로 시작되거나 업데이트된 재탐지 이벤트 (없으면 None)

        Example:
            >>> redet = detector.detect_redetections(block1, node, stock, ctx)
            >>> if redet and redet.is_active():
            ...     print(f"Active redetection #{redet.sequence}")
        """
        # 재진입 설정 없으면 스킵
        if not block_node.has_reentry():
            return None

        # 현재 active 재탐지 확인
        active_redet = block.get_active_redetection()

        if active_redet:
            # Active 재탐지가 있으면 → 종료 조건 체크
            self._check_exit_conditions(
                redetection=active_redet,
                block_node=block_node,
                current=current,
                context=context
            )

            # Peak 업데이트
            if active_redet.is_active():
                active_redet.update_peak(current.high, current.volume)

            return active_redet

        else:
            # Active 재탐지 없으면 → 진입 조건 체크
            if not block.can_start_redetection():
                return None  # Seed Block이 아직 완료 안됨

            # 재탐지 진입 조건 평가
            if self._evaluate_entry_conditions(
                block_node=block_node,
                parent_block=block,
                current=current,
                context=context
            ):
                # 새 재탐지 시작
                sequence = block.get_redetection_count() + 1
                redetection = RedetectionEvent(
                    sequence=sequence,
                    parent_block_id=block.block_id,
                    started_at=current.date,
                    peak_price=current.high,
                    peak_volume=current.volume,
                    status=BlockStatus.ACTIVE
                )
                block.add_redetection(redetection)

                logger.info(
                    f"Redetection started: {block.block_id} #{sequence}",
                    extra={
                        'ticker': block.ticker,
                        'block_id': block.block_id,
                        'redetection_sequence': sequence,
                        'started_at': str(current.date)
                    }
                )

                return redetection

        return None

    def _evaluate_entry_conditions(
        self,
        block_node: BlockNode,
        parent_block: DynamicBlockDetection,
        current: Stock,
        context: dict
    ) -> bool:
        """
        재탐지 진입 조건 평가

        Args:
            block_node: 블록 노드 정의
            parent_block: 원래 Seed Block
            current: 현재 주가 데이터
            context: 평가 컨텍스트

        Returns:
            모든 조건 만족하면 True

        Example:
            >>> satisfied = detector._evaluate_entry_conditions(...)
        """
        if not block_node.reentry_entry_conditions:
            return False

        # Context에 parent_block 추가
        redet_context = {
            **context,
            'parent_block': parent_block,  # 원래 Seed Block 참조
            f'{parent_block.block_id}': parent_block  # block1, block2 등으로도 접근 가능
        }

        # 모든 진입 조건 평가
        for condition_expr in block_node.reentry_entry_conditions:
            try:
                if not condition_expr.evaluate(self.expression_engine, redet_context):
                    return False
            except Exception as e:
                logger.warning(
                    f"Redetection entry condition evaluation failed: {condition_expr}\nError: {str(e)}",
                    extra={
                        'block_id': parent_block.block_id,
                        'expression': condition_expr,
                        'error': str(e)
                    }
                )
                return False

        return True

    def _check_exit_conditions(
        self,
        redetection: RedetectionEvent,
        block_node: BlockNode,
        current: Stock,
        context: dict
    ) -> None:
        """
        재탐지 종료 조건 체크

        종료 조건 만족 시 재탐지를 completed 상태로 변경.

        Args:
            redetection: 현재 active 재탐지
            block_node: 블록 노드 정의
            current: 현재 주가 데이터
            context: 평가 컨텍스트

        Example:
            >>> detector._check_exit_conditions(redet, node, stock, ctx)
        """
        if not block_node.reentry_exit_conditions:
            return  # 종료 조건 없으면 스킵

        # Context에 active_redetection 추가
        redet_context = {
            **context,
            'active_redetection': redetection
        }

        # 종료 조건 평가 (OR 조건: 하나라도 만족하면 종료)
        for condition_expr in block_node.reentry_exit_conditions:
            try:
                if condition_expr.evaluate(self.expression_engine, redet_context):
                    # 종료 조건 만족 → 재탐지 종료
                    redetection.complete(current.date)

                    logger.info(
                        f"Redetection completed: {redetection.parent_block_id} #{redetection.sequence}",
                        extra={
                            'parent_block_id': redetection.parent_block_id,
                            'redetection_sequence': redetection.sequence,
                            'started_at': str(redetection.started_at),
                            'ended_at': str(redetection.ended_at),
                            'exit_condition': condition_expr
                        }
                    )
                    return  # 종료 처리 완료

            except Exception as e:
                logger.warning(
                    f"Redetection exit condition evaluation failed: {condition_expr}\nError: {str(e)}",
                    extra={
                        'redetection_sequence': redetection.sequence,
                        'expression': condition_expr,
                        'error': str(e)
                    }
                )

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"RedetectionDetector(engine={self.expression_engine})"
