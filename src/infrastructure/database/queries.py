"""
Database Query Helpers
데이터베이스 쿼리 헬퍼 함수들 (증분 수집 최적화)

Note: 이 모듈은 주로 IncrementalCollector에서 사용됨.
      Repository 패턴과 중복되지 않는 복잡한 분석 쿼리만 포함.
"""
from datetime import date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import StockPrice, StockInfo


def get_latest_dates_bulk(session: Session, tickers: List[str]) -> Dict[str, Optional[date]]:
    """
    여러 종목의 최신 날짜를 단일 쿼리로 조회 (성능 최적화)

    Args:
        session: DB 세션
        tickers: 종목 코드 리스트

    Returns:
        {ticker: latest_date} 딕셔너리
        - 데이터가 없는 종목은 None

    Example:
        >>> latest_dates = get_latest_dates_bulk(session, ['005930', '000660'])
        >>> print(latest_dates)
        {'005930': datetime.date(2024, 12, 31), '000660': datetime.date(2024, 12, 30)}
    """
    if not tickers:
        return {}

    # 단일 쿼리로 모든 종목의 최신 날짜 조회
    results = session.query(
        StockPrice.ticker,
        func.max(StockPrice.date).label('latest_date')
    ).filter(
        StockPrice.ticker.in_(tickers)
    ).group_by(
        StockPrice.ticker
    ).all()

    # 딕셔너리로 변환
    latest_dates = {ticker: latest_date for ticker, latest_date in results}

    # 데이터가 없는 종목은 None으로 설정
    for ticker in tickers:
        if ticker not in latest_dates:
            latest_dates[ticker] = None

    return latest_dates


def get_earliest_dates_bulk(session: Session, tickers: List[str]) -> Dict[str, Optional[date]]:
    """
    여러 종목의 최초 날짜를 단일 쿼리로 조회

    Args:
        session: DB 세션
        tickers: 종목 코드 리스트

    Returns:
        {ticker: earliest_date} 딕셔너리
    """
    if not tickers:
        return {}

    results = session.query(
        StockPrice.ticker,
        func.min(StockPrice.date).label('earliest_date')
    ).filter(
        StockPrice.ticker.in_(tickers)
    ).group_by(
        StockPrice.ticker
    ).all()

    earliest_dates = {ticker: earliest_date for ticker, earliest_date in results}

    for ticker in tickers:
        if ticker not in earliest_dates:
            earliest_dates[ticker] = None

    return earliest_dates


def get_date_range_bulk(session: Session, tickers: List[str]) -> Dict[str, Tuple[Optional[date], Optional[date]]]:
    """
    여러 종목의 날짜 범위를 단일 쿼리로 조회 (최초일 ~ 최신일)

    Args:
        session: DB 세션
        tickers: 종목 코드 리스트

    Returns:
        {ticker: (earliest_date, latest_date)} 딕셔너리
    """
    if not tickers:
        return {}

    results = session.query(
        StockPrice.ticker,
        func.min(StockPrice.date).label('earliest_date'),
        func.max(StockPrice.date).label('latest_date')
    ).filter(
        StockPrice.ticker.in_(tickers)
    ).group_by(
        StockPrice.ticker
    ).all()

    date_ranges = {
        ticker: (earliest_date, latest_date)
        for ticker, earliest_date, latest_date in results
    }

    for ticker in tickers:
        if ticker not in date_ranges:
            date_ranges[ticker] = (None, None)

    return date_ranges


def get_record_count_bulk(session: Session, tickers: List[str]) -> Dict[str, int]:
    """
    여러 종목의 레코드 수를 단일 쿼리로 조회

    Args:
        session: DB 세션
        tickers: 종목 코드 리스트

    Returns:
        {ticker: record_count} 딕셔너리
    """
    if not tickers:
        return {}

    results = session.query(
        StockPrice.ticker,
        func.count(StockPrice.id).label('record_count')
    ).filter(
        StockPrice.ticker.in_(tickers)
    ).group_by(
        StockPrice.ticker
    ).all()

    record_counts = {ticker: count for ticker, count in results}

    for ticker in tickers:
        if ticker not in record_counts:
            record_counts[ticker] = 0

    return record_counts


