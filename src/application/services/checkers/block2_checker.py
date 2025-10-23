"""
Block2 Checker Service - 블록2 진입/종료 조건 검사 서비스
"""
from datetime import date, timedelta
from typing import List, Optional

from src.domain.entities import (
    Block1Condition,
    Block1Detection,
    Block2Condition,
    Block2Detection,
    Stock,
)

from ..common.utils import get_previous_trading_day_stock
from .block1_checker import Block1Checker

class Block2Checker:
    """블록2 진입 및 종료 조건 검사 서비스"""

    def __init__(self) -> None:
        """Block2Checker 초기화"""
        self.block1_checker = Block1Checker()

    def check_entry(
        self,
        condition: Block2Condition,
        stock: Stock,
        all_stocks: List[Stock],
        prev_seed_block1: Optional[Block1Detection] = None
    ) -> bool:
        """
        블록2 진입 조건 검사
        = 블록1의 모든 조건 + 블록2 추가 조건 2가지

        Args:
            condition: 블록2 조건
            stock: 주식 데이터 (지표 포함)
            all_stocks: 전체 주식 데이터 리스트 (마지막 거래일 조회용)
            prev_seed_block1: 이전 Seed Block1 (volume_ratio, low_price_margin 비교 기준)

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

        # 조건 2: 고가 >= 이동평균선 N (ma_period가 null이면 skip, 값이 있으면 항상 체크)
        if condition.base.block1_entry_ma_period:
            ma_key = f'MA_{condition.base.block1_entry_ma_period}'
            ma_value = indicators.get(ma_key)
            if ma_value is None or stock.high < ma_value:
                return False

        # 조건 3: 이격도 (MA를 100으로 봤을 때 종가 비율)
        if condition.base.block1_entry_max_deviation_ratio is not None:
            # 동적 필드 이름: deviation_60, deviation_120 등
            deviation_field = f'deviation_{condition.base.block1_entry_ma_period}'
            deviation = indicators.get(deviation_field, 100)
            if deviation > condition.base.block1_entry_max_deviation_ratio:
                return False

        # 조건 4: 거래대금 N억 이상
        if condition.base.block1_entry_min_trading_value is not None:
            trading_value = indicators.get('trading_value_100m', 0)
            if trading_value < condition.base.block1_entry_min_trading_value:
                return False

        # 조건 5: N개월 신고거래량
        if condition.base.block1_entry_volume_high_days is not None:
            # 동적 필드 이름: is_volume_high_6m, is_volume_high_12m 등
            field_name = f'is_volume_high_{condition.base.block1_entry_volume_high_days}d'
            is_volume_high = indicators.get(field_name, False)
            if not is_volume_high:
                return False

        # 조건 6: 전날 거래량 대비 N% 수준
        if condition.base.block1_entry_volume_spike_ratio is not None:
            prev_stock = get_previous_trading_day_stock(stock.date, all_stocks)
            if prev_stock is None or prev_stock.volume <= 0:
                return False

            ratio = condition.base.block1_entry_volume_spike_ratio / 100.0
            required_volume = prev_stock.volume * ratio
            if stock.volume < required_volume:
                return False

        # 조건 7: N개월 신고가
        if condition.base.block1_entry_price_high_days is not None:
            # 동적 필드 이름: is_new_high_12m, is_new_high_24m 등
            field_name = f'is_new_high_{condition.base.block1_entry_price_high_days}d'
            is_new_high = indicators.get(field_name, False)
            if not is_new_high:
                return False

        # 2. 블록2 추가 조건 검사
        # None의 의미: 조건값이 None이면 해당 조건 스킵 (pass)
        # prev_seed_block1이 None이어도 검사 진행 (단, 값이 없으면 해당 조건 스킵)

        # 추가 조건 1: 블록 거래량 조건 (선택적)
        # 당일_거래량 >= 이전 Seed Block1_최고_거래량 × (ratio/100)
        # block2_volume_ratio는 % 단위 (예: 15 = 15%)
        # None 처리: condition 값 또는 prev_seed_block1 데이터가 None이면 스킵
        if condition.block2_volume_ratio is not None:
            if (
                prev_seed_block1 is not None
                and prev_seed_block1.peak_volume is not None
            ):
                ratio = condition.block2_volume_ratio / 100.0
                required_volume = prev_seed_block1.peak_volume * ratio
                if stock.volume < required_volume:
                    return False
            # prev_seed_block1이 None이거나 peak_volume이 None이면 이 조건 스킵 (pass)

        # 추가 조건 2: 저가 마진 조건 (선택적) - OR 조건
        # 당일_저가 × (1 + margin/100) > 이전 Seed Block1_peak_price (DB)
        # OR
        # 당일_저가 × (1 + margin/100) > Block1 시작~현재 실제 최고가 (range_high)
        # low_price_margin은 % 단위 (예: 10 = 10%)
        # None 처리: condition 값 또는 prev_seed_block1 데이터가 None이면 스킵
        if condition.block2_low_price_margin is not None:
            if (
                prev_seed_block1 is not None
                and prev_seed_block1.peak_price is not None
            ):
                margin = condition.block2_low_price_margin / 100.0
                threshold_price = stock.low * (1 + margin)

                # 조건 1: DB의 peak_price 체크
                meets_db_peak = threshold_price > prev_seed_block1.peak_price

                # 조건 2: 실제 차트 최고가(range_high) 체크
                range_high = self._get_range_high(
                    prev_seed_block1.started_at,
                    stock.date,
                    stock.ticker,
                    all_stocks
                )
                meets_range_high = range_high is not None and threshold_price > range_high

                # OR 조건: 둘 중 하나라도 만족하면 통과
                if not (meets_db_peak or meets_range_high):
                    return False
            # prev_seed_block1이 None이거나 peak_price가 None이면 이 조건 스킵 (pass)

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
        prev_block1: Optional[Block1Detection] = None,
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
            # 시작 거래량 사용
            detection.prev_block1_peak_volume = prev_block1.entry_volume

        return detection

    def check_cooldown(
        self,
        ticker: str,
        current_date: date,
        existing_detections: List[Block2Detection],
        min_start_interval_days: int
    ) -> bool:
        """
        중복 방지 기간 확인

        Args:
            ticker: 종목코드
            current_date: 현재 날짜
            existing_detections: 기존 블록2 탐지 결과 리스트
            min_start_interval_days: 같은 레벨 블록 중복 방지: 시작 후 N일간 새 블록 탐지 금지

        Returns:
            탐지 가능 여부 (True: 가능, False: 중복 방지 기간 내)
        """
        for detection in existing_detections:
            if detection.ticker != ticker:
                continue

            # 활성 블록2가 있으면 불가
            if detection.status == "active":
                return False

            # 종료된 블록2이지만 min_start_interval 기간 내면 불가
            if detection.ended_at:
                interval_end = detection.started_at + timedelta(
                    days=min_start_interval_days
                )
                if detection.started_at <= current_date < interval_end:
                    return False

        return True

    def check_min_candles(
        self,
        current_date: date,
        prev_seed_block1: Optional[Block1Detection],
        min_candles: int,
        all_stocks: List[Stock],
    ) -> bool:
        """
        이전 Seed Block 시작 후 최소 캔들 수 확인

        중요 - 캔들 카운팅 로직:
        - 이전 Seed Block 시작일을 1번째 캔들로 간주 (포함)
        - min_candles는 "N개 캔들 이후"를 의미 (N+1번째부터 탐지 가능)
        - 따라서 조건: candles_count > min_candles (등호 없음!)

        예시:
        - Block1 시작일: 2024-01-08 (1번째 캔들)
        - min_candles=4 설정 시
        - 2024-01-09 (2번째) → count=2, 2 > 4? False (불가)
        - 2024-01-10 (3번째) → count=3, 3 > 4? False (불가)
        - 2024-01-11 (4번째) → count=4, 4 > 4? False (불가)
        - 2024-01-12 (5번째) → count=5, 5 > 4? True (가능!) ← 여기부터 탐지

        Args:
            current_date: 현재 날짜 (탐지 후보일)
            prev_seed_block1: 이전 Seed Block (Block2 체크 시)
            min_candles: 최소 대기 캔들 수 (N개 캔들 이후부터 탐지)
            all_stocks: 전체 주식 데이터 (날짜순 정렬 필요)

        Returns:
            bool: 조건 만족 여부
                - True: 최소 캔들 수 조건 통과 (탐지 가능)
                - False: 아직 충분한 캔들이 지나지 않음

        Note:
            - prev_seed_block이 None이면 조건 무시 (항상 True 반환)
            - 거래일 기준 카운트 (공휴일/거래정지 자동 제외)
        """
        if prev_seed_block1 is None:
            # 이전 Seed Block1이 없으면 조건 무시
            return True

        # 이전 Seed Block1 시작일부터 현재일까지의 캔들 수 계산
        candles_count = self._count_candles_between(
            prev_seed_block1.started_at,
            current_date,
            all_stocks
        )

        # 이전 Seed Block1 시작일 = 1번째 캔들
        # min_candles=4 → 5번째 캔들부터 가능
        # 즉, candles_count > min_candles
        return candles_count > min_candles

    def check_max_candles(
        self,
        current_date: date,
        prev_seed_block1: Optional[Block1Detection],
        max_candles: int,
        all_stocks: List[Stock],
    ) -> bool:
        """
        이전 Seed Block1 시작 후 최대 캔들 수 확인

        Args:
            current_date: 현재 날짜
            prev_seed_block1: 이전 Seed Block1
            max_candles: 최대 캔들 수
            all_stocks: 전체 주식 데이터 (날짜순 정렬)

        Returns:
            조건 만족 여부 (True: 가능, False: 최대 캔들 수 초과)
        """
        if prev_seed_block1 is None or max_candles is None:
            # 이전 Seed Block1이 없거나 조건이 없으면 무시
            return True

        # 이전 Seed Block1 시작일부터 현재일까지의 캔들 수 계산
        candles_count = self._count_candles_between(
            prev_seed_block1.started_at,
            current_date,
            all_stocks
        )

        # max_candles 이내여야 함
        return candles_count <= max_candles

    def _count_candles_between(
        self, start_date: date, end_date: date, all_stocks: List[Stock]
    ) -> int:
        """
        두 날짜 사이의 실제 거래일 캔들 수 계산

        중요 - 거래일 기준 vs 달력 기준:
        - 이 함수는 "거래일" 기준으로 캔들 수를 셈 (공휴일/거래정지일 제외)
        - DB에는 거래일만 저장되므로 자동으로 비거래일 필터링됨
        - 달력 기준 계산(timedelta)과는 다름 (재탐지 기간은 달력 기준 사용)

        포함 범위:
        - start_date와 end_date 모두 포함 (inclusive, closed interval)
        - 예: start=1/8, end=1/11 → 1/8, 1/9, 1/10, 1/11 모두 카운트

        Args:
            start_date: 시작 날짜 (포함)
            end_date: 종료 날짜 (포함)
            all_stocks: 전체 주식 데이터 리스트 (날짜순 정렬 필요)

        Returns:
            int: 거래일 캔들 수

        Example:
            >>> # 2024-01-08(월), 01-09(화), 01-10(공휴일), 01-11(목)
            >>> # all_stocks = [Stock(2024-01-08), Stock(2024-01-09), Stock(2024-01-11)]
            >>> count = _count_candles_between(date(2024,1,8), date(2024,1,11), all_stocks)
            >>> # 결과: 3 (실제 거래일만 카운트, 공휴일 제외)

        Note:
            - 시간 복잡도: O(n) - 전체 리스트 순회
            - min_candles/max_candles 체크에 사용됨
        """
        count = 0
        for stock in all_stocks:
            if start_date <= stock.date <= end_date:
                count += 1
        return count

    def _get_range_high(
        self,
        start_date: date,
        end_date: date,
        ticker: str,
        all_stocks: List[Stock]
    ) -> Optional[float]:
        """
        지정된 기간의 실제 최고가(range_high) 계산

        Args:
            start_date: 시작일 (포함)
            end_date: 종료일 (포함)
            ticker: 종목 코드
            all_stocks: 전체 주식 데이터

        Returns:
            기간 내 최고가, 데이터가 없으면 None
        """
        max_high = None
        for stock in all_stocks:
            if (stock.ticker == ticker and
                start_date <= stock.date <= end_date):
                if max_high is None or stock.high > max_high:
                    max_high = stock.high
        return max_high

    def _convert_to_block1_detection(
        self, block2: Block2Detection
    ) -> Block1Detection:
        """
        Block2Detection을 Block1Detection 형식으로 변환

        종료 조건 검사를 위해 Block1Checker 재사용

        Args:
            block2: Block2Detection 객체

        Returns:
            Block1Detection 객체
        """
        return Block1Detection(
            ticker=block2.ticker,
            block1_id="",  # 임시
            status=block2.status,
            started_at=block2.started_at,
            ended_at=block2.ended_at,
            # Block2는 open 정보가 없으므로 close 사용
            entry_open=block2.entry_close,
            entry_high=block2.entry_close,
            entry_low=block2.entry_close,
            entry_close=block2.entry_close,
            entry_volume=0,  # Block2에 없음
            entry_trading_value=0.0,
            condition_name=block2.condition_name,
            created_at=date.today(),
        )
