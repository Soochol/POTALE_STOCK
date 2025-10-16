"""
Infrastructure Collectors

데이터 수집을 위한 Collector 클래스들
"""
from .base_collector import BaseCollector, CollectionResult

# Naver Finance Collectors (Primary)
from .naver.naver_base_collector import NaverFinanceCollector
from .naver.naver_investor_collector import NaverInvestorCollector

# PyKRX Collectors (Legacy/Reference)
from .pykrx.stock_price_collector import StockPriceCollector
from .pykrx.market_info_collector import MarketInfoCollector

__all__ = [
    'BaseCollector',
    'CollectionResult',
    # Naver
    'NaverFinanceCollector',
    'NaverInvestorCollector',
    # PyKRX (Reference)
    'StockPriceCollector',
    'MarketInfoCollector',
]
