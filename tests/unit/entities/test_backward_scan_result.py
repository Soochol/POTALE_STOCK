"""
Unit tests for BackwardScanResult entity
"""

import pytest
from datetime import date

from src.domain.entities.patterns import BackwardScanResult
from src.domain.entities.detections import DynamicBlockDetection


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def highlight_block():
    """Create a highlight block with peak price 10,000."""
    return DynamicBlockDetection(
        id=1,
        block_id='block1',
        block_type=1,
        ticker='025980',
        started_at=date(2020, 4, 14),
        ended_at=date(2020, 4, 16),
        peak_price=10000.0,
        peak_volume=83279719,
        status='completed',
        condition_name='test_condition'
    )


@pytest.fixture
def stronger_block():
    """Create a stronger block with peak price 12,000."""
    return DynamicBlockDetection(
        id=2,
        block_id='block1',
        block_type=1,
        ticker='025980',
        started_at=date(2020, 4, 1),
        ended_at=date(2020, 4, 10),
        peak_price=12000.0,
        peak_volume=50000000,
        status='completed',
        condition_name='test_condition'
    )


# ============================================================
# Factory Method Tests
# ============================================================

def test_no_stronger_root_factory():
    """Test factory method for no stronger root."""
    result = BackwardScanResult.no_stronger_root(lookback_days=30)

    assert result.found_stronger_root is False
    assert result.stronger_block is None
    assert result.peak_price_ratio == 1.0
    assert result.lookback_days == 30


def test_with_stronger_root_factory(stronger_block, highlight_block):
    """Test factory method for stronger root found."""
    result = BackwardScanResult.with_stronger_root(
        stronger_block=stronger_block,
        highlight_peak_price=highlight_block.peak_price,
        lookback_days=30
    )

    assert result.found_stronger_root is True
    assert result.stronger_block == stronger_block
    assert result.peak_price_ratio == 1.2  # 12000 / 10000
    assert result.lookback_days == 30


def test_with_stronger_root_factory_rejects_weaker_block(highlight_block):
    """Test that factory rejects block with lower peak than highlight."""
    weaker_block = DynamicBlockDetection(
        id=3,
        block_id='block1',
        block_type=1,
        ticker='025980',
        started_at=date(2020, 4, 1),
        ended_at=date(2020, 4, 10),
        peak_price=8000.0,  # Lower than highlight
        peak_volume=30000000,
        status='completed',
        condition_name='test_condition'
    )

    with pytest.raises(ValueError, match="must be higher than highlight peak"):
        BackwardScanResult.with_stronger_root(
            stronger_block=weaker_block,
            highlight_peak_price=highlight_block.peak_price,
            lookback_days=30
        )


# ============================================================
# Invariant Validation Tests
# ============================================================

def test_found_stronger_root_requires_stronger_block():
    """Test that found_stronger_root=True requires stronger_block."""
    with pytest.raises(ValueError, match="requires stronger_block to be provided"):
        BackwardScanResult(
            found_stronger_root=True,
            stronger_block=None,
            peak_price_ratio=1.2
        )


def test_found_stronger_root_requires_ratio_greater_than_1():
    """Test that found_stronger_root=True requires ratio > 1.0."""
    block = DynamicBlockDetection(
        id=1,
        block_id='block1',
        block_type=1,
        ticker='025980',
        started_at=date(2020, 4, 1),
        ended_at=date(2020, 4, 10),
        peak_price=12000.0,
        peak_volume=50000000,
        status='completed',
        condition_name='test_condition'
    )

    with pytest.raises(ValueError, match="requires peak_price_ratio > 1.0"):
        BackwardScanResult(
            found_stronger_root=True,
            stronger_block=block,
            peak_price_ratio=0.9  # Invalid: <= 1.0
        )


def test_no_stronger_root_should_not_have_block(stronger_block):
    """Test that found_stronger_root=False should not have stronger_block."""
    with pytest.raises(ValueError, match="should not have stronger_block"):
        BackwardScanResult(
            found_stronger_root=False,
            stronger_block=stronger_block,  # Should be None
            peak_price_ratio=1.0
        )


def test_lookback_days_must_be_positive():
    """Test that lookback_days must be positive."""
    with pytest.raises(ValueError, match="must be positive"):
        BackwardScanResult(
            found_stronger_root=False,
            lookback_days=0  # Invalid
        )


# ============================================================
# Method Tests
# ============================================================

