"""
Collector Configuration
수집기 설정 상수
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class HTTPConfig:
    """HTTP 연결 설정"""
    # Connection Pool
    total_limit: int = 100  # Total connection pool size
    per_host_limit: int = 50  # Per-host connection limit

    # DNS & Cache
    dns_ttl: int = 300  # DNS cache TTL (seconds)
    enable_cleanup: bool = True  # Enable closed connection cleanup
    force_close: bool = False  # Keep-Alive enabled

    # Timeout
    total_timeout: int = 30  # HTTP request timeout (seconds)


@dataclass(frozen=True)
class RetryConfig:
    """재시도 설정"""
    max_retries: int = 3  # 최대 재시도 횟수
    base_delay: float = 1.0  # 기본 대기 시간 (초)
    exponential_base: int = 2  # 지수 백오프 베이스 (2^n)
    max_delay: float = 60.0  # 최대 대기 시간 (초)


@dataclass(frozen=True)
class CollectorConfig:
    """수집기 기본 설정"""
    # Rate Limiting
    default_delay: float = 0.1  # 요청 간 기본 대기 시간 (초)
    default_concurrency: int = 10  # 기본 동시 수집 수

    # Batch Processing
    default_batch_size: int = 100  # 배치 크기
    db_batch_size: int = 1000  # DB 저장 배치 크기
    db_flush_timeout: float = 0.5  # DB 저장 타임아웃 (초)

    # Retry
    retry: RetryConfig = RetryConfig()

    # HTTP
    http: HTTPConfig = HTTPConfig()


# 글로벌 설정 인스턴스
DEFAULT_CONFIG = CollectorConfig()
