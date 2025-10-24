"""
Detect Block5 Use Case - 블록5 탐지 유스케이스
"""
from src.domain.entities import Stock
from typing import List, Optional
from datetime import date
from src.domain.entities.conditions.block_conditions import Block5Condition
from src.domain.entities.detections.block5_detection import Block5Detection
from src.domain.entities.detections.block4_detection import Block4Detection
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.checkers.block5_checker import Block5Checker
from src.infrastructure.repositories.detection.block5_repository import Block5Repository
from src.infrastructure.repositories.detection.block4_repository import Block4Repository

class DetectBlock5UseCase:
    """
    블록5 탐지 유스케이스

    주요 기능:
    1. 블록5 진입 조건 검사 (블록1~4 조건 + 블록5 추가 조건)
    2. 블록5 종료 조건 검사 (기존 활성 블록5)
    3. 직전 블록4 찾기 (날짜 기준)
    4. 블록5 탐지 결과 저장
    """

    def __init__(
        self,
        block5_repository: Block5Repository,
        block4_repository: Block4Repository,
        indicator_calculator: Optional[Block1IndicatorCalculator] = None,
        checker: Optional[Block5Checker] = None
    ):
        self.block5_repository = block5_repository
        self.block4_repository = block4_repository
        self.indicator_calculator = indicator_calculator or Block1IndicatorCalculator()
        self.checker = checker or Block5Checker()

    def execute(
        self,
        condition: Block5Condition,
        condition_name: str,
        stocks: List[Stock]
    ) -> List[Block5Detection]:
        """
        블록5 탐지 실행

        Args:
            condition: 블록5 조건
            condition_name: 조건 이름
            stocks: 검사할 주식 데이터 리스트 (동일 종목, 날짜순 정렬)

        Returns:
            새로 탐지된 블록5 리스트
        """
        if not stocks:
            return []

        # 조건 유효성 검사
        if not condition.validate():
            raise ValueError(f"Invalid Block5Condition: {condition}")

        # 종목별로 그룹화
        stocks_by_ticker = self._group_by_ticker(stocks)

        all_detections = []

        # 각 종목에 대해 블록5 탐지
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
        condition: Block5Condition,
        condition_name: str,
        ticker: str,
        stocks: List[Stock]
    ) -> List[Block5Detection]:
        """
        단일 종목에 대한 블록5 탐지

        Args:
            condition: 블록5 조건
            condition_name: 조건 이름
            ticker: 종목코드
            stocks: 주식 데이터 리스트 (날짜순 정렬)

        Returns:
            새로 탐지된 블록5 리스트
        """
        # 지표 계산
        ma_period = condition.base.block1_entry_ma_period or 20
        exit_ma_period = condition.base.block1_exit_ma_period
        volume_high_days = condition.base.block1_entry_volume_high_days or 180
        price_high_days = condition.base.block1_entry_price_high_days or 60

        stocks_with_indicators = self.indicator_calculator.calculate(
            stocks,
            ma_period=ma_period,
            exit_ma_period=exit_ma_period,
            volume_high_days=volume_high_days,
            price_high_days=price_high_days
        )

        # 기존 블록5 조회
        existing_block5s = self.block5_repository.find_by_ticker(ticker)

        new_detections = []

        # 각 날짜별로 검사
        for i, stock in enumerate(stocks_with_indicators):
            # 1. 기존 활성 블록5의 최고가/거래량 갱신
            self._update_peaks(existing_block5s, stock)

            # 2. 기존 활성 블록5의 종료 조건 검사
            self._check_exit_conditions(
                condition,
                existing_block5s,
                stock,
                stocks_with_indicators
            )

            # 3. 새로운 블록5 진입 조건 검사
            # 직전 블록4 찾기 (현재 날짜 이전에 완료된 가장 최근 블록4)
            prev_block4 = self._find_latest_completed_block4(ticker, stock.date)

            if self._check_entry_conditions(
                condition,
                stock,
                prev_block4,
                existing_block5s,
                stocks_with_indicators
            ):
                # 블록5 탐지 결과 생성
                detection = self.checker.create_detection(
                    condition_name,
                    stock,
                    prev_block4
                )

                # 진입 시점의 가격/거래량을 최고가/거래량으로 초기화
                detection.update_peak(stock.high, stock.date, stock.volume)

                # 저장
                saved_detection = self.block5_repository.save(detection)
                new_detections.append(saved_detection)

                # 기존 리스트에 추가 (종료 조건 검사용)
                existing_block5s.append(saved_detection)

        return new_detections

    def _check_entry_conditions(
        self,
        condition: Block5Condition,
        stock: Stock,
        prev_block4: Optional[Block4Detection],
        existing_block5s: List[Block5Detection],
        all_stocks: List[Stock]
    ) -> bool:
        """블록5 진입 조건 검사"""
        # 1. 블록5 진입 조건 검사
        if not self.checker.check_entry(condition, stock, all_stocks, prev_seed_block4=prev_block4):
            return False

        # 2. 중복 방지 기간 검사 (선택적)
        if condition.base.block1_min_start_interval_days is not None:
            if not self.checker.check_cooldown(
                stock.ticker,
                stock.date,
                existing_block5s,
                condition.base.block1_min_start_interval_days
            ):
                return False

        # 3. 최소 캔들 수 검사 (선택적)
        if condition.block5_min_candles_from_block is not None:
            if not self.checker.check_min_candles(
                stock.date,
                prev_block4,
                condition.block5_min_candles_from_block,
                all_stocks
            ):
                return False

        # 4. 최대 캔들 수 검사 (선택적)
        if condition.block5_max_candles_from_block is not None:
            if not self.checker.check_max_candles(
                stock.date,
                prev_block4,
                condition.block5_max_candles_from_block,
                all_stocks
            ):
                return False

        # 5. Lookback 윈도우 검사 (선택적)
        if not self.checker.check_lookback_window(
            stock.date,
            prev_block4,
            condition.block5_lookback_min_candles,
            condition.block5_lookback_max_candles,
            all_stocks
        ):
            return False

        return True

    def _find_latest_completed_block4(
        self,
        ticker: str,
        before_date: date
    ) -> Optional[Block4Detection]:
        """
        특정 날짜 이전의 가장 최근 완료된 블록4 찾기

        Args:
            ticker: 종목코드
            before_date: 기준 날짜

        Returns:
            블록4 탐지 결과 또는 None
        """
        # 완료된 블록4들 조회
        completed_block4s = self.block4_repository.find_by_ticker(
            ticker,
            status="completed"
        )

        # 기준 날짜 이전에 종료된 것들 필터링
        valid_block4s = [
            b for b in completed_block4s
            if b.ended_at and b.ended_at < before_date
        ]

        if not valid_block4s:
            return None

        # 종료일 기준 가장 최근 것 반환
        valid_block4s.sort(key=lambda b: b.ended_at, reverse=True)
        return valid_block4s[0]

    def _update_peaks(
        self,
        existing_block5s: List[Block5Detection],
        current_stock: Stock
    ):
        """
        기존 활성 블록5의 최고가/거래량 갱신

        Args:
            existing_block5s: 기존 블록5 리스트
            current_stock: 현재 주식 데이터
        """
        for detection in existing_block5s:
            # 활성 블록5만 검사
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
                self.block5_repository.update_peak(
                    detection.block5_id,
                    detection.peak_price,
                    detection.peak_date,
                    detection.peak_gain_ratio,
                    detection.peak_volume
                )

    def _check_exit_conditions(
        self,
        condition: Block5Condition,
        existing_block5s: List[Block5Detection],
        current_stock: Stock,
        all_stocks: List[Stock]
    ):
        """기존 활성 블록5의 종료 조건 검사"""
        for detection in existing_block5s:
            # 활성 블록5만 검사
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
                self.block5_repository.update_status(
                    detection.block5_id,
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

    def get_active_blocks(self, ticker: str) -> List[Block5Detection]:
        """
        종목의 활성 블록5 조회

        Args:
            ticker: 종목코드

        Returns:
            활성 블록5 리스트
        """
        return self.block5_repository.find_active_by_ticker(ticker)

    def get_all_blocks(
        self,
        ticker: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Block5Detection]:
        """
        종목의 모든 블록5 조회

        Args:
            ticker: 종목코드
            from_date: 시작일 필터
            to_date: 종료일 필터

        Returns:
            블록5 리스트
        """
        return self.block5_repository.find_by_ticker(
            ticker,
            status=None,
            from_date=from_date,
            to_date=to_date
        )
