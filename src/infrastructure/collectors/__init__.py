"""
Infrastructure Collectors

데이터 수집을 위한 Collector 클래스들
"""
# Common types and utilities
from .common import (
    CollectionResult,
    AsyncCollectionResult,
    CollectionStats,
    CollectionPlan,
    CollectorConfig,
    DEFAULT_CONFIG,
    CollectorLogger,
    get_logger,
)

# Async Unified Collectors
from .naver.async_unified_collector import AsyncUnifiedCollector
from .naver.async_collectors.base import AsyncCollectorBase
from .naver.async_collectors.price_collector import AsyncPriceCollector
from .naver.async_collectors.investor_collector import AsyncInvestorCollector

# Bulk Collectors
from .async_bulk_collector import AsyncBulkCollector, run_async_collection, AsyncBulkCollectionStats

__all__ = [
    # Common
    'CollectionResult',
    'AsyncCollectionResult',
    'CollectionStats',
    'CollectionPlan',
    'CollectorConfig',
    'DEFAULT_CONFIG',
    'CollectorLogger',
    'get_logger',
    # Async Unified
    'AsyncUnifiedCollector',
    'AsyncCollectorBase',
    'AsyncPriceCollector',
    'AsyncInvestorCollector',
    # Bulk
    'AsyncBulkCollector',
    'AsyncBulkCollectionStats',  # Alias for backward compatibility
    'run_async_collection',
]
