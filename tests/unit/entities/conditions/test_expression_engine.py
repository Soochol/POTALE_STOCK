"""
ExpressionEngine 단위 테스트
"""
import pytest
from datetime import date
from dataclasses import dataclass
from src.domain.entities.conditions import ExpressionEngine


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


class TestExpressionEngine:
    """ExpressionEngine 테스트"""

    def test_simple_comparison(self):
        """기본 비교 연산 테스트"""
        engine = ExpressionEngine()

        # Context
        context = {
            'current': MockStock(
                ticker='025980',
                date=date(2024, 1, 1),
                open=10000,
                high=11000,
                low=9500,
                close=10500,
                volume=1000000,
                indicators={'rate': 5.0}
            )
        }

        # 테스트 1: 숫자 비교
        assert engine.evaluate("current.close >= 10000", context) == True
        assert engine.evaluate("current.close < 10000", context) == False

        # 테스트 2: 변수 비교
        assert engine.evaluate("current.high > current.low", context) == True

    def test_logical_operators(self):
        """논리 연산자 테스트"""
        engine = ExpressionEngine()

        context = {
            'current': MockStock(
                ticker='025980',
                date=date(2024, 1, 1),
                open=10000,
                high=11000,
                low=9500,
                close=10500,
                volume=1000000
            )
        }

        # and
        assert engine.evaluate(
            "current.close >= 10000 and current.high >= 11000",
            context
        ) == True

        assert engine.evaluate(
            "current.close >= 10000 and current.high >= 12000",
            context
        ) == False

        # or
        assert engine.evaluate(
            "current.close >= 12000 or current.high >= 11000",
            context
        ) == True

        # not
        assert engine.evaluate(
            "not (current.close < 10000)",
            context
        ) == True

    def test_arithmetic_operations(self):
        """산술 연산 테스트"""
        engine = ExpressionEngine()

        context = {
            'current': MockStock(
                ticker='025980',
                date=date(2024, 1, 1),
                open=10000,
                high=11000,
                low=9500,
                close=10500,
                volume=1000000
            ),
            'prev': MockStock(
                ticker='025980',
                date=date(2023, 12, 31),
                open=9000,
                high=9500,
                low=8800,
                close=9000,
                volume=500000
            )
        }

        # 곱셈
        assert engine.evaluate("current.volume >= prev.volume * 2", context) == True

        # 나눗셈
        assert engine.evaluate("current.close / prev.close >= 1.1", context) == True

        # 복합 연산
        result = engine.evaluate(
            "(current.close - prev.close) / prev.close * 100 >= 15.0",
            context
        )
        # (10500 - 9000) / 9000 * 100 = 16.67%
        assert result == True

    def test_attribute_access(self):
        """속성 접근 테스트"""
        engine = ExpressionEngine()

        context = {
            'current': MockStock(
                ticker='025980',
                date=date(2024, 1, 1),
                open=10000,
                high=11000,
                low=9500,
                close=10500,
                volume=1000000,
                indicators={'rate': 12.5, 'ma_120': 9500}
            )
        }

        # 일반 속성
        assert engine.evaluate("current.close >= 10000", context) == True

        # indicators 딕셔너리
        assert engine.evaluate("current.rate >= 10.0", context) == True
        assert engine.evaluate("current.ma_120 <= 10000", context) == True

    def test_invalid_expression(self):
        """유효하지 않은 표현식 테스트"""
        engine = ExpressionEngine()
        context = {}

        # 구문 오류
        with pytest.raises(ValueError, match="구문 오류"):
            engine.evaluate("current.close >= ", context)

        # 알 수 없는 변수
        with pytest.raises(ValueError, match="알 수 없는 변수"):
            engine.evaluate("unknown_var >= 10", context)

    def test_validate_expression(self):
        """표현식 검증 테스트"""
        engine = ExpressionEngine()

        # 유효한 표현식
        assert engine.validate_expression("current.close >= 10000") == True
        assert engine.validate_expression("a > b and c < d") == True

        # 유효하지 않은 표현식
        assert engine.validate_expression("current.close >=") == False
        assert engine.validate_expression("if x:") == False
