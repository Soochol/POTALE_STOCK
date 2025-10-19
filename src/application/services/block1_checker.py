"""
Block1 Checker Service - 블록1 진입/종료 조건 검사 서비스
"""
from typing import List, Optional, Dict
from datetime import date, timedelta
from ...domain.entities.stock import Stock
from ...domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from ...domain.entities.block1_detection import Block1Detection
from .three_line_break import ThreeLineBreakCalculator


class Block1Checker:
    """블록1 진입 및 종료 조건 검사 서비스"""

    def __init__(self):
        self.tlb_calculator = ThreeLineBreakCalculator(line_count=3)

    def check_entry(
        self,
        condition: Block1Condition,
        stock: Stock,
        prev_stock: Optional[Stock] = None
    ) -> bool:
        """
        블록1 진입 조건 검사 (6가지 조건 개별 판단)

        Args:
            condition: 블록1 조건
            stock: 주식 데이터 (지표 포함)
            prev_stock: 전일 주식 데이터 (전날 거래량 조건용, 선택적)

        Returns:
            모든 조건 만족 여부
        """
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators

        # 조건 1: 등락률 (전일 대비 N% 이상, 양수만)
        if condition.entry_surge_rate is not None:
            rate = indicators.get('rate', 0)
            if rate < condition.entry_surge_rate:
                return False

        # 조건 2: 고가 >= 이동평균선 N
        if condition.entry_ma_period and condition.entry_high_above_ma:
            ma_key = f'MA_{condition.entry_ma_period}'
            ma_value = indicators.get(ma_key)
            if ma_value is None or stock.high < ma_value:
                return False

        # 조건 3: 이격도 (MA를 100으로 봤을 때 종가 비율)
        if condition.entry_max_deviation_ratio is not None:
            deviation = indicators.get('deviation', 100)
            # deviation_threshold = 115 의미: MA를 100으로 봤을 때 115 이하
            if deviation > condition.entry_max_deviation_ratio:
                return False

        # 조건 4: 거래대금 N억 이상
        if condition.entry_min_trading_value is not None:
            trading_value = indicators.get('trading_value_100m', 0)
            if trading_value < condition.entry_min_trading_value:
                return False

        # 조건 5: N개월 신고거래량
        if condition.entry_volume_high_months is not None:
            is_volume_high = indicators.get('is_volume_high', False)
            if not is_volume_high:
                return False

        # 조건 6: 전날 거래량 대비 N% 수준 (필수)
        if condition.entry_volume_spike_ratio is not None:
            if prev_stock is None:
                # 전날 데이터가 없으면 조건 실패
                return False

            # 당일_거래량 >= 전날_거래량 × (N/100)
            # N은 % 단위 (예: 400 = 400%, 즉 4배)
            ratio = condition.entry_volume_spike_ratio / 100.0
            required_volume = prev_stock.volume * ratio
            if stock.volume < required_volume:
                return False
        # prev_day_volume_increase_ratio가 None이면 이 조건은 체크하지 않음 (하위 호환성)

        # 조건 7: N개월 신고가 (선택적)
        if condition.entry_price_high_months is not None:
            indicators = stock.indicators if hasattr(stock, 'indicators') else {}
            is_new_high = indicators.get('is_new_high', False)
            if not is_new_high:
                return False

        # 모든 조건 만족
        return True

    def check_exit(
        self,
        condition: Block1Condition,
        detection: Block1Detection,
        current_stock: Stock,
        all_stocks: List[Stock]
    ) -> Optional[str]:
        """
        블록1 종료 조건 검사 (3가지 중 택1)

        Args:
            condition: 블록1 조건
            detection: 블록1 탐지 결과
            current_stock: 현재 주식 데이터
            all_stocks: 전체 주식 데이터 (삼선전환도 계산용)

        Returns:
            종료 사유 또는 None
        """
        exit_type = condition.exit_condition_type

        # 종료 조건 1: 이동평균선 이탈
        if exit_type == Block1ExitConditionType.MA_BREAK:
            if self._check_ma_break(condition, current_stock):
                return "ma_break"

        # 종료 조건 2: 삼선전환도 첫 음봉
        elif exit_type == Block1ExitConditionType.THREE_LINE_REVERSAL:
            if self._check_three_line_reversal(detection, current_stock, all_stocks):
                return "three_line_reversal"

        # 종료 조건 3: 블록1 캔들 몸통 중간 가격 이탈
        elif exit_type == Block1ExitConditionType.BODY_MIDDLE:
            if self._check_body_middle_break(detection, current_stock):
                return "body_middle"

        return None

    def _check_ma_break(self, condition: Block1Condition, stock: Stock) -> bool:
        """이동평균선 이탈 확인 (종가 < MA)"""
        # 종료용 MA 기간 결정 (exit_ma_period가 있으면 사용, 없으면 ma_period 사용)
        exit_ma = condition.exit_ma_period if condition.exit_ma_period else condition.entry_ma_period

        if not exit_ma:
            return False

        if not hasattr(stock, 'indicators'):
            return False

        ma_key = f'MA_{exit_ma}'
        ma_value = stock.indicators.get(ma_key)

        if ma_value is None:
            return False

        return stock.close < ma_value

    def _check_three_line_reversal(
        self,
        detection: Block1Detection,
        current_stock: Stock,
        all_stocks: List[Stock]
    ) -> bool:
        """삼선전환도 첫 음봉 확인"""
        # 블록1 시작일부터 현재까지의 데이터 필터링
        filtered_stocks = [
            s for s in all_stocks
            if detection.started_at <= s.date <= current_stock.date
        ]

        if not filtered_stocks:
            return False

        # 삼선전환도 계산
        from .block1_indicator_calculator import Block1IndicatorCalculator
        calculator = Block1IndicatorCalculator()
        tlb_bars = calculator.get_three_line_break_bars(filtered_stocks)

        # 첫 번째 음봉 찾기
        first_down_date = self.tlb_calculator.detect_first_down_bar(
            tlb_bars,
            detection.started_at
        )

        if first_down_date and first_down_date <= current_stock.date:
            return True

        return False

    def _check_body_middle_break(
        self,
        detection: Block1Detection,
        current_stock: Stock
    ) -> bool:
        """블록1 캔들 몸통 중간 가격 이탈 확인"""
        body_middle = detection.entry_body_middle
        return current_stock.close < body_middle

    def check_cooldown(
        self,
        ticker: str,
        current_date: date,
        existing_detections: List[Block1Detection],
        cooldown_days: int
    ) -> bool:
        """
        중복 방지 기간 확인

        Args:
            ticker: 종목코드
            current_date: 현재 날짜
            existing_detections: 기존 블록1 탐지 결과 리스트
            cooldown_days: 재탐지 제외 기간 (일)

        Returns:
            탐지 가능 여부 (True: 가능, False: 중복 방지 기간 내)
        """
        for detection in existing_detections:
            if detection.ticker != ticker:
                continue

            # 활성 블록1이 있으면 불가
            if detection.status == "active":
                return False

            # 종료된 블록1이지만 cooldown 기간 내면 불가
            if detection.ended_at:
                cooldown_end = detection.started_at + timedelta(days=cooldown_days)
                if detection.started_at <= current_date < cooldown_end:
                    return False

        return True

    def create_detection(
        self,
        condition_name: str,
        stock: Stock
    ) -> Block1Detection:
        """
        블록1 탐지 결과 생성

        Args:
            condition_name: 조건 이름
            stock: 진입 시점 주식 데이터

        Returns:
            Block1Detection 객체
        """
        indicators = stock.indicators if hasattr(stock, 'indicators') else {}

        # 거래대금을 억 단위로 변환
        trading_value_100m = (stock.close * stock.volume) / 100_000_000

        # MA 값 추출
        ma_value = None
        for key, value in indicators.items():
            if key.startswith('MA_'):
                ma_value = value
                break

        return Block1Detection(
            ticker=stock.ticker,
            block1_id="",  # UUID는 __post_init__에서 생성
            status="active",
            started_at=stock.date,
            entry_open=stock.open,
            entry_high=stock.high,
            entry_low=stock.low,
            entry_close=stock.close,
            entry_volume=stock.volume,
            entry_trading_value=trading_value_100m,
            entry_ma_value=ma_value,
            entry_rate=indicators.get('rate'),
            entry_deviation=indicators.get('deviation'),
            condition_name=condition_name,
            created_at=date.today()
        )
