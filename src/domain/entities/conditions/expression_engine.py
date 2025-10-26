"""
Expression Engine - 표현식 기반 조건 평가 엔진

사용자가 YAML에 작성한 표현식을 안전하게 파싱하고 평가합니다.

예시:
    expression = "current.close >= 10000 AND current.high >= ma(120)"
    result = engine.evaluate(expression, context)  # True/False
"""
import ast
import operator
from typing import Any, Dict, Callable, Optional


class ExpressionEngine:
    """
    안전한 표현식 평가 엔진

    AST (Abstract Syntax Tree)를 사용하여 표현식을 파싱하고,
    허용된 연산자와 함수만 실행하여 보안을 유지합니다.

    지원 기능:
    - 기본 연산자: +, -, *, /, %, >, <, >=, <=, ==, !=
    - 논리 연산자: AND, OR, NOT
    - 변수 접근: current.close, block1.peak_price
    - 함수 호출: ma(120), candles_between(...)

    보안:
    - 허용되지 않은 연산자/함수는 차단
    - 임의 코드 실행 불가
    - 안전한 변수 접근만 허용
    """

    def __init__(self, function_registry: Optional['FunctionRegistry'] = None):
        """
        ExpressionEngine 초기화

        Args:
            function_registry: 함수 레지스트리 (ma, rsi 등의 함수 제공)
        """
        # 허용된 연산자 매핑
        self.operators = {
            # 산술 연산자
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv,
            ast.Pow: operator.pow,

            # 비교 연산자
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,

            # 논리 연산자
            ast.And: lambda a, b: a and b,
            ast.Or: lambda a, b: a or b,
            ast.Not: operator.not_,

            # 단항 연산자 (음수, 양수)
            ast.USub: operator.neg,  # -x (음수)
            ast.UAdd: operator.pos,  # +x (양수)
        }

        # 함수 레지스트리 (외부에서 주입)
        self.function_registry = function_registry

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        표현식을 평가합니다.

        Args:
            expression: 평가할 표현식
                예: "current.close >= 10000"
                예: "(current.high >= ma(120)) AND (volume > prev.volume * 3)"
            context: 평가에 사용할 컨텍스트
                예: {
                    'current': Stock(...),
                    'prev': Stock(...),
                    'block1': Block1Detection(...),
                    'all_stocks': [...]
                }

        Returns:
            평가 결과 (보통 bool, 하지만 숫자나 문자열도 가능)

        Raises:
            ValueError: 표현식이 유효하지 않거나 평가 실패 시
        """
        try:
            # AST 파싱
            tree = ast.parse(expression, mode='eval')

            # 평가
            result = self._eval_node(tree.body, context)

            return result

        except SyntaxError as e:
            raise ValueError(f"표현식 구문 오류: {expression}\n{e}")
        except Exception as e:
            raise ValueError(f"표현식 평가 실패: {expression}\n오류: {e}")

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        AST 노드를 재귀적으로 평가합니다.

        Args:
            node: AST 노드
            context: 평가 컨텍스트

        Returns:
            노드 평가 결과

        Raises:
            ValueError: 지원하지 않는 노드 타입 또는 연산자
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 리터럴 (상수)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if isinstance(node, ast.Constant):
            # 숫자, 문자열, True, False, None
            return node.value

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 변수 (current, prev, block1 등)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name not in context:
                raise ValueError(f"알 수 없는 변수: {var_name}")
            return context[var_name]

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 속성 접근 (current.close, block1.peak_price)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.Attribute):
            # 객체 평가 (예: current)
            obj = self._eval_node(node.value, context)
            attr_name = node.attr

            # 객체의 속성 가져오기
            if hasattr(obj, attr_name):
                return getattr(obj, attr_name)

            # indicators 딕셔너리에서 찾기 (Stock 객체용)
            elif hasattr(obj, 'indicators') and isinstance(obj.indicators, dict):
                return obj.indicators.get(attr_name, None)

            else:
                raise ValueError(f"알 수 없는 속성: {attr_name} (객체: {type(obj).__name__})")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 함수 호출 (ma(120), candles_between(...))
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None

            if not func_name:
                raise ValueError("지원하지 않는 함수 호출 형태")

            # 함수 레지스트리에서 함수 가져오기
            if not self.function_registry:
                raise ValueError(f"함수 레지스트리가 설정되지 않았습니다: {func_name}")

            func = self.function_registry.get(func_name)

            # 인자 평가
            args = [self._eval_node(arg, context) for arg in node.args]

            # 키워드 인자 평가 (선택적)
            kwargs = {
                kw.arg: self._eval_node(kw.value, context)
                for kw in node.keywords
            }

            # 함수 실행 (context 전달)
            # 함수는 (arg1, arg2, ..., context=context) 형태로 호출됨
            return func(*args, context=context, **kwargs)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 비교 연산 (>, <, ==, !=, >=, <=)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.Compare):
            # 왼쪽 값
            left = self._eval_node(node.left, context)

            # 체이닝된 비교 처리 (예: a < b < c)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)

                # 연산자 타입 확인
                if type(op) not in self.operators:
                    raise ValueError(f"지원하지 않는 비교 연산자: {type(op).__name__}")

                # 비교 수행
                if not self.operators[type(op)](left, right):
                    return False

                # 다음 비교를 위해 right를 left로 이동
                left = right

            return True

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 이항 연산 (+, -, *, /, %)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)

            if type(node.op) not in self.operators:
                raise ValueError(f"지원하지 않는 이항 연산자: {type(node.op).__name__}")

            op = self.operators[type(node.op)]
            return op(left, right)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 논리 연산 (AND, OR)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.BoolOp):
            # Short-circuit evaluation: evaluate values one by one and stop early
            if isinstance(node.op, ast.And):
                # AND: return False as soon as any value is False
                for v in node.values:
                    val = self._eval_node(v, context)
                    if not val:
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                # OR: return True as soon as any value is True
                for v in node.values:
                    val = self._eval_node(v, context)
                    if val:
                        return True
                return False
            else:
                # Fallback for other boolean operators (shouldn't happen)
                op = self.operators[type(node.op)]
                values = [self._eval_node(v, context) for v in node.values]
                result = values[0]
                for val in values[1:]:
                    result = op(result, val)
                return result

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 단항 연산 (NOT, -, +)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)

            if type(node.op) not in self.operators:
                raise ValueError(f"지원하지 않는 단항 연산자: {type(node.op).__name__}")

            op = self.operators[type(node.op)]
            return op(operand)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 지원하지 않는 노드
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        else:
            raise ValueError(f"지원하지 않는 표현식 노드: {type(node).__name__}")

    def validate_expression(self, expression: str) -> bool:
        """
        표현식이 유효한지 검증합니다 (실행하지 않고 파싱만).

        Args:
            expression: 검증할 표현식

        Returns:
            유효하면 True, 아니면 False
        """
        try:
            ast.parse(expression, mode='eval')
            return True
        except SyntaxError:
            return False
