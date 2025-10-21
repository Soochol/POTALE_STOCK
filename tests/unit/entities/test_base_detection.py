"""
Unit tests for BaseBlockDetection

Tests the common functionality shared by Block2/3/4 entities.
"""
import pytest
from datetime import date, datetime
from src.domain.entities import Block2Detection, Block3Detection, Block4Detection
from src.domain.entities.detections.base_detection import BaseBlockDetection


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionCreation:
    """Test BaseBlockDetection creation and validation (via Block2)"""

    def test_create_minimal_block2_detection(self):
        """Test creating Block2Detection with minimal required fields"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="seed_condition_1",
            started_at=date(2024, 2, 1),
            entry_close=78000.0
        )

        assert detection.ticker == "005930"
        assert detection.condition_name == "seed_condition_1"
        assert detection.started_at == date(2024, 2, 1)
        assert detection.entry_close == 78000.0
        assert detection.status == "active"
        assert detection.ended_at is None

    def test_block2_id_auto_generation(self):
        """Test that block2_id is automatically generated as UUID"""
        detection1 = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection2 = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        # Each instance should have unique UUID
        assert detection1.block2_id != detection2.block2_id
        assert len(detection1.block2_id) == 36  # UUID format

    def test_invalid_status_raises_error(self):
        """Test that invalid status raises ValueError"""
        with pytest.raises(ValueError, match="status는 'active' 또는 'completed'여야 합니다"):
            Block2Detection(
                ticker="005930",
                condition_name="test",
                started_at=date(2024, 1, 1),
                entry_close=75000.0,
                status="invalid"
            )

    def test_zero_entry_close_raises_error(self):
        """Test that zero entry_close raises ValueError"""
        with pytest.raises(ValueError, match="진입 종가는 0보다 커야 합니다"):
            Block2Detection(
                ticker="005930",
                condition_name="test",
                started_at=date(2024, 1, 1),
                entry_close=0.0
            )

    def test_negative_entry_close_raises_error(self):
        """Test that negative entry_close raises ValueError"""
        with pytest.raises(ValueError, match="진입 종가는 0보다 커야 합니다"):
            Block2Detection(
                ticker="005930",
                condition_name="test",
                started_at=date(2024, 1, 1),
                entry_close=-1000.0
            )


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionPeakTracking:
    """Test peak tracking functionality (common to Block2/3/4)"""

    def test_update_peak_first_time(self, sample_block2_detection):
        """Test updating peak for the first time"""
        detection = sample_block2_detection
        detection.peak_price = None
        detection.peak_date = None
        detection.peak_volume = None

        detection.update_peak(
            price=90000.0,
            current_date=date(2024, 2, 10),
            volume=20000000
        )

        assert detection.peak_price == 90000.0
        assert detection.peak_date == date(2024, 2, 10)
        assert detection.peak_volume == 20000000
        # Peak gain ratio should be calculated
        expected_gain = ((90000.0 - detection.entry_close) / detection.entry_close) * 100
        assert abs(detection.peak_gain_ratio - expected_gain) < 0.01

    def test_update_peak_higher_price(self, sample_block2_detection):
        """Test updating peak when new price is higher"""
        detection = sample_block2_detection
        detection.peak_price = 85000.0
        detection.peak_date = date(2024, 2, 5)

        detection.update_peak(
            price=92000.0,
            current_date=date(2024, 2, 12),
            volume=21000000
        )

        assert detection.peak_price == 92000.0
        assert detection.peak_date == date(2024, 2, 12)

    def test_update_peak_lower_price(self, sample_block2_detection):
        """Test that peak is not updated when price is lower"""
        detection = sample_block2_detection
        original_peak = detection.peak_price
        original_date = detection.peak_date

        detection.update_peak(
            price=80000.0,  # Lower than current peak
            current_date=date(2024, 2, 15),
            volume=18000000
        )

        # Price not updated
        assert detection.peak_price == original_peak
        assert detection.peak_date == original_date

    def test_update_peak_volume_only(self, sample_block2_detection):
        """Test updating peak volume without updating price"""
        detection = sample_block2_detection
        detection.peak_volume = 18000000

        detection.update_peak(
            price=80000.0,  # Lower than peak
            current_date=date(2024, 2, 15),
            volume=25000000  # Higher volume
        )

        # Volume should be updated
        assert detection.peak_volume == 25000000


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionCompletion:
    """Test block completion functionality"""

    def test_complete_block(self, sample_block2_detection):
        """Test completing a block"""
        detection = sample_block2_detection
        detection.status = "active"
        detection.ended_at = None

        detection.complete(
            end_date=date(2024, 2, 20),
            exit_reason="ma_break"
        )

        assert detection.status == "completed"
        assert detection.ended_at == date(2024, 2, 20)
        assert detection.exit_reason == "ma_break"
        # Duration should be calculated
        assert detection.duration_days is not None
        assert detection.duration_days > 0

    def test_complete_block_calculates_duration(self):
        """Test that complete() calculates duration_days correctly"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 2, 1),
            entry_close=78000.0
        )

        detection.complete(
            end_date=date(2024, 2, 11),
            exit_reason="three_line_reversal"
        )

        # 2/1 to 2/11 = 11 days (inclusive)
        assert detection.duration_days == 11


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionMetadata:
    """Test metadata fields"""

    def test_pattern_id_and_detection_type(self, sample_block2_detection):
        """Test pattern_id and detection_type fields"""
        detection = sample_block2_detection

        assert detection.pattern_id == 1
        assert detection.detection_type == "seed"

    def test_created_at_field(self):
        """Test created_at field accepts datetime"""
        now = datetime.now()
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0,
            created_at=now
        )

        assert detection.created_at == now
        assert isinstance(detection.created_at, datetime)

    def test_prev_block_fields(self, sample_block2_detection):
        """Test previous block reference fields"""
        detection = sample_block2_detection

        assert detection.prev_block_id == 1
        assert detection.prev_block_peak_price == 80000.0
        assert detection.prev_block_peak_volume == 15000000


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionBlockName:
    """Test _get_block_name method (polymorphism)"""

    def test_block2_name(self):
        """Test Block2 returns correct name"""
        from src.domain.entities import Block2Detection
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )
        assert detection._get_block_name() == "Block2"

    def test_block3_name(self):
        """Test Block3 returns correct name"""
        from src.domain.entities import Block3Detection
        detection = Block3Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )
        assert detection._get_block_name() == "Block3"

    def test_block4_name(self):
        """Test Block4 returns correct name"""
        from src.domain.entities import Block4Detection
        detection = Block4Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )
        assert detection._get_block_name() == "Block4"


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionRepresentation:
    """Test __repr__ method"""

    def test_repr_with_peak_gain(self, sample_block2_detection):
        """Test __repr__ when peak_gain_ratio exists"""
        detection = sample_block2_detection
        # Set peak_price to calculate peak_gain_ratio
        detection.entry_close = 75000.0
        detection.peak_price = 80000.0

        repr_str = repr(detection)

        # Test that repr includes class name, ticker, status (dataclass default repr)
        assert "Block2Detection(" in repr_str
        assert "ticker='005930'" in repr_str
        assert "status='active'" in repr_str
        # peak_gain_ratio should be calculated
        assert "peak_gain_ratio=" in repr_str

    def test_repr_without_peak_gain(self):
        """Test __repr__ when peak_gain_ratio is None"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )
        detection.peak_price = None

        repr_str = repr(detection)

        # Test that repr includes class name and ticker (dataclass default repr)
        assert "Block2Detection(" in repr_str
        assert "ticker='005930'" in repr_str
        # When peak_price is None, peak_gain_ratio is None
        assert "peak_gain_ratio=None" in repr_str


@pytest.mark.unit
@pytest.mark.entity
class TestBlock2DetectionCompatibility:
    """Test Block2Detection compatibility aliases"""

    def test_prev_block1_id_getter(self):
        """Test prev_block1_id property getter"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0,
            prev_block_id=1
        )

        # Should return prev_block_id value
        assert detection.prev_block1_id == 1

    def test_prev_block1_id_setter(self):
        """Test prev_block1_id property setter"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block1_id = 5

        # Should set prev_block_id value
        assert detection.prev_block_id == 5
        assert detection.prev_block1_id == 5

    def test_prev_block1_peak_price_getter(self):
        """Test prev_block1_peak_price property getter"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0,
            prev_block_peak_price=80000.0
        )

        assert detection.prev_block1_peak_price == 80000.0

    def test_prev_block1_peak_price_setter(self):
        """Test prev_block1_peak_price property setter"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block1_peak_price = 85000.0

        assert detection.prev_block_peak_price == 85000.0
        assert detection.prev_block1_peak_price == 85000.0

    def test_prev_block1_peak_volume_getter(self):
        """Test prev_block1_peak_volume property getter"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0,
            prev_block_peak_volume=15000000
        )

        assert detection.prev_block1_peak_volume == 15000000

    def test_prev_block1_peak_volume_setter(self):
        """Test prev_block1_peak_volume property setter"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block1_peak_volume = 20000000

        assert detection.prev_block_peak_volume == 20000000
        assert detection.prev_block1_peak_volume == 20000000


@pytest.mark.unit
@pytest.mark.entity
class TestBlock3DetectionCompatibility:
    """Test Block3Detection compatibility aliases"""

    def test_prev_block2_id_aliases(self):
        """Test prev_block2_id property getter/setter"""
        detection = Block3Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        # Setter
        detection.prev_block2_id = 10

        # Getter
        assert detection.prev_block2_id == 10
        assert detection.prev_block_id == 10

    def test_prev_block2_peak_price_aliases(self):
        """Test prev_block2_peak_price property getter/setter"""
        detection = Block3Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block2_peak_price = 90000.0

        assert detection.prev_block2_peak_price == 90000.0
        assert detection.prev_block_peak_price == 90000.0

    def test_prev_block2_peak_volume_aliases(self):
        """Test prev_block2_peak_volume property getter/setter"""
        detection = Block3Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block2_peak_volume = 25000000

        assert detection.prev_block2_peak_volume == 25000000
        assert detection.prev_block_peak_volume == 25000000


@pytest.mark.unit
@pytest.mark.entity
class TestBlock4DetectionCompatibility:
    """Test Block4Detection compatibility aliases"""

    def test_prev_block3_id_aliases(self):
        """Test prev_block3_id property getter/setter"""
        detection = Block4Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block3_id = 15

        assert detection.prev_block3_id == 15
        assert detection.prev_block_id == 15

    def test_prev_block3_peak_price_aliases(self):
        """Test prev_block3_peak_price property getter/setter"""
        detection = Block4Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block3_peak_price = 95000.0

        assert detection.prev_block3_peak_price == 95000.0
        assert detection.prev_block_peak_price == 95000.0

    def test_prev_block3_peak_volume_aliases(self):
        """Test prev_block3_peak_volume property getter/setter"""
        detection = Block4Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        detection.prev_block3_peak_volume = 30000000

        assert detection.prev_block3_peak_volume == 30000000
        assert detection.prev_block_peak_volume == 30000000


@pytest.mark.unit
@pytest.mark.entity
class TestBaseBlockDetectionDirect:
    """Test BaseBlockDetection class directly"""

    def test_base_detection_get_block_name(self):
        """Test BaseBlockDetection._get_block_name() returns 'BaseBlock'"""
        # Create a concrete instance for testing
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        # Call parent method directly (normally overridden)
        base_name = BaseBlockDetection._get_block_name(detection)
        assert base_name == "BaseBlock"

    def test_base_detection_repr_with_none_peak_gain(self):
        """Test BaseBlockDetection.__repr__ when peak_gain_ratio is None"""
        detection = Block2Detection(
            ticker="005930",
            condition_name="test",
            started_at=date(2024, 1, 1),
            entry_close=75000.0
        )

        # peak_price is None by default, so peak_gain_ratio is None
        repr_str = BaseBlockDetection.__repr__(detection)

        assert "<" in repr_str
        assert "Detection(" in repr_str
        assert "ticker=005930" in repr_str
        assert "peak_gain=N/A" in repr_str
