"""
Unit tests for Condition entity

Tests the Condition object for representing block conditions.
"""
import pytest
from unittest.mock import Mock

from src.domain.entities.conditions import Condition


@pytest.mark.unit
class TestCondition:
    """Test Condition entity"""

    def test_create_condition_with_all_fields(self):
        """Test creating a condition with all fields"""
        condition = Condition(
            name="price_threshold",
            expression="current.close >= 10000",
            description="가격 10000원 이상"
        )

        assert condition.name == "price_threshold"
        assert condition.expression == "current.close >= 10000"
        assert condition.description == "가격 10000원 이상"

    def test_create_condition_without_description(self):
        """Test creating a condition without description (default empty string)"""
        condition = Condition(
            name="volume_check",
            expression="current.volume >= 1000000"
        )

        assert condition.name == "volume_check"
        assert condition.expression == "current.volume >= 1000000"
        assert condition.description == ""

    def test_name_required(self):
        """Test that name is required"""
        with pytest.raises(ValueError, match="name은 필수입니다"):
            Condition(
                name="",
                expression="current.close >= 10000"
            )

    def test_expression_required(self):
        """Test that expression is required"""
        with pytest.raises(ValueError, match="expression은 필수입니다"):
            Condition(
                name="test_condition",
                expression=""
            )

    def test_evaluate_calls_engine(self):
        """Test that evaluate() calls ExpressionEngine.evaluate()"""
        # Mock engine
        mock_engine = Mock()
        mock_engine.evaluate.return_value = True

        condition = Condition(
            name="test_condition",
            expression="current.close >= 10000"
        )

        context = {'current': Mock(close=15000)}
        result = condition.evaluate(mock_engine, context)

        # Verify engine.evaluate was called with correct arguments
        mock_engine.evaluate.assert_called_once_with(
            "current.close >= 10000",
            context
        )
        assert result is True

    def test_evaluate_returns_false(self):
        """Test that evaluate() returns False when condition not met"""
        mock_engine = Mock()
        mock_engine.evaluate.return_value = False

        condition = Condition(
            name="test_condition",
            expression="current.close >= 10000"
        )

        context = {'current': Mock(close=5000)}
        result = condition.evaluate(mock_engine, context)

        assert result is False

    def test_repr(self):
        """Test __repr__ output"""
        condition = Condition(
            name="long_expression",
            expression="a" * 100  # 100자 expression
        )

        repr_str = repr(condition)

        assert "Condition(name='long_expression'" in repr_str
        assert "..." in repr_str  # Expression이 잘렸는지 확인

    def test_repr_short_expression(self):
        """Test __repr__ with short expression"""
        condition = Condition(
            name="short",
            expression="current.close >= 10000"
        )

        repr_str = repr(condition)

        assert "Condition(name='short'" in repr_str
        assert "current.close >= 10000" in repr_str


@pytest.mark.unit
class TestConditionEquality:
    """Test Condition equality (for deduplication in lists)"""

    def test_same_conditions_are_equal(self):
        """Test that conditions with same values are equal"""
        condition1 = Condition(
            name="price_check",
            expression="current.close >= 10000",
            description="test"
        )
        condition2 = Condition(
            name="price_check",
            expression="current.close >= 10000",
            description="test"
        )

        # Dataclass equality
        assert condition1 == condition2

    def test_different_conditions_not_equal(self):
        """Test that conditions with different values are not equal"""
        condition1 = Condition(
            name="price_check",
            expression="current.close >= 10000"
        )
        condition2 = Condition(
            name="volume_check",
            expression="current.volume >= 1000000"
        )

        assert condition1 != condition2


@pytest.mark.unit
class TestConditionInList:
    """Test Condition behavior in lists"""

    def test_add_condition_to_list(self):
        """Test adding conditions to a list"""
        conditions = []

        condition1 = Condition(name="c1", expression="expr1")
        condition2 = Condition(name="c2", expression="expr2")

        conditions.append(condition1)
        conditions.append(condition2)

        assert len(conditions) == 2
        assert conditions[0].name == "c1"
        assert conditions[1].name == "c2"

    def test_deduplicate_conditions(self):
        """Test deduplicating conditions in a list"""
        condition1 = Condition(name="c1", expression="expr1")
        condition2 = Condition(name="c1", expression="expr1")

        conditions = []
        if condition1 not in conditions:
            conditions.append(condition1)
        if condition2 not in conditions:
            conditions.append(condition2)

        # Should only have 1 condition (duplicates removed)
        assert len(conditions) == 1
