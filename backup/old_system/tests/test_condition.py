"""
Test Condition Entity

Tests for core Condition and Rule entities
"""
import pytest
from src.domain.entities.core.condition import Condition, Rule, RuleType


@pytest.mark.unit
@pytest.mark.entity
class TestRuleType:
    """Test RuleType enum"""

    def test_enum_values(self):
        """Test RuleType enum has correct values"""
        assert RuleType.CROSS_OVER.value == "cross_over"
        assert RuleType.INDICATOR_THRESHOLD.value == "indicator_threshold"
        assert RuleType.VOLUME_INCREASE.value == "volume_increase"
        assert RuleType.PRICE_CHANGE.value == "price_change"

    def test_enum_members(self):
        """Test RuleType enum has all expected members"""
        expected_members = {
            'CROSS_OVER',
            'INDICATOR_THRESHOLD',
            'VOLUME_INCREASE',
            'PRICE_CHANGE'
        }
        assert set(RuleType.__members__.keys()) == expected_members


@pytest.mark.unit
@pytest.mark.entity
class TestRuleCreation:
    """Test Rule entity creation"""

    def test_create_rule_with_type(self):
        """Test creating Rule with RuleType enum"""
        rule = Rule(
            type=RuleType.CROSS_OVER,
            parameters={'indicator1': 'MA5', 'indicator2': 'MA20'}
        )

        assert rule.type == RuleType.CROSS_OVER
        assert rule.parameters == {'indicator1': 'MA5', 'indicator2': 'MA20'}

    def test_create_rule_with_string_type(self):
        """Test creating Rule with string type (auto-converted to enum)"""
        rule = Rule(
            type="cross_over",
            parameters={'indicator1': 'MA5', 'indicator2': 'MA20'}
        )

        assert rule.type == RuleType.CROSS_OVER
        assert isinstance(rule.type, RuleType)

    def test_create_rule_with_empty_parameters(self):
        """Test creating Rule with default empty parameters"""
        rule = Rule(type=RuleType.CROSS_OVER)

        assert rule.type == RuleType.CROSS_OVER
        assert rule.parameters == {}


@pytest.mark.unit
@pytest.mark.entity
class TestRuleValidation:
    """Test Rule validation logic"""

    def test_validate_cross_over_valid(self):
        """Test CROSS_OVER rule validation passes with required params"""
        rule = Rule(
            type=RuleType.CROSS_OVER,
            parameters={'indicator1': 'MA5', 'indicator2': 'MA20'}
        )

        assert rule.validate() is True

    def test_validate_cross_over_invalid(self):
        """Test CROSS_OVER rule validation fails without required params"""
        rule = Rule(
            type=RuleType.CROSS_OVER,
            parameters={'indicator1': 'MA5'}  # Missing indicator2
        )

        assert rule.validate() is False

    def test_validate_indicator_threshold_valid(self):
        """Test INDICATOR_THRESHOLD rule validation passes"""
        rule = Rule(
            type=RuleType.INDICATOR_THRESHOLD,
            parameters={
                'indicator': 'RSI',
                'condition': '>',
                'value': 70
            }
        )

        assert rule.validate() is True

    def test_validate_indicator_threshold_invalid(self):
        """Test INDICATOR_THRESHOLD rule validation fails"""
        rule = Rule(
            type=RuleType.INDICATOR_THRESHOLD,
            parameters={
                'indicator': 'RSI',
                'condition': '>'
                # Missing 'value'
            }
        )

        assert rule.validate() is False

    def test_validate_volume_increase_valid(self):
        """Test VOLUME_INCREASE rule validation passes"""
        rule = Rule(
            type=RuleType.VOLUME_INCREASE,
            parameters={'threshold': 2.0}
        )

        assert rule.validate() is True

    def test_validate_volume_increase_invalid(self):
        """Test VOLUME_INCREASE rule validation fails"""
        rule = Rule(
            type=RuleType.VOLUME_INCREASE,
            parameters={}  # Missing threshold
        )

        assert rule.validate() is False

    def test_validate_price_change_valid(self):
        """Test PRICE_CHANGE rule validation passes"""
        rule = Rule(
            type=RuleType.PRICE_CHANGE,
            parameters={'threshold': 5.0}
        )

        assert rule.validate() is True

    def test_validate_price_change_invalid(self):
        """Test PRICE_CHANGE rule validation fails"""
        rule = Rule(
            type=RuleType.PRICE_CHANGE,
            parameters={}  # Missing threshold
        )

        assert rule.validate() is False


