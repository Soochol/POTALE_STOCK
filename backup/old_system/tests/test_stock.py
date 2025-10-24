"""
Unit tests for Stock entity

Tests the Stock domain entity behavior and properties.
"""
import pytest
from datetime import date
from src.domain.entities.core.stock import Stock


@pytest.mark.unit
@pytest.mark.entity
class TestStockCreation:
    """Test Stock entity creation"""

    def test_create_minimal_stock(self):
        """Test creating Stock with required fields only"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000
        )

        assert stock.ticker == "005930"
        assert stock.name == "삼성전자"
        assert stock.date == date(2024, 1, 15)
        assert stock.open == 75000.0
        assert stock.high == 76000.0
        assert stock.low == 74500.0
        assert stock.close == 75500.0
        assert stock.volume == 10000000

    def test_create_stock_with_optional_fields(self):
        """Test creating Stock with all optional fields"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000,
            market_cap=500000.0,
            per=15.5,
            pbr=1.2,
            eps=5000.0,
            div=2.5,
            trading_value=755,
            adjustment_ratio=1.0
        )

        assert stock.market_cap == 500000.0
        assert stock.per == 15.5
        assert stock.pbr == 1.2
        assert stock.eps == 5000.0
        assert stock.div == 2.5
        assert stock.trading_value == 755
        assert stock.adjustment_ratio == 1.0


@pytest.mark.unit
@pytest.mark.entity
class TestStockValidation:
    """Test Stock validation rules"""

    def test_validation_zero_price_raises_error(self):
        """Test that zero price raises ValueError"""
        with pytest.raises(ValueError, match="가격은 0보다 커야 합니다"):
            Stock(
                ticker="005930",
                name="삼성전자",
                date=date(2024, 1, 15),
                open=0.0,
                high=76000.0,
                low=74500.0,
                close=75500.0,
                volume=10000000
            )

    def test_validation_negative_price_raises_error(self):
        """Test that negative price raises ValueError"""
        with pytest.raises(ValueError, match="가격은 0보다 커야 합니다"):
            Stock(
                ticker="005930",
                name="삼성전자",
                date=date(2024, 1, 15),
                open=75000.0,
                high=76000.0,
                low=-100.0,
                close=75500.0,
                volume=10000000
            )

    def test_validation_negative_volume_raises_error(self):
        """Test that negative volume raises ValueError"""
        with pytest.raises(ValueError, match="거래량은 0 이상이어야 합니다"):
            Stock(
                ticker="005930",
                name="삼성전자",
                date=date(2024, 1, 15),
                open=75000.0,
                high=76000.0,
                low=74500.0,
                close=75500.0,
                volume=-1000
            )

    def test_validation_high_less_than_low_raises_error(self):
        """Test that high < low raises ValueError"""
        with pytest.raises(ValueError, match="고가는 저가보다 높아야 합니다"):
            Stock(
                ticker="005930",
                name="삼성전자",
                date=date(2024, 1, 15),
                open=75000.0,
                high=74000.0,  # high < low
                low=76000.0,
                close=75500.0,
                volume=10000000
            )

    def test_validation_close_outside_range_raises_error(self):
        """Test that close outside high-low range raises ValueError"""
        with pytest.raises(ValueError, match="종가는 고가와 저가 사이에 있어야 합니다"):
            Stock(
                ticker="005930",
                name="삼성전자",
                date=date(2024, 1, 15),
                open=75000.0,
                high=76000.0,
                low=74500.0,
                close=77000.0,  # close > high
                volume=10000000
            )


@pytest.mark.unit
@pytest.mark.entity
class TestStockProperties:
    """Test Stock calculated properties"""

    def test_price_change_positive(self):
        """Test price_change property for positive change"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000
        )

        # price_change = (close - open) / open
        # = (75500 - 75000) / 75000 = 500 / 75000 = 0.006666...
        expected = (75500.0 - 75000.0) / 75000.0
        assert abs(stock.price_change - expected) < 0.0001

    def test_price_change_negative(self):
        """Test price_change property for negative change"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75500.0,
            high=76000.0,
            low=74500.0,
            close=75000.0,
            volume=10000000
        )

        # price_change = (close - open) / open
        # = (75000 - 75500) / 75500 = -500 / 75500 = -0.00662...
        expected = (75000.0 - 75500.0) / 75500.0
        assert abs(stock.price_change - expected) < 0.0001

    def test_price_change_no_change(self):
        """Test price_change when close == open"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75000.0,
            volume=10000000
        )

        # When close == open, price_change should be 0
        assert stock.price_change == 0.0

    def test_is_up_true(self):
        """Test is_up property when close > open"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000
        )

        assert stock.is_up is True

    def test_is_up_false(self):
        """Test is_up property when close <= open"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75500.0,
            high=76000.0,
            low=74500.0,
            close=75000.0,
            volume=10000000
        )

        assert stock.is_up is False

    def test_is_down_true(self):
        """Test is_down property when close < open"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75500.0,
            high=76000.0,
            low=74500.0,
            close=75000.0,
            volume=10000000
        )

        assert stock.is_down is True

    def test_is_down_false(self):
        """Test is_down property when close >= open"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000
        )

        assert stock.is_down is False

    def test_is_up_and_is_down_doji(self):
        """Test is_up and is_down when close == open (doji)"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75000.0,  # Same as open
            volume=10000000
        )

        # When close == open, is_up is False and is_down is False
        assert stock.is_up is False
        assert stock.is_down is False


@pytest.mark.unit
@pytest.mark.entity
class TestStockRepresentation:
    """Test Stock string representation"""

    def test_repr(self):
        """Test __repr__ method"""
        stock = Stock(
            ticker="005930",
            name="삼성전자",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000
        )

        repr_str = repr(stock)

        assert "Stock" in repr_str
        assert "005930" in repr_str
        assert "2024-01-15" in repr_str or "2024, 1, 15" in repr_str
