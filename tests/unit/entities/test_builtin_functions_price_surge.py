"""
is_price_doubling_surge() 함수 단위 테스트

시드 탐지 조건: Block1 상승폭 반복 (2배 상승) 감지
"""
import pytest
from datetime import date

from src.domain.entities.conditions.builtin_functions import is_price_doubling_surge
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.domain.entities.core import Stock


class TestIsPriceDoublingSurge:
    """is_price_doubling_surge() 함수 테스트"""

    def test_success_exact_target_price(self):
        """목표가격 정확히 달성 (성공)"""
        # Block1: prev_close=10000, peak_price=15000
        # 상승폭 = 15000 - 10000 = 5000
        # 목표가격 = 15000 + 5000 = 20000
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=15000.0,
            prev_close=10000.0,
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=19500.0,
            high=20000.0,  # 정확히 목표가격
            low=19000.0,
            close=19800.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is True

    def test_success_exceeds_target_price(self):
        """목표가격 초과 (성공)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=15000.0,
            prev_close=10000.0,
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=19500.0,
            high=21000.0,  # 목표가격 20000 초과
            low=19000.0,
            close=20500.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is True

    def test_failure_below_target_price(self):
        """목표가격 미달 (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=15000.0,
            prev_close=10000.0,
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=18000.0,
            high=19500.0,  # 목표가격 20000 미달
            low=17500.0,
            close=19000.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is False

    def test_failure_no_prev_close(self):
        """prev_close 없음 (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=15000.0,
            prev_close=None,  # prev_close 없음
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=19500.0,
            high=21000.0,
            low=19000.0,
            close=20500.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is False

    def test_failure_no_peak_price(self):
        """peak_price 없음 (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=None,  # peak_price 없음
            prev_close=10000.0,
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=19500.0,
            high=21000.0,
            low=19000.0,
            close=20500.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is False

    def test_failure_no_block(self):
        """블록 없음 (실패)"""
        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=19500.0,
            high=21000.0,
            low=19000.0,
            close=20500.0,
            volume=1000000
        )

        context = {
            'current': current
            # block1 없음
        }

        result = is_price_doubling_surge('block1', context)
        assert result is False

    def test_failure_zero_prev_close(self):
        """prev_close가 0 (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=15000.0,
            prev_close=0.0,  # 0은 유효하지 않음
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=19500.0,
            high=21000.0,
            low=19000.0,
            close=20500.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is False

    def test_realistic_scenario(self):
        """실제 시나리오: 025980 강원랜드 패턴"""
        # Block1: 전일 종가 8000, peak 12000 (상승폭 4000)
        # Block2 목표가: 12000 + 4000 = 16000
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 5),
            peak_price=12000.0,
            prev_close=8000.0,
            status=BlockStatus.COMPLETED
        )

        # Block2 진입 시도: high=16500 (성공)
        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 2, 1),
            open=15000.0,
            high=16500.0,  # 목표가 16000 달성
            low=14800.0,
            close=16200.0,
            volume=2000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is True

    def test_small_surge_scenario(self):
        """작은 상승폭 시나리오"""
        # Block1: prev_close=9000, peak=9500 (상승폭 500)
        # 목표가: 9500 + 500 = 10000
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=9500.0,
            prev_close=9000.0,
            status=BlockStatus.COMPLETED
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),
            open=9800.0,
            high=10100.0,  # 목표가 10000 달성
            low=9700.0,
            close=10000.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current
        }

        result = is_price_doubling_surge('block1', context)
        assert result is True

    def test_no_current_stock(self):
        """current 주가 데이터 없음 (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=15000.0,
            prev_close=10000.0,
            status=BlockStatus.COMPLETED
        )

        context = {
            'block1': block1
            # current 없음
        }

        result = is_price_doubling_surge('block1', context)
        assert result is False
