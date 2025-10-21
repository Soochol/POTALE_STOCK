"""
Unit tests for Block1Detection entity

Tests the business logic and behavior of Block1Detection entity.
"""
import pytest
from datetime import date, datetime
from src.domain.entities import Block1Detection


@pytest.mark.unit
@pytest.mark.entity
class TestBlock1DetectionCreation:
    """Test Block1Detection entity creation and validation"""

    def test_create_minimal_block1_detection(self):
        """Test creating Block1Detection with minimal required fields"""
        detection = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test_condition"
        )

        assert detection.ticker == "005930"
        assert detection.started_at == date(2024, 1, 1)
        assert detection.status == "active"
        assert detection.block1_id != ""  # UUID should be generated
        assert detection.ended_at is None

    def test_create_block1_with_optional_fields(self, sample_block1_detection):
        """Test creating Block1Detection with all optional fields"""
        detection = sample_block1_detection

        assert detection.entry_ma_value == 70000.0
        assert detection.entry_rate == 5.0
        assert detection.entry_deviation == 7.86
        assert detection.peak_price == 80000.0
        assert detection.peak_date == date(2024, 1, 5)
        assert detection.peak_volume == 15000000

    def test_block1_id_auto_generation(self):
        """Test that block1_id is automatically generated as UUID"""
        detection1 = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test"
        )

        detection2 = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test"
        )

        # Each instance should have unique UUID
        assert detection1.block1_id != detection2.block1_id
        assert len(detection1.block1_id) == 36  # UUID format

    def test_invalid_status_raises_error(self):
        """Test that invalid status raises ValueError"""
        with pytest.raises(ValueError, match="Invalid status"):
            Block1Detection(
                ticker="005930",
                started_at=date(2024, 1, 1),
                entry_open=75000.0,
                entry_high=76000.0,
                entry_low=74500.0,
                entry_close=75500.0,
                entry_volume=10000000,
                condition_name="test",
                status="invalid_status"
            )

    def test_completed_without_ended_at_raises_error(self):
        """Test that completed status without ended_at raises ValueError"""
        with pytest.raises(ValueError, match="must have ended_at"):
            Block1Detection(
                ticker="005930",
                started_at=date(2024, 1, 1),
                entry_open=75000.0,
                entry_high=76000.0,
                entry_low=74500.0,
                entry_close=75500.0,
                entry_volume=10000000,
                condition_name="test",
                status="completed",
                ended_at=None
            )


@pytest.mark.unit
@pytest.mark.entity
class TestBlock1DetectionPeakTracking:
    """Test peak price and volume tracking functionality"""

    def test_update_peak_price_first_time(self, sample_block1_detection):
        """Test updating peak price for the first time"""
        detection = sample_block1_detection
        detection.peak_price = None
        detection.peak_date = None

        updated = detection.update_peak(
            current_price=82000.0,
            current_date=date(2024, 1, 6),
            current_volume=16000000
        )

        assert updated is True
        assert detection.peak_price == 82000.0
        assert detection.peak_date == date(2024, 1, 6)
        assert detection.peak_volume == 16000000

    def test_update_peak_price_higher(self, sample_block1_detection):
        """Test updating peak when new price is higher"""
        detection = sample_block1_detection
        detection.peak_price = 80000.0
        detection.peak_date = date(2024, 1, 5)

        updated = detection.update_peak(
            current_price=85000.0,
            current_date=date(2024, 1, 7),
            current_volume=17000000
        )

        assert updated is True
        assert detection.peak_price == 85000.0
        assert detection.peak_date == date(2024, 1, 7)

    def test_update_peak_price_lower(self, sample_block1_detection):
        """Test that peak is not updated when price is lower"""
        detection = sample_block1_detection
        original_peak = detection.peak_price
        original_date = detection.peak_date

        updated = detection.update_peak(
            current_price=78000.0,  # Lower than current peak
            current_date=date(2024, 1, 8),
            current_volume=14000000
        )

        # Price not updated, but volume might be
        assert detection.peak_price == original_peak
        assert detection.peak_date == original_date

    def test_update_peak_volume_only(self, sample_block1_detection):
        """Test updating peak volume without updating price"""
        detection = sample_block1_detection
        detection.peak_volume = 15000000

        updated = detection.update_peak(
            current_price=78000.0,  # Lower than peak
            current_date=date(2024, 1, 8),
            current_volume=20000000  # Higher volume
        )

        # Volume should be updated
        assert detection.peak_volume == 20000000


