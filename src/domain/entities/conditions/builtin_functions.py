"""
Builtin Functions - 내장 함수 모음

표현식에서 사용할 수 있는 내장 함수들을 정의합니다.
모든 함수는 function_registry에 자동 등록됩니다.

사용 예시:
    # 표현식에서
    expression = "current.high >= ma(120)"
    expression = "candles_between(block1.started_at, current.date) >= 2"
"""
from datetime import date, timedelta
from typing import List, Any, Optional
from .function_registry import function_registry


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 이동평균 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='ma',
    category='moving_average',
    description='N일 이동평균',
    params_schema={'period': {'type': 'int', 'min': 1, 'max': 365}}
)
def ma(period: int, context: dict) -> float:
    """
    N일 이동평균

    Args:
        period: 이동평균 기간
        context: 평가 컨텍스트
            - current.indicators에서 ma_{period} 조회
            - 또는 all_stocks에서 직접 계산

    Returns:
        이동평균 값
    """
    # 방법 1: indicators에 이미 계산되어 있는 경우
    current = context.get('current')
    if current and hasattr(current, 'indicators'):
        ma_key = f'ma_{period}'
        ma_value = current.indicators.get(ma_key)
        if ma_value is not None:
            return float(ma_value)

    # 방법 2: all_stocks에서 직접 계산
    all_stocks = context.get('all_stocks', [])
    current_date = context['current'].date if context.get('current') else None

    if not all_stocks or not current_date:
        return 0.0

    # 현재 날짜까지의 종가들
    prices = [
        s.close for s in all_stocks
        if s.ticker == context['current'].ticker and s.date <= current_date
    ][-period:]

    if not prices:
        return 0.0

    return sum(prices) / len(prices)


@function_registry.register(
    name='volume_ma',
    category='moving_average',
    description='N일 거래량 이동평균',
    params_schema={'period': {'type': 'int', 'min': 1, 'max': 365}}
)
def volume_ma(period: int, context: dict) -> float:
    """
    N일 거래량 이동평균

    Args:
        period: 이동평균 기간
        context: 평가 컨텍스트

    Returns:
        거래량 이동평균
    """
    all_stocks = context.get('all_stocks', [])
    current = context.get('current')

    if not all_stocks or not current:
        return 0.0

    # 현재 날짜까지의 거래량들
    volumes = [
        s.volume for s in all_stocks
        if s.ticker == current.ticker and s.date <= current.date
    ][-period:]

    if not volumes:
        return 0.0

    return sum(volumes) / len(volumes)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시간 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='candles_between',
    category='time',
    description='두 날짜 사이의 거래일 캔들 수',
    params_schema={
        'start_date': {'type': 'date', 'required': True},
        'end_date': {'type': 'date', 'required': True}
    }
)
def candles_between(start_date: date, end_date: date, context: dict) -> int:
    """
    두 날짜 사이의 거래일 캔들 수

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        context: 평가 컨텍스트 (all_stocks 필요)

    Returns:
        거래일 캔들 수
    """
    all_stocks = context.get('all_stocks', [])
    current = context.get('current')

    if not all_stocks or not current:
        return 0

    # 같은 종목의 주식만 필터링
    ticker = current.ticker

    # start_date와 end_date 사이의 거래일 수 계산
    trading_days = [
        s.date for s in all_stocks
        if s.ticker == ticker and start_date <= s.date <= end_date
    ]

    return len(trading_days)


@function_registry.register(
    name='days_since',
    category='time',
    description='특정 날짜로부터 경과한 달력 일수',
    params_schema={'start_date': {'type': 'date', 'required': True}}
)
def days_since(start_date: date, context: dict) -> int:
    """
    특정 날짜로부터 경과한 달력 일수

    Args:
        start_date: 시작 날짜
        context: 평가 컨텍스트 (current 필요)

    Returns:
        경과 일수 (달력 기준)
    """
    current = context.get('current')

    if not current or not hasattr(current, 'date'):
        return 0

    current_date = current.date

    return (current_date - start_date).days


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 가격 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='within_range',
    category='price',
    description='기준가 대비 ±N% 이내 여부',
    params_schema={
        'value': {'type': 'float', 'required': True},
        'base': {'type': 'float', 'required': True},
        'tolerance_pct': {'type': 'float', 'min': 0.0, 'max': 100.0, 'required': True}
    }
)
def within_range(value: float, base: float, tolerance_pct: float, context: dict) -> bool:
    """
    기준가 대비 ±N% 이내 여부

    Args:
        value: 비교할 값
        base: 기준 값
        tolerance_pct: 허용 범위 (%, 예: 10.0 = ±10%)
        context: 평가 컨텍스트

    Returns:
        범위 내에 있으면 True, 아니면 False
    """
    if base == 0:
        return False

    lower = base * (1 - tolerance_pct / 100)
    upper = base * (1 + tolerance_pct / 100)

    return lower <= value <= upper


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기술 지표 함수 (Skeleton)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='rsi',
    category='indicator',
    description='RSI 지표',
    params_schema={'period': {'type': 'int', 'min': 1, 'max': 100}}
)
def rsi(period: int, context: dict) -> float:
    """
    RSI 지표

    Args:
        period: RSI 기간
        context: 평가 컨텍스트

    Returns:
        RSI 값 (0~100)

    Note:
        현재는 indicators에서 조회만 함
        추후 실제 계산 로직 추가 필요
    """
    current = context.get('current')
    if current and hasattr(current, 'indicators'):
        rsi_key = f'rsi_{period}'
        rsi_value = current.indicators.get(rsi_key)
        if rsi_value is not None:
            return float(rsi_value)

    # 기본값
    return 50.0


