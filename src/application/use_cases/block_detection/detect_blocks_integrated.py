"""
Detect Blocks Integrated Use Case - 블록1/2/3 통합 탐지 유스케이스

Block1/2/3를 Chain 구조로 통합 탐지하는 UseCase입니다.

Chain 구조:
- 각 Block1은 독립적인 Campaign의 시작점
- Block1 → (0 or 1) Block2 → (0 or 1) Block3
- Block2 시작 시 → Block1 종료일 자동 조정
- Block3 시작 시 → Block2 종료일 자동 조정

중첩 루프 구조:
for stock in stocks:  # 메인 루프
    if Block1_entry:
        block1 = create_block1()
        for future in stocks[i+1:]:  # Block1 기간 중 Block2 모니터링
            if Block2_entry:
                # Block1 종료일 조정!
                block2 = create_block2()
                for future2 in stocks[j+1:]:  # Block2 기간 중 Block3 모니터링
                    if Block3_entry:
                        # Block2 종료일 조정!
                        block3 = create_block3()
                        # Block3 종료 조건 모니터링
                    if Block2_exit:
                        break
            if Block1_exit:
                break
"""
from src.domain.entities import Stock
from typing import List, Tuple, Optional
from datetime import date, timedelta
from src.domain.entities.conditions.block_conditions import Block1Condition, Block2Condition, Block3Condition
from src.domain.entities.detections.block1_detection import Block1Detection
from src.domain.entities.detections.block2_detection import Block2Detection
from src.domain.entities.detections.block3_detection import Block3Detection
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.checkers.block1_checker import Block1Checker
from src.application.services.checkers.block2_checker import Block2Checker
from src.application.services.checkers.block3_checker import Block3Checker
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block3_repository import Block3Repository

