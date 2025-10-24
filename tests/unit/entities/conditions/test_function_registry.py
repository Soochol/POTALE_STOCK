"""
FunctionRegistry 단위 테스트
"""
import pytest
from src.domain.entities.conditions import FunctionRegistry


class TestFunctionRegistry:
    """FunctionRegistry 테스트"""

    def test_register_and_get_function(self):
        """함수 등록 및 조회 테스트"""
        registry = FunctionRegistry()

        # 함수 등록
        @registry.register('test_func', category='test')
        def test_func(x: int, context: dict) -> int:
            return x * 2

        # 함수 조회
        func = registry.get('test_func')
        assert func(10, context={}) == 20

    def test_register_with_metadata(self):
        """메타데이터와 함께 등록 테스트"""
        registry = FunctionRegistry()

        @registry.register(
            name='ma',
            category='moving_average',
            description='N일 이동평균',
            params_schema={'period': {'type': 'int', 'min': 1, 'max': 365}},
            version='1.0'
        )
        def ma(period: int, context: dict) -> float:
            return context.get(f'ma_{period}', 0.0)

        # 메타데이터 확인
        meta = registry.get_metadata('ma')
        assert meta.name == 'ma'
        assert meta.category == 'moving_average'
        assert meta.description == 'N일 이동평균'
        assert meta.params_schema == {'period': {'type': 'int', 'min': 1, 'max': 365}}
        assert meta.version == '1.0'
        assert meta.enabled == True

    def test_list_functions(self):
        """함수 목록 조회 테스트"""
        registry = FunctionRegistry()

        @registry.register('func1', category='cat1')
        def func1(context: dict): return 1

        @registry.register('func2', category='cat1')
        def func2(context: dict): return 2

        @registry.register('func3', category='cat2')
        def func3(context: dict): return 3

        # 전체 함수 목록
        all_funcs = registry.list_functions()
        assert set(all_funcs) == {'func1', 'func2', 'func3'}

        # 카테고리 필터
        cat1_funcs = registry.list_functions(category='cat1')
        assert set(cat1_funcs) == {'func1', 'func2'}

    def test_enable_disable_function(self):
        """함수 활성화/비활성화 테스트"""
        registry = FunctionRegistry()

        @registry.register('test_func', category='test')
        def test_func(context: dict): return 42

        # 기본적으로 활성화됨
        assert registry.get('test_func')

        # 비활성화
        registry.disable('test_func')
        with pytest.raises(ValueError, match="비활성화"):
            registry.get('test_func')

        # 목록에서도 제외됨
        assert 'test_func' not in registry.list_functions(enabled_only=True)

        # 재활성화
        registry.enable('test_func')
        assert registry.get('test_func')

    def test_get_categories(self):
        """카테고리 목록 조회 테스트"""
        registry = FunctionRegistry()

        @registry.register('func1', category='cat_a')
        def func1(context: dict): return 1

        @registry.register('func2', category='cat_b')
        def func2(context: dict): return 2

        @registry.register('func3', category='cat_a')
        def func3(context: dict): return 3

        categories = registry.get_categories()
        assert set(categories) == {'cat_a', 'cat_b'}

    def test_get_functions_by_category(self):
        """카테고리별 함수 목록 조회 테스트"""
        registry = FunctionRegistry()

        @registry.register('ma', category='moving_average')
        def ma(context: dict): return 1

        @registry.register('rsi', category='indicator')
        def rsi(context: dict): return 2

        @registry.register('macd', category='indicator')
        def macd(context: dict): return 3

        by_category = registry.get_functions_by_category()
        assert by_category['moving_average'] == ['ma']
        assert set(by_category['indicator']) == {'macd', 'rsi'}

    def test_validate_params(self):
        """파라미터 검증 테스트"""
        registry = FunctionRegistry()

        @registry.register(
            name='test_func',
            category='test',
            params_schema={
                'period': {'type': 'int', 'min': 1, 'max': 100, 'required': True},
                'threshold': {'type': 'float', 'min': 0.0, 'max': 1.0}
            }
        )
        def test_func(period: int, threshold: float, context: dict): return period

        # 유효한 파라미터
        valid, msg = registry.validate_params('test_func', {'period': 50, 'threshold': 0.5})
        assert valid == True
        assert msg is None

        # 필수 파라미터 누락
        valid, msg = registry.validate_params('test_func', {'threshold': 0.5})
        assert valid == False
        assert "필수 파라미터 누락" in msg

        # 타입 오류
        valid, msg = registry.validate_params('test_func', {'period': '50'})
        assert valid == False
        assert "int 타입" in msg

        # 범위 오류
        valid, msg = registry.validate_params('test_func', {'period': 200})
        assert valid == False
        assert "100 이하" in msg

    def test_unknown_function(self):
        """존재하지 않는 함수 조회 테스트"""
        registry = FunctionRegistry()

        with pytest.raises(ValueError, match="알 수 없는 함수"):
            registry.get('unknown_func')

        with pytest.raises(ValueError, match="알 수 없는 함수"):
            registry.get_metadata('unknown_func')

    def test_decorator_return_value(self):
        """데코레이터가 원래 함수를 반환하는지 테스트"""
        registry = FunctionRegistry()

        @registry.register('my_func', category='test')
        def my_func(x: int, context: dict) -> int:
            """Docstring test"""
            return x + 1

        # 원래 함수가 그대로 반환되는지 확인
        assert my_func.__name__ == 'my_func'
        assert my_func.__doc__ == 'Docstring test'
        assert my_func(5, {}) == 6
