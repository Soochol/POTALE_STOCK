"""
Unit tests for BaseEntryCondition entity
"""
import pytest
from src.domain.entities.conditions.base_entry_condition import (
    BaseEntryCondition,
    Block1ExitConditionType
)


@pytest.mark.unit
@pytest.mark.entity
class TestBlock1ExitConditionType:
    """Test Block1ExitConditionType enum"""

    def test_enum_values(self):
        """Test enum has correct values"""
        assert Block1ExitConditionType.MA_BREAK.value == "ma_break"
        assert Block1ExitConditionType.THREE_LINE_REVERSAL.value == "three_line_reversal"
        assert Block1ExitConditionType.BODY_MIDDLE.value == "body_middle"

    def test_enum_members(self):
        """Test all enum members exist"""
        assert hasattr(Block1ExitConditionType, 'MA_BREAK')
        assert hasattr(Block1ExitConditionType, 'THREE_LINE_REVERSAL')
        assert hasattr(Block1ExitConditionType, 'BODY_MIDDLE')


@pytest.mark.unit
@pytest.mark.entity
class TestBaseEntryConditionCreation:
    """Test BaseEntryCondition creation"""

    def test_create_empty_condition(self):
        """Test creating empty condition with all None values"""
        condition = BaseEntryCondition()

        assert condition.block1_entry_surge_rate is None
        assert condition.block1_entry_ma_period is None
        assert condition.block1_entry_high_above_ma is None
        assert condition.block1_entry_max_deviation_ratio is None
        assert condition.block1_entry_min_trading_value is None
        assert condition.block1_entry_volume_high_months is None
        assert condition.block1_entry_volume_spike_ratio is None

    def test_create_with_surge_rate(self):
        """Test creating condition with surge rate"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=5.0
        )

        assert condition.block1_entry_surge_rate == 5.0

    def test_create_with_ma_conditions(self):
        """Test creating condition with MA settings"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_entry_high_above_ma=True,
            block1_entry_max_deviation_ratio=115.0
        )

        assert condition.block1_entry_ma_period == 20
        assert condition.block1_entry_high_above_ma is True
        assert condition.block1_entry_max_deviation_ratio == 115.0

    def test_create_with_trading_value(self):
        """Test creating condition with trading value"""
        condition = BaseEntryCondition(
            block1_entry_min_trading_value=100.0
        )

        assert condition.block1_entry_min_trading_value == 100.0

    def test_create_with_volume_conditions(self):
        """Test creating condition with volume settings"""
        condition = BaseEntryCondition(
            block1_entry_volume_high_months=3,
            block1_entry_volume_spike_ratio=1.5
        )

        assert condition.block1_entry_volume_high_months == 3
        assert condition.block1_entry_volume_spike_ratio == 1.5

    def test_create_with_all_conditions(self):
        """Test creating condition with all fields"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=5.0,
            block1_entry_ma_period=20,
            block1_entry_high_above_ma=True,
            block1_entry_max_deviation_ratio=115.0,
            block1_entry_min_trading_value=100.0,
            block1_entry_volume_high_months=3,
            block1_entry_volume_spike_ratio=1.5
        )

        assert condition.block1_entry_surge_rate == 5.0
        assert condition.block1_entry_ma_period == 20
        assert condition.block1_entry_high_above_ma is True
        assert condition.block1_entry_max_deviation_ratio == 115.0
        assert condition.block1_entry_min_trading_value == 100.0
        assert condition.block1_entry_volume_high_months == 3
        assert condition.block1_entry_volume_spike_ratio == 1.5


@pytest.mark.unit
@pytest.mark.entity
class TestBaseEntryConditionExitSettings:
    """Test exit condition settings"""

    def test_create_with_exit_ma_period(self):
        """Test creating with exit MA period"""
        condition = BaseEntryCondition(
            block1_exit_ma_period=20
        )

        assert condition.block1_exit_ma_period == 20

    def test_create_with_exit_condition_type(self):
        """Test creating with exit condition type"""
        condition = BaseEntryCondition(
            block1_exit_condition_type=Block1ExitConditionType.MA_BREAK
        )

        assert condition.block1_exit_condition_type == Block1ExitConditionType.MA_BREAK

    def test_exit_condition_type_three_line_reversal(self):
        """Test THREE_LINE_REVERSAL exit type"""
        condition = BaseEntryCondition(
            block1_exit_condition_type=Block1ExitConditionType.THREE_LINE_REVERSAL
        )

        assert condition.block1_exit_condition_type == Block1ExitConditionType.THREE_LINE_REVERSAL

    def test_exit_condition_type_body_middle(self):
        """Test BODY_MIDDLE exit type"""
        condition = BaseEntryCondition(
            block1_exit_condition_type=Block1ExitConditionType.BODY_MIDDLE
        )

        assert condition.block1_exit_condition_type == Block1ExitConditionType.BODY_MIDDLE


@pytest.mark.unit
@pytest.mark.entity
class TestBaseEntryConditionDefaults:
    """Test default values"""

    def test_all_fields_default_to_none(self):
        """Test that all entry fields have None as default"""
        condition = BaseEntryCondition()

        # Entry conditions default to None
        assert condition.block1_entry_surge_rate is None
        assert condition.block1_entry_ma_period is None
        assert condition.block1_entry_high_above_ma is None
        assert condition.block1_entry_max_deviation_ratio is None
        assert condition.block1_entry_min_trading_value is None
        assert condition.block1_entry_volume_high_months is None
        assert condition.block1_entry_volume_spike_ratio is None

        # Exit conditions have defaults
        assert condition.block1_exit_ma_period is None  # None is default
        assert condition.block1_exit_condition_type == Block1ExitConditionType.MA_BREAK  # MA_BREAK is default
        assert condition.block1_cooldown_days == 120  # 120 days is default

    def test_partial_initialization(self):
        """Test that unspecified fields remain None"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=5.0,
            block1_entry_ma_period=20
        )

        # Specified fields
        assert condition.block1_entry_surge_rate == 5.0
        assert condition.block1_entry_ma_period == 20

        # Unspecified fields should be None
        assert condition.block1_entry_high_above_ma is None
        assert condition.block1_entry_max_deviation_ratio is None
        assert condition.block1_entry_min_trading_value is None


