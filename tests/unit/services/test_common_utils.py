"""
Unit tests for common utility functions

Tests service layer utility functions.
"""
import pytest
from datetime import date
from src.domain.entities import Stock
from src.application.services.common.utils import (
    get_previous_trading_day_stock,
    get_trading_day_gap,
    has_sufficient_trading_history
)


@pytest.fixture
def sample_stocks_with_gaps():
    """Create sample stocks with trading day gaps (weekends, holidays)"""
    return [
        Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 2),
              open=75000.0, high=76000.0, low=74000.0, close=75500.0, volume=10000000),
        Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 3),
              open=75500.0, high=76500.0, low=75000.0, close=76000.0, volume=11000000),
        Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 4),
              open=76000.0, high=77000.0, low=75500.0, close=76500.0, volume=12000000),
        # Gap: 1/5 (holiday), 1/6-7 (weekend)
        Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 8),
              open=76500.0, high=77500.0, low=76000.0, close=77000.0, volume=13000000),
        Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 9),
              open=77000.0, high=78000.0, low=76500.0, close=77500.0, volume=14000000),
        Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 10),
              open=77500.0, high=78500.0, low=77000.0, close=78000.0, volume=15000000),
    ]


@pytest.mark.unit
@pytest.mark.service
class TestGetPreviousTradingDayStock:
    """Test get_previous_trading_day_stock function"""

    def test_get_previous_trading_day_simple(self, sample_stocks_with_gaps):
        """Test getting previous trading day (simple case)"""
        stocks = sample_stocks_with_gaps
        current_date = date(2024, 1, 4)

        prev_stock = get_previous_trading_day_stock(current_date, stocks)

        assert prev_stock is not None
        assert prev_stock.date == date(2024, 1, 3)

    def test_get_previous_trading_day_with_gap(self, sample_stocks_with_gaps):
        """Test getting previous trading day when there's a gap"""
        stocks = sample_stocks_with_gaps
        # 1/8 is after holiday + weekend gap
        current_date = date(2024, 1, 8)

        prev_stock = get_previous_trading_day_stock(current_date, stocks)

        assert prev_stock is not None
        # Should skip weekend/holiday and return 1/4
        assert prev_stock.date == date(2024, 1, 4)

    def test_get_previous_trading_day_no_history(self, sample_stocks_with_gaps):
        """Test when there's no previous trading day"""
        stocks = sample_stocks_with_gaps
        # Earlier than all data
        current_date = date(2024, 1, 1)

        prev_stock = get_previous_trading_day_stock(current_date, stocks)

        assert prev_stock is None

    def test_get_previous_trading_day_empty_list(self):
        """Test with empty stock list"""
        stocks = []
        current_date = date(2024, 1, 10)

        prev_stock = get_previous_trading_day_stock(current_date, stocks)

        assert prev_stock is None

    def test_get_previous_trading_day_returns_most_recent(self):
        """Test that it returns the most recent previous day"""
        stocks = [
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 1),
                  open=75000.0, high=76000.0, low=74000.0, close=75500.0, volume=10000000),
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 5),
                  open=76000.0, high=77000.0, low=75500.0, close=76500.0, volume=12000000),
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 8),
                  open=77000.0, high=78000.0, low=76500.0, close=77500.0, volume=14000000),
        ]
        current_date = date(2024, 1, 10)

        prev_stock = get_previous_trading_day_stock(current_date, stocks)

        assert prev_stock is not None
        assert prev_stock.date == date(2024, 1, 8)  # Most recent


