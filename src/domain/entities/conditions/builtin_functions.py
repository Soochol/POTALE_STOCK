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
    name='is_spot_candidate',
    category='detection',
    description='이전 블록의 spot 추가 후보인지 체크',
    params_schema={
        'prev_block_id': {'type': 'str', 'required': True},
        'min_days': {'type': 'int', 'required': True, 'min': 0},
        'max_days': {'type': 'int', 'required': True, 'min': 0}
    }
)
def is_spot_candidate(
    prev_block_id: str,
    min_days: int,
    max_days: int,
    context: dict
) -> bool:
    """
    이전 블록의 spot 추가 후보인지 확인

    Block 발생 후 D+1, D+2일에 상위 Block 조건이 만족되면,
    새 Block을 생성하지 않고 기존 Block에 spot 데이터를 추가.

    Args:
        prev_block_id: 이전 블록 ID (예: 'block1')
        min_days: 최소 일수 (1 = D+1)
        max_days: 최대 일수 (2 = D+2)
        context: 평가 컨텍스트
            - {prev_block_id}: 이전 블록 객체
            - current: 현재 주가 데이터
            - all_stocks: 전체 주가 데이터

    Returns:
        True: spot 후보임 (새 블록 생성하지 않고 spot 추가)
        False: spot 후보 아님 (새 블록 생성)

    Logic:
        1. prev_block이 context에 존재하고 active인가?
        2. prev_block이 spot2를 아직 안 가졌나?
        3. candles_between(prev_block.started_at, current.date) in [min_days+1, max_days+1]?
           (candles_between는 시작/종료일 포함이므로 +1)

    Examples:
        >>> is_spot_candidate('block1', 1, 2)
        # Block1 시작일로부터 D+1 또는 D+2일이면 True

        >>> is_spot_candidate('block2', 1, 3)
        # Block2 시작일로부터 D+1~D+3일이면 True

    Note:
        - spot 최대 개수는 DynamicBlockDetection.add_spot()에서 제어
        - 이 함수는 시간 조건만 체크
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

    # 4. 날짜 간격 체크
    current = context.get('current')
    if not current:
        return False

    try:
        # candles_between은 시작일과 종료일을 포함하여 계산
        # prev_block.started_at = Day 10
        # current.date = Day 11 → candles_between = 2 (Day 10, Day 11) → D+1
        # current.date = Day 12 → candles_between = 3 (Day 10, Day 11, Day 12) → D+2
        days_diff = candles_between(prev_block.started_at, current.date, context)

        # min_days=1, max_days=2 → days_diff는 2 또는 3이어야 함
        # D+1: days_diff == 2 (min_days + 1)
        # D+2: days_diff == 3 (max_days + 1)
        target_min = min_days + 1
        target_max = max_days + 1

        return target_min <= days_diff <= target_max

    except Exception:
        # candles_between 계산 실패 시 False
        return False


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