@pytest.mark.unit
@pytest.mark.entity
class TestConditionCreation:
    """Test Condition entity creation"""

    def test_create_condition_with_rules(self):
        """Test creating Condition with Rule objects"""
        rule1 = Rule(
            type=RuleType.CROSS_OVER,
            parameters={'indicator1': 'MA5', 'indicator2': 'MA20'}
        )
        rule2 = Rule(
            type=RuleType.VOLUME_INCREASE,
            parameters={'threshold': 2.0}
        )

        condition = Condition(
            name="test_condition",
            description="Test condition description",
            rules=[rule1, rule2]
        )

        assert condition.name == "test_condition"
        assert condition.description == "Test condition description"
        assert len(condition.rules) == 2
        assert all(isinstance(rule, Rule) for rule in condition.rules)

    def test_create_condition_with_dict_rules(self):
        """Test creating Condition with dict rules (auto-converted to Rule)"""
        condition = Condition(
            name="test_condition",
            description="Test description",
            rules=[
                {
                    'type': RuleType.CROSS_OVER,
                    'parameters': {'indicator1': 'MA5', 'indicator2': 'MA20'}
                }
            ]
        )

        assert len(condition.rules) == 1
        assert isinstance(condition.rules[0], Rule)
        assert condition.rules[0].type == RuleType.CROSS_OVER

    def test_create_condition_empty_name_raises_error(self):
        """Test creating Condition with empty name raises ValueError"""
        with pytest.raises(ValueError, match="조건 이름은 필수입니다"):
            Condition(
                name="",
                description="Test",
                rules=[Rule(type=RuleType.CROSS_OVER)]
            )

    def test_create_condition_no_rules_raises_error(self):
        """Test creating Condition without rules raises ValueError"""
        with pytest.raises(ValueError, match="최소 1개 이상의 규칙이 필요합니다"):
            Condition(
                name="test_condition",
                description="Test",
                rules=[]
            )


@pytest.mark.unit
@pytest.mark.entity
class TestConditionValidation:
    """Test Condition validation logic"""

    def test_validate_all_rules_valid(self):
        """Test validation passes when all rules are valid"""
        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[
                Rule(
                    type=RuleType.CROSS_OVER,
                    parameters={'indicator1': 'MA5', 'indicator2': 'MA20'}
                ),
                Rule(
                    type=RuleType.VOLUME_INCREASE,
                    parameters={'threshold': 2.0}
                )
            ]
        )

        assert condition.validate() is True

    def test_validate_some_rules_invalid(self):
        """Test validation fails when some rules are invalid"""
        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[
                Rule(
                    type=RuleType.CROSS_OVER,
                    parameters={'indicator1': 'MA5', 'indicator2': 'MA20'}
                ),
                Rule(
                    type=RuleType.VOLUME_INCREASE,
                    parameters={}  # Invalid - missing threshold
                )
            ]
        )

        assert condition.validate() is False


@pytest.mark.unit
@pytest.mark.entity
class TestConditionRuleManagement:
    """Test Condition rule management methods"""

    def test_add_rule(self):
        """Test adding a rule to condition"""
        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[
                Rule(type=RuleType.CROSS_OVER, parameters={'indicator1': 'MA5', 'indicator2': 'MA20'})
            ]
        )

        new_rule = Rule(type=RuleType.VOLUME_INCREASE, parameters={'threshold': 2.0})
        condition.add_rule(new_rule)

        assert len(condition.rules) == 2
        assert condition.rules[1] == new_rule

    def test_add_rule_with_non_rule_raises_error(self):
        """Test adding non-Rule object raises TypeError"""
        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[
                Rule(type=RuleType.CROSS_OVER, parameters={'indicator1': 'MA5', 'indicator2': 'MA20'})
            ]
        )

        with pytest.raises(TypeError, match="Rule 객체만 추가할 수 있습니다"):
            condition.add_rule({"type": "cross_over"})

    def test_remove_rule_valid_index(self):
        """Test removing a rule with valid index"""
        rule1 = Rule(type=RuleType.CROSS_OVER, parameters={'indicator1': 'MA5', 'indicator2': 'MA20'})
        rule2 = Rule(type=RuleType.VOLUME_INCREASE, parameters={'threshold': 2.0})

        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[rule1, rule2]
        )

        condition.remove_rule(0)

        assert len(condition.rules) == 1
        assert condition.rules[0] == rule2

    def test_remove_rule_invalid_index_does_nothing(self):
        """Test removing a rule with invalid index does nothing"""
        rule1 = Rule(type=RuleType.CROSS_OVER, parameters={'indicator1': 'MA5', 'indicator2': 'MA20'})

        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[rule1]
        )

        condition.remove_rule(10)  # Invalid index

        assert len(condition.rules) == 1  # No change

    def test_remove_rule_negative_index_does_nothing(self):
        """Test removing a rule with negative index does nothing"""
        rule1 = Rule(type=RuleType.CROSS_OVER, parameters={'indicator1': 'MA5', 'indicator2': 'MA20'})

        condition = Condition(
            name="test_condition",
            description="Test",
            rules=[rule1]
        )

        condition.remove_rule(-1)  # Negative index

        assert len(condition.rules) == 1  # No change