def test_get_root_block_returns_stronger_when_found(stronger_block, highlight_block):
    """Test get_root_block returns stronger block when found."""
    result = BackwardScanResult.with_stronger_root(
        stronger_block=stronger_block,
        highlight_peak_price=highlight_block.peak_price,
        lookback_days=30
    )

    root = result.get_root_block(highlight_block)

    assert root == stronger_block
    assert root.id == stronger_block.id


def test_get_root_block_returns_highlight_when_not_found(highlight_block):
    """Test get_root_block returns highlight when no stronger found."""
    result = BackwardScanResult.no_stronger_root(lookback_days=30)

    root = result.get_root_block(highlight_block)

    assert root == highlight_block
    assert root.id == highlight_block.id


def test_to_dict_with_stronger_root(stronger_block, highlight_block):
    """Test to_dict serialization with stronger root."""
    result = BackwardScanResult.with_stronger_root(
        stronger_block=stronger_block,
        highlight_peak_price=highlight_block.peak_price,
        lookback_days=30
    )

    data = result.to_dict()

    assert data['found_stronger_root'] is True
    assert data['stronger_block_id'] == stronger_block.id
    assert data['peak_price_ratio'] == 1.2
    assert data['lookback_days'] == 30


def test_to_dict_without_stronger_root():
    """Test to_dict serialization without stronger root."""
    result = BackwardScanResult.no_stronger_root(lookback_days=30)

    data = result.to_dict()

    assert data['found_stronger_root'] is False
    assert data['stronger_block_id'] is None
    assert data['peak_price_ratio'] == 1.0
    assert data['lookback_days'] == 30


# ============================================================
# String Representation Tests
# ============================================================

def test_str_with_stronger_root(stronger_block, highlight_block):
    """Test string representation with stronger root."""
    result = BackwardScanResult.with_stronger_root(
        stronger_block=stronger_block,
        highlight_peak_price=highlight_block.peak_price,
        lookback_days=30
    )

    s = str(result)

    assert 'found_stronger_root=True' in s
    assert 'ratio=1.20x' in s
    assert 'lookback=30d' in s


def test_str_without_stronger_root():
    """Test string representation without stronger root."""
    result = BackwardScanResult.no_stronger_root(lookback_days=30)

    s = str(result)

    assert 'no_stronger_root' in s
    assert 'lookback=30d' in s


# ============================================================
# Immutability Tests
# ============================================================

def test_backward_scan_result_is_immutable(stronger_block, highlight_block):
    """Test that BackwardScanResult is immutable (frozen dataclass)."""
    result = BackwardScanResult.with_stronger_root(
        stronger_block=stronger_block,
        highlight_peak_price=highlight_block.peak_price,
        lookback_days=30
    )

    with pytest.raises(Exception):  # FrozenInstanceError
        result.found_stronger_root = False

    with pytest.raises(Exception):
        result.lookback_days = 60


# ============================================================
# Edge Cases
# ============================================================

def test_exact_equal_peak_price_rejected(highlight_block):
    """Test that exact equal peak price is rejected."""
    equal_block = DynamicBlockDetection(
        id=3,
        block_id='block1',
        block_type=1,
        ticker='025980',
        started_at=date(2020, 4, 1),
        ended_at=date(2020, 4, 10),
        peak_price=10000.0,  # Exact same as highlight
        peak_volume=30000000,
        status='completed',
        condition_name='test_condition'
    )

    with pytest.raises(ValueError, match="must be higher"):
        BackwardScanResult.with_stronger_root(
            stronger_block=equal_block,
            highlight_peak_price=highlight_block.peak_price,
            lookback_days=30
        )


def test_very_large_lookback_days():
    """Test with very large lookback period."""
    result = BackwardScanResult.no_stronger_root(lookback_days=365)

    assert result.lookback_days == 365
    assert result.found_stronger_root is False


def test_ratio_calculation_accuracy():
    """Test that peak_price_ratio is calculated accurately."""
    stronger = DynamicBlockDetection(
        id=1,
        block_id='block1',
        block_type=1,
        ticker='025980',
        started_at=date(2020, 4, 1),
        ended_at=date(2020, 4, 10),
        peak_price=15750.0,
        peak_volume=50000000,
        status='completed',
        condition_name='test_condition'
    )

    result = BackwardScanResult.with_stronger_root(
        stronger_block=stronger,
        highlight_peak_price=10500.0,
        lookback_days=30
    )

    expected_ratio = 15750.0 / 10500.0
    assert abs(result.peak_price_ratio - expected_ratio) < 0.0001
