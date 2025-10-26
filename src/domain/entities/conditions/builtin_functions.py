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


@function_registry.register(
    name='normalized_volume',
    category='moving_average',
    description='정규화된 거래량 (N일 평균 대비 비율, %)',
    params_schema={'period': {'type': 'int', 'min': 1, 'max': 365}}
)
def normalized_volume(period: int, context: dict) -> float:
    """
    정규화된 거래량 (Normalized Volume)

    현재 거래량을 N일 평균 거래량으로 나눈 후 100을 곱하여 백분율로 반환.

    Args:
        period: 평균 거래량 계산 기간 (일)
        context: 평가 컨텍스트
            - current: 현재 주가 데이터
            - all_stocks: 전체 주가 데이터 리스트

    Returns:
        (현재 거래량 / N일 평균 거래량) * 100 (%)

    Examples:
        >>> normalized_volume(20)  # 현재 거래량이 20일 평균의 150%인 경우 → 150.0 반환
        >>> normalized_volume(60)  # 현재 거래량이 60일 평균의 50%인 경우 → 50.0 반환
    """
    current = context.get('current')
    if not current:
        return 0.0

    # 현재 거래량
    current_volume = current.volume
    if current_volume == 0:
        return 0.0

    # N일 평균 거래량 계산
    avg_volume = volume_ma(period, context)

    if avg_volume == 0:
        return 0.0

    # 비율 계산 (백분율)
    ratio_pct = (current_volume / avg_volume) * 100.0

    return ratio_pct


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


@function_registry.register(
    name='upside_extension_ratio',
    category='price',
    description='기준 가격 대비 고가/저가 확장 비율 (방향성 포함)',
    params_schema={
        'base_price': {'type': 'float', 'required': True},
        'high_price': {'type': 'float', 'required': True},
        'low_price': {'type': 'float', 'required': True}
    }
)
def upside_extension_ratio(
    base_price: float,
    high_price: float,
    low_price: float,
    context: dict
) -> float:
    """
    기준 가격 대비 고가/저가 확장 비율 (방향성 포함)

    기준 가격에서 고가까지의 거리와 저가까지의 거리의 비율을 계산합니다.
    부호는 방향성을 나타냅니다 (+ = 고가가 기준보다 위, - = 고가가 기준보다 아래).

    Args:
        base_price: 기준 가격 (예: check_day.close, prev.close)
        high_price: 당일 고가 (예: current.high)
        low_price: 당일 저가 (예: current.low)
        context: 평가 컨텍스트

    Returns:
        (고가 확장 거리) / (저가 확장 거리) * 100 (부호 포함)
        예: +200 = 고가가 기준보다 위 + 상승폭이 하락폭보다 2배
        예: -50 = 고가가 기준보다 아래 + 하락폭이 상승폭보다 2배

    Examples:
        >>> # 상승 케이스: base=10000, high=12000, low=11000
        >>> upside_extension_ratio(10000, 12000, 11000, {})
        200.0  # +방향 (상승), 상승폭(2000)이 하락폭(1000)보다 2배

        >>> # 하락 케이스: base=10000, high=9000, low=8000
        >>> upside_extension_ratio(10000, 9000, 8000, {})
        -50.0  # -방향 (하락), 상승폭(1000)이 하락폭(2000)의 0.5배

        >>> # 검사일 종가 기준, D일 고저 비율
        >>> upside_extension_ratio(check_day.close, current.high, current.low)

    Note:
        - 0으로 나누기 방지: 분모가 0이면 0.0 반환
        - 절댓값으로 거리 계산 후 고가 방향으로 부호 결정
        - 전제 조건: 일반적으로 high_price > base_price 상황에서 사용 권장
    """
    # 거리 계산 (절댓값으로 크기만)
    distance_to_high = abs(base_price - high_price)
    distance_to_low = abs(base_price - low_price)

    # 0으로 나누기 방지
    if distance_to_low == 0:
        return 0.0

    # 비율 계산 (절댓값)
    ratio = (distance_to_high / distance_to_low) * 100

    # 방향 결정 (고가 기준)
    if high_price >= base_price:
        return ratio   # + 방향 (상승)
    else:
        return -ratio  # - 방향 (하락)


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
    name='exists',
    category='block',
    description='블록 존재 여부 확인',
    params_schema={'block_name': {'type': 'str', 'required': True}}
)
def exists(block_name: str, context: dict) -> bool:
    """
    블록 존재 여부 확인

    Args:
        block_name: 블록 이름 (예: 'block1', 'block2_strong')
        context: 평가 컨텍스트

    Returns:
        블록이 context에 존재하면 True, 아니면 False

    Example:
        expression = "exists('block1') and block1.status == 'active'"
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
    """
    current = context.get('current')

    # 방법 1: indicators에 이미 계산되어 있는 경우
    if current and hasattr(current, 'indicators'):
        field_name = f'is_volume_high_{days}d'
        indicator_value = current.indicators.get(field_name)
        if indicator_value is not None:
            return indicator_value

    # 방법 2: all_stocks에서 직접 계산
    all_stocks = context.get('all_stocks', [])
    if not all_stocks or not current:
        print(f"  [DEBUG is_volume_high] No all_stocks or current")
        return False

    # 현재 날짜 기준 N일 전부터의 거래량들
    cutoff_date = current.date - timedelta(days=days)
    recent_volumes = [
        s.volume for s in all_stocks
        if s.ticker == current.ticker and cutoff_date <= s.date <= current.date
    ]

    if not recent_volumes:
        print(f"  [DEBUG is_volume_high] No recent volumes for {days} days")
        return False

    # 현재 거래량이 N일 중 최대인지 확인
    max_volume = max(recent_volumes)
    is_high = current.volume == max_volume
    print(f"  [DEBUG is_volume_high] date={current.date}, volume={current.volume:,}, max={max_volume:,}, is_high={is_high}")
    return is_high


