"""
Unit tests for BlockPattern entity
"""
import pytest
from datetime import date, timedelta
from src.domain.entities.patterns.block_pattern import BlockPattern


@pytest.mark.unit
@pytest.mark.entity
class TestBlockPatternCreation:
    """Test BlockPattern creation"""

    def test_create_block_pattern_without_block4(self):
        """Test creating BlockPattern without Block4 seed"""
        pattern = BlockPattern(
            pattern_id=1,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2029, 1, 1)
        )

        assert pattern.pattern_id == 1
        assert pattern.ticker == "005930"
        assert pattern.seed_block1_id == "b1-uuid"
        assert pattern.seed_block2_id == "b2-uuid"
        assert pattern.seed_block3_id == "b3-uuid"
        assert pattern.seed_block4_id is None
        assert pattern.redetection_start == date(2024, 1, 1)
        assert pattern.redetection_end == date(2029, 1, 1)

    def test_create_block_pattern_with_block4(self):
        """Test creating BlockPattern with Block4 seed"""
        pattern = BlockPattern(
            pattern_id=1,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2029, 1, 1),
            seed_block4_id="b4-uuid"
        )

        assert pattern.seed_block4_id == "b4-uuid"

    def test_create_block_pattern_without_pattern_id(self):
        """Test creating BlockPattern without pattern_id (before DB save)"""
        pattern = BlockPattern(
            pattern_id=None,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2029, 1, 1)
        )

        assert pattern.pattern_id is None


@pytest.mark.unit
@pytest.mark.entity
class TestBlockPatternRepr:
    """Test BlockPattern __repr__"""

    def test_repr_format(self):
        """Test __repr__ string format"""
        pattern = BlockPattern(
            pattern_id=123,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2029, 1, 1)
        )

        repr_str = repr(pattern)

        assert "<BlockPattern(" in repr_str
        assert "id=123" in repr_str
        assert "ticker=005930" in repr_str
        assert "period=2024-01-01~2029-01-01" in repr_str
        assert repr_str.endswith(")>")

    def test_repr_without_pattern_id(self):
        """Test __repr__ when pattern_id is None"""
        pattern = BlockPattern(
            pattern_id=None,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2029, 1, 1)
        )

        repr_str = repr(pattern)

        assert "id=None" in repr_str


@pytest.mark.unit
@pytest.mark.entity
class TestBlockPatternMethods:
    """Test BlockPattern methods"""

    def test_get_redetection_days(self):
        """Test get_redetection_days calculates correct days"""
        pattern = BlockPattern(
            pattern_id=1,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2024, 1, 31)
        )

        # 30 days difference (Jan 1 to Jan 31 = 30 days)
        assert pattern.get_redetection_days() == 30

    def test_get_redetection_days_5_years(self):
        """Test get_redetection_days for 5 year period"""
        start = date(2024, 1, 1)
        end = date(2029, 1, 1)

        pattern = BlockPattern(
            pattern_id=1,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=start,
            redetection_end=end
        )

        # 5 years = 1826 or 1827 days (depending on leap years)
        days = (end - start).days
        assert pattern.get_redetection_days() == days

    def test_get_redetection_days_same_date(self):
        """Test get_redetection_days when start == end"""
        pattern = BlockPattern(
            pattern_id=1,
            ticker="005930",
            seed_block1_id="b1-uuid",
            seed_block2_id="b2-uuid",
            seed_block3_id="b3-uuid",
            redetection_start=date(2024, 1, 1),
            redetection_end=date(2024, 1, 1)
        )

        assert pattern.get_redetection_days() == 0
