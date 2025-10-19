"""
Block2 조건 진단 스크립트

왜 Block2가 탐지되지 않았는지 분석합니다.
각 Block1 이후에 Block2 조건이 거의 충족된 날들을 찾아 출력합니다.
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.block1_condition_preset_repository import Block1ConditionPresetRepository
from src.infrastructure.database.connection import DatabaseConnection
from src.domain.entities.block2_condition import Block2Condition
from src.application.services.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.block1_checker import Block1Checker
from src.application.services.block2_checker import Block2Checker


def main():
    """메인 함수"""
    print("="*70)
    print("Block2 조건 진단")
    print("="*70)
    print()

    # ===================================================================
    # 1. Repository 초기화
    # ===================================================================
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    preset_repo = Block1ConditionPresetRepository(db_conn)
    stock_repo = SqliteStockRepository(db_path)
    block1_repo = Block1Repository(db_conn)

    # ===================================================================
    # 2. Block1 조건 및 Block2 조건 로드
    # ===================================================================
    preset_name = "custom"
    block1_cond = preset_repo.load(preset_name)

    block2_cond = Block2Condition(
        block1_condition=block1_cond,
        block_volume_ratio=15.0,  # 블록1 최고 거래량의 15%
        low_price_margin=10.0,    # 저가 10% 마진
        cooldown_days=20,
        min_candles_after_block1=4
    )

    print(f"Block2 조건:")
    print(f"  - Block1 최고 거래량의 {block2_cond.block_volume_ratio}% 이상")
    print(f"  - 저가 × 1.{block2_cond.low_price_margin:.0f} > Block1 최고가")
    print(f"  - Block1 시작 후 최소 {block2_cond.min_candles_after_block1} 캔들")
    print()

    # ===================================================================
    # 3. 주가 데이터 로드
    # ===================================================================
    ticker = "025980"
    start_date = date(2015, 1, 2)
    end_date = date(2025, 10, 17)

    stocks = stock_repo.get_stock_data(ticker, start_date, end_date)

    # 지표 계산
    indicator_calculator = Block1IndicatorCalculator()
    stocks_with_indicators = indicator_calculator.calculate(
        stocks,
        ma_period=block1_cond.entry_ma_period or 20,
        exit_ma_period=block1_cond.exit_ma_period,
        volume_months=block1_cond.volume_high_months or 6,
        new_high_months=block1_cond.price_high_months or 2
    )

    # ===================================================================
    # 4. 기존 Block1 로드
    # ===================================================================
    block1_list = block1_repo.find_by_ticker(ticker)
    print(f"분석 대상 Block1: {len(block1_list)}건")
    print()

    # ===================================================================
    # 5. 각 Block1 이후 Block2 조건 충족 여부 분석
    # ===================================================================
    block1_checker = Block1Checker()
    block2_checker = Block2Checker()

    for idx, block1 in enumerate(sorted(block1_list, key=lambda b: b.started_at), 1):
        print(f"[{idx}] Block1: {block1.started_at} ~ {block1.ended_at}")
        print(f"    최고가: {block1.peak_price:,.0f}원 ({block1.peak_date})")
        print(f"    최고 거래량: {block1.entry_volume:,}주")
        print()

        # Block1 종료일 이후부터 검사
        if not block1.ended_at:
            print("    → Block1이 아직 진행 중입니다.")
            print()
            continue

        # Block1 종료일 이후 30일간 검사
        block1_end_idx = None
        for i, stock in enumerate(stocks_with_indicators):
            if stock.date == block1.ended_at:
                block1_end_idx = i
                break

        if block1_end_idx is None:
            print("    → Block1 종료일을 찾을 수 없습니다.")
            print()
            continue

        # Block1 종료일 다음날부터 30일간 검사
        near_misses = []
        for i in range(block1_end_idx + 1, min(block1_end_idx + 31, len(stocks_with_indicators))):
            stock = stocks_with_indicators[i]
            prev_stock = stocks_with_indicators[i - 1] if i > 0 else None

            # Block1 조건 체크
            block1_ok = block1_checker.check_entry(block1_cond, stock, prev_stock)

            # Block2 추가 조건 체크
            volume_ok = False
            price_ok = False

            if block2_cond.block_volume_ratio and block1.entry_volume:
                required_volume = block1.entry_volume * (block2_cond.block_volume_ratio / 100.0)
                volume_ok = stock.volume >= required_volume
                volume_ratio = stock.volume / required_volume if required_volume > 0 else 0
            else:
                volume_ok = True
                volume_ratio = 1.0

            if block2_cond.low_price_margin and block1.peak_price:
                threshold_price = stock.low * (1 + block2_cond.low_price_margin / 100.0)
                price_ok = threshold_price > block1.peak_price
                price_margin = ((threshold_price / block1.peak_price) - 1) * 100 if block1.peak_price > 0 else 0
            else:
                price_ok = True
                price_margin = 0

            # 거의 충족한 경우
            if block1_ok or volume_ok or price_ok:
                near_misses.append({
                    'date': stock.date,
                    'block1_ok': block1_ok,
                    'volume_ok': volume_ok,
                    'volume_ratio': volume_ratio,
                    'price_ok': price_ok,
                    'price_margin': price_margin,
                    'rate': stock.indicators.get('rate', 0) if hasattr(stock, 'indicators') else 0
                })

        if near_misses:
            print(f"    Block1 종료 후 30일 내 조건 분석:")
            for nm in near_misses[:5]:  # 상위 5개만 출력
                print(f"      {nm['date']}: Block1조건={'OK' if nm['block1_ok'] else 'X'}, " +
                      f"거래량={'OK' if nm['volume_ok'] else 'X'}({nm['volume_ratio']:.1f}배), " +
                      f"저가마진={'OK' if nm['price_ok'] else 'X'}({nm['price_margin']:+.1f}%), " +
                      f"등락률={nm['rate']:+.2f}%")
        else:
            print(f"    → Block1 종료 후 30일 내 Block2 조건에 근접한 날이 없습니다.")

        print()

    print("="*70)
    print("진단 완료!")
    print("="*70)


if __name__ == "__main__":
    main()