@function_registry.register(
    name='is_new_high',
    category='condition',
    description='N일 신고가 여부',
    params_schema={'days': {'type': 'int', 'min': 1}}
)
def is_new_high(days: int, context: dict) -> bool:
    """N일 신고가 여부"""
    current = context.get('current')

    # 방법 1: indicators에 이미 계산되어 있는 경우
    if current and hasattr(current, 'indicators'):
        field_name = f'is_new_high_{days}d'
        indicator_value = current.indicators.get(field_name)
        if indicator_value is not None:
            return indicator_value

    # 방법 2: all_stocks에서 직접 계산
    all_stocks = context.get('all_stocks', [])
    if not all_stocks or not current:
        return False

    # 현재 날짜 기준 N일 전부터의 고가들
    cutoff_date = current.date - timedelta(days=days)
    recent_highs = [
        s.high for s in all_stocks
        if s.ticker == current.ticker and cutoff_date <= s.date <= current.date
    ]

    if not recent_highs:
        return False

    # 현재 고가가 N일 중 최대인지 확인
    return current.high == max(recent_highs)


@function_registry.register(
    name='last_valid_volume',
    category='volume',
    description='[DEPRECATED] Use prev.volume instead - 가장 최근의 정상 거래일 거래량 반환',
    params_schema={}
)
def last_valid_volume(context: dict) -> int:
    """
    [DEPRECATED] 이 함수는 더 이상 필요하지 않습니다.

    `prev.volume`을 직접 사용하세요.
    `prev`는 자동으로 마지막 정상 거래일을 반환합니다.

    Args:
        context: 평가 컨텍스트
            - all_stocks: 전체 주가 데이터 (현재까지)
            - current: 현재 주가

    Returns:
        가장 최근 정상 거래일의 거래량 (없으면 0)

    Example (Old):
        expression = "current.volume >= last_valid_volume() * 3.0"

    Example (New):
        expression = "current.volume >= prev.volume * 3.0"
    """
    from src.infrastructure.logging import get_logger
    logger = get_logger(__name__)

    logger.warning(
        "last_valid_volume() is deprecated. Use 'prev.volume' instead.",
        context={
            'function': 'last_valid_volume',
            'replacement': 'prev.volume',
            'current_date': str(context.get('current').date) if context.get('current') else 'unknown'
        }
    )

    # 기존 로직 유지 (호환성)
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
# Detection Functions (블록 감지 관련)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='is_price_breakout',
    category='detection',
    description='현재 시가가 이전 블록의 고점 대비 -N% 이상인지 체크 (레벨업 판단)',
    params_schema={
        'prev_block_id': {'type': 'str', 'required': True},
        'tolerance_pct': {'type': 'float', 'required': True, 'min': 0.0, 'max': 100.0}
    }
)
def is_price_breakout(
    prev_block_id: str,
    tolerance_pct: float,
    context: dict
) -> bool:
    """
    현재 시가가 이전 블록의 고점 대비 -N% 이상인지 체크

    기준점(baseline) 결정 로직:
    1. 이전 블록의 peak_price (전체 범위 중 최고가)
    2. spot2의 high (spot2가 있으면)
    3. spot1의 high (spot2가 없고 spot1이 있으면)

    위 값들 중 가장 **작은** 값을 baseline으로 사용 (보수적 접근)

    Args:
        prev_block_id: 이전 블록 ID (예: 'block1')
        tolerance_pct: 허용 하락 퍼센트 (예: 10.0 = -10%까지 허용)
        context: 평가 컨텍스트

    Returns:
        True: 현재 시가가 baseline * (1 - tolerance_pct/100) 이상
        False: 조건 불만족 또는 데이터 없음

    Example:
        is_price_breakout('block1', 10.0)
        # Block1의 고점 대비 -10% 이상에서 시작했는지 체크
    """
    # 1. 이전 블록 조회
    prev_block = context.get(prev_block_id)
    if prev_block is None:
        return False

    # 2. 현재 시가 조회
    current = context.get('current')
    if not current or not hasattr(current, 'open'):
        return False

    current_open = current.open
    if current_open is None or current_open <= 0:
        return False

    # 3. 사용 가능한 baseline 값들 수집
    baselines = []

    # 3-1. peak_price 추가
    if hasattr(prev_block, 'peak_price') and prev_block.peak_price:
        if prev_block.peak_price > 0:
            baselines.append(prev_block.peak_price)

    # 3-2. spot 데이터에서 high 값 추출
    spots = []
    if hasattr(prev_block, 'custom_metadata') and prev_block.custom_metadata:
        spots = prev_block.custom_metadata.get('spots', [])

    # spot2 찾기
    spot2 = None
    spot1 = None
    for spot in spots:
        if spot.get('spot_number') == 2:
            spot2 = spot
        elif spot.get('spot_number') == 1:
            spot1 = spot

    # 3-3. spot2가 있으면 spot2.high 추가
    if spot2 and spot2.get('high'):
        if spot2['high'] > 0:
            baselines.append(spot2['high'])

    # 3-4. spot2가 없고 spot1이 있으면 spot1.high 추가
    elif spot1 and spot1.get('high'):
        if spot1['high'] > 0:
            baselines.append(spot1['high'])

    # 4. baseline 없으면 False
    if not baselines:
        return False

    # 5. 가장 작은 값을 baseline으로 선택 (보수적 접근)
    baseline = min(baselines)

    # 6. 허용 하락폭 계산
    threshold = baseline * (1 - tolerance_pct / 100.0)

    # 7. 현재 시가가 threshold 이상인지 체크
    return current_open >= threshold


