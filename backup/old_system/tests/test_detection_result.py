"""
Unit tests for DetectionResult entity
"""
import pytest
from datetime import datetime, date
from src.domain.entities.core.detection_result import DetectionResult
from src.domain.entities.core.stock import Stock


@pytest.fixture
def sample_stocks():
    """Create sample stocks"""
    stocks = []
    for i in range(3):
        stock = Stock(
            ticker=f"00593{i}",
            name=f"테스트{i}",
            date=date(2024, 1, 1),
            open=75000.0 + i * 1000,
            high=76000.0 + i * 1000,
            low=74500.0 + i * 1000,
            close=75500.0 + i * 1000,
            volume=10000000 + i * 1000000,
            trading_value=755.0 + i * 10
        )
        stocks.append(stock)
    return stocks


@pytest.mark.unit
@pytest.mark.entity
class TestDetectionResultCreation:
    """Test DetectionResult creation"""

    def test_create_minimal_detection_result(self):
        """Test creating DetectionResult with minimal fields"""
        result = DetectionResult(
            condition_name="test_condition",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        assert result.condition_name == "test_condition"
        assert result.detected_at == datetime(2024, 1, 1, 10, 0, 0)
        assert result.stocks == []
        assert result.metadata == {}

    def test_create_with_stocks(self, sample_stocks):
        """Test creating DetectionResult with stocks"""
        result = DetectionResult(
            condition_name="test_condition",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        assert len(result.stocks) == 3
        assert result.stocks[0].ticker == "005930"

    def test_create_with_metadata(self):
        """Test creating DetectionResult with metadata"""
        metadata = {"source": "seed", "version": "1.0"}
        result = DetectionResult(
            condition_name="test_condition",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            metadata=metadata
        )

        assert result.metadata["source"] == "seed"
        assert result.metadata["version"] == "1.0"


@pytest.mark.unit
@pytest.mark.entity
class TestDetectionResultValidation:
    """Test DetectionResult validation"""

    def test_empty_condition_name_raises_error(self):
        """Test that empty condition_name raises ValueError"""
        with pytest.raises(ValueError, match="조건 이름은 필수입니다"):
            DetectionResult(
                condition_name="",
                detected_at=datetime(2024, 1, 1, 10, 0, 0)
            )

    def test_none_condition_name_raises_error(self):
        """Test that None condition_name raises ValueError"""
        with pytest.raises(ValueError, match="조건 이름은 필수입니다"):
            DetectionResult(
                condition_name=None,
                detected_at=datetime(2024, 1, 1, 10, 0, 0)
            )


@pytest.mark.unit
@pytest.mark.entity
class TestDetectionResultProperties:
    """Test DetectionResult properties"""

    def test_count_property(self, sample_stocks):
        """Test count property"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        assert result.count == 3

    def test_count_empty(self):
        """Test count when no stocks"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        assert result.count == 0

    def test_is_empty_true(self):
        """Test is_empty when no stocks"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        assert result.is_empty is True

    def test_is_empty_false(self, sample_stocks):
        """Test is_empty when has stocks"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        assert result.is_empty is False


@pytest.mark.unit
@pytest.mark.entity
class TestDetectionResultMethods:
    """Test DetectionResult methods"""

    def test_add_stock(self, sample_stocks):
        """Test adding a stock"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        result.add_stock(sample_stocks[0])

        assert result.count == 1
        assert result.stocks[0].ticker == "005930"

    def test_add_multiple_stocks(self, sample_stocks):
        """Test adding multiple stocks"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        for stock in sample_stocks:
            result.add_stock(stock)

        assert result.count == 3

    def test_add_stock_invalid_type_raises_error(self):
        """Test that adding non-Stock raises TypeError"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        with pytest.raises(TypeError, match="Stock 객체만 추가할 수 있습니다"):
            result.add_stock("not a stock")

    def test_get_tickers(self, sample_stocks):
        """Test getting ticker list"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        tickers = result.get_tickers()

        assert len(tickers) == 3
        assert tickers == ["005930", "005931", "005932"]

    def test_get_tickers_empty(self):
        """Test getting tickers when no stocks"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        tickers = result.get_tickers()

        assert tickers == []

    def test_filter_by_ticker(self, sample_stocks):
        """Test filtering stocks by ticker"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        filtered = result.filter_by_ticker(["005930", "005932"])

        assert len(filtered) == 2
        assert filtered[0].ticker == "005930"
        assert filtered[1].ticker == "005932"

    def test_filter_by_ticker_no_match(self, sample_stocks):
        """Test filtering with no matches"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        filtered = result.filter_by_ticker(["999999"])

        assert len(filtered) == 0

    def test_filter_by_ticker_empty_list(self, sample_stocks):
        """Test filtering with empty ticker list"""
        result = DetectionResult(
            condition_name="test",
            detected_at=datetime(2024, 1, 1, 10, 0, 0),
            stocks=sample_stocks
        )

        filtered = result.filter_by_ticker([])

        assert len(filtered) == 0
