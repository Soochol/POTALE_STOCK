"""
DB에 저장된 조건 프리셋을 로드해서 Block1 탐지를 수행하는 스크립트
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.domain.entities.block1_condition import Block1Condition
from src.application.use_cases.detect_block1 import DetectBlock1UseCase
from src.application.services.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.block1_checker import Block1Checker
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.block1_condition_preset_repository import Block1ConditionPresetRepository
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.database.connection import DatabaseConnection


def main(preset_name: str, ticker: str = "025980"):
    """
    DB에 저장된 조건 프리셋으로 Block1 탐지

    Args:
        preset_name: 조건 프리셋 이름 (standard, custom, aggressive 등)
        ticker: 종목코드 (기본값: 025980 아난티)
    """
    print("\n" + "="*70)
    print(f"Block1 Detection - 프리셋: {preset_name}")
    print("="*70 + "\n")

    # DB 연결
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    # Repository 초기화
    preset_repo = Block1ConditionPresetRepository(db_conn)
    stock_repo = SqliteStockRepository(db_path)
    block1_repo = Block1Repository(db_conn)

    # 1. 조건 프리셋 로드
    print(f"[1/4] 조건 프리셋 로드: {preset_name}")

    condition = preset_repo.load(preset_name)

    if not condition:
        print(f"[ERROR] 조건 프리셋을 찾을 수 없습니다: {preset_name}")
        print("\n사용 가능한 프리셋 목록:")
        presets = preset_repo.list_all()
        for p in presets:
            print(f"  - {p.name}")
        return False

    print(f"[OK] 조건 로드 완료")
    print()

    # 조건 출력
    print(f"[조건 상세]")
    print(f"  1. 등락률: {condition.entry_surge_rate}%")
    print(f"  2. MA Period: MA{condition.entry_ma_period}")
    print(f"  3. High Above MA: {condition.high_above_ma}")
    print(f"  4. 이격도: {condition.max_deviation_ratio}%")
    print(f"  5. 거래대금: {condition.min_trading_value}억")
    print(f"  6. 거래량: {condition.volume_high_months}개월 신고")
    print(f"  7. 전날 거래량: {condition.volume_spike_ratio}%")
    print(f"  8. 신고가: {condition.price_high_months}개월")
    print(f"  9. Exit MA: MA{condition.exit_ma_period}")
    print(f"  10. Cooldown: {condition.cooldown_days}일")
    print()

    # 2. 데이터 로드
    print(f"[2/4] 주가 데이터 로드: {ticker}")

    start_date = date(2015, 1, 2)
    end_date = date(2025, 10, 17)
    stocks = stock_repo.get_stock_data(ticker, start_date, end_date)

    if not stocks:
        print(f"[ERROR] {ticker} 데이터가 없습니다.")
        return False

    print(f"[OK] 데이터 로드: {len(stocks)}건")
    print(f"    기간: {stocks[0].date} ~ {stocks[-1].date}")
    print()

    # 3. Block1 탐지 실행
    print("[3/4] Block1 탐지 실행...")

    use_case = DetectBlock1UseCase(
        repository=block1_repo,
        indicator_calculator=Block1IndicatorCalculator(),
        checker=Block1Checker()
    )

    try:
        detections = use_case.execute(
            condition=condition,
            condition_name=preset_name,
            stocks=stocks
        )

        print(f"[OK] 탐지 완료: {len(detections)}건 발견")
        print()

    except Exception as e:
        print(f"[ERROR] 탐지 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 탐지 결과 출력
    if detections:
        print("[4/4] 탐지 결과:")
        print("-" * 70)

        for i, detection in enumerate(detections[:20], 1):
            print(f"\n[Block1 #{i}]")
            print(f"  시작일: {detection.started_at}")
            print(f"  종료일: {detection.ended_at if detection.ended_at else '진행중'}")
            print(f"  상태: {detection.status}")
            print(f"  진입가: {detection.entry_close:,.0f}원")

            if detection.peak_price:
                print(f"  최고가: {detection.peak_price:,.0f}원 ({detection.peak_date})")
                gain = detection.peak_gain_ratio
                if gain:
                    print(f"  수익률: +{gain:.2f}%")

            if detection.exit_reason:
                print(f"  종료사유: {detection.exit_reason}")

            if detection.duration_days:
                print(f"  지속기간: {detection.duration_days}일")

        if len(detections) > 20:
            print(f"\n... 외 {len(detections) - 20}건")

        print("-" * 70)
        print()
    else:
        print("[4/4] 탐지 결과: 없음")
        print()

    # 통계
    print("="*70)
    print("[SUMMARY]")
    print(f"  프리셋: {preset_name}")
    print(f"  총 탐지 건수: {len(detections)}건")

    if detections:
        # 지속 기간
        durations = [d.duration_days for d in detections if d.duration_days]
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            print(f"  평균 지속기간: {avg_duration:.1f}일")
            print(f"  최대 지속기간: {max_duration}일")
            print(f"  최소 지속기간: {min_duration}일")

        # 수익률
        gains = [d.peak_gain_ratio for d in detections if d.peak_gain_ratio]
        if gains:
            avg_gain = sum(gains) / len(gains)
            max_gain = max(gains)
            min_gain = min(gains)
            print(f"  평균 수익률: +{avg_gain:.2f}%")
            print(f"  최대 수익률: +{max_gain:.2f}%")
            print(f"  최소 수익률: +{min_gain:.2f}%")

    print("="*70 + "\n")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        preset_name = sys.argv[1]
    else:
        preset_name = "custom"  # 기본값

    if len(sys.argv) > 2:
        ticker = sys.argv[2]
    else:
        ticker = "025980"  # 기본값

    success = main(preset_name, ticker)
    sys.exit(0 if success else 1)