@function_registry.register(
    name='is_price_doubling_surge',
    category='detection',
    description='현재 고가가 이전 블록의 상승폭을 반복했는지 체크 (2배 상승)',
    params_schema={
        'prev_block_id': {'type': 'str', 'required': True}
    }
)
def is_price_doubling_surge(
    prev_block_id: str,
    context: dict
) -> bool:
    """
    현재 고가가 이전 블록의 상승폭을 반복했는지 체크

    계산 로직:
    1. 전일 종가 = prev_block.prev_close (블록 시작 전일 종가)
    2. 상승폭 = prev_block.peak_price - prev_block.prev_close
    3. 목표가격 = prev_block.peak_price + 상승폭
                = 2 * prev_block.peak_price - prev_block.prev_close
    4. 조건: current.high >= 목표가격

    예시:
        Block1: prev_close=10000, peak_price=15000
        상승폭 = 15000 - 10000 = 5000
        목표가격 = 15000 + 5000 = 20000
        Block2 진입: current.high >= 20000

    Args:
        prev_block_id: 이전 블록 ID (예: 'block1')
        context: 평가 컨텍스트

    Returns:
        True: 상승폭 반복 성공 (current.high >= 목표가격)
        False: 조건 불만족 또는 데이터 없음

    Example:
        is_price_doubling_surge('block1')
        # Block1 상승폭을 반복했는지 체크 (2배 상승 달성)
    """
    # 1. 이전 블록 조회
    prev_block = context.get(prev_block_id)
    if prev_block is None:
        return False

    # 2. 필수 데이터 검증
    if not hasattr(prev_block, 'peak_price') or prev_block.peak_price is None:
        return False

    if not hasattr(prev_block, 'prev_close') or prev_block.prev_close is None:
        return False

    if prev_block.peak_price <= 0 or prev_block.prev_close <= 0:
        return False

    # 3. 현재 고가 조회
    current = context.get('current')
    if not current or not hasattr(current, 'high'):
        return False

    current_high = current.high
    if current_high is None or current_high <= 0:
        return False

    # 4. 목표가격 계산
    # 목표가격 = 2 * peak_price - prev_close
    target_price = 2 * prev_block.peak_price - prev_block.prev_close

    # 5. 조건 평가
    return current_high >= target_price


