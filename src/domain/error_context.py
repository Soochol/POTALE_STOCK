"""
POTALE Stock - Error Context Utilities
에러 컨텍스트 유틸리티

에러 발생 시 컨텍스트 정보를 캡처하고 관리하는 유틸리티입니다.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
import sys


class ErrorContext:
    """
    에러 컨텍스트 빌더

    에러 발생 시점의 컨텍스트 정보를 쉽게 수집할 수 있습니다.

    Example:
        ctx = ErrorContext()
        ctx.add("ticker", "025980")
        ctx.add("block_type", 1)
        ctx.add("date", current_date)

        try:
            detect_block(...)
        except Exception as e:
            raise BlockDetectionError(
                "Block detection failed",
                context=ctx.build()
            )
    """

    def __init__(self):
        """컨텍스트 초기화"""
        self._context: Dict[str, Any] = {}

    def add(self, key: str, value: Any) -> 'ErrorContext':
        """
        컨텍스트 항목 추가

        Args:
            key: 컨텍스트 키
            value: 컨텍스트 값

        Returns:
            self (체이닝 가능)

        Example:
            ctx.add("ticker", "025980").add("block_type", 1)
        """
        self._context[key] = value
        return self

    def add_many(self, **kwargs) -> 'ErrorContext':
        """
        여러 컨텍스트 항목 추가

        Args:
            **kwargs: 키-값 쌍

        Returns:
            self (체이닝 가능)

        Example:
            ctx.add_many(ticker="025980", block_type=1, date=current_date)
        """
        self._context.update(kwargs)
        return self

    def build(self) -> Dict[str, Any]:
        """
        컨텍스트 딕셔너리 반환

        Returns:
            컨텍스트 딕셔너리
        """
        return self._context.copy()


def capture_exception_context(exc: Exception) -> Dict[str, Any]:
    """
    예외 객체에서 컨텍스트 추출

    Args:
        exc: 예외 객체

    Returns:
        컨텍스트 딕셔너리

    Example:
        try:
            risky_operation()
        except Exception as e:
            ctx = capture_exception_context(e)
            logger.error("Operation failed", context=ctx, exc=e)
    """
    context = {
        'exception_type': type(exc).__name__,
        'exception_message': str(exc),
        'timestamp': datetime.now().isoformat(),
    }

    # PotaleStockError인 경우 내장 context 추가
    if hasattr(exc, 'context') and isinstance(exc.context, dict):
        context['error_context'] = exc.context

    return context


def capture_traceback(exc: Optional[Exception] = None) -> str:
    """
    예외 traceback 문자열로 캡처

    Args:
        exc: 예외 객체 (None이면 현재 exception 사용)

    Returns:
        traceback 문자열

    Example:
        try:
            risky_operation()
        except Exception as e:
            tb_str = capture_traceback(e)
            logger.error("Operation failed", context={"traceback": tb_str})
    """
    if exc is None:
        # 현재 exception 사용
        return traceback.format_exc()
    else:
        # 특정 exception의 traceback
        return "".join(traceback.format_exception(
            type(exc),
            exc,
            exc.__traceback__
        ))


def create_operation_context(
    operation: str,
    **kwargs
) -> Dict[str, Any]:
    """
    작업 컨텍스트 생성 (표준화된 형식)

    Args:
        operation: 작업 이름
        **kwargs: 추가 컨텍스트 정보

    Returns:
        컨텍스트 딕셔너리

    Example:
        context = create_operation_context(
            operation="block_detection",
            ticker="025980",
            block_type=1,
            date="2020-01-15"
        )

        logger.info("Operation started", context=context)
    """
    context = {
        'operation': operation,
        'timestamp': datetime.now().isoformat(),
    }
    context.update(kwargs)
    return context


def create_db_operation_context(
    table: str,
    operation: str,
    **kwargs
) -> Dict[str, Any]:
    """
    DB 작업 컨텍스트 생성 (표준화된 형식)

    Args:
        table: 테이블 이름
        operation: 작업 종류 (select, insert, update, delete)
        **kwargs: 추가 컨텍스트 정보

    Returns:
        컨텍스트 딕셔너리

    Example:
        context = create_db_operation_context(
            table="dynamic_block_detection",
            operation="insert",
            ticker="025980",
            block_type=1
        )

        try:
            db.execute(...)
        except Exception as e:
            raise DatabaseError("Insert failed", context=context)
    """
    context = {
        'operation': 'database',
        'table': table,
        'db_operation': operation,
        'timestamp': datetime.now().isoformat(),
    }
    context.update(kwargs)
    return context


def create_external_api_context(
    api_name: str,
    endpoint: str,
    method: str = 'GET',
    **kwargs
) -> Dict[str, Any]:
    """
    외부 API 호출 컨텍스트 생성 (표준화된 형식)

    Args:
        api_name: API 이름 (예: "naver_finance")
        endpoint: 엔드포인트 URL
        method: HTTP 메서드
        **kwargs: 추가 컨텍스트 정보

    Returns:
        컨텍스트 딕셔너리

    Example:
        context = create_external_api_context(
            api_name="naver_finance",
            endpoint="https://finance.naver.com/item/sise_day.naver",
            method="GET",
            ticker="025980"
        )

        try:
            response = requests.get(...)
        except Exception as e:
            raise NetworkError("API call failed", context=context)
    """
    context = {
        'operation': 'external_api',
        'api_name': api_name,
        'endpoint': endpoint,
        'method': method,
        'timestamp': datetime.now().isoformat(),
    }
    context.update(kwargs)
    return context


def create_file_operation_context(
    file_path: str,
    operation: str,
    **kwargs
) -> Dict[str, Any]:
    """
    파일 작업 컨텍스트 생성 (표준화된 형식)

    Args:
        file_path: 파일 경로
        operation: 작업 종류 (read, write, parse)
        **kwargs: 추가 컨텍스트 정보

    Returns:
        컨텍스트 딕셔너리

    Example:
        context = create_file_operation_context(
            file_path="presets/seed_conditions.yaml",
            operation="parse"
        )

        try:
            data = yaml.safe_load(...)
        except Exception as e:
            raise YAMLConfigError("YAML parsing failed", context=context)
    """
    context = {
        'operation': 'file_operation',
        'file_path': file_path,
        'file_operation': operation,
        'timestamp': datetime.now().isoformat(),
    }
    context.update(kwargs)
    return context
