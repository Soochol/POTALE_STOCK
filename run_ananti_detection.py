"""
아난티(025980) 패턴 탐지 실행 스크립트
2015-01-01 ~ 현재까지 Block1/2/3/4 Seed + 재탐지
"""
import sys
import os
from pathlib import Path
from datetime import date

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.preset.seed_condition_preset_repository import SeedConditionPresetRepository
from src.infrastructure.repositories.preset.redetection_condition_preset_repository import RedetectionConditionPresetRepository
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block3_repository import Block3Repository
from src.application.use_cases.pattern_detection.detect_patterns import DetectPatternsUseCase


def main():
    print("=" * 80)
    print("아난티(025980) 패턴 탐지")
    print("=" * 80)

    # 1. DB 연결
    db_path = "data/database/stock_data.db"
    db = DatabaseConnection(db_path)

    # 2. Repository 초기화
    stock_repo = SqliteStockRepository(db_path)
    block1_repo = Block1Repository(db)
    block2_repo = Block2Repository(db)
    block3_repo = Block3Repository(db)

    # 3. 데이터 로드
    ticker = "025980"  # 아난티
    start_date = date(2015, 1, 1)
    end_date = date.today()

    print(f"\n데이터 로드 중...")
    print(f"  종목: {ticker} (아난티)")
    print(f"  기간: {start_date} ~ {end_date}")

    stocks = stock_repo.get_stock_data(ticker, start_date, end_date)
    print(f"  로드 완료: {len(stocks)}건\n")

    if not stocks:
        print("[!] 데이터가 없습니다.")
        return

    # 4. Preset 로드
    print("Preset 로드 중...")
    seed_repo = SeedConditionPresetRepository(db)
    redetect_repo = RedetectionConditionPresetRepository(db)

    seed_condition = seed_repo.load('default_seed')
    redetect_condition = redetect_repo.load('default_redetect')

    if not seed_condition or not redetect_condition:
        print("[!] Preset을 찾을 수 없습니다.")
        return

    print("  Seed 조건 로드 완료")
    print("  재탐지 조건 로드 완료\n")

    # 5. 패턴 탐지 실행
    print("패턴 탐지 실행 중...")
    print("  (Block1/2/3/4 Seed + 5년 재탐지)\n")

    use_case = DetectPatternsUseCase(db)
    result = use_case.execute(
        ticker=ticker,
        stocks=stocks,
        seed_condition=seed_condition,
        redetection_condition=redetect_condition
    )

    # 6. 결과 출력
    print("\n" + "=" * 80)
    print("탐지 결과")
    print("=" * 80)

    patterns = result.get('patterns', [])

    if not patterns:
        print("\n[!] 탐지된 패턴이 없습니다.")
        return

    print(f"\n총 {len(patterns)}개의 패턴 발견\n")

    # 각 패턴 출력
    for idx, pattern in enumerate(patterns, 1):
        print("=" * 80)
        print(f"Pattern #{idx}")
        print("=" * 80)

        # Block1 Seed
        block1_seed = pattern.get('seed_block1')
        if block1_seed:
            print(f"\n[Block1 Seed]")
            print(f"  시작: {block1_seed.started_at}")
            print(f"  종료: {block1_seed.ended_at if block1_seed.ended_at else '진행중'}")
            print(f"  진입가: {block1_seed.entry_close:,.0f}원")
            if hasattr(block1_seed, 'peak_price') and block1_seed.peak_price:
                print(f"  최고가: {block1_seed.peak_price:,.0f}원")
                gain = (block1_seed.peak_price - block1_seed.entry_close) / block1_seed.entry_close * 100
                print(f"  수익률: {gain:+.2f}%")

        # Block1 재탐지 (DB에서 조회)
        pattern_id = pattern.get('pattern_id')
        block1_redetections = block1_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
        print(f"\n  Block1 재탐지: {len(block1_redetections)}개")

        # Block2 Seed
        block2_seed = pattern.get('seed_block2')
        if block2_seed:
            print(f"\n[Block2 Seed]")
            print(f"  시작: {block2_seed.started_at}")
            print(f"  종료: {block2_seed.ended_at if block2_seed.ended_at else '진행중'}")
            print(f"  진입가: {block2_seed.entry_close:,.0f}원")
            if hasattr(block2_seed, 'peak_price') and block2_seed.peak_price:
                print(f"  최고가: {block2_seed.peak_price:,.0f}원")
                gain = (block2_seed.peak_price - block2_seed.entry_close) / block2_seed.entry_close * 100
                print(f"  수익률: {gain:+.2f}%")

        # Block2 재탐지 (DB에서 조회)
        block2_redetections = block2_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
        print(f"\n  Block2 재탐지: {len(block2_redetections)}개")

        # Block3 Seed
        block3_seed = pattern.get('seed_block3')
        if block3_seed:
            print(f"\n[Block3 Seed]")
            print(f"  시작: {block3_seed.started_at}")
            print(f"  종료: {block3_seed.ended_at if block3_seed.ended_at else '진행중'}")
            print(f"  진입가: {block3_seed.entry_close:,.0f}원")
            if hasattr(block3_seed, 'peak_price') and block3_seed.peak_price:
                print(f"  최고가: {block3_seed.peak_price:,.0f}원")
                gain = (block3_seed.peak_price - block3_seed.entry_close) / block3_seed.entry_close * 100
                print(f"  수익률: {gain:+.2f}%")

        # Block3 재탐지 (DB에서 조회)
        block3_redetections = block3_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
        print(f"\n  Block3 재탐지: {len(block3_redetections)}개")

        # Block4 Seed (있으면)
        block4_seed = pattern.get('seed_block4')
        if block4_seed:
            print(f"\n[Block4 Seed]")
            print(f"  시작: {block4_seed.started_at}")
            print(f"  종료: {block4_seed.ended_at if block4_seed.ended_at else '진행중'}")
            print(f"  진입가: {block4_seed.entry_close:,.0f}원")
            if hasattr(block4_seed, 'peak_price') and block4_seed.peak_price:
                print(f"  최고가: {block4_seed.peak_price:,.0f}원")
                gain = (block4_seed.peak_price - block4_seed.entry_close) / block4_seed.entry_close * 100
                print(f"  수익률: {gain:+.2f}%")

            # Block4 재탐지
            block4_redetections = pattern.get('block4_redetections', [])
            print(f"\n  Block4 재탐지: {len(block4_redetections)}개")

        print()

    # 통계
    total_stats = result.get('total_stats', {})
    print("=" * 80)
    print("통계 요약")
    print("=" * 80)
    print(f"\n총 패턴 수: {len(patterns)}개")
    print(f"Block1 재탐지 총합: {total_stats.get('block1_redetections', 0)}개")
    print(f"Block2 재탐지 총합: {total_stats.get('block2_redetections', 0)}개")
    print(f"Block3 재탐지 총합: {total_stats.get('block3_redetections', 0)}개")
    print(f"Block4 재탐지 총합: {total_stats.get('block4_redetections', 0)}개")

    print("\n" + "=" * 80)
    print("완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