@function_registry.register(
    name='is_stay_spot',
    category='detection',
    description='회고적 spot 패턴 체크 (음수 오프셋 사용) - Block 유지 전략',
    params_schema={
        'prev_block_id': {'type': 'str', 'required': True},
        'offset_start': {'type': 'int', 'required': True, 'max': -1},
        'offset_end': {'type': 'int', 'required': True, 'max': -1}
    }
)
def is_stay_spot(
    prev_block_id: str,
    offset_start: int,
    offset_end: int,
    context: dict
) -> bool:
    """
    회고적 spot 패턴 체크 (Stay Spot) - Block 유지 전략

    다음 블록 조건이 D일에 만족될 때, 지정된 오프셋 범위의 날짜를 회고적으로 검사하여
    spot_entry_conditions를 만족하면 현재 블록에 spot을 추가하고
    다음 블록으로 전환하지 않습니다 (블록 유지).

    실제 회고 로직은 StaySpotStrategy에서 수행되며,
    이 함수는 기본 검증(블록 존재, active 상태, spot2 여부)만 수행합니다.

    Args:
        prev_block_id: 이전 블록 ID (예: 'block1')
        offset_start: 시작 오프셋 (-1 = D-1일, -2 = D-2일)
        offset_end: 종료 오프셋 (-2 = D-2일, -5 = D-5일)
        context: 평가 컨텍스트
            - {prev_block_id}: 이전 블록 객체
            - current: 현재 주가 데이터
            - all_stocks: 전체 주가 데이터

    Returns:
        True: 이전 블록이 존재하고 active이며 spot2가 없음 (Stay 전략 적용 가능)
        False: 조건 불만족 (다음 블록으로 전환)

    Logic:
        1. prev_block이 context에 존재하는가?
        2. prev_block이 active 상태인가?
        3. prev_block이 spot2를 아직 안 가졌나?
        4. 조건 만족 시 StaySpotStrategy가 offset_start ~ offset_end일 검사 수행

    Examples:
        >>> is_stay_spot('block1', -1, -2)
        # D-1, D-2일 회고 검사 (가장 일반적)

        >>> is_stay_spot('block1', -1, -1)
        # D-1일만 체크

        >>> is_stay_spot('block1', -1, -5)
        # D-1~D-5일 회고 검사 (5일 범위)

        >>> is_stay_spot('block1', -2, -4)
        # D-2~D-4일 회고 검사 (D-1 건너뜀)

        >>> # YAML에서 사용 예시 (Block2 spot_condition)
        >>> spot_condition: "is_stay_spot('block1', -1, -2)"

    Note:
        - 음수 오프셋 사용: -1 = "1일 전", -2 = "2일 전" (직관적)
        - 우선순위: D-1 > D-2 > D-3 > ... (먼저 만족하는 날짜 선택)
        - spot_entry_conditions가 BlockNode에 정의되어 있어야 함
        - Block 유지 전략: Block1 유지, Block2로 넘어가지 않음
        - 파라미터 변경만으로 확장 가능 (코드 수정 불필요)
    """
    # 1. 이전 블록 조회
    prev_block = context.get(prev_block_id)

    if prev_block is None:
        # 이전 블록이 context에 없음
        return False

    # 2. 이전 블록이 active 상태인지 확인
    if not prev_block.is_active():
        return False

    # 3. spot2가 이미 있으면 제외
    if prev_block.has_spot2():
        return False

    # 4. 기본 검증 통과 → ContinuationSpotStrategy가 회고 로직 수행
    return True


