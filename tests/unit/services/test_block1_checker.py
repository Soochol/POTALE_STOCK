"""
Unit tests for Block1Checker

Tests Block1 entry and exit condition checking logic.
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch
from src.application.services.checkers.block1_checker import Block1Checker
from src.domain.entities import Stock, Block1Condition, Block1Detection
from src.domain.entities.conditions.base_entry_condition import BaseEntryCondition


@pytest.fixture
def block1_checker():
    """Create Block1Checker instance"""
    return Block1Checker()


@pytest.fixture
def sample_condition():
    """Create a sample Block1Condition"""
    base = BaseEntryCondition(
        block1_entry_surge_rate=5.0,
        block1_entry_ma_period=20,
        block1_entry_high_above_ma=True,
        block1_entry_max_deviation_ratio=115.0,
        block1_entry_min_trading_value=100.0,
        block1_entry_volume_high_months=3,
        block1_entry_volume_spike_ratio=1.5
    )

    condition = Mock(spec=Block1Condition)
    condition.name = "test_condition"
    condition.base = base
    return condition


@pytest.fixture
def sample_stock_with_indicators():
    """Create a stock with all required indicators"""
    stock = Stock(
            name="삼성전자",
        ticker="005930",
        date=date(2024, 1, 15),
        open=75000.0,
        high=76000.0,
        low=74500.0,
        close=75500.0,
        volume=10000000,
        trading_value=755.0
    )

    # Add indicators as dict (matches actual implementation)
    stock.indicators = {
        'rate': 6.0,  # 등락률
        'MA_20': 70000.0,  # 20일 이동평균
        'deviation': 107.86,  # 이격도
        'trading_value_100m': 150.0,  # 거래대금 (억)
        'is_volume_high': True,  # N개월 신고거래량
        'volume_ratio': 180.0,  # 전날 대비 거래량 비율
    }

    return stock


@pytest.fixture
def all_stocks_list():
    """Create a list of stocks for historical comparison"""
    stocks = []
    for i in range(30):
        stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, i + 1),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=8000000 + i * 100000,
            trading_value=600.0 + i * 10
        )
        stocks.append(stock)
    return stocks


@pytest.mark.unit
@pytest.mark.checker
class TestBlock1CheckerEntry:
    """Test Block1 entry condition checking"""

    def test_check_entry_all_conditions_pass(
        self, block1_checker, sample_condition, sample_stock_with_indicators, all_stocks_list
    ):
        """Test entry check when all conditions pass"""
        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=sample_stock_with_indicators,
            all_stocks=all_stocks_list
        )

        assert result is True

    def test_check_entry_no_indicators(self, block1_checker, sample_condition, all_stocks_list):
        """Test entry check fails when stock has no indicators"""
        stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000,
            trading_value=755.0
        )
        # No indicators attribute

        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=stock,
            all_stocks=all_stocks_list
        )

        assert result is False

    def test_check_entry_surge_rate_fail(
        self, block1_checker, sample_condition, sample_stock_with_indicators, all_stocks_list
    ):
        """Test entry check fails when surge rate is too low"""
        stock = sample_stock_with_indicators
        stock.indicators['rate'] = 3.0  # Below threshold (5.0)

        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=stock,
            all_stocks=all_stocks_list
        )

        assert result is False

    def test_check_entry_ma_high_fail(
        self, block1_checker, sample_condition, sample_stock_with_indicators, all_stocks_list
    ):
        """Test entry check fails when high is below MA"""
        stock = sample_stock_with_indicators
        stock.high = 68000.0  # Below MA_20 (70000.0)

        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=stock,
            all_stocks=all_stocks_list
        )

        assert result is False

    def test_check_entry_deviation_fail(
        self, block1_checker, sample_condition, sample_stock_with_indicators, all_stocks_list
    ):
        """Test entry check fails when deviation is too high"""
        stock = sample_stock_with_indicators
        stock.indicators['deviation'] = 120.0  # Above threshold (115.0)

        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=stock,
            all_stocks=all_stocks_list
        )

        assert result is False

    def test_check_entry_trading_value_fail(
        self, block1_checker, sample_condition, sample_stock_with_indicators, all_stocks_list
    ):
        """Test entry check fails when trading value is too low"""
        stock = sample_stock_with_indicators
        stock.indicators['trading_value_100m'] = 50.0  # Below threshold (100.0)

        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=stock,
            all_stocks=all_stocks_list
        )

        assert result is False

    def test_check_entry_volume_high_fail(
        self, block1_checker, sample_condition, sample_stock_with_indicators, all_stocks_list
    ):
        """Test entry check fails when not volume high"""
        stock = sample_stock_with_indicators
        stock.indicators['is_volume_high'] = False

        result = block1_checker.check_entry(
            condition=sample_condition,
            stock=stock,
            all_stocks=all_stocks_list
        )

        assert result is False

    def test_check_entry_none_conditions_skipped(
        self, block1_checker, sample_stock_with_indicators, all_stocks_list
    ):
        """Test that None conditions are properly skipped"""
        # Create condition with all None values
        base = BaseEntryCondition(
            block1_entry_surge_rate=None,
            block1_entry_ma_period=None,
            block1_entry_high_above_ma=False,
            block1_entry_max_deviation_ratio=None,
            block1_entry_min_trading_value=None,
            block1_entry_volume_high_months=None,
            block1_entry_volume_spike_ratio=None
        )

        condition = Mock(spec=Block1Condition)
        condition.name = "test_condition"
        condition.base = base

        result = block1_checker.check_entry(
            condition=condition,
            stock=sample_stock_with_indicators,
            all_stocks=all_stocks_list
        )

        # All conditions skipped should pass
        assert result is True


@pytest.mark.unit
@pytest.mark.checker
class TestBlock1CheckerExit:
    """Test Block1 exit condition checking"""

    @pytest.fixture
    def active_block1_detection(self):
        """Create an active Block1Detection"""
        return Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test_condition",
            status="active",
            peak_price=80000.0,
            peak_date=date(2024, 1, 5)
        )

    @pytest.fixture
    def exit_condition(self):
        """Create exit condition"""
        from src.domain.entities.conditions.base_entry_condition import Block1ExitConditionType

        condition = Mock()
        condition.base = Mock()
        condition.base.block1_entry_ma_period = 20
        condition.base.block1_exit_ma_period = None  # Will use entry_ma_period
        condition.base.block1_exit_condition_type = Block1ExitConditionType.MA_BREAK
        return condition

    def test_check_exit_ma_break(self, block1_checker, active_block1_detection, exit_condition, all_stocks_list):
        """Test exit check for MA break condition"""
        stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 10),
            open=73000.0,
            high=74000.0,
            low=72000.0,
            close=72500.0,
            volume=12000000,
            trading_value=870.0
        )

        stock.indicators = {
            'MA_20': 75000.0  # Close (72500) is below MA
        }

        detection = active_block1_detection

        result = block1_checker.check_exit(
            condition=exit_condition,
            detection=detection,
            current_stock=stock,
            all_stocks=all_stocks_list
        )

        # Should detect MA break exit
        assert result is not None
        assert "ma_break" in result.lower()

    def test_check_exit_body_middle_break(
        self, block1_checker, active_block1_detection, all_stocks_list
    ):
        """Test exit check for body middle break condition"""
        from src.domain.entities.conditions.base_entry_condition import Block1ExitConditionType

        stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 10),
            open=75000.0,
            high=76000.0,
            low=72000.0,
            close=72500.0,  # Close below body middle
            volume=12000000,
            trading_value=870.0
        )

        stock.indicators = {
            'MA_20': 70000.0  # Above close, so no MA break
        }

        # Create condition with BODY_MIDDLE exit type
        body_middle_condition = Mock()
        body_middle_condition.base = Mock()
        body_middle_condition.base.block1_entry_ma_period = 20
        body_middle_condition.base.block1_exit_condition_type = Block1ExitConditionType.BODY_MIDDLE

        detection = active_block1_detection
        # Entry body middle = (75000 + 75500) / 2 = 75250
        # Close (72500) < 75250, so should exit

        result = block1_checker.check_exit(
            condition=body_middle_condition,
            detection=detection,
            current_stock=stock,
            all_stocks=all_stocks_list
        )

        # Should detect body middle break
        assert result is not None
        assert "body_middle" in result.lower()

    def test_check_exit_no_exit_conditions_met(
        self, block1_checker, active_block1_detection, exit_condition, all_stocks_list
    ):
        """Test exit check when no conditions are met (continues)"""
        stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 10),
            open=76000.0,
            high=77000.0,
            low=75500.0,
            close=76500.0,  # Above everything
            volume=12000000,
            trading_value=918.0
        )

        stock.indicators = {
            'MA_20': 70000.0  # Well below close
        }

        detection = active_block1_detection

        result = block1_checker.check_exit(
            condition=exit_condition,
            detection=detection,
            current_stock=stock,
            all_stocks=all_stocks_list
        )

        # No exit condition met
        assert result is None


@pytest.mark.unit
@pytest.mark.checker
class TestBlock1CheckerUpdatePeak:
    """Test Block1 peak update logic"""

    def test_update_detection_peak_new_high(self, block1_checker):
        """Test updating peak when new price is higher"""
        detection = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            peak_price=80000.0,
            peak_date=date(2024, 1, 5),
            peak_volume=15000000
        )

        stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 10),
            open=82000.0,
            high=85000.0,  # New high
            low=81000.0,
            close=84000.0,
            volume=20000000,  # New volume high
            trading_value=1680.0
        )

        # Call update_peak (if Block1Checker has such method)
        # Or test Detection.update_peak directly
        updated = detection.update_peak(
            current_price=stock.high,
            current_date=stock.date,
            current_volume=stock.volume
        )

        assert updated is True
        assert detection.peak_price == 85000.0
        assert detection.peak_date == date(2024, 1, 10)
        assert detection.peak_volume == 20000000


@pytest.mark.unit
@pytest.mark.checker
class TestBlock1CheckerIntegration:
    """Integration tests for Block1Checker"""

    def test_full_entry_to_exit_workflow(
        self, block1_checker, sample_condition, all_stocks_list
    ):
        """Test complete workflow from entry to exit"""
        # Entry stock
        entry_stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 15),
            open=75000.0,
            high=76000.0,
            low=74500.0,
            close=75500.0,
            volume=10000000,
            trading_value=755.0
        )
        entry_stock.indicators = {
            'rate': 6.0,
            'MA_20': 70000.0,
            'deviation': 107.86,
            'trading_value_100m': 150.0,
            'is_volume_high': True,
            'volume_ratio': 180.0,
        }

        # Check entry
        entry_result = block1_checker.check_entry(
            condition=sample_condition,
            stock=entry_stock,
            all_stocks=all_stocks_list
        )

        assert entry_result is True

        # Create detection from entry
        detection = Block1Detection(
            ticker=entry_stock.ticker,
            started_at=entry_stock.date,
            entry_open=entry_stock.open,
            entry_high=entry_stock.high,
            entry_low=entry_stock.low,
            entry_close=entry_stock.close,
            entry_volume=entry_stock.volume,
            condition_name="test_condition",
            entry_ma_value=entry_stock.indicators.get('MA_20')
        )

        # Update peak over several days
        for days_offset in range(1, 6):
            current_date = date(2024, 1, 15 + days_offset)
            price = 75500.0 + days_offset * 1000

            detection.update_peak(
                current_price=price,
                current_date=current_date,
                current_volume=10000000 + days_offset * 500000
            )

        # Check peak was updated
        assert detection.peak_price > entry_stock.close
        assert detection.peak_volume > entry_stock.volume

        # Exit stock (MA break)
        exit_stock = Stock(
            name="삼성전자",
            ticker="005930",
            date=date(2024, 1, 25),
            open=73000.0,
            high=74000.0,
            low=72000.0,
            close=72500.0,  # Below MA
            volume=12000000,
            trading_value=870.0
        )
        exit_stock.indicators = {
            'MA_20': 75000.0
        }

        exit_condition = Mock()
        exit_condition.exit_ma_break = True
        exit_condition.exit_three_line_reversal = False
        exit_condition.exit_body_middle_break = False
        exit_condition.base = sample_condition.base

        # Check exit
        exit_reason = block1_checker.check_exit(
            condition=exit_condition,
            detection=detection,
            current_stock=exit_stock,
            all_stocks=all_stocks_list
        )

        assert exit_reason is not None
        assert "ma_break" in exit_reason.lower()

        # Complete the detection
        detection.complete(
            ended_at=exit_stock.date,
            exit_reason=exit_reason,
            exit_price=exit_stock.close
        )

        assert detection.status == "completed"
        assert detection.ended_at == exit_stock.date
        assert detection.duration_days is not None
