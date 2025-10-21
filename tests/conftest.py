"""
Pytest configuration and shared fixtures

This file contains fixtures that are available to all tests.
"""
import pytest
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import List
from unittest.mock import Mock, MagicMock

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.domain.entities import (
    Block1Detection,
    Block2Detection,
    Block3Detection,
    Block4Detection,
)
from src.infrastructure.database.connection import DatabaseConnection


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def db_connection():
    """Create a test database connection (session-scoped)"""
    # Use in-memory SQLite for tests
    db = DatabaseConnection(db_path=":memory:")
    yield db
    # Cleanup handled by in-memory DB


@pytest.fixture
def db_session(db_connection):
    """Create a clean database session for each test"""
    with db_connection.session_scope() as session:
        yield session
        # Rollback after each test to ensure isolation
        session.rollback()


# ============================================================================
# Date Fixtures
# ============================================================================

@pytest.fixture
def today():
    """Return today's date"""
    return date.today()


@pytest.fixture
def yesterday():
    """Return yesterday's date"""
    return date.today() - timedelta(days=1)


@pytest.fixture
def last_week():
    """Return date from one week ago"""
    return date.today() - timedelta(weeks=1)


@pytest.fixture
def sample_date_range():
    """Return a sample date range (30 days)"""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


# ============================================================================
# Entity Fixtures - Block1Detection
# ============================================================================

@pytest.fixture
def sample_block1_detection():
    """Create a sample Block1Detection entity for testing"""
    return Block1Detection(
        ticker="005930",  # Samsung Electronics
        started_at=date(2024, 1, 1),
        entry_open=75000.0,
        entry_high=76000.0,
        entry_low=74500.0,
        entry_close=75500.0,
        entry_volume=10000000,
        entry_trading_value=755.0,  # 억 단위
        condition_name="seed_condition_1",
        entry_ma_value=70000.0,
        entry_rate=5.0,
        entry_deviation=7.86,
        peak_price=80000.0,
        peak_date=date(2024, 1, 5),
        peak_volume=15000000,
        pattern_id=1,
        detection_type="seed"
    )


@pytest.fixture
def active_block1_detection(sample_block1_detection):
    """Create an active Block1Detection (not completed)"""
    detection = sample_block1_detection
    detection.status = "active"
    detection.ended_at = None
    return detection


@pytest.fixture
def completed_block1_detection(sample_block1_detection):
    """Create a completed Block1Detection"""
    detection = sample_block1_detection
    detection.status = "completed"
    detection.ended_at = date(2024, 1, 10)
    detection.exit_reason = "ma_break"
    detection.exit_price = 73000.0
    return detection


# ============================================================================
# Entity Fixtures - Block2/3/4Detection
# ============================================================================

@pytest.fixture
def sample_block2_detection():
    """Create a sample Block2Detection entity for testing"""
    return Block2Detection(
        ticker="005930",
        condition_name="seed_condition_1",
        started_at=date(2024, 2, 1),
        entry_close=78000.0,
        entry_rate=3.0,
        prev_block_id=1,
        prev_block_peak_price=80000.0,
        prev_block_peak_volume=15000000,
        peak_price=85000.0,
        peak_date=date(2024, 2, 5),
        peak_gain_ratio=8.97,
        peak_volume=18000000,
        pattern_id=1,
        detection_type="seed"
    )


@pytest.fixture
def sample_block3_detection():
    """Create a sample Block3Detection entity for testing"""
    return Block3Detection(
        ticker="005930",
        condition_name="seed_condition_1",
        started_at=date(2024, 3, 1),
        entry_close=82000.0,
        entry_rate=2.5,
        prev_block_id=2,
        prev_block_peak_price=85000.0,
        prev_block_peak_volume=18000000,
        peak_price=90000.0,
        peak_date=date(2024, 3, 5),
        peak_gain_ratio=9.76,
        peak_volume=20000000,
        pattern_id=1,
        detection_type="seed"
    )


@pytest.fixture
def sample_block4_detection():
    """Create a sample Block4Detection entity for testing"""
    return Block4Detection(
        ticker="005930",
        condition_name="seed_condition_1",
        started_at=date(2024, 4, 1),
        entry_close=88000.0,
        entry_rate=3.5,
        prev_block_id=3,
        prev_block_peak_price=90000.0,
        prev_block_peak_volume=20000000,
        peak_price=95000.0,
        peak_date=date(2024, 4, 5),
        peak_gain_ratio=7.95,
        peak_volume=22000000,
        pattern_id=1,
        detection_type="seed"
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_stock_repository():
    """Create a mock StockRepository"""
    mock_repo = Mock()
    mock_repo.find_by_ticker = Mock(return_value=None)
    mock_repo.find_all = Mock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_block1_repository():
    """Create a mock Block1Repository"""
    mock_repo = Mock()
    mock_repo.save = Mock(return_value=None)
    mock_repo.find_by_pattern_and_condition = Mock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_database_connection():
    """Create a mock DatabaseConnection"""
    mock_db = MagicMock()
    mock_db.session_scope = MagicMock()
    return mock_db


# ============================================================================
# Stock Data Fixtures
# ============================================================================

@pytest.fixture
def sample_stock_data():
    """Create sample stock price data"""
    from src.domain.entities import Stock

    base_date = date(2024, 1, 1)
    stocks = []

    for i in range(30):
        current_date = base_date + timedelta(days=i)
        stock = Stock(
            ticker="005930",
            date=current_date,
            open=75000 + i * 100,
            high=76000 + i * 100,
            low=74000 + i * 100,
            close=75500 + i * 100,
            volume=10000000 + i * 100000,
            trading_value=755.0 + i * 0.1
        )
        stocks.append(stock)

    return stocks


# ============================================================================
# Condition Fixtures
# ============================================================================

@pytest.fixture
def sample_condition_dict():
    """Create a sample condition dictionary"""
    return {
        "name": "seed_condition_1",
        "block1_entry": {
            "surge_rate": 5.0,
            "ma_high": 1.2,
            "deviation": 5.0,
            "trading_value": 100.0,
            "volume_high": 1.5,
            "volume_spike": 2.0,
            "price_high": 1.3
        },
        "block1_exit": {
            "ma_break": True,
            "three_line_reversal": True,
            "body_middle": True
        }
    }


# ============================================================================
# Helper Functions
# ============================================================================

def assert_entity_equal(entity1, entity2, exclude_fields=None):
    """
    Assert that two entities are equal, excluding certain fields

    Args:
        entity1: First entity
        entity2: Second entity
        exclude_fields: List of field names to exclude from comparison
    """
    exclude_fields = exclude_fields or []

    for field in entity1.__dataclass_fields__:
        if field not in exclude_fields:
            assert getattr(entity1, field) == getattr(entity2, field), \
                f"Field {field} mismatch: {getattr(entity1, field)} != {getattr(entity2, field)}"
