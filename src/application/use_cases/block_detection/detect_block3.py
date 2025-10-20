"""
Detect Block3 Use Case - 블록3 탐지 유스케이스
"""
from src.domain.entities import Stock
from typing import List, Optional
from datetime import date
from src.domain.entities.conditions.block_conditions import Block3Condition
from src.domain.entities.detections.block3_detection import Block3Detection
from src.domain.entities.detections.block2_detection import Block2Detection
from src.domain.entities.detections.block1_detection import Block1Detection
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.checkers.block3_checker import Block3Checker
from src.infrastructure.repositories.detection.block3_repository import Block3Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block1_repository import Block1Repository

class DetectBlock3UseCase:
    """
    블록3 탐지 유스케이스

    주요 기능:
    1. 블록3 진입 조건 검사 (블록2 조건 + 블록3 추가 조건)
    2. 블록3 종료 조건 검사 (기존 활성 블록3)
    3. 직전 블록1/블록2 찾기 (날짜 기준)
    4. 블록3 탐지 결과 저장
    """

    def __init__(
        self,
        block3_repository: Block3Repository,
        block2_repository: Block2Repository,
        block1_repository: Block1Repository,
        indicator_calculator: Optional[Block1IndicatorCalculator] = None,
        checker: Optional[Block3Checker] = None
    ):
        self.block3_repository = block3_repository
        self.block2_repository = block2_repository
        self.block1_repository = block1_repository
        self.indicator_calculator = indicator_calculator or Block1IndicatorCalculator()
        self.checker = checker or Block3Checker()

    def execute(
        self,
        condition: Block3Condition,
        condition_name: str,
        stocks: List[Stock]
    ) -> List[Block3Detection]:
        """
        블록3 탐지 실행

        Args:
            condition: 블록3 조건
            condition_name: 조건 이름
            stocks: 검사할 주식 데이터 리스트 (동일 종목, 날짜순 정렬)

        Returns:
            새로 탐지된 블록3 리스트
        """
        if not stocks:
            return []

        # 조건 유효성 검사
        if not condition.validate():
            raise ValueError(f"Invalid Block3Condition: {condition}")

        # 종목별로 그룹화
        stocks_by_ticker = self._group_by_ticker(stocks)

        all_detections = []

        # 각 종목에 대해 블록3 탐지
        for ticker, ticker_stocks in stocks_by_ticker.items():
            detections = self._detect_ticker(
                condition,
                condition_name,
                ticker,
                ticker_stocks
            )
            all_detections.extend(detections)

        return all_detections

    def _detect_ticker(
        self,
        condition: Block3Condition,
        condition_name: str,
        ticker: str,
        stocks: List[Stock]
    ) -> List[Block3Detection]:
        """
        단일 종목에 대한 블록3 탐지

        Args:
            condition: 블록3 조건
            condition_name: 조건 이름
            ticker: 종목코드
            stocks: 주식 데이터 리스트 (날짜순 정렬)

        Returns:
            새로 탐지된 블록3 리스트
        """
        # 지표 계산 (블록1 조건 사용)
        block1_condition = condition.block2_condition.block1_condition
        ma_period = block1_condition.ma_period or 20
        exit_ma_period = block1_condition.exit_ma_period
        volume_months = block1_condition.volume_months or 6
        new_high_months = block1_condition.new_high_months or 2  # 기본값 2개월

        stocks_with_indicators = self.indicator_calculator.calculate(
            stocks,
            ma_period=ma_period,
            exit_ma_period=exit_ma_period,
            volume_months=volume_months,
            new_high_months=new_high_months
        )

        # 기존 블록3 조회
        existing_block3s = self.block3_repository.find_by_ticker(ticker)

        new_detections = []

        # 각 날짜별로 검사
        for i, stock in enumerate(stocks_with_indicators):
            # 전일 주식 데이터 (전날 거래량 조건용)
            prev_stock = stocks_with_indicators[i - 1] if i > 0 else None

            # 1. 기존 활성 블록3의 최고가/거래량 갱신
            self._update_peaks(existing_block3s, stock)

            # 2. 기존 활성 블록3의 종료 조건 검사
            self._check_exit_conditions(
                condition,
                existing_block3s,
                stock,
                stocks_with_indicators
            )

            # 3. 새로운 블록3 진입 조건 검사
            # 직전 블록1/블록2 찾기
            prev_block1 = self._find_latest_completed_block1(ticker, stock.date)
            prev_block2 = self._find_latest_completed_block2(ticker, stock.date)

            if self._check_entry_conditions(
                condition,
                stock,
                prev_stock,
                prev_block1,
                prev_block2,
                existing_block3s,
                stocks_with_indicators
            ):
                # 블록3 탐지 결과 생성
                detection = self.checker.create_detection(
                    condition_name,
                    stock,
                    prev_block2
                )

                # 진입 시점의 가격/거래량을 최고가/거래량으로 초기화
                detection.update_peak(stock.high, stock.date, stock.volume)

                # 저장
                saved_detection = self.block3_repository.save(detection)
                new_detections.append(saved_detection)

                # 기존 리스트에 추가 (종료 조건 검사용)
                existing_block3s.append(saved_detection)

        return new_detections

    def _check_entry_conditions(
        self,
        condition: Block3Condition,
        stock: Stock,
        prev_stock: Optional[Stock],
        prev_block1: Optional[Block1Detection],
        prev_block2: Optional[Block2Detection],
        existing_block3s: List[Block3Detection],
        all_stocks: List[Stock]
    ) -> bool:
        """블록3 진입 조건 검사"""
        # 1. 활성 블록3가 있으면 불가 (중복 방지)
        for block3 in existing_block3s:
            if block3.status == "active" and block3.ticker == stock.ticker:
                return False

        # 2. 블록3 진입 조건 검사 (블록2 조건 + 블록3 추가 조건)
        if not self.checker.check_entry(condition, stock, prev_stock, prev_block1, prev_block2):
            return False

        # 3. 최소 캔들 수 검사 (선택적)
        if condition.min_candles_after_block2 is not None:
            if not self.checker.check_min_candles(
                stock.date,
                prev_block2,
                condition.min_candles_after_block2,
                all_stocks
            ):
                return False

        # 4. 최대 캔들 수 검사 (선택적)
        if condition.max_candles_after_block2 is not None:
            if not self.checker.check_max_candles(
                stock.date,
                prev_block2,
                condition.max_candles_after_block2,
                all_stocks
            ):
                return False

        return True

    def _find_latest_completed_block1(
        self,
        ticker: str,
        before_date: date
    ) -> Optional[Block1Detection]:
        """
        특정 날짜 이전의 가장 최근 완료된 블록1 찾기

        Args:
            ticker: 종목코드
            before_date: 기준 날짜

        Returns:
            블록1 탐지 결과 또는 None
        """
        # 완료된 블록1들 조회
        completed_block1s = self.block1_repository.find_by_ticker(
            ticker,
            status="completed"
        )

        # 기준 날짜 이전에 종료된 것들 필터링
        valid_block1s = [
            b for b in completed_block1s
            if b.ended_at and b.ended_at < before_date
        ]

        if not valid_block1s:
            return None

        # 종료일 기준 가장 최근 것 반환
        valid_block1s.sort(key=lambda b: b.ended_at, reverse=True)
        return valid_block1s[0]

    def _find_latest_completed_block2(
        self,
        ticker: str,
        before_date: date
    ) -> Optional[Block2Detection]:
        """
        특정 날짜 이전의 가장 최근 완료된 블록2 찾기

        Args:
            ticker: 종목코드
            before_date: 기준 날짜

        Returns:
            블록2 탐지 결과 또는 None
        """
        # 완료된 블록2들 조회
        completed_block2s = self.block2_repository.find_by_ticker(
            ticker,
            status="completed"
        )

        # 기준 날짜 이전에 종료된 것들 필터링
        valid_block2s = [
            b for b in completed_block2s
            if b.ended_at and b.ended_at < before_date
        ]

        if not valid_block2s:
            return None

        # 종료일 기준 가장 최근 것 반환
        valid_block2s.sort(key=lambda b: b.ended_at, reverse=True)
        return valid_block2s[0]

    def _update_peaks(
        self,
        existing_block3s: List[Block3Detection],
        current_stock: Stock
    ):
        """
        기존 활성 블록3의 최고가/거래량 갱신

        Args:
            existing_block3s: 기존 블록3 리스트
            current_stock: 현재 주식 데이터
        """
        for detection in existing_block3s:
            # 활성 블록3만 검사
            if detection.status != "active":
                continue

            # 같은 종목만
            if detection.ticker != current_stock.ticker:
                continue

            # 시작일 이후만
            if current_stock.date <= detection.started_at:
                continue

            # 최고가/거래량 갱신 시도
            old_peak_price = detection.peak_price
            old_peak_volume = detection.peak_volume

            detection.update_peak(current_stock.high, current_stock.date, current_stock.volume)

            # 변경되었으면 DB 업데이트
            if (detection.peak_price != old_peak_price or
                detection.peak_volume != old_peak_volume):
                self.block3_repository.update_peak(
                    detection.block3_id,
                    detection.peak_price,
                    detection.peak_date,
                    detection.peak_gain_ratio,
                    detection.peak_volume
                )

    def _check_exit_conditions(
        self,
        condition: Block3Condition,
        existing_block3s: List[Block3Detection],
        current_stock: Stock,
        all_stocks: List[Stock]
    ):
        """기존 활성 블록3의 종료 조건 검사"""
        for detection in existing_block3s:
            # 활성 블록3만 검사
            if detection.status != "active":
                continue

            # 같은 종목만
            if detection.ticker != current_stock.ticker:
                continue

            # 시작일 이후만
            if current_stock.date <= detection.started_at:
                continue

            # 종료 조건 검사
            exit_reason = self.checker.check_exit(
                condition,
                detection,
                current_stock,
                all_stocks
            )

            if exit_reason:
                # 종료 처리
                detection.complete(
                    end_date=current_stock.date,
                    exit_reason=exit_reason
                )

                # DB 업데이트
                self.block3_repository.update_status(
                    detection.block3_id,
                    status="completed",
                    ended_at=current_stock.date,
                    exit_reason=exit_reason
                )

    def _group_by_ticker(self, stocks: List[Stock]) -> dict:
        """종목별로 그룹화"""
        grouped = {}
        for stock in stocks:
            if stock.ticker not in grouped:
                grouped[stock.ticker] = []
            grouped[stock.ticker].append(stock)

        # 각 종목별로 날짜순 정렬
        for ticker in grouped:
            grouped[ticker].sort(key=lambda s: s.date)

        return grouped

    def get_active_blocks(self, ticker: str) -> List[Block3Detection]:
        """
        종목의 활성 블록3 조회

        Args:
            ticker: 종목코드

        Returns:
            활성 블록3 리스트
        """
        return self.block3_repository.find_active_by_ticker(ticker)

    def get_all_blocks(
        self,
        ticker: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Block3Detection]:
        """
        종목의 모든 블록3 조회

        Args:
            ticker: 종목코드
            from_date: 시작일 필터
            to_date: 종료일 필터

        Returns:
            블록3 리스트
        """
        return self.block3_repository.find_by_ticker(
            ticker,
            status=None,
            from_date=from_date,
            to_date=to_date
        )
