"""
Condition Entity - 조건 도메인 엔티티
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class RuleType(Enum):
    """규칙 타입"""
    CROSS_OVER = "cross_over"
    INDICATOR_THRESHOLD = "indicator_threshold"
    VOLUME_INCREASE = "volume_increase"
    PRICE_CHANGE = "price_change"


@dataclass
class Rule:
    """규칙 엔티티"""
    type: RuleType
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """유효성 검사"""
        if isinstance(self.type, str):
            self.type = RuleType(self.type)

    def validate(self) -> bool:
        """규칙 파라미터 유효성 검사"""
        if self.type == RuleType.CROSS_OVER:
            required = ['indicator1', 'indicator2']
            return all(key in self.parameters for key in required)

        elif self.type == RuleType.INDICATOR_THRESHOLD:
            required = ['indicator', 'condition', 'value']
            return all(key in self.parameters for key in required)

        elif self.type == RuleType.VOLUME_INCREASE:
            return 'threshold' in self.parameters

        elif self.type == RuleType.PRICE_CHANGE:
            return 'threshold' in self.parameters

        return False


@dataclass
class Condition:
    """조건 엔티티"""
    name: str
    description: str
    rules: List[Rule] = field(default_factory=list)

    def __post_init__(self):
        """유효성 검사"""
        if not self.name:
            raise ValueError("조건 이름은 필수입니다")
        if not self.rules:
            raise ValueError("최소 1개 이상의 규칙이 필요합니다")

        # Rule 객체로 변환
        self.rules = [
            rule if isinstance(rule, Rule) else Rule(**rule)
            for rule in self.rules
        ]

    def validate(self) -> bool:
        """조건의 모든 규칙 유효성 검사"""
        return all(rule.validate() for rule in self.rules)

    def add_rule(self, rule: Rule) -> None:
        """규칙 추가"""
        if not isinstance(rule, Rule):
            raise TypeError("Rule 객체만 추가할 수 있습니다")
        self.rules.append(rule)

    def remove_rule(self, index: int) -> None:
        """규칙 제거"""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