@function_registry.register(
    name='bollinger_upper',
    category='indicator',
    description='볼린저 밴드 상단',
    params_schema={
        'period': {'type': 'int', 'min': 1, 'max': 100},
        'std_dev': {'type': 'float', 'min': 0.1, 'max': 5.0}
    }
)
def bollinger_upper(period: int, std_dev: float, context: dict) -> float:
    """
    볼린저 밴드 상단

    Args:
        period: 이동평균 기간
        std_dev: 표준편차 배수
        context: 평가 컨텍스트

    Returns:
        볼린저 밴드 상단 값

    Note:
        현재는 간단한 근사값만 계산
        추후 실제 표준편차 계산 로직 추가 필요
    """
    ma_val = ma(period, context)

    # 임시: 간단한 근사값 (실제로는 표준편차 계산 필요)
    return ma_val * (1 + std_dev * 0.02)


@function_registry.register(
    name='bollinger_lower',
    category='indicator',
    description='볼린저 밴드 하단',
    params_schema={
        'period': {'type': 'int', 'min': 1, 'max': 100},
        'std_dev': {'type': 'float', 'min': 0.1, 'max': 5.0}
    }
)
def bollinger_lower(period: int, std_dev: float, context: dict) -> float:
    """볼린저 밴드 하단"""
    ma_val = ma(period, context)
    return ma_val * (1 - std_dev * 0.02)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 블록 관련 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='EXISTS',
    category='block',
    description='블록 존재 여부 확인',
    params_schema={'block_name': {'type': 'str', 'required': True}}
)
def EXISTS(block_name: str, context: dict) -> bool:
    """
    블록 존재 여부 확인

    Args:
        block_name: 블록 이름 (예: 'block1', 'block2_strong')
        context: 평가 컨텍스트

    Returns:
        블록이 context에 존재하면 True, 아니면 False

    Example:
        expression = "EXISTS('block1') and block1.status == 'active'"
    """
    return block_name in context and context[block_name] is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 조건 확인 함수 (Skeleton)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='is_volume_high',
    category='condition',
    description='N일 신고거래량 여부',
    params_schema={'days': {'type': 'int', 'min': 1}}
)
def is_volume_high(days: int, context: dict) -> bool:
    """
    N일 신고거래량 여부

    Args:
        days: 기간 (달력 기준 일수)
        context: 평가 컨텍스트

    Returns:
        신고거래량이면 True, 아니면 False

    Note:
        현재는 indicators에서 조회만 함
    """
    current = context.get('current')
    if current and hasattr(current, 'indicators'):
        field_name = f'is_volume_high_{days}d'
        return current.indicators.get(field_name, False)

    return False


@function_registry.register(
    name='is_new_high',
    category='condition',
    description='N일 신고가 여부',
    params_schema={'days': {'type': 'int', 'min': 1}}
)
def is_new_high(days: int, context: dict) -> bool:
    """N일 신고가 여부"""
    current = context.get('current')
    if current and hasattr(current, 'indicators'):
        field_name = f'is_new_high_{days}d'
        return current.indicators.get(field_name, False)

    return False


@function_registry.register(
    name='last_valid_volume',
    category='volume',
    description='가장 최근의 정상 거래일 거래량 반환 (거래량 > 0)',
    params_schema={}
)
def last_valid_volume(context: dict) -> int:
    """
    가장 최근의 정상 거래일 거래량 반환

    전일 데이터가 오류(거래량 0)인 경우를 대비하여,
    현재 이전의 가장 최근 정상 거래일 거래량을 반환합니다.

    Args:
        context: 평가 컨텍스트
            - all_stocks: 전체 주가 데이터 (현재까지)
            - current: 현재 주가

    Returns:
        가장 최근 정상 거래일의 거래량 (없으면 0)

    Example:
        expression = "current.volume >= last_valid_volume() * 3.0"
        # 전일이 데이터 오류여도 마지막 정상 거래일 기준으로 비교
    """
    all_stocks = context.get('all_stocks', [])
    current = context.get('current')

    if not all_stocks or not current:
        return 0

    # 현재 날짜 이전의 주가들을 역순으로 검색
    for i in range(len(all_stocks) - 2, -1, -1):  # 현재(마지막) 제외하고 역순
        stock = all_stocks[i]
        if stock.ticker == current.ticker and stock.volume > 0:
            return stock.volume

    # 정상 거래일이 없으면 0 반환
    return 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 모듈 로드 시 자동 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 이 파일이 import되면 모든 함수가 function_registry에 자동 등록됨

if __name__ == "__main__":
    # 테스트: 등록된 함수 목록 출력
    function_registry.print_summary()
