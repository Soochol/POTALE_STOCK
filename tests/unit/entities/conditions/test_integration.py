"""
통합 테스트: ExpressionEngine + FunctionRegistry + Builtin Functions
"""
import pytest
from datetime import date
from dataclasses import dataclass
from src.domain.entities.conditions import (
    ExpressionEngine,
    function_registry
)


@dataclass
class MockStock:
    """테스트용 Mock Stock 객체"""
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    indicators: dict = None

    def __post_init__(self):
        if self.indicators is None:
            self.indicators = {}


@dataclass
class MockBlockDetection:
    """테스트용 Mock Block Detection 객체"""
    ticker: str
    started_at: date
    peak_price: float
    peak_volume: int
    status: str


class TestIntegration:
    """통합 테스트"""

    def test_expression_with_ma_function(self):
        """이동평균 함수를 사용한 표현식 테스트"""
        engine = ExpressionEngine(function_registry)

        # Mock data (timedelta를 사용하여 날짜 생성)
        from datetime import timedelta
        base_date = date(2024, 1, 1)
        all_stocks = [
            MockStock('025980', base_date + timedelta(days=i), 10000, 10000+i*100, 10000-i*50, 10000+i*50, 1000000)
            for i in range(120)
        ]

        context = {
            'current': all_stocks[-1],
            'all_stocks': all_stocks
        }

        # 테스트: current.high >= ma(120)
        result = engine.evaluate("current.high >= ma(120)", context)
        assert isinstance(result, bool)

    def test_expression_with_candles_between(self):
        """candles_between 함수 테스트"""
        engine = ExpressionEngine(function_registry)

        # Mock data
        all_stocks = [
            MockStock('025980', date(2024, 1, i), 10000, 11000, 9500, 10500, 1000000)
            for i in range(1, 31)
        ]

        block1 = MockBlockDetection(
            ticker='025980',
            started_at=date(2024, 1, 10),
            peak_price=11000,
            peak_volume=2000000,
            status='active'
        )

        context = {
            'current': all_stocks[-1],  # 2024-01-30
            'all_stocks': all_stocks,
            'block1': block1
        }

        # 테스트: candles_between(block1.started_at, current.date) >= 20
        result = engine.evaluate(
            "candles_between(block1.started_at, current.date) >= 20",
            context
        )
        # 2024-01-10 ~ 2024-01-30 = 21일
        assert result == True

    def test_expression_with_within_range(self):
        """within_range 함수 테스트"""
        engine = ExpressionEngine(function_registry)

        current = MockStock('025980', date(2024, 1, 30), 10000, 10500, 9800, 10200, 1000000)
        seed_block = MockBlockDetection(
            ticker='025980',
            started_at=date(2024, 1, 10),
            peak_price=10000,
            peak_volume=2000000,
            status='completed'
        )

        context = {
            'current': current,
            'seed_block1': seed_block
        }

        # 테스트: within_range(current.close, seed_block1.peak_price, 10.0)
        result = engine.evaluate(
            "within_range(current.close, seed_block1.peak_price, 10.0)",
            context
        )
        # 10200은 10000의 ±10% 범위 내 (9000~11000)
        assert result == True

        # 범위 밖
        current.close = 12000
        result = engine.evaluate(
            "within_range(current.close, seed_block1.peak_price, 10.0)",
            context
        )
        assert result == False

    def test_expression_with_days_since(self):
        """days_since 함수 테스트"""
        engine = ExpressionEngine(function_registry)

        current = MockStock('025980', date(2024, 1, 30), 10000, 10500, 9800, 10200, 1000000)
        block1 = MockBlockDetection(
            ticker='025980',
            started_at=date(2024, 1, 10),
            peak_price=11000,
            peak_volume=2000000,
            status='completed'
        )
        block1.ended_at = date(2024, 1, 20)

        context = {
            'current': current,
            'block1': block1
        }

        # 테스트: days_since(block1.ended_at) <= 15
        result = engine.evaluate(
            "days_since(block1.ended_at) <= 15",
            context
        )
        # 2024-01-20 ~ 2024-01-30 = 10일
        assert result == True

    def test_complex_expression(self):
        """복잡한 표현식 통합 테스트"""
        engine = ExpressionEngine(function_registry)

        # Mock data (timedelta를 사용하여 날짜 생성)
        from datetime import timedelta
        base_date = date(2024, 1, 1)
        all_stocks = [
            MockStock('025980', base_date + timedelta(days=i), 10000, 10000+i*100, 10000-i*50, 10000+i*50, 1000000)
            for i in range(120)
        ]

        current = all_stocks[-1]
        current.close = 15000
        current.high = 15500
        current.volume = 3000000

        prev = all_stocks[-2]

        block1 = MockBlockDetection(
            ticker='025980',
            started_at=date(2024, 1, 10),
            peak_price=14000,
            peak_volume=2500000,
            status='active'
        )

        context = {
            'current': current,
            'prev': prev,
            'all_stocks': all_stocks,
            'block1': block1
        }

        # 복잡한 표현식
        expression = (
            "(current.close >= 10000) and "
            "(current.high >= ma(120)) and "
            "(current.volume >= prev.volume * 2) and "
            "(candles_between(block1.started_at, current.date) >= 2) and "
            "(current.close >= block1.peak_price * 0.95)"
        )

        result = engine.evaluate(expression, context)
        assert isinstance(result, bool)

    def test_builtin_functions_registered(self):
        """내장 함수들이 제대로 등록되었는지 확인"""
        # 핵심 함수들이 등록되어 있는지 확인
        essential_functions = ['ma', 'candles_between', 'days_since', 'within_range']

        for func_name in essential_functions:
            assert func_name in function_registry.list_functions()

        # 카테고리별로 함수가 있는지 확인
        by_category = function_registry.get_functions_by_category()
        assert 'moving_average' in by_category
        assert 'time' in by_category
        assert 'price' in by_category

    def test_EXISTS_function(self):
        """EXISTS 함수 테스트"""
        engine = ExpressionEngine(function_registry)

        block1 = MockBlockDetection(
            ticker='025980',
            started_at=date(2024, 1, 10),
            peak_price=11000,
            peak_volume=2000000,
            status='active'
        )

        context = {
            'current': MockStock('025980', date(2024, 1, 30), 10000, 10500, 9800, 10200, 1000000),
            'block1': block1
        }

        # block1이 존재함
        result = engine.evaluate("EXISTS('block1')", context)
        assert result == True

        # block2는 존재하지 않음
        result = engine.evaluate("EXISTS('block2')", context)
        assert result == False

    def test_is_volume_high_from_indicators(self):
        """indicators에서 is_volume_high 조회 테스트"""
        engine = ExpressionEngine(function_registry)

        current = MockStock(
            '025980',
            date(2024, 1, 30),
            10000,
            10500,
            9800,
            10200,
            1000000,
            indicators={'is_volume_high_120d': True}
        )

        context = {'current': current}

        result = engine.evaluate("is_volume_high(120)", context)
        assert result == True
