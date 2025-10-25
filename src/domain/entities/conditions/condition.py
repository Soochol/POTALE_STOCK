"""
Condition - 블록 조건 표현 객체

YAML의 조건을 객체로 표현하여 데이터 일관성 유지.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .expression_engine import ExpressionEngine


@dataclass
class Condition:
    """
    블록 조건 표현 객체

    YAML에서 정의한 조건을 객체로 표현하여 메타데이터를 보존하고
    평가 로직을 캡슐화합니다.

    Attributes:
        name: 조건 이름 (예: "price_threshold", "volume_surge")
        expression: 평가 표현식 (예: "current.close >= 10000")
        description: 조건 설명 (선택적)

    Example:
        >>> condition = Condition(
        ...     name="price_check",
        ...     expression="current.close >= 10000",
        ...     description="가격 10000원 이상"
        ... )
        >>> result = condition.evaluate(engine, context)
    """

    name: str
    expression: str
    description: str = ""

    def __post_init__(self):
        """조건 검증"""
        if not self.name:
            raise ValueError("name은 필수입니다")

        if not self.expression:
            raise ValueError("expression은 필수입니다")

    def evaluate(self, engine: 'ExpressionEngine', context: dict) -> bool:
        """
        조건 평가

        Args:
            engine: ExpressionEngine 인스턴스
            context: 평가 컨텍스트

        Returns:
            평가 결과 (True/False)

        Raises:
            ExpressionEvaluationError: 표현식 평가 실패 시
        """
        return engine.evaluate(self.expression, context)

    def __repr__(self) -> str:
        return f"Condition(name='{self.name}', expression='{self.expression[:50]}...')"
