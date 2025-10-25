"""
Tests for Stock Data Utilities
"""
import pytest
from datetime import date
from src.domain.entities.core import Stock
from src.infrastructure.utils.stock_data_utils import (
    forward_fill_prices,
    get_last_valid_stock,
    count_valid_trading_days,
    has_trading_gap
)


@pytest.fixture
def sample_stocks():
    """정상 거래 데이터"""
    return [
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
              open=1000, high=1100, low=900, close=1050, volume=100, trading_value=105000),
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 2),
              open=1050, high=1150, low=1000, close=1100, volume=150, trading_value=165000),
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 3),
              open=1100, high=1200, low=1050, close=1150, volume=200, trading_value=230000),
    ]


@pytest.fixture
def stocks_with_gap():
    """거래 정지가 포함된 데이터"""
    return [
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
              open=1000, high=1100, low=900, close=1050, volume=100, trading_value=105000),
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 2),
              open=0, high=0, low=0, close=0, volume=0, trading_value=0),  # 거래 정지
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 3),
              open=1100, high=1200, low=1050, close=1150, volume=200, trading_value=230000),
    ]


@pytest.fixture
def stocks_with_multiple_gaps():
    """연속 거래 정지가 포함된 데이터"""
    return [
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
              open=1000, high=1100, low=900, close=1050, volume=100, trading_value=105000),
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 2),
              open=0, high=0, low=0, close=0, volume=0, trading_value=0),  # 거래 정지
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 3),
              open=0, high=0, low=0, close=0, volume=0, trading_value=0),  # 거래 정지
        Stock(ticker="025980", name="아난티", date=date(2024, 1, 4),
              open=1100, high=1200, low=1050, close=1150, volume=200, trading_value=230000),
    ]


class TestForwardFillPrices:
    """forward_fill_prices() 함수 테스트"""

    def test_no_gaps(self, sample_stocks):
        """거래 정지가 없는 정상 데이터"""
        result = forward_fill_prices(sample_stocks)

        # 원본과 동일해야 함
        assert len(result) == len(sample_stocks)
        assert result[0].close == 1050
        assert result[1].close == 1100
        assert result[2].close == 1150

        # 거래량도 유지
        assert result[0].volume == 100
        assert result[1].volume == 150
        assert result[2].volume == 200

    def test_single_gap(self, stocks_with_gap):
        """하루 거래 정지"""
        result = forward_fill_prices(stocks_with_gap)

        assert len(result) == 3

        # 첫날: 정상
        assert result[0].close == 1050
        assert result[0].volume == 100

        # 둘째날: 가격은 전날 종가로 채워짐, 거래량은 0 유지
        assert result[1].close == 1050  # Forward-filled
        assert result[1].open == 1050
        assert result[1].high == 1050
        assert result[1].low == 1050
        assert result[1].volume == 0  # 거래량은 0 유지

        # 셋째날: 정상
        assert result[2].close == 1150
        assert result[2].volume == 200

    def test_multiple_gaps(self, stocks_with_multiple_gaps):
        """연속 거래 정지"""
        result = forward_fill_prices(stocks_with_multiple_gaps)

        assert len(result) == 4

        # 첫날: 정상
        assert result[0].close == 1050
        assert result[0].volume == 100

        # 둘째날: 전날 종가로 채워짐
        assert result[1].close == 1050
        assert result[1].volume == 0

        # 셋째날: 전날(첫날) 종가로 채워짐
        assert result[2].close == 1050
        assert result[2].volume == 0

        # 넷째날: 정상
        assert result[3].close == 1150
        assert result[3].volume == 200

    def test_empty_list(self):
        """빈 리스트"""
        result = forward_fill_prices([])
        assert result == []

    def test_start_with_zero_volume(self):
        """첫날부터 거래 없음"""
        stocks = [
            Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
                  open=0, high=0, low=0, close=0, volume=0, trading_value=0),
            Stock(ticker="025980", name="아난티", date=date(2024, 1, 2),
                  open=1100, high=1200, low=1050, close=1150, volume=200, trading_value=230000),
        ]

        result = forward_fill_prices(stocks)

        # 첫날은 그대로 (채울 이전 가격 없음)
        assert result[0].close == 0
        assert result[0].volume == 0

        # 둘째날은 정상
        assert result[1].close == 1150
        assert result[1].volume == 200


class TestGetLastValidStock:
    """get_last_valid_stock() 함수 테스트"""

    def test_immediate_prev(self, sample_stocks):
        """바로 전날이 정상 거래일"""
        result = get_last_valid_stock(sample_stocks, 2)
        assert result is not None
        assert result.date == date(2024, 1, 2)
        assert result.close == 1100

    def test_skip_gap(self, stocks_with_gap):
        """거래 정지 건너뛰기"""
        result = get_last_valid_stock(stocks_with_gap, 2)
        assert result is not None
        assert result.date == date(2024, 1, 1)  # 2일(거래정지) 건너뜀
        assert result.close == 1050

    def test_multiple_gaps(self, stocks_with_multiple_gaps):
        """연속 거래 정지 건너뛰기"""
        result = get_last_valid_stock(stocks_with_multiple_gaps, 3)
        assert result is not None
        assert result.date == date(2024, 1, 1)  # 2일, 3일 모두 건너뜀
        assert result.close == 1050

    def test_no_valid_prev(self):
        """유효한 이전 거래일 없음"""
        stocks = [
            Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
                  open=0, high=0, low=0, close=0, volume=0, trading_value=0),
        ]
        result = get_last_valid_stock(stocks, 0)
        assert result is None

    def test_first_index(self, sample_stocks):
        """첫 인덱스에서 호출"""
        result = get_last_valid_stock(sample_stocks, 0)
        assert result is None


class TestCountValidTradingDays:
    """count_valid_trading_days() 함수 테스트"""

    def test_all_valid(self, sample_stocks):
        """모두 정상 거래일"""
        count = count_valid_trading_days(sample_stocks)
        assert count == 3

    def test_with_gap(self, stocks_with_gap):
        """거래 정지 포함"""
        count = count_valid_trading_days(stocks_with_gap)
        assert count == 2  # 1일, 3일만 정상

    def test_with_multiple_gaps(self, stocks_with_multiple_gaps):
        """연속 거래 정지 포함"""
        count = count_valid_trading_days(stocks_with_multiple_gaps)
        assert count == 2  # 1일, 4일만 정상

    def test_empty_list(self):
        """빈 리스트"""
        count = count_valid_trading_days([])
        assert count == 0


class TestHasTradingGap:
    """has_trading_gap() 함수 테스트"""

    def test_consecutive_days(self, sample_stocks):
        """연속된 날짜"""
        result = has_trading_gap(sample_stocks[0], sample_stocks[1])
        assert result is False

    def test_with_gap(self):
        """날짜 간격 있음"""
        stock1 = Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
                      open=1000, high=1100, low=900, close=1050, volume=100, trading_value=105000)
        stock2 = Stock(ticker="025980", name="아난티", date=date(2024, 1, 5),
                      open=1100, high=1200, low=1050, close=1150, volume=200, trading_value=230000)

        result = has_trading_gap(stock1, stock2)
        assert result is True

    def test_none_input(self):
        """None 입력"""
        stock = Stock(ticker="025980", name="아난티", date=date(2024, 1, 1),
                     open=1000, high=1100, low=900, close=1050, volume=100, trading_value=105000)

        assert has_trading_gap(None, stock) is False
        assert has_trading_gap(stock, None) is False
        assert has_trading_gap(None, None) is False