@pytest.mark.unit
@pytest.mark.service
class TestGetTradingDayGap:
    """Test get_trading_day_gap function"""

    def test_get_trading_day_gap_no_gaps(self):
        """Test trading day gap with consecutive days"""
        stocks = [
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 2),
                  open=75000.0, high=76000.0, low=74000.0, close=75500.0, volume=10000000),
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 3),
                  open=75500.0, high=76500.0, low=75000.0, close=76000.0, volume=11000000),
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 4),
                  open=76000.0, high=77000.0, low=75500.0, close=76500.0, volume=12000000),
        ]

        gap = get_trading_day_gap(date(2024, 1, 2), date(2024, 1, 4), stocks)

        assert gap == 3

    def test_get_trading_day_gap_with_gaps(self, sample_stocks_with_gaps):
        """Test trading day gap with weekends/holidays"""
        stocks = sample_stocks_with_gaps

        # From 1/4 to 1/10 (inclusive)
        # Trading days: 1/4, 1/8, 1/9, 1/10 = 4 days
        gap = get_trading_day_gap(date(2024, 1, 4), date(2024, 1, 10), stocks)

        assert gap == 4

    def test_get_trading_day_gap_single_day(self, sample_stocks_with_gaps):
        """Test trading day gap for same day"""
        stocks = sample_stocks_with_gaps

        gap = get_trading_day_gap(date(2024, 1, 3), date(2024, 1, 3), stocks)

        assert gap == 1

    def test_get_trading_day_gap_no_trading_days(self, sample_stocks_with_gaps):
        """Test trading day gap when no trading days in range"""
        stocks = sample_stocks_with_gaps

        # 1/5 to 1/7 (all holidays/weekends)
        gap = get_trading_day_gap(date(2024, 1, 5), date(2024, 1, 7), stocks)

        assert gap == 0

    def test_get_trading_day_gap_empty_list(self):
        """Test trading day gap with empty list"""
        stocks = []

        gap = get_trading_day_gap(date(2024, 1, 1), date(2024, 1, 10), stocks)

        assert gap == 0


@pytest.mark.unit
@pytest.mark.service
class TestHasSufficientTradingHistory:
    """Test has_sufficient_trading_history function"""

    def test_sufficient_history_true(self, sample_stocks_with_gaps):
        """Test when there is sufficient history"""
        stocks = sample_stocks_with_gaps  # 6 stocks total

        result = has_sufficient_trading_history(
            current_date=date(2024, 1, 10),
            all_stocks=stocks,
            required_days=5
        )

        assert result is True

    def test_sufficient_history_false(self, sample_stocks_with_gaps):
        """Test when there is insufficient history"""
        stocks = sample_stocks_with_gaps  # 6 stocks total

        result = has_sufficient_trading_history(
            current_date=date(2024, 1, 10),
            all_stocks=stocks,
            required_days=20  # Need 20 days, only have 6
        )

        assert result is False

    def test_sufficient_history_exact(self, sample_stocks_with_gaps):
        """Test when history exactly meets requirement"""
        stocks = sample_stocks_with_gaps  # 6 stocks total

        result = has_sufficient_trading_history(
            current_date=date(2024, 1, 10),
            all_stocks=stocks,
            required_days=6
        )

        assert result is True

    def test_sufficient_history_empty_list(self):
        """Test with empty stock list"""
        stocks = []

        result = has_sufficient_trading_history(
            current_date=date(2024, 1, 10),
            all_stocks=stocks,
            required_days=1
        )

        assert result is False

    def test_sufficient_history_excludes_future_dates(self):
        """Test that future dates are excluded from history"""
        stocks = [
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 1),
                  open=75000.0, high=76000.0, low=74000.0, close=75500.0, volume=10000000),
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 5),
                  open=76000.0, high=77000.0, low=75500.0, close=76500.0, volume=12000000),
            Stock(ticker="005930", name="삼성전자", date=date(2024, 1, 20),  # Future
                  open=77000.0, high=78000.0, low=76500.0, close=77500.0, volume=14000000),
        ]

        result = has_sufficient_trading_history(
            current_date=date(2024, 1, 10),
            all_stocks=stocks,
            required_days=2
        )

        # Only 2 stocks on or before 1/10
        assert result is True

        result = has_sufficient_trading_history(
            current_date=date(2024, 1, 10),
            all_stocks=stocks,
            required_days=3
        )

        # Need 3 but only have 2 (1/20 is in future)
        assert result is False