class DetectBlocksIntegratedUseCase:
    """
    Block1/2/3 통합 탐지 UseCase (Chain 구조)

    주요 기능:
    1. Block1 진입 → Block2 진입 → Block3 진입 순차 탐지
    2. 하위 Block 시작 시 상위 Block 종료일 자동 조정
    3. 각 Block의 최고가 추적
    4. 종료 조건 검사 및 DB 저장
    """

    def __init__(
        self,
        block1_repo: Block1Repository,
        block2_repo: Block2Repository,
        block3_repo: Block3Repository,
        indicator_calculator: Optional[Block1IndicatorCalculator] = None,
        block1_checker: Optional[Block1Checker] = None,
        block2_checker: Optional[Block2Checker] = None,
        block3_checker: Optional[Block3Checker] = None
    ):
        self.block1_repo = block1_repo
        self.block2_repo = block2_repo
        self.block3_repo = block3_repo
        self.indicator_calculator = indicator_calculator or Block1IndicatorCalculator()
        self.block1_checker = block1_checker or Block1Checker()
        self.block2_checker = block2_checker or Block2Checker()
        self.block3_checker = block3_checker or Block3Checker()

    def execute(
        self,
        block1_condition: Block1Condition,
        block2_condition: Block2Condition,
        block3_condition: Block3Condition,
        condition_name: str,
        stocks: List[Stock]
    ) -> Tuple[List[Block1Detection], List[Block2Detection], List[Block3Detection]]:
        """
        Block1/2/3 통합 탐지 실행

        Args:
            block1_condition: Block1 조건
            block2_condition: Block2 조건
            block3_condition: Block3 조건
            condition_name: 조건 이름
            stocks: 주식 데이터 리스트 (동일 종목, 날짜순 정렬)

        Returns:
            (block1_list, block2_list, block3_list) 튜플
        """
        if not stocks:
            return [], [], []

        # 조건 유효성 검사
        if not block1_condition.validate():
            raise ValueError(f"Invalid Block1Condition: {block1_condition}")
        if not block2_condition.validate():
            raise ValueError(f"Invalid Block2Condition: {block2_condition}")
        if not block3_condition.validate():
            raise ValueError(f"Invalid Block3Condition: {block3_condition}")

        # 지표 계산
        stocks_with_indicators = self._calculate_indicators(
            stocks,
            block1_condition
        )

        # 통합 탐지 실행 (중첩 루프)
        block1_list, block2_list, block3_list = self._detect_all_blocks(
            block1_condition,
            block2_condition,
            block3_condition,
            condition_name,
            stocks_with_indicators
        )

        return block1_list, block2_list, block3_list

    def _calculate_indicators(
        self,
        stocks: List[Stock],
        condition: Block1Condition
    ) -> List[Stock]:
        """주가 데이터에 지표 계산"""
        ma_period = condition.base.block1_entry_ma_period or 20
        exit_ma_period = condition.base.block1_exit_ma_period
        volume_days = condition.base.block1_entry_volume_high_days  # None이면 조건 비활성화
        new_high_days = condition.base.block1_entry_price_high_days  # None이면 조건 비활성화

        return self.indicator_calculator.calculate(
            stocks,
            ma_period=ma_period,
            exit_ma_period=exit_ma_period,
            volume_days=volume_days,
            new_high_days=new_high_days
        )

    def _detect_all_blocks(
        self,
        cond1: Block1Condition,
        cond2: Block2Condition,
        cond3: Block3Condition,
        condition_name: str,
        stocks: List[Stock]
    ) -> Tuple[List[Block1Detection], List[Block2Detection], List[Block3Detection]]:
        """
        메인 탐지 로직 - 중첩된 루프 구조

        Returns:
            (block1_list, block2_list, block3_list)
        """
        block1_list = []
        block2_list = []
        block3_list = []

        # 기존 탐지 결과 로드 (종목별)
        ticker = stocks[0].ticker if stocks else None
        if not ticker:
            return [], [], []

        existing_block1s = self.block1_repo.find_by_ticker(ticker)

        # 메인 루프: Block1 탐지
        for i, stock in enumerate(stocks):
            # 전일 주식 데이터
            prev_stock = stocks[i - 1] if i > 0 else None

            # Block1 진입 조건 체크
            if self._check_block1_entry(stock, prev_stock, cond1, existing_block1s, condition_name):
                # Block1 생성 및 저장
                block1 = self._create_block1(stock, condition_name)
                block1.update_peak(stock.high, stock.date)

                saved_block1 = self.block1_repo.save(block1)
                block1_list.append(saved_block1)
                existing_block1s.append(saved_block1)

                # 중첩 루프 1: Block1 기간 동안 Block2 모니터링
                block2_detected = False
                for j in range(i + 1, len(stocks)):
                    future = stocks[j]
                    future_prev = stocks[j - 1] if j > 0 else None

                    # Block1 최고가 갱신
                    if saved_block1.update_peak(future.high, future.date):
                        self.block1_repo.update_peak(
                            saved_block1.block1_id,
                            saved_block1.peak_price,
                            saved_block1.peak_date
                        )

                    # Block2 진입 조건 체크 (우선순위!)
                    if self._check_block2_entry(
                        future,
                        future_prev,
                        saved_block1,
                        cond2,
                        j,
                        i,
                        stocks
                    ):
                        # Block1 종료일 조정!
                        saved_block1.complete(
                            ended_at=future.date - timedelta(days=1),
                            exit_reason="block2_started",
                            exit_price=future_prev.close if future_prev else saved_block1.entry_close
                        )
                        self.block1_repo.update_status(
                            saved_block1.block1_id,
                            status="completed",
                            ended_at=saved_block1.ended_at,
                            exit_reason="block2_started",
                            exit_price=saved_block1.exit_price
                        )

                        # Block2 생성 및 저장
                        block2 = self._create_block2(future, saved_block1, condition_name)
                        block2.update_peak(future.high, future.date, future.volume)

                        saved_block2 = self.block2_repo.save(block2)
                        block2_list.append(saved_block2)
                        block2_detected = True

                        # 중첩 루프 2: Block2 기간 동안 Block3 모니터링
                        block3_detected = False
                        for k in range(j + 1, len(stocks)):
                            future2 = stocks[k]
                            future2_prev = stocks[k - 1] if k > 0 else None

                            # Block2 최고가 갱신
                            if saved_block2.peak_price is None or future2.high > saved_block2.peak_price:
                                saved_block2.update_peak(future2.high, future2.date, future2.volume)
                                self.block2_repo.update_peak(
                                    saved_block2.id,
                                    saved_block2.peak_price,
                                    saved_block2.peak_date
                                )

                            # Block3 진입 조건 체크
                            if self._check_block3_entry(
                                future2,
                                future2_prev,
                                saved_block1,
                                saved_block2,
                                cond3,
                                k,
                                j,
                                stocks
                            ):
                                # Block2 종료일 조정!
                                saved_block2.complete(
                                    end_date=future2.date - timedelta(days=1),
                                    exit_reason="block3_started"
                                )
                                self.block2_repo.update_status(
                                    saved_block2.id,
                                    status="completed",
                                    ended_at=saved_block2.ended_at,
                                    exit_reason="block3_started"
                                )

                                # Block3 생성 및 저장
                                block3 = self._create_block3(future2, saved_block2, condition_name)
                                block3.update_peak(future2.high, future2.date, future2.volume)

                                saved_block3 = self.block3_repo.save(block3)
                                block3_list.append(saved_block3)
                                block3_detected = True

                                # 중첩 루프 3: Block3 기간 동안 종료 조건 모니터링
                                for m in range(k + 1, len(stocks)):
                                    future3 = stocks[m]

                                    # Block3 최고가 갱신
                                    if saved_block3.peak_price is None or future3.high > saved_block3.peak_price:
                                        saved_block3.update_peak(future3.high, future3.date, future3.volume)
                                        self.block3_repo.update_peak(
                                            saved_block3.id,
                                            saved_block3.peak_price,
                                            saved_block3.peak_date
                                        )

                                    # Block3 종료 조건 체크
                                    exit_reason = self.block3_checker.check_exit(
                                        cond3,
                                        saved_block3,
                                        future3,
                                        stocks
                                    )
                                    if exit_reason:
                                        saved_block3.complete(
                                            end_date=future3.date,
                                            exit_reason=exit_reason
                                        )
                                        self.block3_repo.update_status(
                                            saved_block3.id,
                                            status="completed",
                                            ended_at=saved_block3.ended_at,
                                            exit_reason=exit_reason
                                        )
                                        break

                                break  # Block3 탐지 완료 후 Block2 루프 종료

                            # Block2 종료 조건 체크
                            exit_reason = self.block2_checker.check_exit(
                                cond2,
                                saved_block2,
                                future2,
                                stocks
                            )
                            if exit_reason:
                                saved_block2.complete(
                                    end_date=future2.date,
                                    exit_reason=exit_reason
                                )
                                self.block2_repo.update_status(
                                    saved_block2.id,
                                    status="completed",
                                    ended_at=saved_block2.ended_at,
                                    exit_reason=exit_reason
                                )
                                break

                        break  # Block2 탐지 완료 후 Block1 루프 종료

                    # Block1 종료 조건 체크
                    exit_reason = self.block1_checker.check_exit(
                        cond1,
                        saved_block1,
                        future,
                        stocks
                    )
                    if exit_reason:
                        saved_block1.complete(
                            ended_at=future.date,
                            exit_reason=exit_reason,
                            exit_price=future.close
                        )
                        self.block1_repo.update_status(
                            saved_block1.block1_id,
                            status="completed",
                            ended_at=saved_block1.ended_at,
                            exit_reason=exit_reason,
                            exit_price=saved_block1.exit_price
                        )
                        break

        return block1_list, block2_list, block3_list

    def _check_block1_entry(
        self,
        stock: Stock,
        prev_stock: Optional[Stock],
        condition: Block1Condition,
        existing_detections: List[Block1Detection],
        condition_name: str
    ) -> bool:
        """Block1 진입 조건 체크"""
        # 1. 진입 조건 검사
        if not self.block1_checker.check_entry(condition, stock, prev_stock):
            return False

        # 2. 중복 방지 기간 검사
        if not self.block1_checker.check_cooldown(
            stock.ticker,
            stock.date,
            existing_detections,
            condition.cooldown_days
        ):
            return False

        return True

    def _check_block2_entry(
        self,
        stock: Stock,
        prev_stock: Optional[Stock],
        prev_block1: Block1Detection,
        condition: Block2Condition,
        current_idx: int,
        block1_idx: int,
        all_stocks: List[Stock]
    ) -> bool:
        """Block2 진입 조건 체크"""
        # 1. Block2 진입 조건 검사 (Block1 조건 + Block2 추가 조건)
        if not self.block2_checker.check_entry(condition, stock, prev_stock, prev_block1):
            return False

        # 2. 최소 캔들 수 체크 (옵션)
        if condition.min_candles_after_block1 is not None:
            if not self.block2_checker.check_min_candles(
                stock.date,
                prev_block1,
                condition.min_candles_after_block1,
                all_stocks
            ):
                return False

        return True

    def _check_block3_entry(
        self,
        stock: Stock,
        prev_stock: Optional[Stock],
        prev_block1: Block1Detection,
        prev_block2: Block2Detection,
        condition: Block3Condition,
        current_idx: int,
        block2_idx: int,
        all_stocks: List[Stock]
    ) -> bool:
        """Block3 진입 조건 체크"""
        # 1. Block3 진입 조건 검사 (Block2 조건 + Block3 추가 조건)
        if not self.block3_checker.check_entry(
            condition,
            stock,
            prev_stock,
            prev_block1,
            prev_block2
        ):
            return False

        # 2. 최소 캔들 수 체크 (옵션)
        if condition.min_candles_after_block2 is not None:
            if not self.block3_checker.check_min_candles(
                stock.date,
                prev_block2,
                condition.min_candles_after_block2,
                all_stocks
            ):
                return False

        return True

    def _create_block1(
        self,
        stock: Stock,
        condition_name: str
    ) -> Block1Detection:
        """Block1 엔티티 생성"""
        return self.block1_checker.create_detection(condition_name, stock)

    def _create_block2(
        self,
        stock: Stock,
        prev_block1: Block1Detection,
        condition_name: str
    ) -> Block2Detection:
        """Block2 엔티티 생성 (prev_block1_id 설정)"""
        return self.block2_checker.create_detection(
            condition_name,
            stock,
            prev_block1
        )

    def _create_block3(
        self,
        stock: Stock,
        prev_block2: Block2Detection,
        condition_name: str
    ) -> Block3Detection:
        """Block3 엔티티 생성 (prev_block2_id 설정)"""
        return self.block3_checker.create_detection(
            condition_name,
            stock,
            prev_block2
        )
