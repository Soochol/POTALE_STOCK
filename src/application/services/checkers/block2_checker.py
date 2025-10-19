"""
Block2 Checker Service - 블록2 진입/종료 조건 검사 서비스
"""
from typing import Optional, List
from datetime import date, timedelta
from src.domain.entities.stock import Stock
from src.domain.entities.block2_condition import Block2Condition
from src.domain.entities.block2_detection import Block2Detection
from src.domain.entities.block1_detection import Block1Detection
from src.domain.entities.block1_condition import Block1Condition
from .block1_checker import Block1Checker


class Block2Checker:
    """블록2 진입 및 종료 조건 검사 서비스"""

    def __init__(self):
        self.block1_checker = Block1Checker()

    def check_entry(
        self,
        condition: Block2Condition,
        stock: Stock,
        prev_stock: Optional[Stock] = None,
        prev_block1: Optional[Block1Detection] = None
    ) -> bool:
        """
        블록2 진입 조건 검사
        = 블록1의 모든 조건 + 블록2 추가 조건 2가지

        Args:
            condition: 블록2 조건
            stock: 주식 데이터 (지표 포함)
            prev_stock: 전일 주식 데이터 (전날 거래량 조건용, 선택적)
            prev_block1: 직전 블록1 탐지 결과 (추가 조건용, 선택적)

        Returns:
            모든 조건 만족 여부
        """
        # 1. Block1 기본 조건 검사
        if not hasattr(stock, 'indicators'):
            return False

        indicators = stock.indicators

        # 조건 1: 등락률 (전일 대비 N% 이상, 양수만)
        if condition.base.block1_entry_surge_rate is not None:
            rate = indicators.get('rate', 0)
            if rate < condition.base.block1_entry_surge_rate:
                return False

        # 조건 2: 고가 >= 이동평균선 N
        if condition.base.block1_entry_ma_period and condition.base.block1_entry_high_above_ma:
            ma_key = f'MA_{condition.base.block1_entry_ma_period}'
            ma_value = indicators.get(ma_key)
            if ma_value is None or stock.high < ma_value:
                return False

        # 조건 3: 이격도 (MA를 100으로 봤을 때 종가 비율)
        if condition.base.block1_entry_max_deviation_ratio is not None:
            deviation = indicators.get('deviation', 100)
            if deviation > condition.base.block1_entry_max_deviation_ratio:
                return False

        # 조건 4: 거래대금 N억 이상
        if condition.base.block1_entry_min_trading_value is not None:
            trading_value = indicators.get('trading_value_100m', 0)
            if trading_value < condition.base.block1_entry_min_trading_value:
                return False

        # 조건 5: N개월 신고거래량
        if condition.base.block1_entry_volume_high_months is not None:
            is_volume_high = indicators.get('is_volume_high', False)
            if not is_volume_high:
                return False

        # 조건 6: 전날 거래량 대비 N% 수준
        if condition.base.block1_entry_volume_spike_ratio is not None:
            if prev_stock is None:
                return False

            ratio = condition.base.block1_entry_volume_spike_ratio / 100.0
            required_volume = prev_stock.volume * ratio
            if stock.volume < required_volume:
                return False

        # 조건 7: N개월 신고가
        if condition.base.block1_entry_price_high_months is not None:
            is_new_high = indicators.get('is_new_high', False)
            if not is_new_high:
                return False

        # 2. 블록2 추가 조건 검사
        # 추가 조건을 위해서는 prev_block1이 필요 (독립적으로 시작하는 경우 prev_block1이 없을 수 있음)
        if prev_block1 is None:
            # 독립적으로 시작하는 경우: 블록1 조건만 만족하면 OK
            # (실제로는 직전 블록1을 찾아서 전달해야 하지만, 없으면 추가 조건 스킵)
            return True

        # 추가 조건 1: 블록 거래량 조건 (선택적)
        # 당일_거래량 >= 블록1_최고_거래량 × (block_volume_ratio/100)
        # block_volume_ratio는 % 단위 (예: 15 = 15%)
        if condition.block2_volume_ratio is not None and prev_block1.peak_volume is not None:
            ratio = condition.block2_volume_ratio / 100.0
            required_volume = prev_block1.peak_volume * ratio
            if stock.volume < required_volume:
                return False

        # 추가 조건 2: 저가 마진 조건 (선택적)
        # 당일_저가 × (1 + low_price_margin/100) > 블록1_peak_price
        # low_price_margin은 % 단위 (예: 10 = 10%)
        if condition.block2_low_price_margin is not None and prev_block1.peak_price is not None:
            margin = condition.block2_low_price_margin / 100.0
            threshold_price = stock.low * (1 + margin)
            if threshold_price <= prev_block1.peak_price:
                return False

        # 모든 조건 만족
        return True

    def check_exit(
        self,
        condition: Block2Condition,
        detection: Block2Detection,
        current_stock: Stock,
        all_stocks: list
    ) -> Optional[str]:
        """
        블록2 종료 조건 검사
        = 블록1과 동일한 3가지 종료 조건 중 택1

        Args:
            condition: 블록2 조건
            detection: 블록2 탐지 결과
            current_stock: 현재 주식 데이터
            all_stocks: 전체 주식 데이터 (삼선전환도 계산용)

        Returns:
            종료 사유 또는 None
        """
        # Block1Detection 형식으로 변환하여 block1_checker 재사용
        temp_block1 = self._convert_to_block1_detection(detection)

        # Block2Condition에서 Block1Condition 임시 생성
        temp_block1_condition = Block1Condition(
            base=condition.base  # BaseEntryCondition을 그대로 사용
        )

        # Block1 종료 조건 검사 재사용
        exit_reason = self.block1_checker.check_exit(
            temp_block1_condition,
            temp_block1,
            current_stock,
            all_stocks
        )

        return exit_reason

    def create_detection(
        self,
        condition_name: str,
        stock: Stock,
        prev_block1: Optional[Block1Detection] = None
    ) -> Block2Detection:
        """
        블록2 탐지 결과 생성

        Args:
            condition_name: 조건 이름
            stock: 진입 시점 주식 데이터
            prev_block1: 직전 블록1 탐지 결과

        Returns:
            Block2Detection 객체
        """
        indicators = stock.indicators if hasattr(stock, 'indicators') else {}

        detection = Block2Detection(
            ticker=stock.ticker,
            condition_name=condition_name,
            started_at=stock.date,
            status="active",
            entry_close=stock.close,
            entry_rate=indicators.get('rate'),
        )

        # 직전 블록1 정보 저장
        if prev_block1:
            detection.prev_block1_id = prev_block1.id
            detection.prev_block1_peak_price = prev_block1.peak_price
            detection.prev_block1_peak_volume = prev_block1.entry_volume  # 시작 거래량 사용

        return detection

    def check_cooldown(
        self,
        ticker: str,
        current_date: date,
        existing_detections: List[Block2Detection],
        cooldown_days: int
    ) -> bool:
        """
        중복 방지 기간 확인

        Args:
            ticker: 종목코드
            current_date: 현재 날짜
            existing_detections: 기존 블록2 탐지 결과 리스트
            cooldown_days: 재탐지 제외 기간 (일)

        Returns:
            탐지 가능 여부 (True: 가능, False: 중복 방지 기간 내)
        """
        for detection in existing_detections:
            if detection.ticker != ticker:
                continue

            # 활성 블록2가 있으면 불가
            if detection.status == "active":
                return False

            # 종료된 블록2이지만 cooldown 기간 내면 불가
            if detection.ended_at:
                cooldown_end = detection.started_at + timedelta(days=cooldown_days)
                if detection.started_at <= current_date < cooldown_end:
                    return False

        return True

    def check_min_candles(
        self,
        current_date: date,
        prev_block1: Optional[Block1Detection],
        min_candles: int,
        all_stocks: List[Stock]
    ) -> bool:
        """
        블록1 시작 후 최소 캔들 수 확인

        Args:
            current_date: 현재 날짜
            prev_block1: 직전 블록1
            min_candles: 최소 캔들 수
            all_stocks: 전체 주식 데이터 (캔들 수 계산용, 날짜순 정렬)

        Returns:
            조건 만족 여부 (True: 가능, False: 최소 캔들 수 미만)
        """
        if prev_block1 is None:
            # 직전 블록1이 없으면 조건 무시
            return True

        # 블록1 시작일부터 현재일까지의 캔들 수 계산
        candles_count = self._count_candles_between(
            prev_block1.started_at,
            current_date,
            all_stocks
        )

        # 블록1 시작일 = 1번째 캔들
        # min_candles=4 → 5번째 캔들부터 가능
        # 즉, candles_count > min_candles
        return candles_count > min_candles

    def _count_candles_between(
        self,
        start_date: date,
        end_date: date,
        all_stocks: List[Stock]
    ) -> int:
        """
        두 날짜 사이의 캔들 수 계산 (start_date와 end_date 포함)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            all_stocks: 전체 주식 데이터 리스트

        Returns:
            캔들 수
        """
        count = 0
        for stock in all_stocks:
            if start_date <= stock.date <= end_date:
                count += 1
        return count

    def _convert_to_block1_detection(self, block2: Block2Detection) -> Block1Detection:
        """
        Block2Detection을 Block1Detection 형식으로 변환
        (종료 조건 검사를 위해 Block1Checker 재사용)
        """
        return Block1Detection(
            ticker=block2.ticker,
            block1_id="",  # 임시
            status=block2.status,
            started_at=block2.started_at,
            ended_at=block2.ended_at,
            entry_open=block2.entry_close,  # Block2는 open 정보가 없으므로 close 사용
            entry_high=block2.entry_close,
            entry_low=block2.entry_close,
            entry_close=block2.entry_close,
            entry_volume=0,  # Block2에 없음
            entry_trading_value=0.0,
            condition_name=block2.condition_name,
            created_at=date.today()
        )
