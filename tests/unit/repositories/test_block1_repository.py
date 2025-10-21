"""
Unit tests for Block1Repository

Tests Entity/Model conversion and repository methods.
"""
import pytest
from datetime import date, datetime
from src.domain.entities import Block1Detection
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.database.models import Block1Detection as Block1DetectionModel


@pytest.mark.unit
@pytest.mark.repository
class TestBlock1RepositoryConversion:
    """Test Entity ↔ Model conversion"""

    def test_entity_to_model_conversion(self, sample_block1_detection):
        """Test converting Block1Detection entity to database model"""
        repo = Block1Repository()
        entity = sample_block1_detection

        model = repo._entity_to_model(entity)

        assert isinstance(model, Block1DetectionModel)
        assert model.block1_id == entity.block1_id
        assert model.ticker == entity.ticker
        assert model.started_at == entity.started_at
        assert model.entry_open == entity.entry_open
        assert model.entry_high == entity.entry_high
        assert model.entry_low == entity.entry_low
        assert model.entry_close == entity.entry_close
        assert model.entry_volume == entity.entry_volume
        assert model.entry_trading_value == entity.entry_trading_value
        assert model.peak_price == entity.peak_price
        assert model.peak_date == entity.peak_date
        assert model.peak_volume == entity.peak_volume
        assert model.pattern_id == entity.pattern_id
        assert model.detection_type == entity.detection_type

    def test_model_to_entity_conversion(self):
        """Test converting database model to Block1Detection entity"""
        repo = Block1Repository()

        # Create a model instance
        model = Block1DetectionModel(
            block1_id="test-uuid-123",
            ticker="005930",
            status="active",
            started_at=date(2024, 1, 1),
            ended_at=None,
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            entry_trading_value=755.0,
            entry_ma_value=70000.0,
            entry_rate=5.0,
            entry_deviation=7.86,
            peak_price=80000.0,
            peak_date=date(2024, 1, 5),
            peak_volume=15000000,
            condition_name="seed_condition_1",
            pattern_id=1,
            detection_type="seed",
            created_at=datetime(2024, 1, 1, 10, 30, 0)
        )

        entity = repo._model_to_entity(model)

        assert isinstance(entity, Block1Detection)
        assert entity.block1_id == model.block1_id
        assert entity.ticker == model.ticker
        assert entity.started_at == model.started_at
        assert entity.entry_open == model.entry_open
        assert entity.entry_high == model.entry_high
        assert entity.entry_low == model.entry_low
        assert entity.entry_close == model.entry_close
        assert entity.entry_volume == model.entry_volume
        assert entity.entry_trading_value == model.entry_trading_value
        assert entity.peak_price == model.peak_price
        assert entity.peak_date == model.peak_date
        assert entity.peak_volume == model.peak_volume
        assert entity.pattern_id == model.pattern_id
        assert entity.detection_type == model.detection_type
        assert entity.created_at == model.created_at
        assert isinstance(entity.created_at, datetime)

    def test_round_trip_conversion(self, sample_block1_detection):
        """Test entity → model → entity preserves data"""
        repo = Block1Repository()
        original = sample_block1_detection

        # Convert to model and back
        model = repo._entity_to_model(original)
        # Simulate DB persistence by setting created_at
        model.created_at = datetime.now()
        restored = repo._model_to_entity(model)

        # Check critical fields
        assert restored.ticker == original.ticker
        assert restored.started_at == original.started_at
        assert restored.entry_close == original.entry_close
        assert restored.peak_price == original.peak_price
        assert restored.peak_volume == original.peak_volume
        assert restored.pattern_id == original.pattern_id
        assert restored.detection_type == original.detection_type

    def test_null_entry_trading_value_preserved(self):
        """Test that NULL entry_trading_value is preserved (not converted to 0.0)"""
        repo = Block1Repository()

        # Create entity with None trading_value
        entity = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            entry_trading_value=None  # NULL
        )

        # Convert to model
        model = repo._entity_to_model(entity)
        assert model.entry_trading_value is None

        # Convert back
        model.created_at = datetime.now()
        restored = repo._model_to_entity(model)
        assert restored.entry_trading_value is None  # Should remain None, not 0.0

    def test_datetime_created_at_preserved(self):
        """Test that created_at datetime is preserved (not converted to date)"""
        repo = Block1Repository()

        now = datetime(2024, 1, 1, 15, 30, 45)
        model = Block1DetectionModel(
            block1_id="test-uuid",
            ticker="005930",
            status="active",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            created_at=now
        )

        entity = repo._model_to_entity(model)

        assert entity.created_at == now
        assert isinstance(entity.created_at, datetime)
        # Should NOT be converted to date - time info preserved


@pytest.mark.unit
@pytest.mark.repository
class TestBlock1RepositoryFieldMapping:
    """Test specific field mappings and edge cases"""

    def test_completed_block_fields(self):
        """Test that completed block fields are properly mapped"""
        repo = Block1Repository()

        entity = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            status="completed",
            ended_at=date(2024, 1, 10),
            exit_reason="ma_break",
            exit_price=73000.0
        )

        model = repo._entity_to_model(entity)

        assert model.status == "completed"
        assert model.ended_at == date(2024, 1, 10)
        assert model.exit_reason == "ma_break"
        assert model.exit_price == 73000.0

    def test_optional_indicator_fields(self):
        """Test that optional indicator fields can be None"""
        repo = Block1Repository()

        entity = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            entry_ma_value=None,
            entry_rate=None,
            entry_deviation=None
        )

        model = repo._entity_to_model(entity)

        assert model.entry_ma_value is None
        assert model.entry_rate is None
        assert model.entry_deviation is None

    def test_peak_fields_all_none(self):
        """Test entity with no peak information"""
        repo = Block1Repository()

        entity = Block1Detection(
            ticker="005930",
            started_at=date(2024, 1, 1),
            entry_open=75000.0,
            entry_high=76000.0,
            entry_low=74500.0,
            entry_close=75500.0,
            entry_volume=10000000,
            condition_name="test",
            peak_price=None,
            peak_date=None,
            peak_volume=None
        )

        model = repo._entity_to_model(entity)

        assert model.peak_price is None
        assert model.peak_date is None
        assert model.peak_volume is None


@pytest.mark.unit
@pytest.mark.repository
class TestBlock1RepositoryGetIdField:
    """Test _get_id_field method"""

    def test_get_id_field_returns_block1_id(self):
        """Test that _get_id_field returns block1_id column"""
        repo = Block1Repository()

        id_field = repo._get_id_field()

        # Should return the SQLAlchemy column for block1_id
        assert id_field.name == "block1_id"
