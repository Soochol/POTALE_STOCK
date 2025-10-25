"""
POTALE Stock - Unified Logging System
통일된 로깅 시스템

모든 POTALE_STOCK 로그를 일관된 형식으로 관리합니다.
context 딕셔너리와 exception 객체를 지원하여 디버깅을 용이하게 합니다.
"""
import logging
import sys
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class LogLevel(Enum):
    """로그 레벨"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class PotaleLogger:
    """
    POTALE Stock 전용 구조화된 로거

    Features:
    - 일관된 메시지 포맷 (timestamp, level, logger name, message)
    - context 딕셔너리 지원 (key=value 형식으로 출력)
    - exception 객체 자동 포맷팅 (traceback 포함)
    - 컬러 출력 지원 (콘솔)

    Example:
        logger = get_logger(__name__)
        logger.info("Block detection started", context={"ticker": "025980"})
        logger.error("Detection failed", context={"ticker": "025980"}, exc=e)
    """

    def __init__(self, name: str):
        """
        Args:
            name: 로거 이름 (일반적으로 __name__ 사용)
        """
        self.name = name
        self.logger = logging.getLogger(name)

        # 핸들러가 없으면 콘솔 핸들러 추가
        if not self.logger.handlers:
            self._setup_console_handler()

    def _setup_console_handler(self):
        """콘솔 핸들러 설정"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # 포맷터 설정 (기본 포맷만 사용, 커스텀 포맷은 _format_message에서 처리)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def _format_message(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ) -> str:
        """
        로그 메시지 포맷팅

        Format:
            [YYYY-MM-DD HH:MM:SS] [LEVEL] [logger.name] message | context_key1=value1, context_key2=value2
            Error: error_type: error_message

        Args:
            level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: 메시지
            context: 컨텍스트 딕셔너리
            exc: 예외 객체

        Returns:
            포맷팅된 메시지 문자열
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parts = [f"[{timestamp}]", f"[{level}]", f"[{self.name}]", message]

        # Context 추가
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            parts.append(f"| Context: {context_str}")

        # Exception 추가
        if exc:
            exc_type = type(exc).__name__
            exc_msg = str(exc)
            parts.append(f"\n  Error: {exc_type}: {exc_msg}")

            # PotaleStockError인 경우 context 추가
            if hasattr(exc, 'context') and exc.context:
                exc_context_str = ", ".join(f"{k}={v}" for k, v in exc.context.items())
                parts.append(f"\n  Exception Context: {exc_context_str}")

        return " ".join(parts)

    def debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ):
        """
        DEBUG 레벨 로그

        Args:
            message: 로그 메시지
            context: 추가 컨텍스트 정보
            exc: 예외 객체 (선택)
        """
        formatted = self._format_message("DEBUG", message, context, exc)
        self.logger.debug(formatted)

    def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ):
        """
        INFO 레벨 로그

        Args:
            message: 로그 메시지
            context: 추가 컨텍스트 정보
            exc: 예외 객체 (선택)
        """
        formatted = self._format_message("INFO", message, context, exc)
        self.logger.info(formatted)

    def warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ):
        """
        WARNING 레벨 로그

        Args:
            message: 로그 메시지
            context: 추가 컨텍스트 정보
            exc: 예외 객체 (선택)
        """
        formatted = self._format_message("WARNING", message, context, exc)
        self.logger.warning(formatted)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ):
        """
        ERROR 레벨 로그

        Args:
            message: 로그 메시지
            context: 추가 컨텍스트 정보
            exc: 예외 객체 (선택)
        """
        formatted = self._format_message("ERROR", message, context, exc)
        self.logger.error(formatted, exc_info=(exc is not None))

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ):
        """
        CRITICAL 레벨 로그

        Args:
            message: 로그 메시지
            context: 추가 컨텍스트 정보
            exc: 예외 객체 (선택)
        """
        formatted = self._format_message("CRITICAL", message, context, exc)
        self.logger.critical(formatted, exc_info=(exc is not None))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Logger Factory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_loggers: Dict[str, PotaleLogger] = {}


def get_logger(name: str) -> PotaleLogger:
    """
    로거 팩토리 함수

    싱글톤 패턴으로 동일 이름의 로거는 재사용됩니다.

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)

    Returns:
        PotaleLogger 인스턴스

    Example:
        # 모듈 상단에서
        logger = get_logger(__name__)

        # 사용
        logger.info("Process started", context={"ticker": "025980"})

        # 에러 로깅
        try:
            risky_operation()
        except Exception as e:
            logger.error("Operation failed", context={"ticker": "025980"}, exc=e)
    """
    if name not in _loggers:
        _loggers[name] = PotaleLogger(name)
    return _loggers[name]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Convenience Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def set_global_log_level(level: LogLevel):
    """
    전역 로그 레벨 설정

    Args:
        level: LogLevel enum 값

    Example:
        from src.infrastructure.logging.logger import set_global_log_level, LogLevel
        set_global_log_level(LogLevel.WARNING)  # WARNING 이상만 출력
    """
    logging.root.setLevel(level.value)

    # 모든 existing logger의 레벨도 변경
    for logger_instance in _loggers.values():
        logger_instance.logger.setLevel(level.value)
