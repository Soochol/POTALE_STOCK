"""
Logging Infrastructure Package (DEPRECATED)
로깅 인프라 패키지 (사용 중단)

⚠️ DEPRECATED: This module has been moved to src.common.logging
⚠️ 사용 중단: 이 모듈은 src.common.logging으로 이동되었습니다

Please update your imports:
- OLD: from src.infrastructure.logging import get_logger
- NEW: from src.common.logging import get_logger

This module will be removed in a future version.
"""
import warnings

# Backward compatibility: re-export from common.logging
from src.common.logging import (
    PotaleLogger,
    get_logger,
    set_global_log_level,
    LogLevel,
    handle_errors,
    handle_db_errors,
    log_execution,
    retry_on_error
)

# Emit deprecation warning
warnings.warn(
    "src.infrastructure.logging is deprecated. "
    "Please use src.common.logging instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    # Logger
    'PotaleLogger',
    'get_logger',
    'set_global_log_level',
    'LogLevel',

    # Decorators
    'handle_errors',
    'handle_db_errors',
    'log_execution',
    'retry_on_error',
]
