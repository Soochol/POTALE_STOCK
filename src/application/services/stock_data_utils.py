"""
Stock Data Utilities - 주가 데이터 전처리 유틸리티

주가 데이터 전처리 및 변환 함수들

NOTE: 이 모듈은 infrastructure/utils/stock_data_utils.py에서 이동되었습니다.
      Clean Architecture 원칙에 따라 application layer로 이동.
"""
from typing import List, Optional
from src.domain.entities.core import Stock
from src.common.logging import get_logger

logger = get_logger(__name__)


def forward_fill_prices(stocks: List[Stock]) -> List[Stock]:
    """
    거래 없는 날의 가격을 마지막 유효 가격으로 채움 (Forward Fill)

    거래 없는 날(`volume=0`)의 가격(`open`, `high`, `low`, `close`)을
    마지막 거래일의 종가로 채웁니다. 이렇게 하면:
    - 이동평균 계산이 정확해짐 (0이 아닌 실제 가격 사용)
    - `prev.close`로 나누기 시 ZeroDivisionError 방지

    Args:
        stocks: 주가 데이터 리스트 (시간순 정렬)

    Returns:
        Forward-fill 적용된 새 주가 데이터 리스트

    Example:
        원본 데이터:
        - 2024-01-01: close=1000, volume=100
        - 2024-01-02: close=0, volume=0      (거래 정지)
        - 2024-01-03: close=1100, volume=200

        Forward-fill 후:
        - 2024-01-01: close=1000, volume=100
        - 2024-01-02: close=1000, volume=0    (가격만 채움, 거래량은 0 유지)
        - 2024-01-03: close=1100, volume=200

    Note:
        - 원본 리스트는 수정하지 않음 (새 리스트 반환)
        - 거래량(`volume`)은 0으로 유지
        - 첫 거래일 이전 데이터는 그대로 유지
    """
    if not stocks:
        logger.debug("Forward fill: empty stock list, returning empty")
        return []

    result = []
    last_valid_prices = None
    fill_count = 0

    for i, stock in enumerate(stocks):
        if stock.volume > 0:
            # 정상 거래일: 그대로 추가하고 가격 기록
            last_valid_prices = {
                'open': stock.open,
                'high': stock.high,
                'low': stock.low,
                'close': stock.close
            }
            result.append(stock)

        else:
            # 거래 없는 날: 가격 채우기
            if last_valid_prices:
                # 마지막 거래일 종가로 모든 가격 채움
                filled_stock = Stock(
                    ticker=stock.ticker,
                    name=stock.name,
                    date=stock.date,
                    open=last_valid_prices['close'],
                    high=last_valid_prices['close'],
                    low=last_valid_prices['close'],
                    close=last_valid_prices['close'],
                    volume=0,  # 거래량은 0 유지
                    trading_value=0
                )
                result.append(filled_stock)
                fill_count += 1

                logger.debug(
                    "Forward filled price data",
                    context={
                        'ticker': stock.ticker,
                        'date': str(stock.date),
                        'filled_price': last_valid_prices['close']
                    }
                )
            else:
                # 첫 거래 전: 그대로 유지
                result.append(stock)

    if fill_count > 0:
        logger.info(
            "Forward fill completed",
            context={
                'ticker': stocks[0].ticker if stocks else 'unknown',
                'total_records': len(stocks),
                'filled_records': fill_count,
                'fill_percentage': f"{fill_count / len(stocks) * 100:.1f}%"
            }
        )

    return result


def get_last_valid_stock(stocks: List[Stock], current_index: int) -> Optional[Stock]:
    """
    마지막 정상 거래일 주가 반환

    현재 인덱스 이전의 가장 최근 정상 거래일(`volume > 0`) 주가를 반환합니다.

    Args:
        stocks: 주가 데이터 리스트
        current_index: 현재 인덱스

    Returns:
        마지막 정상 거래일 주가, 없으면 None

    Example:
        stocks = [day1(vol=100), day2(vol=0), day3(vol=0), day4(vol=200)]
        get_last_valid_stock(stocks, 3) → day1
    """
    for i in range(current_index - 1, -1, -1):
        if stocks[i].volume > 0:
            return stocks[i]
    return None


def count_valid_trading_days(stocks: List[Stock]) -> int:
    """
    정상 거래일 수 반환 (`volume > 0`인 날)

    Args:
        stocks: 주가 데이터 리스트

    Returns:
        정상 거래일 수
    """
    return sum(1 for s in stocks if s.volume > 0)


def has_trading_gap(stock1: Stock, stock2: Stock) -> bool:
    """
    두 주가 데이터 사이에 거래 정지 기간이 있는지 확인

    Args:
        stock1: 이전 주가
        stock2: 이후 주가

    Returns:
        날짜 차이가 1일보다 크면 True (거래 정지 기간 존재)
    """
    if not stock1 or not stock2:
        return False

    date_diff = (stock2.date - stock1.date).days
    return date_diff > 1