@pytest.mark.unit
@pytest.mark.entity
class TestBlock1DetectionCalculations:
    """Test calculated properties and methods"""

    def test_duration_days_calculation(self, sample_block1_detection):
        """Test duration_days property calculation"""
        detection = sample_block1_detection
        detection.started_at = date(2024, 1, 1)
        detection.ended_at = date(2024, 1, 10)

        assert detection.duration_days == 9

    def test_duration_days_for_active_block(self, active_block1_detection):
        """Test duration_days returns None for active blocks"""
        detection = active_block1_detection
        assert detection.duration_days is None

    def test_entry_body_middle_calculation(self, sample_block1_detection):
        """Test entry_body_middle property"""
        detection = sample_block1_detection
        detection.entry_open = 75000.0
        detection.entry_close = 75500.0

        expected = (75000.0 + 75500.0) / 2
        assert detection.entry_body_middle == expected

    def test_peak_gain_ratio_calculation(self, sample_block1_detection):
        """Test peak_gain_ratio property"""
        detection = sample_block1_detection
        detection.entry_close = 75500.0
        detection.peak_price = 80000.0

        expected = ((80000.0 - 75500.0) / 75500.0) * 100
        assert abs(detection.peak_gain_ratio - expected) < 0.01

    def test_peak_gain_ratio_when_no_peak(self, sample_block1_detection):
        """Test peak_gain_ratio returns None when no peak price"""
        detection = sample_block1_detection
        detection.peak_price = None

        assert detection.peak_gain_ratio is None


@pytest.mark.unit
@pytest.mark.entity
class TestBlock1DetectionCompletion:
    """Test block completion functionality"""

    def test_complete_block(self, active_block1_detection):
        """Test completing an active block"""
        detection = active_block1_detection

        detection.complete(
            ended_at=date(2024, 1, 10),
            exit_reason="ma_break",
            exit_price=73000.0
        )

        assert detection.status == "completed"
        assert detection.ended_at == date(2024, 1, 10)
        assert detection.exit_reason == "ma_break"
        assert detection.exit_price == 73000.0

    def test_complete_block_updates_all_fields(self, active_block1_detection):
        """Test that complete() updates all necessary fields"""
        detection = active_block1_detection

        detection.complete(
            ended_at=date(2024, 1, 15),
            exit_reason="three_line_reversal",
            exit_price=72500.0
        )

        assert detection.status == "completed"
        assert detection.ended_at is not None
        assert detection.exit_reason == "three_line_reversal"
        assert detection.exit_price == 72500.0


@pytest.mark.unit
@pytest.mark.entity
class TestBlock1DetectionMetadata:
    """Test metadata fields (pattern_id, detection_type, created_at)"""

    def test_pattern_id_and_detection_type(self, sample_block1_detection):
        """Test pattern_id and detection_type fields"""
        detection = sample_block1_detection

        assert detection.pattern_id == 1
        assert detection.detection_type == "seed"

    def test_created_at_field(self):
        """Test created_at field accepts datetime"""
        now = datetime.now()
        detection = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            created_at=now
        )

        assert detection.created_at == now
        assert isinstance(detection.created_at, datetime)

    def test_entry_trading_value_optional(self):
        """Test entry_trading_value can be None"""
        detection = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            entry_trading_value=None
        )

        assert detection.entry_trading_value is None
