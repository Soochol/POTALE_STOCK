"""
Stock Entity - 주식 도메인 엔티티
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Stock:
    """주식 엔티티"""
    ticker: str
    name: str
    date: date
    open: float  # 수정주가
    high: float  # 수정주가
    low: float   # 수정주가
    close: float # 수정주가
    volume: int  # 수정거래량

    # 선택적 필드
    market_cap: Optional[float] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    eps: Optional[float] = None
    div: Optional[float] = None

    # 하이브리드 수집기 추가 필드
    trading_value: Optional[int] = None      # 거래대금
    adjustment_ratio: Optional[float] = None # 조정 비율 (원본종가/수정종가)
    raw_close: Optional[float] = None        # 원본종가 (참고용)
    raw_volume: Optional[int] = None         # 원본거래량 (참고용)

    def __post_init__(self):
        """유효성 검사"""
        if self.open <= 0 or self.high <= 0 or self.low <= 0 or self.close <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
        if self.volume < 0:
            raise ValueError("거래량은 0 이상이어야 합니다")
        if self.high < self.low:
            raise ValueError("고가는 저가보다 높아야 합니다")
        if self.high < self.close or self.low > self.close:
            raise ValueError("종가는 고가와 저가 사이에 있어야 합니다")

    @property
    def price_change(self) -> Optional[float]:
        """가격 변화율"""
        if self.open == 0:
            return None
        return (self.close - self.open) / self.open

    @property
    def is_up(self) -> bool:
        """상승 여부"""
        return self.close > self.open

    @property
    def is_down(self) -> bool:
        """하락 여부"""
        return self.close < self.open
