"""
Exit Condition Processor Service

블록 탐지의 종료 조건 후처리 서비스
모든 활성 블록(ended_at=None)에 대해 종료 조건 체크 및 업데이트
"""
from typing import Dict, List, Optional, Union
from datetime import date

from src.domain.entities import (
    Stock,
    Block1Detection,
    Block2Detection,
    Block3Detection,
    Block4Detection,
)
from src.application.services.common.utils import get_latest_trading_day_before
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

    def process_auto_exit_on_next_block(
        self,
        prev_block_detections: List[Union[Block1Detection, Block2Detection, Block3Detection]],
        next_block_detections: List[Union[Block2Detection, Block3Detection, Block4Detection]],
        auto_exit_enabled: bool,
        all_stocks: List[Stock],
        block_level: int  # 1, 2, 3
    ) -> int:
        """
        다음 블록 시작 시 이전 블록 자동 종료 처리

        Block N+1이 M일에 시작하면 Block N을 M-1일(전 거래일)에 종료
        OR 조건: 기존 종료 조건 OR 다음 블록 시작 (먼저 충족된 조건으로 종료)

        Args:
            prev_block_detections: 이전 블록(Block N) 탐지 리스트 (활성 블록 포함)
            next_block_detections: 다음 블록(Block N+1) 탐지 리스트 (전체)
            auto_exit_enabled: auto_exit_on_next_block 설정값 (true/false)
            all_stocks: 전체 주식 데이터 (거래일 계산용)
            block_level: 블록 레벨 (1=Block1→Block2, 2=Block2→Block3, 3=Block3→Block4)

        Returns:
            자동 종료 처리된 블록 개수

        Example:
            # Block2가 2024-01-10에 시작 → Block1을 2024-01-09(전 거래일)에 종료
            count = processor.process_auto_exit_on_next_block(
                prev_block_detections=active_block1_list,
                next_block_detections=all_block2_list,
                auto_exit_enabled=True,
                all_stocks=stocks,
                block_level=1
            )

        Note:
            - auto_exit_enabled가 False면 즉시 0 반환 (처리 안 함)
            - 이미 종료된 이전 블록은 자동으로 스킵
            - 거래일 기준으로 M-1 계산 (공휴일 자동 건너뜀)
            - 종료 사유: "next_block_start"
        """
        if not auto_exit_enabled:
            return 0

        completed_count = 0

        # Repository 및 block_id 속성 선택
        if block_level == 1:
            repo = self.block1_repo
            block_id_attr = 'block1_id'
        elif block_level == 2:
            repo = self.block2_repo
            block_id_attr = 'block2_id'
        elif block_level == 3:
            repo = self.block3_repo
            block_id_attr = 'block3_id'
        else:
            raise ValueError(f"Invalid block_level: {block_level}. Must be 1, 2, or 3.")

        # 다음 블록의 시작일 목록 추출 (중복 제거)
        next_block_start_dates = set(d.started_at for d in next_block_detections)

        for prev_block in prev_block_detections:
            # 이미 종료된 블록은 스킵
            if prev_block.ended_at is not None:
                continue

            # 같은 ticker의 다음 블록 중, 이전 블록 시작 이후에 시작한 것 찾기
            relevant_next_blocks = [
                d for d in next_block_detections
                if d.ticker == prev_block.ticker and d.started_at > prev_block.started_at
            ]

            if not relevant_next_blocks:
                # 다음 블록이 없으면 스킵
                continue

            # 가장 먼저 시작한 다음 블록 찾기
            earliest_next_block = min(relevant_next_blocks, key=lambda d: d.started_at)
            next_block_start_date = earliest_next_block.started_at

            # 전 거래일 계산 (M-1)
            exit_date = get_latest_trading_day_before(next_block_start_date, all_stocks)

            if exit_date is None:
                # 전 거래일이 없으면 스킵 (데이터 부족)
                continue

            # 종료일이 시작일보다 이전이면 스킵 (불가능한 상황)
            if exit_date <= prev_block.started_at:
                continue

            # 이전 블록 종료 처리
            exit_reason = "next_block_start"

            # Block1Detection만 exit_price 인자를 받음
            if block_level == 1:
                # exit_price 계산: exit_date의 종가
                exit_stock = next((s for s in all_stocks if s.date == exit_date and s.ticker == prev_block.ticker), None)
                exit_price = exit_stock.close if exit_stock else None

                prev_block.complete(
                    ended_at=exit_date,
                    exit_reason=exit_reason,
                    exit_price=exit_price
                )

                # DB 업데이트
                block_id = getattr(prev_block, block_id_attr)
                repo.update_status(
                    block_id,
                    status="completed",
                    ended_at=exit_date,
                    exit_reason=exit_reason,
                    exit_price=exit_price
                )
            else:
                # Block2/3 Detection
                prev_block.complete(
                    end_date=exit_date,
                    exit_reason=exit_reason
                )

                # DB 업데이트
                block_id = getattr(prev_block, block_id_attr)
                repo.update_status(
                    block_id,
                    status="completed",
                    ended_at=exit_date,
                    exit_reason=exit_reason
                )

            completed_count += 1

        return completed_count

    def process_block1_exits_with_auto_exit(
        self,
        detections: List[Block1Detection],
        condition: Block1Condition,
        next_block_detections: List[Block2Detection],
        auto_exit_enabled: bool,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block1 종료 조건 통합 처리 (OR 조건: 전통적 종료 OR 다음 블록 시작)

        모든 종료 조건을 동시에 평가하여 가장 빠른 종료 시점 선택

        Args:
            detections: Block1 탐지 결과 리스트
            condition: Block1 조건
            next_block_detections: Block2 탐지 결과 리스트 (auto_exit용)
            auto_exit_enabled: auto_exit_on_next_block 설정값
            all_stocks: 전체 주식 데이터

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
                continue

            # 1. 전통적 종료 조건 체크 (MA_BREAK, THREE_LINE_REVERSAL, BODY_MIDDLE)
            exit_candidates = []

            for stock in stocks_after_start:
                exit_reason = self.block1_checker.check_exit(
                    condition=condition,
                    detection=detection,
                    current_stock=stock,
                    all_stocks=all_stocks
                )

                if exit_reason:
                    exit_candidates.append({
                        'date': stock.date,
                        'reason': exit_reason,
                        'price': stock.close
                    })
                    # 첫 번째 전통적 종료만 수집 (날짜순이므로)
                    break

            # 2. Auto-exit 조건 체크 (다음 블록 시작)
            if auto_exit_enabled:
                auto_exit = self._find_auto_exit_date(
                    prev_block=detection,
                    next_block_detections=next_block_detections,
                    all_stocks=all_stocks,
                    block_level=1
                )

                if auto_exit:
                    exit_candidates.append({
                        'date': auto_exit['date'],
                        'reason': 'next_block_start',
                        'price': auto_exit['price']
                    })

            # 3. 후보가 없으면 스킵 (아직 종료 안 됨)
            if not exit_candidates:
                continue

            # 4. 가장 빠른 종료 날짜 선택
            earliest_exit = min(exit_candidates, key=lambda x: x['date'])

            # 5. 엔티티 업데이트
            detection.complete(
                ended_at=earliest_exit['date'],
                exit_reason=earliest_exit['reason'],
                exit_price=earliest_exit['price']
            )

            # 6. DB 업데이트
            self.block1_repo.update_status(
                detection.block1_id,
                status="completed",
                ended_at=earliest_exit['date'],
                exit_reason=earliest_exit['reason'],
                exit_price=earliest_exit['price']
            )

            completed_count += 1

        return completed_count

    def process_block2_exits_with_auto_exit(
        self,
        detections: List[Block2Detection],
        condition: Block2Condition,
        next_block_detections: List[Block3Detection],
        auto_exit_enabled: bool,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block2 종료 조건 통합 처리 (OR 조건: 전통적 종료 OR 다음 블록 시작)

        Args:
            detections: Block2 탐지 결과 리스트
            condition: Block2 조건
            next_block_detections: Block3 탐지 결과 리스트 (auto_exit용)
            auto_exit_enabled: auto_exit_on_next_block 설정값
            all_stocks: 전체 주식 데이터

        Returns:
            종료 처리된 블록 개수
        """
        completed_count = 0

        for detection in detections:
            if detection.ended_at is not None:
                continue

            stocks_after_start = [
                s for s in all_stocks
                if s.date > detection.started_at and s.ticker == detection.ticker
            ]

            if not stocks_after_start:
                continue

            # 1. 전통적 종료 조건 체크
            exit_candidates = []

            for stock in stocks_after_start:
                exit_reason = self.block2_checker.check_exit(
                    condition=condition,
                    detection=detection,
                    current_stock=stock,
                    all_stocks=all_stocks
                )

                if exit_reason:
                    exit_candidates.append({
                        'date': stock.date,
                        'reason': exit_reason,
                        'price': None  # Block2는 exit_price 없음
                    })
                    break

            # 2. Auto-exit 조건 체크
            if auto_exit_enabled:
                auto_exit = self._find_auto_exit_date(
                    prev_block=detection,
                    next_block_detections=next_block_detections,
                    all_stocks=all_stocks,
                    block_level=2
                )

                if auto_exit:
                    exit_candidates.append({
                        'date': auto_exit['date'],
                        'reason': 'next_block_start',
                        'price': None
                    })

            if not exit_candidates:
                continue

            # 3. 가장 빠른 종료 날짜 선택
            earliest_exit = min(exit_candidates, key=lambda x: x['date'])

            # 4. 엔티티 업데이트 (Block2는 end_date 파라미터 사용)
            detection.complete(
                end_date=earliest_exit['date'],
                exit_reason=earliest_exit['reason']
            )

            # 5. DB 업데이트
            self.block2_repo.update_status(
                detection.block2_id,
                status="completed",
                ended_at=earliest_exit['date'],
                exit_reason=earliest_exit['reason']
            )

            completed_count += 1

        return completed_count

    def process_block3_exits_with_auto_exit(
        self,
        detections: List[Block3Detection],
        condition: Block3Condition,
        next_block_detections: List[Block4Detection],
        auto_exit_enabled: bool,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block3 종료 조건 통합 처리 (OR 조건: 전통적 종료 OR 다음 블록 시작)

        Args:
            detections: Block3 탐지 결과 리스트
            condition: Block3 조건
            next_block_detections: Block4 탐지 결과 리스트 (auto_exit용)
            auto_exit_enabled: auto_exit_on_next_block 설정값
            all_stocks: 전체 주식 데이터

        Returns:
            종료 처리된 블록 개수
        """
        completed_count = 0

        for detection in detections:
            if detection.ended_at is not None:
                continue

            stocks_after_start = [
                s for s in all_stocks
                if s.date > detection.started_at and s.ticker == detection.ticker
            ]

            if not stocks_after_start:
                continue

            # 1. 전통적 종료 조건 체크
            exit_candidates = []

            for stock in stocks_after_start:
                exit_reason = self.block3_checker.check_exit(
                    condition=condition,
                    detection=detection,
                    current_stock=stock,
                    all_stocks=all_stocks
                )

                if exit_reason:
                    exit_candidates.append({
                        'date': stock.date,
                        'reason': exit_reason,
                        'price': None
                    })
                    break

            # 2. Auto-exit 조건 체크
            if auto_exit_enabled:
                auto_exit = self._find_auto_exit_date(
                    prev_block=detection,
                    next_block_detections=next_block_detections,
                    all_stocks=all_stocks,
                    block_level=3
                )

                if auto_exit:
                    exit_candidates.append({
                        'date': auto_exit['date'],
                        'reason': 'next_block_start',
                        'price': None
                    })

            if not exit_candidates:
                continue

            # 3. 가장 빠른 종료 날짜 선택
            earliest_exit = min(exit_candidates, key=lambda x: x['date'])

            # 4. 엔티티 업데이트
            detection.complete(
                end_date=earliest_exit['date'],
                exit_reason=earliest_exit['reason']
            )

            # 5. DB 업데이트
            self.block3_repo.update_status(
                detection.block3_id,
                status="completed",
                ended_at=earliest_exit['date'],
                exit_reason=earliest_exit['reason']
            )

            completed_count += 1

        return completed_count

    def process_block4_exits_with_auto_exit(
        self,
        detections: List[Block4Detection],
        condition: Block4Condition,
        all_stocks: List[Stock]
    ) -> int:
        """
        Block4 종료 조건 처리

        Block4는 다음 블록이 없으므로 전통적 종료 조건만 사용
        (일관성을 위해 _with_auto_exit 네이밍 유지)

        Args:
            detections: Block4 탐지 결과 리스트
            condition: Block4 조건
            all_stocks: 전체 주식 데이터

        Returns:
            종료 처리된 블록 개수
        """
        completed_count = 0

        for detection in detections:
            if detection.ended_at is not None:
                continue

            stocks_after_start = [
                s for s in all_stocks
                if s.date > detection.started_at and s.ticker == detection.ticker
            ]

            if not stocks_after_start:
                continue

            # Block4는 전통적 종료 조건만 사용
            for stock in stocks_after_start:
                exit_reason = self.block4_checker.check_exit(
                    condition=condition,
                    detection=detection,
                    current_stock=stock,
                    all_stocks=all_stocks
                )

                if exit_reason:
                    # 엔티티 업데이트
                    detection.complete(
                        end_date=stock.date,
                        exit_reason=exit_reason
                    )

                    # DB 업데이트
                    self.block4_repo.update_status(
                        detection.block4_id,
                        status="completed",
                        ended_at=stock.date,
                        exit_reason=exit_reason
                    )

                    completed_count += 1
                    break

        return completed_count

    def _find_auto_exit_date(
        self,
        prev_block,
        next_block_detections: List,
        all_stocks: List[Stock],
        block_level: int
    ) -> Optional[Dict]:
        """
        다음 블록 시작 시 자동 종료 날짜 계산

        Args:
            prev_block: 이전 블록 탐지 객체
            next_block_detections: 다음 블록 탐지 리스트
            all_stocks: 전체 주식 데이터
            block_level: 블록 레벨 (1, 2, 3)

        Returns:
            Dict with 'date' and 'price', or None if no auto-exit
        """
        # 같은 ticker의 다음 블록 중, 이전 블록 시작 이후에 시작한 것
        relevant_next_blocks = [
            d for d in next_block_detections
            if d.ticker == prev_block.ticker and d.started_at > prev_block.started_at
        ]

        if not relevant_next_blocks:
            return None

        # 가장 먼저 시작한 다음 블록
        earliest_next_block = min(relevant_next_blocks, key=lambda d: d.started_at)

        # 전 거래일 계산
        exit_date = get_latest_trading_day_before(earliest_next_block.started_at, all_stocks)

        if not exit_date or exit_date <= prev_block.started_at:
            return None

        # exit_price 계산 (Block1만 필요)
        exit_price = None
        if block_level == 1:
            exit_stock = next((s for s in all_stocks
                              if s.date == exit_date and s.ticker == prev_block.ticker), None)
            exit_price = exit_stock.close if exit_stock else None

        return {
            'date': exit_date,
            'price': exit_price
        }

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
