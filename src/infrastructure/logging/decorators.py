"""
POTALE Stock - Error Handling Decorators
에러 처리 데코레이터

일관된 에러 처리를 위한 데코레이터 시스템
"""
from functools import wraps
from typing import Callable, Type, Optional, Dict, Any
import inspect

from src.domain.exceptions import PotaleStockError, DatabaseError
from src.domain.error_context import create_operation_context, create_db_operation_context
from .logger import get_logger


def handle_errors(
    exception_class: Type[PotaleStockError] = PotaleStockError,
    error_message: Optional[str] = None,
    reraise: bool = True,
    default_return: Any = None,
    context_builder: Optional[Callable] = None
):
    """
    에러 처리 데코레이터

    함수 실행 중 발생하는 예외를 자동으로 캡처하고 로깅한 후,
    커스텀 예외로 래핑하여 재발생시킵니다.

    Args:
        exception_class: 발생시킬 커스텀 예외 클래스
        error_message: 에러 메시지 템플릿 (None이면 함수 이름 사용)
        reraise: True면 예외 재발생, False면 default_return 반환
        default_return: reraise=False일 때 반환할 기본값
        context_builder: 컨텍스트 생성 함수 (None이면 자동 생성)

    Example:
        @handle_errors(DatabaseError, "Failed to fetch stock data")
        def get_stock_data(self, ticker: str, date: date):
            # DB 쿼리 실행...
            pass

        # 에러 발생 시:
        # 1. 로그 남김: logger.error("Failed to fetch stock data", context={...}, exc=...)
        # 2. DatabaseError 예외 발생

    Example with custom context:
        def build_context(**kwargs):
            return create_db_operation_context(
                table='stock_price',
                operation='select',
                **kwargs
            )

        @handle_errors(DatabaseError, context_builder=build_context)
        def get_stock_data(self, ticker: str, date: date):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 로거 가져오기 (함수가 속한 모듈의 로거 사용)
            logger = get_logger(func.__module__)

            # 에러 메시지 생성
            msg = error_message or f"{func.__name__} failed"

            # 컨텍스트 생성
            if context_builder:
                # 커스텀 컨텍스트 빌더 사용
                try:
                    # 함수 인자를 컨텍스트 빌더에 전달
                    sig = inspect.signature(func)
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    ctx = context_builder(**bound.arguments)
                except Exception:
                    # 컨텍스트 생성 실패 시 기본 컨텍스트
                    ctx = create_operation_context(
                        operation=func.__name__,
                        args=str(args[:3]),  # 처음 3개 인자만
                        kwargs=str(list(kwargs.keys()))
                    )
            else:
                # 기본 컨텍스트
                ctx = create_operation_context(
                    operation=func.__name__,
                    args=str(args[:3]),  # 처음 3개 인자만
                    kwargs=str(list(kwargs.keys()))
                )

            try:
                return func(*args, **kwargs)

            except exception_class as e:
                # 이미 커스텀 예외면 그대로 재발생
                logger.error(msg, context=ctx, exc=e)
                if reraise:
                    raise
                else:
                    return default_return

            except Exception as e:
                # 다른 예외를 커스텀 예외로 래핑
                logger.error(msg, context=ctx, exc=e)

                if reraise:
                    raise exception_class(
                        msg,
                        context={**ctx, 'original_error': str(e), 'original_type': type(e).__name__}
                    ) from e
                else:
                    return default_return

        return wrapper
    return decorator


def handle_db_errors(
    table: str,
    operation: str,
    error_message: Optional[str] = None,
    reraise: bool = True
):
    """
    데이터베이스 에러 처리 전용 데코레이터

    DB 작업 중 발생하는 에러를 자동으로 처리하고 로깅합니다.

    Args:
        table: 테이블 이름
        operation: 작업 종류 (select, insert, update, delete)
        error_message: 에러 메시지 템플릿
        reraise: True면 예외 재발생, False면 None 반환

    Example:
        @handle_db_errors(table="stock_price", operation="select")
        def get_stock_data(self, ticker: str, date: date):
            # DB 쿼리...
            pass
    """
    def context_builder(**kwargs):
        # 함수 인자를 DB 컨텍스트에 포함
        return create_db_operation_context(
            table=table,
            operation=operation,
            **{k: v for k, v in kwargs.items() if k not in ['self', 'cls']}
        )

    return handle_errors(
        exception_class=DatabaseError,
        error_message=error_message or f"Database {operation} failed on {table}",
        reraise=reraise,
        context_builder=context_builder
    )


def log_execution(level: str = "info"):
    """
    함수 실행 로깅 데코레이터

    함수 시작/종료 시점에 로그를 남깁니다.

    Args:
        level: 로그 레벨 (debug, info, warning)

    Example:
        @log_execution(level="debug")
        def process_data(self, ticker: str):
            # 처리 로직...
            pass

        # 출력:
        # [DEBUG] process_data started | ticker=025980
        # [DEBUG] process_data completed | ticker=025980, duration=1.23s
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            logger = get_logger(func.__module__)

            # 함수 인자를 컨텍스트로 생성
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # self, cls 제외
            context = {
                k: v for k, v in bound.arguments.items()
                if k not in ['self', 'cls']
            }

            # 시작 로그
            log_func = getattr(logger, level, logger.info)
            log_func(f"{func.__name__} started", context=context)

            # 실행
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 종료 로그
                log_func(
                    f"{func.__name__} completed",
                    context={**context, 'duration': f"{duration:.2f}s"}
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed",
                    context={**context, 'duration': f"{duration:.2f}s"},
                    exc=e
                )
                raise

        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    에러 발생 시 재시도 데코레이터

    지정된 예외가 발생하면 재시도합니다.

    Args:
        max_retries: 최대 재시도 횟수
        delay_seconds: 초기 대기 시간 (초)
        backoff_multiplier: 대기 시간 증가 배율
        exceptions: 재시도할 예외 타입들

    Example:
        @retry_on_error(max_retries=3, delay_seconds=1.0)
        def fetch_data_from_api(self, url: str):
            # API 호출...
            pass

        # 실행:
        # 1차 시도 실패 → 1초 대기 → 2차 시도 실패 → 2초 대기 → 3차 시도 실패 → 예외 발생
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            logger = get_logger(func.__module__)

            last_exception = None
            delay = delay_seconds

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed, retrying",
                            context={
                                'attempt': attempt + 1,
                                'max_retries': max_retries,
                                'delay': f"{delay:.1f}s"
                            },
                            exc=e
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"{func.__name__} failed after max retries",
                            context={
                                'attempts': max_retries + 1,
                                'max_retries': max_retries
                            },
                            exc=e
                        )

            # 모든 재시도 실패
            raise last_exception

        return wrapper
    return decorator
