"""
Function Registry - 함수 레지스트리

표현식에서 사용할 수 있는 함수들을 등록하고 관리합니다.
ML Feature Registry와 동일한 패턴을 사용합니다.

예시:
    @function_registry.register('ma', category='moving_average')
    def ma(period: int, context: dict) -> float:
        return context.get(f'ma_{period}', 0.0)

    # 사용
    func = function_registry.get('ma')
    result = func(120, context={'ma_120': 15000})
"""
from typing import Dict, Callable, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class FunctionMetadata:
    """함수 메타데이터"""
    name: str
    func: Callable
    category: str
    description: str = ""
    params_schema: dict = field(default_factory=dict)
    enabled: bool = True
    version: str = "1.0"


class FunctionRegistry:
    """
    함수 레지스트리

    데코레이터 패턴으로 함수를 등록하고, 표현식 엔진에서 사용할 수 있도록 합니다.

    특징:
    - Decorator 기반 등록: @function_registry.register(...)
    - 함수 메타데이터 관리
    - 카테고리별 분류
    - Enable/Disable 기능
    - 파라미터 스키마 (validation용)

    사용 예시:
        >>> registry = FunctionRegistry()
        >>>
        >>> @registry.register('ma', category='moving_average')
        >>> def ma(period: int, context: dict) -> float:
        >>>     return context.get(f'ma_{period}', 0.0)
        >>>
        >>> func = registry.get('ma')
        >>> result = func(120, context={'ma_120': 15000})
        >>> # result = 15000
    """

    def __init__(self):
        """FunctionRegistry 초기화"""
        self._functions: Dict[str, FunctionMetadata] = {}

    def register(
        self,
        name: str,
        category: str,
        description: str = "",
        params_schema: dict = None,
        version: str = "1.0"
    ):
        """
        함수 등록 데코레이터

        Args:
            name: 함수 이름 (표현식에서 사용할 이름)
            category: 카테고리 (moving_average, indicator, time, etc.)
            description: 함수 설명
            params_schema: 파라미터 스키마 (validation용)
                예: {'period': {'type': 'int', 'min': 1, 'max': 365}}
            version: 함수 버전

        Returns:
            데코레이터 함수

        Example:
            @function_registry.register(
                name='ma',
                category='moving_average',
                description='N일 이동평균',
                params_schema={'period': {'type': 'int', 'min': 1, 'max': 365}}
            )
            def ma(period: int, context: dict) -> float:
                return context.get(f'ma_{period}', 0.0)
        """
        def decorator(func: Callable):
            self._functions[name] = FunctionMetadata(
                name=name,
                func=func,
                category=category,
                description=description,
                params_schema=params_schema or {},
                enabled=True,
                version=version
            )
            return func
        return decorator

    def get(self, name: str) -> Callable:
        """
        함수 조회

        Args:
            name: 함수 이름

        Returns:
            함수 객체

        Raises:
            ValueError: 함수가 존재하지 않거나 비활성화된 경우
        """
        if name not in self._functions:
            raise ValueError(f"알 수 없는 함수: {name}")

        meta = self._functions[name]

        if not meta.enabled:
            raise ValueError(f"함수 '{name}'는 비활성화되었습니다")

        return meta.func

    def get_metadata(self, name: str) -> FunctionMetadata:
        """
        함수 메타데이터 조회

        Args:
            name: 함수 이름

        Returns:
            FunctionMetadata 객체

        Raises:
            ValueError: 함수가 존재하지 않는 경우
        """
        if name not in self._functions:
            raise ValueError(f"알 수 없는 함수: {name}")
        return self._functions[name]

    def list_functions(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """
        등록된 함수 목록 조회

        Args:
            category: 카테고리 필터 (None이면 전체)
            enabled_only: 활성화된 함수만 표시

        Returns:
            함수 이름 리스트 (정렬됨)
        """
        functions = []

        for name, meta in self._functions.items():
            # 비활성화 필터
            if enabled_only and not meta.enabled:
                continue

            # 카테고리 필터
            if category and meta.category != category:
                continue

            functions.append(name)

        return sorted(functions)

    def enable(self, name: str):
        """
        함수 활성화

        Args:
            name: 함수 이름

        Raises:
            ValueError: 함수가 존재하지 않는 경우
        """
        if name not in self._functions:
            raise ValueError(f"알 수 없는 함수: {name}")
        self._functions[name].enabled = True

    def disable(self, name: str):
        """
        함수 비활성화

        Args:
            name: 함수 이름

        Raises:
            ValueError: 함수가 존재하지 않는 경우
        """
        if name not in self._functions:
            raise ValueError(f"알 수 없는 함수: {name}")
        self._functions[name].enabled = False

    def get_categories(self) -> List[str]:
        """
        등록된 카테고리 목록 조회

        Returns:
            카테고리 리스트 (정렬됨)
        """
        categories = set(meta.category for meta in self._functions.values())
        return sorted(categories)

    def get_functions_by_category(self) -> Dict[str, List[str]]:
        """
        카테고리별 함수 목록 조회

        Returns:
            {category: [function_names]} 형태의 딕셔너리
        """
        result = {}

        for name, meta in self._functions.items():
            if meta.category not in result:
                result[meta.category] = []
            result[meta.category].append(name)

        # 각 카테고리 내부 정렬
        for category in result:
            result[category].sort()

        return result

    def print_summary(self):
        """등록된 함수 요약 출력"""
        categories = self.get_functions_by_category()

        print(f"\nFunction Registry Summary")
        print(f"{'='*60}")
        print(f"Total functions: {len(self._functions)}")
        print(f"Categories: {len(categories)}")
        print()

        for category in sorted(categories.keys()):
            functions = categories[category]
            print(f"[{category.upper()}] ({len(functions)} functions)")

            for name in functions:
                meta = self.get_metadata(name)
                status = "ENABLED" if meta.enabled else "DISABLED"
                print(f"  - {name:30} [{status}] v{meta.version}")

                if meta.description:
                    print(f"    {meta.description}")

                if meta.params_schema:
                    params_str = ", ".join(
                        f"{k}({v.get('type', 'any')})"
                        for k, v in meta.params_schema.items()
                    )
                    print(f"    Parameters: {params_str}")

            print()

    def validate_params(
        self,
        func_name: str,
        params: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        함수 파라미터 검증 (선택적)

        Args:
            func_name: 함수 이름
            params: 검증할 파라미터

        Returns:
            (유효성, 오류메시지) 튜플
                유효하면: (True, None)
                유효하지 않으면: (False, "오류 메시지")
        """
        meta = self.get_metadata(func_name)
        schema = meta.params_schema

        if not schema:
            # 스키마가 없으면 검증 생략
            return (True, None)

        for param_name, param_schema in schema.items():
            # 필수 파라미터 체크
            if param_schema.get('required', False) and param_name not in params:
                return (False, f"필수 파라미터 누락: {param_name}")

            if param_name in params:
                value = params[param_name]

                # 타입 체크
                expected_type = param_schema.get('type')
                if expected_type:
                    if expected_type == 'int' and not isinstance(value, int):
                        return (False, f"{param_name}은(는) int 타입이어야 합니다")
                    elif expected_type == 'float' and not isinstance(value, (int, float)):
                        return (False, f"{param_name}은(는) float 타입이어야 합니다")
                    elif expected_type == 'str' and not isinstance(value, str):
                        return (False, f"{param_name}은(는) str 타입이어야 합니다")

                # 범위 체크 (숫자)
                if isinstance(value, (int, float)):
                    if 'min' in param_schema and value < param_schema['min']:
                        return (False, f"{param_name}은(는) {param_schema['min']} 이상이어야 합니다")
                    if 'max' in param_schema and value > param_schema['max']:
                        return (False, f"{param_name}은(는) {param_schema['max']} 이하여야 합니다")

        return (True, None)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Global Registry Instance
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전역 레지스트리 (모든 함수가 여기에 등록됨)
function_registry = FunctionRegistry()
