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

from src.domain.entities import DynamicBlockDetection, BlockStatus, Stock
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
# Entity Fixtures - DynamicBlockDetection
# ============================================================================

@pytest.fixture
def sample_dynamic_block_detection():
    """Create a sample DynamicBlockDetection entity for testing"""
    return DynamicBlockDetection(
        block_id="block1",
        block_type=1,
        ticker="005930",  # Samsung Electronics
        condition_name="seed",
        started_at=date(2024, 1, 1),
        ended_at=date(2024, 1, 10),
        status=BlockStatus.COMPLETED,
        peak_price=80000.0,
        peak_volume=15000000,
        peak_date=date(2024, 1, 5),
        pattern_id=1
    )


@pytest.fixture
def active_block_detection():
    """Create an active DynamicBlockDetection (not completed)"""
    return DynamicBlockDetection(
        block_id="block1",
        block_type=1,
        ticker="005930",
        condition_name="seed",
        started_at=date(2024, 1, 1),
        peak_price=80000.0,
        peak_volume=15000000,
        peak_date=date(2024, 1, 5)
    )


@pytest.fixture
def completed_block_detection():
    """Create a completed DynamicBlockDetection"""
    return DynamicBlockDetection(
        block_id="block1",
        block_type=1,
        ticker="005930",
        condition_name="seed",
        started_at=date(2024, 1, 1),
        ended_at=date(2024, 1, 10),
        status=BlockStatus.COMPLETED,
        peak_price=80000.0,
        peak_volume=15000000,
        peak_date=date(2024, 1, 5)
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
    base_date = date(2024, 1, 1)
    stocks = []

    for i in range(30):
        current_date = base_date + timedelta(days=i)
        stock = Stock(
            ticker="005930",
            name="삼성전자",
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