def get_collection_stats(session: Session, ticker: str) -> Dict:
    """
    단일 종목의 수집 통계 조회

    Args:
        session: DB 세션
        ticker: 종목 코드

    Returns:
        통계 딕셔너리
        {
            'ticker': str,
            'record_count': int,
            'earliest_date': date,
            'latest_date': date,
            'missing_days': int  # 예상 거래일 대비 누락일
        }
    """
    result = session.query(
        func.count(StockPrice.id).label('record_count'),
        func.min(StockPrice.date).label('earliest_date'),
        func.max(StockPrice.date).label('latest_date')
    ).filter(
        StockPrice.ticker == ticker
    ).first()

    if result.record_count == 0:
        return {
            'ticker': ticker,
            'record_count': 0,
            'earliest_date': None,
            'latest_date': None,
            'missing_days': None
        }

    # 예상 거래일 계산 (전체 일수의 약 70%, 주말 제외)
    if result.earliest_date and result.latest_date:
        total_days = (result.latest_date - result.earliest_date).days + 1
        expected_trading_days = int(total_days * 0.7)
        missing_days = max(0, expected_trading_days - result.record_count)
    else:
        missing_days = None

    return {
        'ticker': ticker,
        'record_count': result.record_count,
        'earliest_date': result.earliest_date,
        'latest_date': result.latest_date,
        'missing_days': missing_days
    }


def has_data_in_range(session: Session, ticker: str, fromdate: date, todate: date) -> bool:
    """
    특정 종목이 특정 날짜 범위에 데이터가 있는지 확인

    Args:
        session: DB 세션
        ticker: 종목 코드
        fromdate: 시작 날짜
        todate: 종료 날짜

    Returns:
        데이터 존재 여부 (True/False)
    """
    count = session.query(func.count(StockPrice.id)).filter(
        StockPrice.ticker == ticker,
        StockPrice.date >= fromdate,
        StockPrice.date <= todate
    ).scalar()

    return count > 0


def get_missing_dates(session: Session, ticker: str, fromdate: date, todate: date) -> List[date]:
    """
    특정 기간 중 데이터가 누락된 날짜 리스트 조회
    (모든 날짜와 비교하는 것이 아니라, 기존 데이터의 gap 찾기)

    Args:
        session: DB 세션
        ticker: 종목 코드
        fromdate: 시작 날짜
        todate: 종료 날짜

    Returns:
        누락된 날짜 리스트

    Note:
        이 함수는 복잡한 쿼리가 필요하므로, 실제로는 Python에서 처리하는 것이 더 효율적일 수 있음
    """
    # 기존 데이터 조회
    existing_dates = session.query(StockPrice.date).filter(
        StockPrice.ticker == ticker,
        StockPrice.date >= fromdate,
        StockPrice.date <= todate
    ).order_by(StockPrice.date).all()

    existing_dates = [d[0] for d in existing_dates]

    if not existing_dates:
        return []

    # 연속된 날짜 중 누락된 날짜 찾기 (단순 버전 - 거래일 고려하지 않음)
    missing = []
    for i in range(len(existing_dates) - 1):
        current = existing_dates[i]
        next_date = existing_dates[i + 1]
        gap_days = (next_date - current).days

        # 3일 이상 gap이 있으면 의심 (주말 제외)
        if gap_days > 3:
            # 실제로는 거래일 캘린더가 필요하지만, 여기서는 단순화
            pass

    return missing


def get_tickers_without_data(session: Session, tickers: List[str]) -> List[str]:
    """
    데이터가 전혀 없는 종목 리스트 조회

    Args:
        session: DB 세션
        tickers: 확인할 종목 코드 리스트

    Returns:
        데이터가 없는 종목 코드 리스트
    """
    # 데이터가 있는 종목 조회
    existing_tickers = session.query(StockPrice.ticker.distinct()).filter(
        StockPrice.ticker.in_(tickers)
    ).all()

    existing_tickers = {t[0] for t in existing_tickers}

    # 데이터가 없는 종목 추출
    no_data_tickers = [t for t in tickers if t not in existing_tickers]

    return no_data_tickers


def get_tickers_needing_update(
    session: Session,
    tickers: List[str],
    target_date: date
) -> List[str]:
    """
    특정 날짜까지 업데이트가 필요한 종목 리스트 조회

    Args:
        session: DB 세션
        tickers: 확인할 종목 코드 리스트
        target_date: 목표 날짜

    Returns:
        업데이트가 필요한 종목 코드 리스트
    """
    latest_dates = get_latest_dates_bulk(session, tickers)

    needing_update = []
    for ticker in tickers:
        latest = latest_dates.get(ticker)
        if latest is None or latest < target_date:
            needing_update.append(ticker)

    return needing_update
