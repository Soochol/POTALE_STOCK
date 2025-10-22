"""
Exit Condition Processor Service

블록 탐지의 종료 조건 후처리 서비스
모든 활성 블록(ended_at=None)에 대해 종료 조건 체크 및 업데이트
"""
from typing import List, Optional
from datetime import date

from src.domain.entities import (
    Stock,
    Block1Detection,
    Block2Detection,
    Block3Detection,
    Block4Detection,
)
from src.domain.entities.conditions.block_conditions import (
    Block1Condition,
    Block2Condition,
    Block3Condition,
    Block4Condition,
)
from src.application.services.checkers.block1_checker import Block1Checker
from src.application.services.checkers.block2_checker import Block2Checker
from src.application.services.checkers.block3_checker import Block3Checker
from src.application.services.checkers.block4_checker import Block4Checker
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block3_repository import Block3Repository
from src.infrastructure.repositories.detection.block4_repository import Block4Repository


class ExitConditionProcessor:
    """
    블록 탐지의 종료 조건 후처리 서비스

    Pattern Detection에서 생성된 블록들(Seed + 재탐지)의 종료 조건을 체크하고
    종료 조건이 충족된 블록의 상태를 업데이트합니다.
    """

    def __init__(
        self,
        block1_checker: Block1Checker,
        block2_checker: Block2Checker,
        block3_checker: Block3Checker,
        block4_checker: Block4Checker,
        block1_repo: Block1Repository,
        block2_repo: Block2Repository,
        block3_repo: Block3Repository,
        block4_repo: Block4Repository
    ):
        """
        ExitConditionProcessor 초기화

        Args:
            block1_checker: Block1 체커
            block2_checker: Block2 체커
            block3_checker: Block3 체커
            block4_checker: Block4 체커
            block1_repo: Block1 Repository
            block2_repo: Block2 Repository
            block3_repo: Block3 Repository
            block4_repo: Block4 Repository
        """
        self.block1_checker = block1_checker
        self.block2_checker = block2_checker
        self.block3_checker = block3_checker
        self.block4_checker = block4_checker
        self.block1_repo = block1_repo
        self.block2_repo = block2_repo
        self.block3_repo = block3_repo
        self.block4_repo = block4_repo

    def process_block1_exits(
        self,
        detections: List[Block1Detection],
        condition: Block1Condition,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block1 리스트의 종료 조건 체크 및 업데이트

        Args:
            detections: Block1 탐지 결과 리스트
            condition: Block1 조건
            all_stocks: 전체 주식 데이터 (종료 조건 체크용)

        Returns:
            종료 처리된 블록 개수
        """
        return self._process_exits(
            detections=detections,
            condition=condition,
            all_stocks=all_stocks,
            checker=self.block1_checker,
            repo=self.block1_repo,
            block_id_attr='block1_id'
        )

    def process_block2_exits(
        self,
        detections: List[Block2Detection],
        condition: Block2Condition,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block2 리스트의 종료 조건 체크 및 업데이트

        Args:
            detections: Block2 탐지 결과 리스트
            condition: Block2 조건
            all_stocks: 전체 주식 데이터

        Returns:
            종료 처리된 블록 개수
        """
        return self._process_exits(
            detections=detections,
            condition=condition,
            all_stocks=all_stocks,
            checker=self.block2_checker,
            repo=self.block2_repo,
            block_id_attr='block2_id'
        )

    def process_block3_exits(
        self,
        detections: List[Block3Detection],
        condition: Block3Condition,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block3 리스트의 종료 조건 체크 및 업데이트

        Args:
            detections: Block3 탐지 결과 리스트
            condition: Block3 조건
            all_stocks: 전체 주식 데이터

        Returns:
            종료 처리된 블록 개수
        """
        return self._process_exits(
            detections=detections,
            condition=condition,
            all_stocks=all_stocks,
            checker=self.block3_checker,
            repo=self.block3_repo,
            block_id_attr='block3_id'
        )

    def process_block4_exits(
        self,
        detections: List[Block4Detection],
        condition: Block4Condition,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block4 리스트의 종료 조건 체크 및 업데이트

        Args:
            detections: Block4 탐지 결과 리스트
            condition: Block4 조건
            all_stocks: 전체 주식 데이터

        Returns:
            종료 처리된 블록 개수
        """
        return self._process_exits(
            detections=detections,
            condition=condition,
            all_stocks=all_stocks,
            checker=self.block4_checker,
            repo=self.block4_repo,
            block_id_attr='block4_id'
        )

    def _process_exits(
        self,
        detections: List,
        condition,
        all_stocks: List[Stock],
        checker,
        repo,
        block_id_attr: str
    ) -> int:
        """
        공통 종료 조건 처리 로직

        Args:
            detections: 블록 탐지 결과 리스트
            condition: 블록 조건
            all_stocks: 전체 주식 데이터
            checker: 블록 체커
            repo: 블록 Repository
            block_id_attr: 블록 ID 속성명 ('block1_id', 'block2_id' 등)

        Returns:
            종료 처리된 블록 개수
        """
        completed_count = 0

        for detection in detections:
            # 이미 종료된 블록은 스킵
            if detection.ended_at is not None:
                continue

            # 블록 시작일 이후의 데이터만 필터링
            stocks_after_start = [
                s for s in all_stocks
                if s.date > detection.started_at and s.ticker == detection.ticker
            ]

            if not stocks_after_start:
                # 시작일 이후 데이터가 없으면 종료 체크 불가
                continue

            # 시작일 이후 각 시점마다 종료 조건 체크
            for stock in stocks_after_start:
                exit_reason = checker.check_exit(
                    condition=condition,
                    detection=detection,
                    current_stock=stock,
                    all_stocks=all_stocks
                )

                if exit_reason:
                    # 종료 조건 충족: 엔티티 업데이트
                    # Block1Detection만 exit_price 인자를 받음
                    if block_id_attr == 'block1_id':
                        detection.complete(
                            ended_at=stock.date,
                            exit_reason=exit_reason,
                            exit_price=stock.close
                        )
                    else:
                        # Block2/3/4Detection은 BaseBlockDetection의 complete() 사용
                        detection.complete(
                            end_date=stock.date,
                            exit_reason=exit_reason
                        )

                    # DB 업데이트
                    block_id = getattr(detection, block_id_attr)
                    # Repository의 update_status는 block1_id, block2_id 등을 위치 인자로 받음
                    # Block1만 exit_price 인자를 받음
                    if block_id_attr == 'block1_id':
                        repo.update_status(
                            block_id,  # 첫 번째 위치 인자
                            status="completed",
                            ended_at=stock.date,
                            exit_reason=exit_reason,
                            exit_price=stock.close
                        )
                    else:
                        repo.update_status(
                            block_id,  # 첫 번째 위치 인자
                            status="completed",
                            ended_at=stock.date,
                            exit_reason=exit_reason
                        )

                    completed_count += 1

                    # 종료되었으므로 더 이상 체크할 필요 없음
                    break

        return completed_count
