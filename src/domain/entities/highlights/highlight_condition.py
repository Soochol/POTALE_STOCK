"""
HighlightCondition - 하이라이트 탐지 조건 Value Object

하이라이트 블록을 식별하기 위한 조건을 정의하는 불변 객체.
"""
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class HighlightCondition:
    """
    하이라이트 탐지 조건 (Value Object)

    하이라이트는 패턴의 앵커 포인트로 사용되는 특별한 블록.
    예: Forward spot - Block1 고점 위에서 연속 2개 거래량 spot 발생

    Attributes:
        type: 하이라이트 타입 ("forward_spot", "backward_spot", etc.)
        enabled: 하이라이트 탐지 활성화 여부 (기본: True)
        priority: 우선순위 (1=Primary, 2+=Secondary)
        parameters: 타입별 파라미터 (예: required_spot_count, day_offsets)
        description: 조건 설명

    Example:
        >>> condition = HighlightCondition(
        ...     type="forward_spot",
        ...     enabled=True,
        ...     priority=1,
        ...     parameters={
        ...         "required_spot_count": 2,
        ...         "consecutive": True,
        ...         "day_offsets": [1, 2]
        ...     },
        ...     description="2 consecutive spots at D+1, D+2"
        ... )
        >>> condition.is_enabled()
        True
    """

    type: str
    enabled: bool = True
    priority: int = 1
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self):
        """검증"""
        # type 필수 확인
        if not self.type:
            raise ValueError("HighlightCondition.type은 필수입니다")

        # priority 범위 확인
        if self.priority < 1:
            raise ValueError(f"priority는 1 이상이어야 합니다: {self.priority}")

        # 지원하는 타입 확인 (확장 가능)
        SUPPORTED_TYPES = ["forward_spot", "backward_spot", "custom"]
        if self.type not in SUPPORTED_TYPES:
            raise ValueError(
                f"지원하지 않는 하이라이트 타입: {self.type}. "
                f"지원 타입: {SUPPORTED_TYPES}"
            )

    def is_enabled(self) -> bool:
        """하이라이트 탐지가 활성화되어 있는지 확인"""
        return self.enabled

    def is_primary(self) -> bool:
        """Primary 하이라이트인지 확인"""
        return self.priority == 1

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        파라미터 조회

        Args:
            key: 파라미터 키
            default: 기본값 (없을 때)

        Returns:
            파라미터 값 또는 기본값

        Example:
            >>> condition.get_parameter("required_spot_count", 2)
            2
        """
        return self.parameters.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            'type': self.type,
            'enabled': self.enabled,
            'priority': self.priority,
            'parameters': self.parameters.copy(),
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HighlightCondition':
        """
        딕셔너리에서 생성

        Args:
            data: 딕셔너리 데이터

        Returns:
            HighlightCondition 인스턴스

        Example:
            >>> data = {
            ...     "type": "forward_spot",
            ...     "enabled": True,
            ...     "parameters": {"required_spot_count": 2}
            ... }
            >>> condition = HighlightCondition.from_dict(data)
        """
        return cls(
            type=data['type'],
            enabled=data.get('enabled', True),
            priority=data.get('priority', 1),
            parameters=data.get('parameters', {}),
            description=data.get('description', '')
        )

    def __repr__(self) -> str:
        return (
            f"HighlightCondition(type='{self.type}', "
            f"enabled={self.enabled}, priority={self.priority})"
        )

    def __str__(self) -> str:
        status = "ENABLED" if self.enabled else "DISABLED"
        priority_str = "PRIMARY" if self.is_primary() else f"SECONDARY(P{self.priority})"
        return f"Highlight [{status}] {priority_str}: {self.type}"
