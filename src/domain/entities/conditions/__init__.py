"""
Conditions Module - 동적 조건 시스템

표현식 기반 조건 평가, 함수 레지스트리, 블록 관계 관리
"""
from .condition import Condition
from .expression_engine import ExpressionEngine
from .function_registry import FunctionRegistry, FunctionMetadata, function_registry

# Import builtin functions to auto-register them
from . import builtin_functions

__all__ = [
    'Condition',
    'ExpressionEngine',
    'FunctionRegistry',
    'FunctionMetadata',
    'function_registry',
    'builtin_functions',
]
