"""
Detection Result Entity - 탐지 결과 엔티티
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from .stock import Stock


@dataclass
class DetectionResult:
    """탐지 결과 엔티티"""
    condition_name: str
    detected_at: datetime
    stocks: List[Stock] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.condition_name:
            raise ValueError("조건 이름은 필수입니다")

    @property
    def count(self) -> int:
        """탐지된 종목 수"""
        return len(self.stocks)

    @property
    def is_empty(self) -> bool:
        """결과가 비어있는지"""
        return self.count == 0

    def add_stock(self, stock: Stock) -> None:
        """주식 추가"""
        if not isinstance(stock, Stock):
            raise TypeError("Stock 객체만 추가할 수 있습니다")
        self.stocks.append(stock)

    def get_tickers(self) -> List[str]:
        """종목 코드 목록 반환"""
        return [stock.ticker for stock in self.stocks]

    def filter_by_ticker(self, tickers: List[str]) -> List[Stock]:
        """특정 종목만 필터링"""
        return [stock for stock in self.stocks if stock.ticker in tickers]