@pytest.mark.unit
@pytest.mark.entity
class TestBaseEntryConditionValidation:
    """Test BaseEntryCondition validation"""

    def test_validate_with_surge_rate(self):
        """Test validation passes with surge rate"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=5.0
        )

        assert condition.validate() is True

    def test_validate_with_ma_period(self):
        """Test validation passes with MA period"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20
        )

        assert condition.validate() is True

    def test_validate_with_trading_value(self):
        """Test validation passes with trading value"""
        condition = BaseEntryCondition(
            block1_entry_min_trading_value=100.0
        )

        assert condition.validate() is True

    def test_validate_with_volume_high_months(self):
        """Test validation passes with volume high months"""
        condition = BaseEntryCondition(
            block1_entry_volume_high_months=3
        )

        assert condition.validate() is True

    def test_validate_fails_with_no_conditions(self):
        """Test validation fails with no conditions"""
        condition = BaseEntryCondition()

        assert condition.validate() is False

    def test_validate_fails_with_negative_surge_rate(self):
        """Test validation fails with negative surge rate"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=-5.0
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_surge_rate(self):
        """Test validation fails with zero surge rate"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=0.0
        )

        assert condition.validate() is False

    def test_validate_fails_with_negative_ma_period(self):
        """Test validation fails with negative MA period"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=-20
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_ma_period(self):
        """Test validation fails with zero MA period"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=0
        )

        assert condition.validate() is False

    def test_validate_fails_with_negative_deviation_ratio(self):
        """Test validation fails with negative deviation ratio"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,  # Need at least one valid condition
            block1_entry_max_deviation_ratio=-115.0
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_deviation_ratio(self):
        """Test validation fails with zero deviation ratio"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_entry_max_deviation_ratio=0.0
        )

        assert condition.validate() is False

    def test_validate_fails_with_negative_trading_value(self):
        """Test validation fails with negative trading value"""
        condition = BaseEntryCondition(
            block1_entry_min_trading_value=-100.0
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_trading_value(self):
        """Test validation fails with zero trading value"""
        condition = BaseEntryCondition(
            block1_entry_min_trading_value=0.0
        )

        assert condition.validate() is False

    def test_validate_fails_with_negative_volume_high_months(self):
        """Test validation fails with negative volume high months"""
        condition = BaseEntryCondition(
            block1_entry_volume_high_months=-3
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_volume_high_months(self):
        """Test validation fails with zero volume high months"""
        condition = BaseEntryCondition(
            block1_entry_volume_high_months=0
        )

        assert condition.validate() is False

    def test_validate_fails_with_negative_volume_spike_ratio(self):
        """Test validation fails with negative volume spike ratio"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,  # Need at least one valid condition
            block1_entry_volume_spike_ratio=-1.5
        )

        assert condition.validate() is False

    def test_validate_allows_zero_volume_spike_ratio(self):
        """Test validation allows zero volume spike ratio"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_entry_volume_spike_ratio=0.0
        )

        assert condition.validate() is True

    def test_validate_fails_with_negative_price_high_months(self):
        """Test validation fails with negative price high months"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_entry_price_high_months=-2
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_price_high_months(self):
        """Test validation fails with zero price high months"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_entry_price_high_months=0
        )

        assert condition.validate() is False

    def test_validate_fails_with_negative_cooldown_days(self):
        """Test validation fails with negative cooldown days"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_cooldown_days=-120
        )

        assert condition.validate() is False

    def test_validate_fails_with_zero_cooldown_days(self):
        """Test validation fails with zero cooldown days"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_cooldown_days=0
        )

        assert condition.validate() is False


