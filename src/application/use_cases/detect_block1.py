"""
Detect Block1 Use Case - 블록1 탐지 유스케이스
"""
from typing import List, Optional
from datetime import date, timedelta
from ...domain.entities.stock import Stock
from ...domain.entities.block1_condition import Block1Condition
from ...domain.entities.block1_detection import Block1Detection
from ..services.block1_indicator_calculator import Block1IndicatorCalculator
from ..services.block1_checker import Block1Checker
from ...infrastructure.repositories.block1_repository import Block1Repository


class DetectBlock1UseCase:
    """
    블록1 탐지 유스케이스

    주요 기능:
    1. 블록1 진입 조건 검사
    2. 블록1 종료 조건 검사 (기존 활성 블록1)
    3. 중복 방지 (cooldown 기간 체크)
    4. 블록1 탐지 결과 저장
    """

    def __init__(
        self,
        repository: Block1Repository,
        indicator_calculator: Optional[Block1IndicatorCalculator] = None,
        checker: Optional[Block1Checker] = None
    ):
        self.repository = repository
        self.indicator_calculator = indicator_calculator or Block1IndicatorCalculator()
        self.checker = checker or Block1Checker()

    def execute(
        self,
        condition: Block1Condition,
        condition_name: str,
        stocks: List[Stock]
    ) -> List[Block1Detection]:
        """
        블록1 탐지 실행

        Args:
            condition: 블록1 조건
            condition_name: 조건 이름
            stocks: 검사할 주식 데이터 리스트 (동일 종목, 날짜순 정렬)

        Returns:
            새로 탐지된 블록1 리스트
        """
        if not stocks:
            return []

        # 조건 유효성 검사
        if not condition.validate():
            raise ValueError(f"Invalid Block1Condition: {condition}")

        # 종목별로 그룹화
        stocks_by_ticker = self._group_by_ticker(stocks)

        all_detections = []

        # 각 종목에 대해 블록1 탐지
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
        condition: Block1Condition,
        condition_name: str,
        ticker: str,
        stocks: List[Stock]
    ) -> List[Block1Detection]:
        """
        단일 종목에 대한 블록1 탐지

        Args:
            condition: 블록1 조건
            condition_name: 조건 이름
            ticker: 종목코드
            stocks: 주식 데이터 리스트 (날짜순 정렬)

        Returns:
            새로 탐지된 블록1 리스트
        """
        # 지표 계산
        ma_period = condition.entry_ma_period or 20
        exit_ma_period = condition.exit_ma_period
        volume_months = condition.volume_high_months or 6
        new_high_months = condition.price_high_months or 2  # 기본값 2개월

        stocks_with_indicators = self.indicator_calculator.calculate(
            stocks,
            ma_period=ma_period,
            exit_ma_period=exit_ma_period,
            volume_months=volume_months,
            new_high_months=new_high_months
        )

        # 기존 블록1 조회
        existing_detections = self.repository.find_by_ticker(ticker)

        new_detections = []

        # 각 날짜별로 검사
        for i, stock in enumerate(stocks_with_indicators):
            # 전일 주식 데이터 (전날 거래량 조건용)
            prev_stock = stocks_with_indicators[i - 1] if i > 0 else None

            # 1. 기존 활성 블록1의 최고가 갱신
            self._update_peak_prices(existing_detections, stock)

            # 2. 기존 활성 블록1의 종료 조건 검사
            self._check_exit_conditions(
                condition,
                existing_detections,
                stock,
                stocks_with_indicators
            )

            # 3. 새로운 블록1 진입 조건 검사
            if self._check_entry_conditions(
                condition,
                stock,
                prev_stock,
                existing_detections,
                condition_name
            ):
                # 블록1 탐지 결과 생성
                detection = self.checker.create_detection(condition_name, stock)

                # 진입 시점의 고가를 최고가로 초기화
                detection.update_peak(stock.high, stock.date)

                # 저장
                saved_detection = self.repository.save(detection)
                new_detections.append(saved_detection)

                # 기존 리스트에 추가 (종료 조건 검사용)
                existing_detections.append(saved_detection)

        return new_detections

    def _check_entry_conditions(
        self,
        condition: Block1Condition,
        stock: Stock,
        prev_stock: Optional[Stock],
        existing_detections: List[Block1Detection],
        condition_name: str
    ) -> bool:
        """블록1 진입 조건 검사"""
        # 1. 진입 조건 검사 (전날 거래량 조건 포함)
        if not self.checker.check_entry(condition, stock, prev_stock):
            return False

        # 2. 중복 방지 기간 검사
        if not self.checker.check_cooldown(
            stock.ticker,
            stock.date,
            existing_detections,
            condition.cooldown_days
        ):
            return False

        return True

    def _update_peak_prices(
        self,
        existing_detections: List[Block1Detection],
        current_stock: Stock
    ):
        """
        기존 활성 블록1의 최고가 갱신

        Args:
            existing_detections: 기존 블록1 리스트
            current_stock: 현재 주식 데이터
        """
        for detection in existing_detections:
            # 활성 블록1만 검사
            if detection.status != "active":
                continue

            # 같은 종목만
            if detection.ticker != current_stock.ticker:
                continue

            # 시작일 이후만
            if current_stock.date <= detection.started_at:
                continue

            # 최고가 갱신 시도
            if detection.update_peak(current_stock.high, current_stock.date):
                # DB 업데이트
                self.repository.update_peak(
                    detection.block1_id,
                    detection.peak_price,
                    detection.peak_date
                )

    def _check_exit_conditions(
        self,
        condition: Block1Condition,
        existing_detections: List[Block1Detection],
        current_stock: Stock,
        all_stocks: List[Stock]
    ):
        """기존 활성 블록1의 종료 조건 검사"""
        for detection in existing_detections:
            # 활성 블록1만 검사
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
                    ended_at=current_stock.date,
                    exit_reason=exit_reason,
                    exit_price=current_stock.close
                )

                # DB 업데이트
                self.repository.update_status(
                    detection.block1_id,
                    status="completed",
                    ended_at=current_stock.date,
                    exit_reason=exit_reason,
                    exit_price=current_stock.close
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

    def get_active_blocks(self, ticker: str) -> List[Block1Detection]:
        """
        종목의 활성 블록1 조회

        Args:
            ticker: 종목코드

        Returns:
            활성 블록1 리스트
        """
        return self.repository.find_active_by_ticker(ticker)

    def get_all_blocks(
        self,
        ticker: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Block1Detection]:
        """
        종목의 모든 블록1 조회

        Args:
            ticker: 종목코드
            from_date: 시작일 필터
            to_date: 종료일 필터

        Returns:
            블록1 리스트
        """
        return self.repository.find_by_ticker(
            ticker,
            status=None,
            from_date=from_date,
            to_date=to_date
        )
