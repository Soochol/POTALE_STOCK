"""
2018-06-01이 Block3 Seed로 탐지되지 않은 원인 분석
모든 조건을 상세히 체크
"""
import sys
import os
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import date, datetime
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.preset.seed_condition_preset_repository import SeedConditionPresetRepository
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator

# DB 연결
db = DatabaseConnection('data/database/stock_data.db')
stock_repo = SqliteStockRepository('data/database/stock_data.db')
seed_repo = SeedConditionPresetRepository(db)

# 데이터 로드
ticker = '025980'
stocks = stock_repo.get_stock_data(ticker, date(2015, 1, 1), date.today())

# 지표 계산 (고가 기준 등락률 포함)
calculator = Block1IndicatorCalculator()
stocks = calculator.calculate(
    stocks,
    ma_period=120,
    exit_ma_period=60,
    volume_months=12,
    new_high_months=1
)

# Seed 조건 로드
seed_condition = seed_repo.load('default_seed')

# 2018-06-01과 전일 찾기
target_date = date(2018, 6, 1)
target_stock = None
prev_stock = None

for idx, stock in enumerate(stocks):
    if stock.date == target_date:
        target_stock = stock
        if idx > 0:
            prev_stock = stocks[idx - 1]
        break

if not target_stock:
    print('2018-06-01 데이터를 찾을 수 없습니다.')
    exit()

indicators = target_stock.indicators if hasattr(target_stock, 'indicators') else {}

print('╔' + '═' * 98 + '╗')
print('║' + ' 2018-06-01 주가 데이터 및 지표'.center(98) + '║')
print('╚' + '═' * 98 + '╝')
print()
print(f'  날짜:        {target_stock.date}')
print(f'  종가:        {target_stock.close:,}원')
print(f'  고가:        {target_stock.high:,}원')
print(f'  저가:        {target_stock.low:,}원')
print(f'  거래량:      {target_stock.volume:,}주')
if prev_stock:
    print(f'  전일 종가:   {prev_stock.close:,}원')
    print(f'  전일 거래량: {prev_stock.volume:,}주')
print()

# Block2 정보 조회
with db.session_scope() as session:
    from sqlalchemy import text

    block2_result = session.execute(text('''
        SELECT started_at, peak_price, peak_volume
        FROM block2_detection
        WHERE ticker=:ticker
        AND condition_name='seed'
        ORDER BY started_at
        LIMIT 1
    '''), {'ticker': ticker}).fetchone()

    if not block2_result:
        print('[!] Block2 Seed 데이터를 찾을 수 없습니다.')
        exit()

    block2_start_date = block2_result[0]
    block2_peak_price = block2_result[1]
    block2_peak_volume = block2_result[2]

print('╔' + '═' * 98 + '╗')
print('║' + ' Pattern #1 Block2 Seed 정보'.center(98) + '║')
print('╚' + '═' * 98 + '╝')
print()
print(f'  Block2 시작:       {block2_start_date}')
print(f'  Block2 최고가:     {block2_peak_price:,}원')
print(f'  Block2 최고 거래량: {block2_peak_volume if block2_peak_volume else "NULL (비어있음)"}')
print()

print('╔' + '═' * 98 + '╗')
print('║' + ' Block3 Seed 진입 조건 상세 검증'.center(98) + '║')
print('╚' + '═' * 98 + '╝')
print()

all_pass = True
failed_conditions = []

# Block1 조건 1: 등락률
entry_surge_rate = seed_condition.block3_entry_surge_rate or seed_condition.base.block1_entry_surge_rate
rate = indicators.get('rate', 0)
surge_pass = rate >= entry_surge_rate
print(f'[Block1-1] 등락률 >= {entry_surge_rate}%')
print(f'  실제 등락률 (고가 기준): {rate:.2f}%')
print(f'  결과: {"✓ 통과" if surge_pass else "✗ 실패"}')
if not surge_pass:
    all_pass = False
    failed_conditions.append(f'등락률: {rate:.2f}% < {entry_surge_rate}%')
print()

# Block1 조건 2: 고가 >= MA120
ma_period = seed_condition.base.block1_entry_ma_period
entry_high_above_ma = seed_condition.base.block1_entry_high_above_ma
if ma_period and entry_high_above_ma:
    ma_key = f'MA_{ma_period}'
    ma_value = indicators.get(ma_key)
    ma_pass = ma_value is not None and target_stock.high >= ma_value
    print(f'[Block1-2] 고가 >= MA{ma_period}')
    print(f'  MA{ma_period}: {ma_value:,.2f}원' if ma_value else f'  MA{ma_period}: NULL')
    print(f'  당일 고가: {target_stock.high:,}원')
    if ma_value:
        print(f'  차이: {target_stock.high - ma_value:+,.2f}원')
    print(f'  결과: {"✓ 통과" if ma_pass else "✗ 실패"}')
    if not ma_pass:
        all_pass = False
        failed_conditions.append(f'고가 < MA{ma_period}' if ma_value else 'MA값 없음')
    print()

# Block1 조건 3: 이격도
max_deviation = seed_condition.base.block1_entry_max_deviation_ratio
if max_deviation:
    deviation = indicators.get('deviation', 100)
    deviation_pass = deviation <= max_deviation
    print(f'[Block1-3] 이격도 <= {max_deviation}%')
    print(f'  실제 이격도: {deviation:.2f}%')
    print(f'  결과: {"✓ 통과" if deviation_pass else "✗ 실패"}')
    if not deviation_pass:
        all_pass = False
        failed_conditions.append(f'이격도: {deviation:.2f}% > {max_deviation}%')
    print()