@function_registry.register(
    name='is_levelup_spot',
    category='detection',
    description='회고적 spot 패턴 체크 (음수 오프셋 사용) - Block 전환 전략',
    params_schema={
        'prev_block_id': {'type': 'str', 'required': True},
        'offset_start': {'type': 'int', 'required': True, 'max': -1},
        'offset_end': {'type': 'int', 'required': True, 'max': -1}
    }
)
def is_levelup_spot(
    prev_block_id: str,
    offset_start: int,
    offset_end: int,
    context: dict
) -> bool:
    """
    회고적 spot 패턴 체크 (Levelup Spot) - Block 전환 전략

    다음 블록 조건이 D일에 만족될 때, 지정된 오프셋 범위의 날짜를 회고적으로 검사하여
    조건을 만족하면 다음 블록을 생성하되 시작일을 앞당깁니다.
    (Block1 → Block2 전환, "레벨업")

    실제 회고 로직은 LevelupSpotStrategy에서 수행되며,
    이 함수는 기본 검증(블록 존재, active 상태, spot2 여부)만 수행합니다.

    Args:
        prev_block_id: 이전 블록 ID (예: 'block1')
        offset_start: 시작 오프셋 (-1 = D-1일, -2 = D-2일)
        offset_end: 종료 오프셋 (-2 = D-2일, -5 = D-5일)
        context: 평가 컨텍스트
            - {prev_block_id}: 이전 블록 객체
            - current: 현재 주가 데이터
            - all_stocks: 전체 주가 데이터

    Returns:
        True: 이전 블록이 존재하고 active이며 spot2가 없음 (Levelup 전략 적용 가능)
        False: 조건 불만족 (일반 블록 생성)

    Logic:
        1. prev_block이 context에 존재하는가?
        2. prev_block이 active 상태인가?
        3. prev_block이 spot2를 아직 안 가졌나?
        4. 조건 만족 시 LevelupSpotStrategy가 offset_start ~ offset_end일 검사 수행
        5. 어느 날짜가 조건 만족 시:
           - Block2 생성 (started_at = 만족한 날짜, "조기 시작")
           - Block2.spots = [{spot1: 만족한 날짜}, {spot2: D}]
           - Block1 종료 (ended_at = spot1 - 1일)

    Examples:
        >>> is_levelup_spot('block1', -1, -2)
        # D-1, D-2일 회고 검사 (가장 일반적)

        >>> is_levelup_spot('block1', -1, -1)
        # D-1일만 체크

        >>> is_levelup_spot('block1', -1, -5)
        # D-1~D-5일 회고 검사 (5일 범위)

        >>> is_levelup_spot('block1', -2, -4)
        # D-2~D-4일 회고 검사 (D-1 제외)

        >>> # YAML에서 사용 예시 (Block2 spot_condition)
        >>> spot_condition:
        >>>   function: "is_levelup_spot"
        >>>   args:
        >>>     prev_block_id: "block1"
        >>>     min_days: 1
        >>>     max_days: 2
        >>>   exclude_conditions:
        >>>     - "price_doubling_surge_from_block1"

    Note:
        - 실제 D-min_days ~ D-max_days 조건 평가는 LevelupSpotStrategy에서 수행
        - spot_condition.exclude_conditions로 제외할 조건 지정 가능
        - 우선순위: D-1 > D-2 > D-3 > ... (먼저 만족하는 날짜 선택)
        - Block1은 spot1-1일에 자동 종료됨
        - Block 전환 전략: Block1 종료, Block2로 레벨업
        - 파라미터 변경만으로 확장 가능 (코드 수정 불필요)
    """
    # 1. 이전 블록 조회
    prev_block = context.get(prev_block_id)

    if prev_block is None:
        # 이전 블록이 context에 없음
        return False

    # 2. 이전 블록이 active 상태인지 확인
    if not prev_block.is_active():
        return False

    # 3. spot2가 이미 있으면 제외
    if prev_block.has_spot2():
        return False

    # 4. 기본 검증 통과 → EarlyStartSpotStrategy가 회고 로직 수행
    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 재탐지 (Redetection) 관련 함수 (NEW - 2025-10-25)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@function_registry.register(
    name='has_active_redetection',
    category='redetection',
    description='Check if a block has an active redetection event',
    params_schema={
        'block_id': {
            'type': 'str',
            'description': 'Block ID to check (e.g., "block1", "block2")'
        }
    }
)
def has_active_redetection(block_id: str, context: dict) -> bool:
    """
    해당 블록에 active 재탐지가 있는지 확인

    Args:
        block_id: 블록 ID (예: 'block1', 'block2')
        context: 평가 컨텍스트

    Returns:
        Active 재탐지가 있으면 True

    Example:
        >>> # YAML에서 사용
        >>> "has_active_redetection('block1')"  # Block1에 active 재탐지 있는지
    """
    block = context.get(block_id)
    if not block:
        return False

    return block.get_active_redetection() is not None


