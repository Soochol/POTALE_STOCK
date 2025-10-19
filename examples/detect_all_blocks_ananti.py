"""
아난티(025980) 종목으로 Block1/2/3 전체 탐지 테스트

2015-2025 데이터로 블록1, 블록2, 블록3를 모두 탐지하여 결과 출력
"""
import sys
from pathlib import Path
from datetime import date

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.block2_repository import Block2Repository
from src.infrastructure.repositories.block3_repository import Block3Repository

from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from src.domain.entities.block2_condition import Block2Condition
from src.domain.entities.block3_condition import Block3Condition

from src.application.use_cases.detect_block1 import DetectBlock1UseCase
from src.application.use_cases.detect_block2 import DetectBlock2UseCase
from src.application.use_cases.detect_block3 import DetectBlock3UseCase


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("Block1/2/3 전체 탐지 테스트 - 아난티(025980)")
    print("=" * 80)
    print()

    # 1. DB 연결
    db_path = project_root / "stock_data.db"
    db_connection = DatabaseConnection(str(db_path))

    # 2. Repository 초기화
    stock_repo = SqliteStockRepository(db_connection)
    block1_repo = Block1Repository(db_connection)
    block2_repo = Block2Repository(db_connection)
    block3_repo = Block3Repository(db_connection)

    # 3. UseCase 초기화
    detect_block1 = DetectBlock1UseCase(block1_repo)
    detect_block2 = DetectBlock2UseCase(block2_repo, block1_repo)
    detect_block3 = DetectBlock3UseCase(block3_repo, block2_repo, block1_repo)

    # 4. 조건 설정
    # Block1 조건 (기본)
    block1_condition = Block1Condition(
        rate_threshold=8.0,                     # 고가 기준 등락률 8% 이상
        ma_period=120,                          # 진입: MA120
        high_above_ma=True,                     # 고가 >= MA120
        deviation_threshold=120.0,              # 이격도 120 이하 (MA를 100으로 봤을 때)
        trading_value_threshold=300.0,          # 거래대금 300억원 이상
        volume_months=24,                       # 24개월 신고거래량
        prev_day_volume_increase_ratio=400,     # 전날 거래량 대비 400% (4배, 필수)
        new_high_months=2,                      # 2개월 신고가 (필수)
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=60,                      # 종료: 종가 < MA60
        cooldown_days=120
    )

    # Block2 조건 (Block1 + 추가 조건)
    block2_condition = Block2Condition(
        block1_condition=block1_condition,
        block_volume_ratio=15,                  # 블록1 최고 거래량의 15%
        low_price_margin=10,                    # 저가 마진 10%
        min_candles_after_block1=4              # 블록1 시작 후 최소 4캔들 (5번째부터 블록2 가능)
    )

    # Block3 조건 (Block2 + 추가 조건)
    block3_condition = Block3Condition(
        block2_condition=block2_condition,
        block_volume_ratio=15,                  # 블록2 최고 거래량의 15%
        low_price_margin=10,                    # 저가 마진 10%
        min_candles_after_block2=4              # 블록2 시작 후 최소 4캔들 (5번째부터 블록3 가능)
    )

    # 5. 데이터 로드
    ticker = "025980"  # 아난티
    from_date = date(2015, 1, 1)
    to_date = date(2025, 12, 31)

    print(f"종목: {ticker} (아난티)")
    print(f"기간: {from_date} ~ {to_date}")
    print()

    stocks = stock_repo.get_stock_data(ticker, from_date, to_date)
    print(f"✓ 로드된 데이터: {len(stocks)}개 레코드")
    print()

    if not stocks:
        print("❌ 데이터가 없습니다. 먼저 데이터를 수집하세요.")
        return

    # 6. Block1 탐지
    print("-" * 80)
    print("📊 Block1 탐지 시작...")
    print("-" * 80)

    block1_detections = detect_block1.execute(
        condition=block1_condition,
        condition_name="아난티_2015-2025_Block1",
        stocks=stocks
    )

    print(f"✓ Block1 탐지 완료: {len(block1_detections)}개 발견")
    print()

    # Block1 결과 출력
    if block1_detections:
        print("Block1 상세 결과:")
        print("-" * 80)
        for i, detection in enumerate(block1_detections, 1):
            duration = (detection.ended_at - detection.started_at).days + 1 if detection.ended_at else "진행중"
            peak_gain = ((detection.peak_price - detection.entry_close) / detection.entry_close * 100) if detection.peak_price else 0

            print(f"{i}. {detection.started_at} ~ {detection.ended_at or '진행중'}")
            print(f"   진입가: {detection.entry_close:,.0f}원 | 최고가: {detection.peak_price:,.0f}원 ({detection.peak_date})")
            print(f"   최고 수익률: {peak_gain:.2f}% | 기간: {duration}일")
            print(f"   종료 사유: {detection.exit_reason or 'N/A'}")
            print()
    print()

    # 7. Block2 탐지
    print("-" * 80)
    print("📊 Block2 탐지 시작...")
    print("-" * 80)

    block2_detections = detect_block2.execute(
        condition=block2_condition,
        condition_name="아난티_2015-2025_Block2",
        stocks=stocks
    )

    print(f"✓ Block2 탐지 완료: {len(block2_detections)}개 발견")
    print()

    # Block2 결과 출력
    if block2_detections:
        print("Block2 상세 결과:")
        print("-" * 80)
        for i, detection in enumerate(block2_detections, 1):
            duration = detection.duration_days or "진행중"

            print(f"{i}. {detection.started_at} ~ {detection.ended_at or '진행중'}")
            print(f"   진입가: {detection.entry_close:,.0f}원 | 최고가: {detection.peak_price:,.0f}원 ({detection.peak_date})")
            print(f"   최고 수익률: {detection.peak_gain_ratio:.2f}% | 기간: {duration}일")
            print(f"   직전 Block1 ID: {detection.prev_block1_id}")
            print(f"   종료 사유: {detection.exit_reason or 'N/A'}")
            print()
    print()

    # 8. Block3 탐지
    print("-" * 80)
    print("📊 Block3 탐지 시작...")
    print("-" * 80)

    block3_detections = detect_block3.execute(
        condition=block3_condition,
        condition_name="아난티_2015-2025_Block3",
        stocks=stocks
    )

    print(f"✓ Block3 탐지 완료: {len(block3_detections)}개 발견")
    print()

    # Block3 결과 출력
    if block3_detections:
        print("Block3 상세 결과:")
        print("-" * 80)
        for i, detection in enumerate(block3_detections, 1):
            duration = detection.duration_days or "진행중"

            print(f"{i}. {detection.started_at} ~ {detection.ended_at or '진행중'}")
            print(f"   진입가: {detection.entry_close:,.0f}원 | 최고가: {detection.peak_price:,.0f}원 ({detection.peak_date})")
            print(f"   최고 수익률: {detection.peak_gain_ratio:.2f}% | 기간: {duration}일")
            print(f"   직전 Block2 ID: {detection.prev_block2_id}")
            print(f"   종료 사유: {detection.exit_reason or 'N/A'}")
            print()
    print()

    # 9. 전체 요약
    print("=" * 80)
    print("📈 전체 탐지 결과 요약")
    print("=" * 80)
    print(f"Block1: {len(block1_detections)}개")
    print(f"Block2: {len(block2_detections)}개")
    print(f"Block3: {len(block3_detections)}개")
    print()

    # Block1 통계
    if block1_detections:
        completed_block1s = [d for d in block1_detections if d.status == "completed"]
        if completed_block1s:
            avg_duration = sum((d.ended_at - d.started_at).days + 1 for d in completed_block1s) / len(completed_block1s)
            avg_gain = sum(((d.peak_price - d.entry_close) / d.entry_close * 100) for d in completed_block1s if d.peak_price) / len(completed_block1s)
            max_gain = max(((d.peak_price - d.entry_close) / d.entry_close * 100) for d in completed_block1s if d.peak_price)

            print(f"Block1 평균 기간: {avg_duration:.1f}일")
            print(f"Block1 평균 수익률: {avg_gain:.2f}%")
            print(f"Block1 최고 수익률: {max_gain:.2f}%")
            print()

    # Block2 통계
    if block2_detections:
        completed_block2s = [d for d in block2_detections if d.status == "completed"]
        if completed_block2s:
            avg_duration = sum(d.duration_days for d in completed_block2s) / len(completed_block2s)
            avg_gain = sum(d.peak_gain_ratio for d in completed_block2s if d.peak_gain_ratio) / len(completed_block2s)
            max_gain = max(d.peak_gain_ratio for d in completed_block2s if d.peak_gain_ratio)

            print(f"Block2 평균 기간: {avg_duration:.1f}일")
            print(f"Block2 평균 수익률: {avg_gain:.2f}%")
            print(f"Block2 최고 수익률: {max_gain:.2f}%")
            print()

    # Block3 통계
    if block3_detections:
        completed_block3s = [d for d in block3_detections if d.status == "completed"]
        if completed_block3s:
            avg_duration = sum(d.duration_days for d in completed_block3s) / len(completed_block3s)
            avg_gain = sum(d.peak_gain_ratio for d in completed_block3s if d.peak_gain_ratio) / len(completed_block3s)
            max_gain = max(d.peak_gain_ratio for d in completed_block3s if d.peak_gain_ratio)

            print(f"Block3 평균 기간: {avg_duration:.1f}일")
            print(f"Block3 평균 수익률: {avg_gain:.2f}%")
            print(f"Block3 최고 수익률: {max_gain:.2f}%")
            print()

    print("=" * 80)
    print("✅ 탐지 완료")
    print("=" * 80)


if __name__ == "__main__":
    main()
