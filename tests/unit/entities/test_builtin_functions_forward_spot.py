"""
is_forward_spot() 함수 단위 테스트

전진형 Spot 패턴 감지: Block 시작 후 D+1, D+2일 체크
"""
import pytest
from datetime import date

from src.domain.entities.conditions.builtin_functions import is_forward_spot
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.domain.entities.core import Stock


class TestIsForwardSpot:
    """is_forward_spot() 함수 테스트"""

    def test_success_at_d_plus_1(self):
        """D+1일에 조건 만족 (성공)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),  # D일
            peak_price=15000.0,
            status=BlockStatus.ACTIVE
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 11),  # D+1일
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        # all_stocks: D일부터 D+1일까지
        all_stocks = [
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 10),  # D일
                open=14000.0,
                high=15000.0,
                low=13500.0,
                close=14800.0,
                volume=500000
            ),
            current  # D+1일
        ]

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': all_stocks
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is True

    def test_success_at_d_plus_2(self):
        """D+2일에 조건 만족 (성공)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),  # D일
            peak_price=15000.0,
            status=BlockStatus.ACTIVE
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 12),  # D+2일
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        # all_stocks: D일부터 D+2일까지
        all_stocks = [
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 10),  # D일
                open=14000.0,
                high=15000.0,
                low=13500.0,
                close=14800.0,
                volume=500000
            ),
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 11),  # D+1일
                open=14800.0,
                high=15200.0,
                low=14500.0,
                close=15000.0,
                volume=600000
            ),
            current  # D+2일
        ]

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': all_stocks
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is True

    def test_failure_at_d_plus_0(self):
        """D일 (시작일 당일)에는 False (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),  # D일
            peak_price=15000.0,
            status=BlockStatus.ACTIVE
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 10),  # D일 (당일)
            open=14000.0,
            high=15000.0,
            low=13500.0,
            close=14800.0,
            volume=500000
        )

        all_stocks = [current]

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': all_stocks
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is False

    def test_failure_at_d_plus_3(self):
        """D+3일 (범위 초과)에는 False (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),  # D일
            peak_price=15000.0,
            status=BlockStatus.ACTIVE
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 15),  # D+3일 (범위 초과)
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        # all_stocks: D일부터 D+3일까지
        all_stocks = [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10), open=14000.0, high=15000.0, low=13500.0, close=14800.0, volume=500000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 11), open=14800.0, high=15200.0, low=14500.0, close=15000.0, volume=600000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 12), open=15000.0, high=15500.0, low=14800.0, close=15300.0, volume=700000),
            current
        ]

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': all_stocks
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is False

    def test_failure_block_not_active(self):
        """블록이 ACTIVE 상태가 아니면 False (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),
            peak_price=15000.0,
            status=BlockStatus.COMPLETED  # ACTIVE가 아님
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 11),  # D+1일
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        all_stocks = [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10), open=14000.0, high=15000.0, low=13500.0, close=14800.0, volume=500000),
            current
        ]

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': all_stocks
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is False

    def test_failure_block_not_exists(self):
        """블록이 존재하지 않으면 False (실패)"""
        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 11),
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        context = {
            'current': current,
            'all_stocks': [current]
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is False

    def test_failure_all_stocks_empty(self):
        """all_stocks가 비어있으면 False (실패)"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),
            peak_price=15000.0,
            status=BlockStatus.ACTIVE
        )

        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 11),
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': []  # 비어있음
        }

        result = is_forward_spot('block1', 1, 2, context)
        assert result is False

    def test_custom_offset_range(self):
        """커스텀 offset 범위 (1~5) 테스트"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),
            peak_price=15000.0,
            status=BlockStatus.ACTIVE
        )

        # D+3일 테스트
        current = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 13),  # D+3일
            open=15000.0,
            high=16500.0,
            low=15000.0,
            close=16000.0,
            volume=1000000
        )

        all_stocks = [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10), open=14000.0, high=15000.0, low=13500.0, close=14800.0, volume=500000),  # D
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 11), open=14800.0, high=15200.0, low=14500.0, close=15000.0, volume=600000),  # D+1
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 12), open=15000.0, high=15500.0, low=14800.0, close=15300.0, volume=700000),  # D+2
            current  # D+3
        ]

        context = {
            'block1': block1,
            'current': current,
            'all_stocks': all_stocks
        }

        # offset_start=1, offset_end=5 범위에서는 D+3일이 True
        result = is_forward_spot('block1', 1, 5, context)
        assert result is True

        # offset_start=1, offset_end=2 범위에서는 D+3일이 False
        result = is_forward_spot('block1', 1, 2, context)
        assert result is False
