"""
Common Utility Functions for Services
서비스 계층 공통 유틸리티 함수
"""
from typing import List, Optional
from datetime import date
from src.domain.entities import Stock


def get_previous_trading_day_stock(
    current_date: date,
    all_stocks: List[Stock]
) -> Optional[Stock]:
    """
    현재 날짜 이전의 가장 최근 거래일 Stock 반환

    거래일 Gap(공휴일, 거래정지)을 자동으로 건너뛰고
    실제 마지막 거래일의 데이터를 반환합니다.

    Args:
        current_date: 현재 날짜
        all_stocks: 전체 주식 데이터 리스트

    Returns:
        Optional[Stock]: 마지막 거래일 Stock 또는 None (과거 데이터가 없는 경우)

    Example:
        >>> stocks = [
        ...     Stock(date=date(2024, 1, 8), close=1000, volume=100),  # 월
        ...     Stock(date=date(2024, 1, 9), close=1000, volume=0),    # 화 (거래정지)
        ...     Stock(date=date(2024, 1, 10), close=1100, volume=200), # 수
        ... ]
        >>> prev = get_previous_trading_day_stock(date(2024, 1, 10), stocks)
        >>> print(prev.date)  # 2024-01-08 (거래정지일 건너뜀)

    Note:
        - 거래량이 0인 날(거래정지)은 자동으로 건너뜀
        - 시간 복잡도: O(n) - 전체 리스트 순회
    """
    # 현재 날짜 이전의 모든 Stock 필터링 (거래량 > 0인 것만)
    prev_stocks = [s for s in all_stocks if s.date < current_date and s.volume > 0]

    if not prev_stocks:
        return None

    # 가장 최근 거래일 반환 (날짜 기준 max)
    return max(prev_stocks, key=lambda s: s.date)


def get_latest_trading_day_before(
    target_date: date,
    all_stocks: List[Stock]
) -> Optional[date]:
    """
    특정 날짜 이전의 가장 최근 거래일 날짜 반환

    Block N+1이 M일에 시작할 때, Block N의 종료일을 M-1일(전 거래일)로 설정하기 위해 사용

    Args:
        target_date: 기준 날짜 (이 날짜 이전의 거래일 검색)
        all_stocks: 전체 주식 데이터 리스트

    Returns:
        Optional[date]: 가장 최근 거래일 날짜 또는 None (이전 거래일이 없는 경우)

    Example:
        >>> stocks = [
        ...     Stock(date=date(2024, 1, 8)),   # 월
        ...     Stock(date=date(2024, 1, 9)),   # 화 (거래정지)
        ...     Stock(date=date(2024, 1, 10)),  # 수 (Block2 시작일)
        ... ]
        >>> # Block2가 1/10에 시작 → Block1은 1/9에 종료되어야 함
        >>> exit_date = get_latest_trading_day_before(date(2024, 1, 10), stocks)
        >>> print(exit_date)  # 2024-01-08 (실제 거래일)

    Note:
        - 거래정지일(거래량 0)은 자동으로 건너뜀
        - get_previous_trading_day_stock()과 유사하지만 date만 반환
        - auto_exit_on_next_block 기능에서 사용
    """
    prev_stock = get_previous_trading_day_stock(target_date, all_stocks)
    return prev_stock.date if prev_stock else None


def get_trading_day_gap(
    from_date: date,
    to_date: date,
    all_stocks: List[Stock]
) -> int:
    """
    두 날짜 사이의 실제 거래일 수 계산

    Args:
        from_date: 시작일
        to_date: 종료일
        all_stocks: 전체 주식 데이터 리스트

    Returns:
        int: 거래일 수 (from_date와 to_date 사이의 Stock 개수)

    Example:
        >>> stocks = [
        ...     Stock(date=date(2024, 1, 8)),
        ...     Stock(date=date(2024, 1, 10)),  # 9일 공휴일
        ...     Stock(date=date(2024, 1, 11)),
        ... ]
        >>> gap = get_trading_day_gap(date(2024, 1, 8), date(2024, 1, 11), stocks)
        >>> print(gap)  # 3 (실제 거래일만 카운트)
    """
    trading_stocks = [s for s in all_stocks if from_date <= s.date <= to_date]
    return len(trading_stocks)


def has_sufficient_trading_history(
    current_date: date,
    all_stocks: List[Stock],
    required_days: int
) -> bool:
    """
    충분한 거래 이력이 있는지 확인

    MA 계산 등을 위해 최소 N일의 거래 데이터가 필요한 경우 사용

    Args:
        current_date: 현재 날짜
        all_stocks: 전체 주식 데이터 리스트
        required_days: 필요한 최소 거래일 수

    Returns:
        bool: 충분한 이력이 있으면 True

    Example:
        >>> # MA20 계산을 위해서는 최소 20일의 데이터 필요
        >>> has_enough = has_sufficient_trading_history(
        ...     date(2024, 1, 31), stocks, required_days=20
        ... )
    """
    prev_stocks = [s for s in all_stocks if s.date <= current_date]
    return len(prev_stocks) >= required_days
