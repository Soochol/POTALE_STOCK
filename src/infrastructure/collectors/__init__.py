"""
Infrastructure Collectors

데이터 수집을 위한 Collector 클래스들
"""
from .base_collector import BaseCollector, CollectionResult

# Naver Finance Collectors
from .naver.naver_base_collector import NaverFinanceCollector
from .naver.naver_investor_collector import NaverInvestorCollector
from .naver.naver_hybrid_collector import NaverHybridCollector
from .naver.naver_price_collector import NaverPriceCollector

# Bulk Collector
from .bulk_collector import BulkCollector

__all__ = [
    'BaseCollector',
    'CollectionResult',
    # Naver Finance
    'NaverFinanceCollector',
    'NaverInvestorCollector',
    'NaverHybridCollector',
    'NaverPriceCollector',
    # Bulk
    'BulkCollector',
]