@function_registry.register(
    name='redetection_count',
    category='redetection',
    description='Get total number of redetections for a block',
    params_schema={
        'block_id': {
            'type': 'str',
            'description': 'Block ID to check'
        }
    }
)
def redetection_count(block_id: str, context: dict) -> int:
    """
    해당 블록의 총 재탐지 개수 (active + completed)

    Args:
        block_id: 블록 ID
        context: 평가 컨텍스트

    Returns:
        재탐지 개수

    Example:
        >>> "redetection_count('block1') >= 2"  # Block1 재탐지가 2회 이상
    """
    block = context.get(block_id)
    if not block:
        return 0

    return block.get_redetection_count()


@function_registry.register(
    name='completed_redetection_count',
    category='redetection',
    description='Get number of completed redetections for a block',
    params_schema={
        'block_id': {
            'type': 'str',
            'description': 'Block ID to check'
        }
    }
)
def completed_redetection_count(block_id: str, context: dict) -> int:
    """
    해당 블록의 완료된 재탐지 개수

    Args:
        block_id: 블록 ID
        context: 평가 컨텍스트

    Returns:
        완료된 재탐지 개수

    Example:
        >>> "completed_redetection_count('block1') >= 1"
    """
    block = context.get(block_id)
    if not block:
        return 0

    return block.get_completed_redetection_count()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 모듈 로드 시 자동 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 이 파일이 import되면 모든 함수가 function_registry에 자동 등록됨

if __name__ == "__main__":
    # 테스트: 등록된 함수 목록 출력
    function_registry.print_summary()