@pytest.mark.unit
@pytest.mark.entity
class TestBaseEntryConditionRepr:
    """Test BaseEntryCondition __repr__"""

    def test_repr_with_surge_rate(self):
        """Test __repr__ with surge rate"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=5.0
        )

        repr_str = repr(condition)

        assert "<BaseEntryCondition(" in repr_str
        assert "등락률>=5.0%" in repr_str

    def test_repr_with_entry_ma_period(self):
        """Test __repr__ with entry MA period"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20
        )

        repr_str = repr(condition)

        assert "진입MA20" in repr_str

    def test_repr_with_exit_ma_period(self):
        """Test __repr__ with exit MA period"""
        condition = BaseEntryCondition(
            block1_entry_ma_period=20,
            block1_exit_ma_period=10
        )

        repr_str = repr(condition)

        assert "종료MA10" in repr_str

    def test_repr_with_trading_value(self):
        """Test __repr__ with trading value"""
        condition = BaseEntryCondition(
            block1_entry_min_trading_value=100.0
        )

        repr_str = repr(condition)

        assert "거래대금>=100.0억" in repr_str

    def test_repr_with_volume_high_months(self):
        """Test __repr__ with volume high months"""
        condition = BaseEntryCondition(
            block1_entry_volume_high_months=3
        )

        repr_str = repr(condition)

        assert "3개월신고거래량" in repr_str

    def test_repr_with_volume_spike_ratio(self):
        """Test __repr__ with volume spike ratio"""
        condition = BaseEntryCondition(
            block1_entry_volume_spike_ratio=1.5
        )

        repr_str = repr(condition)

        assert "전날대비150%증가" in repr_str

    def test_repr_with_multiple_conditions(self):
        """Test __repr__ with multiple conditions"""
        condition = BaseEntryCondition(
            block1_entry_surge_rate=5.0,
            block1_entry_ma_period=20,
            block1_entry_min_trading_value=100.0
        )

        repr_str = repr(condition)

        assert "등락률>=5.0%" in repr_str
        assert "진입MA20" in repr_str
        assert "거래대금>=100.0억" in repr_str

    def test_repr_with_no_conditions(self):
        """Test __repr__ with no conditions set"""
        condition = BaseEntryCondition()

        repr_str = repr(condition)

        assert repr_str == "<BaseEntryCondition()>"