# Block1 조건 4: 거래대금
min_trading_value = seed_condition.base.block1_entry_min_trading_value
if min_trading_value:
    trading_value = indicators.get('trading_value_100m', 0)
    trading_pass = trading_value >= min_trading_value
    print(f'[Block1-4] 거래대금 >= {min_trading_value}억원')
    print(f'  실제 거래대금: {trading_value:.2f}억원')
    print(f'  결과: {"✓ 통과" if trading_pass else "✗ 실패"}')
    if not trading_pass:
        all_pass = False
        failed_conditions.append(f'거래대금: {trading_value:.2f}억 < {min_trading_value}억')
    print()

# Block1 조건 5: N개월 신고 거래량
volume_high_months = seed_condition.base.block1_entry_volume_high_months
if volume_high_months:
    is_volume_high = indicators.get('is_volume_high', False)
    volume_high_pass = is_volume_high
    print(f'[Block1-5] {volume_high_months}개월 신고 거래량')
    print(f'  신고 거래량 여부: {"예" if is_volume_high else "아니오"}')
    print(f'  결과: {"✓ 통과" if volume_high_pass else "✗ 실패"}')
    if not volume_high_pass:
        all_pass = False
        failed_conditions.append(f'{volume_high_months}개월 신고 거래량 아님')
    print()

# Block1 조건 6: 전일 대비 거래량 급증
volume_spike_ratio = seed_condition.base.block1_entry_volume_spike_ratio
if volume_spike_ratio and prev_stock:
    required_volume = prev_stock.volume * (volume_spike_ratio / 100.0)
    volume_spike_pass = target_stock.volume >= required_volume
    print(f'[Block1-6] 거래량 >= 전일 × {volume_spike_ratio}%')
    print(f'  전일 거래량: {prev_stock.volume:,}주')
    print(f'  필요 거래량: {required_volume:,.0f}주')
    print(f'  실제 거래량: {target_stock.volume:,}주')
    print(f'  결과: {"✓ 통과" if volume_spike_pass else "✗ 실패"}')
    if not volume_spike_pass:
        all_pass = False
        failed_conditions.append(f'거래량 급증: {target_stock.volume:,}주 < {required_volume:,.0f}주')
    print()

# Block1 조건 7: N개월 신고가
price_high_months = seed_condition.base.block1_entry_price_high_months
if price_high_months:
    is_new_high = indicators.get('is_new_high', False)
    new_high_pass = is_new_high
    print(f'[Block1-7] {price_high_months}개월 신고가')
    print(f'  신고가 여부: {"예" if is_new_high else "아니오"}')
    print(f'  결과: {"✓ 통과" if new_high_pass else "✗ 실패"}')
    if not new_high_pass:
        all_pass = False
        failed_conditions.append(f'{price_high_months}개월 신고가 아님')
    print()

# Block3 조건 1: 거래량 비율
volume_ratio = seed_condition.block3_volume_ratio
if volume_ratio and block2_peak_volume:
    required_volume = block2_peak_volume * (volume_ratio / 100.0)
    block3_volume_pass = target_stock.volume >= required_volume
    print(f'[Block3-1] 거래량 >= Block2 최고 × {volume_ratio}%')
    print(f'  Block2 최고 거래량: {block2_peak_volume:,}주')
    print(f'  필요 거래량: {required_volume:,.0f}주')
    print(f'  실제 거래량: {target_stock.volume:,}주')
    print(f'  결과: {"✓ 통과" if block3_volume_pass else "✗ 실패"}')
    if not block3_volume_pass:
        all_pass = False
        failed_conditions.append(f'Block3 거래량: {target_stock.volume:,}주 < {required_volume:,.0f}주')
    print()
elif volume_ratio:
    print(f'[Block3-1] 거래량 >= Block2 최고 × {volume_ratio}%')
    print(f'  Block2 최고 거래량: NULL (조건 스킵됨)')
    print(f'  결과: ⊘ 체크 안 함')
    print()

# Block3 조건 2: 저가 마진
low_price_margin = seed_condition.block3_low_price_margin
if low_price_margin and block2_peak_price:
    margin = low_price_margin / 100.0
    threshold_price = target_stock.low * (1 + margin)
    margin_pass = threshold_price > block2_peak_price
    print(f'[Block3-2] 당일_저가 × (1 + {low_price_margin}%) > Block2_최고가')
    print(f'  Block2 최고가: {block2_peak_price:,}원')
    print(f'  당일 저가: {target_stock.low:,}원')
    print(f'  저가 × 1.{int(low_price_margin):02d}: {threshold_price:,.0f}원')
    print(f'  차이: {threshold_price - block2_peak_price:+,.0f}원')
    print(f'  결과: {"✓ 통과" if margin_pass else "✗ 실패"}')
    if not margin_pass:
        all_pass = False
        failed_conditions.append(f'저가 마진: {threshold_price:,.0f}원 <= {block2_peak_price:,}원')
    print()

# 종합 결과
print('═' * 100)
if all_pass:
    print('  ✓ 모든 조건 통과 - Block3 Seed 진입 가능')
    print()
    print('  ⚠️  조건은 통과했지만 실제로는 탐지되지 않았음!')
    print('     → 다른 숨겨진 이슈가 있을 가능성')
else:
    print('  ✗ 조건 미달 - Block3 Seed 진입 불가')
    print()
    print('  실패 원인:')
    for i, reason in enumerate(failed_conditions, 1):
        print(f'    {i}. {reason}')
print('═' * 100)