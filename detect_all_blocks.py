"""
Block1/2/3 통합 탐지 스크립트

Block1 → Block2 → Block3 Chain 구조로 통합 탐지합니다.

실행 방법:
    python detect_all_blocks.py
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.application.use_cases.detect_blocks_integrated import DetectBlocksIntegratedUseCase
from src.infrastructure.repositories.block1_condition_preset_repository import Block1ConditionPresetRepository
from src.infrastructure.repositories.block2_condition_preset_repository import Block2ConditionPresetRepository
from src.infrastructure.repositories.block3_condition_preset_repository import Block3ConditionPresetRepository
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.block2_repository import Block2Repository
from src.infrastructure.repositories.block3_repository import Block3Repository
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.database.connection import DatabaseConnection


def main():
    """메인 함수"""
    print("="*70)
    print("Block1/2/3 통합 탐지 시작")
    print("="*70)
    print()

    # ===================================================================
    # 1. DB 연결 및 Repository 초기화
    # ===================================================================
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    block1_preset_repo = Block1ConditionPresetRepository(db_conn)
    block2_preset_repo = Block2ConditionPresetRepository(db_conn)
    block3_preset_repo = Block3ConditionPresetRepository(db_conn)
    stock_repo = SqliteStockRepository(db_path)
    block1_repo = Block1Repository(db_conn)
    block2_repo = Block2Repository(db_conn)
    block3_repo = Block3Repository(db_conn)

    print("[1/6] Repository 초기화 완료")
    print()

    # ===================================================================
    # 2. 프리셋 이름 지정
    # ===================================================================
    preset_name = "custom"  # "standard", "custom", "aggressive" 중 선택
    print(f"[2/6] 사용할 프리셋: {preset_name}")
    print()

    # ===================================================================
    # 3. Block1 조건 로드
    # ===================================================================
    block1_cond = block1_preset_repo.load(preset_name)

    if not block1_cond:
        print(f"[ERROR] Block1 프리셋 '{preset_name}'을 찾을 수 없습니다.")
        print("먼저 'python save_all_conditions.py'를 실행하세요.")
        return

    print(f"[3/6] Block1 조건 로드 완료: {preset_name}")
    print(f"  - entry_surge_rate: {block1_cond.entry_surge_rate}%")
    print(f"  - entry_ma_period: {block1_cond.entry_ma_period}일")
    print(f"  - max_deviation_ratio: {block1_cond.max_deviation_ratio}%")
    print(f"  - min_trading_value: {block1_cond.min_trading_value}억")
    print(f"  - volume_high_months: {block1_cond.volume_high_months}개월")
    print(f"  - volume_spike_ratio: {block1_cond.volume_spike_ratio}%")
    print(f"  - price_high_months: {block1_cond.price_high_months}개월")
    print(f"  - exit_ma_period: {block1_cond.exit_ma_period}일")
    print(f"  - cooldown_days: {block1_cond.cooldown_days}일")
    print()

    # ===================================================================
    # 4. Block2 조건 로드
    # ===================================================================
    block2_cond = block2_preset_repo.load(preset_name)

    if not block2_cond:
        print(f"[ERROR] Block2 프리셋 '{preset_name}'을 찾을 수 없습니다.")
        print("먼저 'python save_all_conditions.py'를 실행하세요.")
        return

    print(f"[4/6] Block2 조건 로드 완료: {preset_name}")
    print(f"  - block_volume_ratio: {block2_cond.block_volume_ratio}%")
    print(f"  - low_price_margin: {block2_cond.low_price_margin}%")
    print(f"  - cooldown_days: {block2_cond.cooldown_days}일")
    print(f"  - min_candles_after_block1: {block2_cond.min_candles_after_block1}캔들")
    print()

    # ===================================================================
    # 5. Block3 조건 로드
    # ===================================================================
    block3_cond = block3_preset_repo.load(preset_name)

    if not block3_cond:
        print(f"[ERROR] Block3 프리셋 '{preset_name}'을 찾을 수 없습니다.")
        print("먼저 'python save_all_conditions.py'를 실행하세요.")
        return

    print(f"[5/6] Block3 조건 로드 완료: {preset_name}")
    print(f"  - block_volume_ratio: {block3_cond.block_volume_ratio}%")
    print(f"  - low_price_margin: {block3_cond.low_price_margin}%")
    print(f"  - min_candles_after_block2: {block3_cond.min_candles_after_block2}캔들")
    print()

    # ===================================================================
    # 6. 주가 데이터 로드
    # ===================================================================
    ticker = "025980"  # 아난티
    start_date = date(2015, 1, 2)
    end_date = date(2025, 10, 17)

    stocks = stock_repo.get_stock_data(ticker, start_date, end_date)

    print(f"[6/7] 주가 데이터 로드 완료: {ticker}")
    print(f"  - 데이터 건수: {len(stocks)}건")
    print(f"  - 기간: {stocks[0].date} ~ {stocks[-1].date}")
    print(f"  - 일수: {(stocks[-1].date - stocks[0].date).days}일")
    print()

    # ===================================================================
    # 7. 통합 탐지 실행
    # ===================================================================
    print("[7/7] 통합 탐지 실행 중...")
    print()

    use_case = DetectBlocksIntegratedUseCase(
        block1_repo=block1_repo,
        block2_repo=block2_repo,
        block3_repo=block3_repo
    )

    block1_list, block2_list, block3_list = use_case.execute(
        block1_condition=block1_cond,
        block2_condition=block2_cond,
        block3_condition=block3_cond,
        condition_name=preset_name,
        stocks=stocks
    )

    # ===================================================================
    # 7. 결과 출력
    # ===================================================================
    print("="*70)
    print("통합 탐지 결과")
    print("="*70)
    print()

    print(f"Block1: {len(block1_list)}건")
    print(f"Block2: {len(block2_list)}건")
    print(f"Block3: {len(block3_list)}건")
    print()

    if not block1_list:
        print("탐지된 블록이 없습니다.")
        return

    # ===================================================================
    # 8. Chain 출력
    # ===================================================================
    print("="*70)
    print("Chain 구조 (Block1 → Block2 → Block3)")
    print("="*70)
    print()

    for idx, block1 in enumerate(sorted(block1_list, key=lambda b: b.started_at), 1):
        # Block1 정보
        gain_str = f"+{block1.peak_gain_ratio:.2f}%" if block1.peak_gain_ratio else "N/A"
        duration_str = f"{block1.duration_days}일" if block1.duration_days else "진행중"

        print(f"[{idx}] Block1 #{block1.block1_id[:8]}...")
        print(f"    시작: {block1.started_at} | 종료: {block1.ended_at or '진행중'} ({duration_str})")
        print(f"    진입가: {block1.entry_close:,.0f}원 | 최고가: {block1.peak_price:,.0f}원" if block1.peak_price else "")
        print(f"    수익률: {gain_str} | 종료사유: {block1.exit_reason or '-'}")

        # 연결된 Block2 찾기
        block2 = None
        for b2 in block2_list:
            # block1의 DB ID와 block2의 prev_block1_id 비교
            # (주의: block1.id는 DB auto increment ID이지만, 여기서는 block1_id UUID를 사용)
            # Repository에서 저장 시 ID가 설정되므로, 실제로는 UUID가 아닌 DB ID로 비교해야 함
            # 하지만 현재 Block1Detection에는 id 필드가 없음 → 개선 필요
            # 임시로 시작일로 추론
            if b2.prev_block1_id and b2.started_at > block1.started_at:
                # 정확한 매칭을 위해서는 Block1Repository.save()가 반환하는 객체에 id가 포함되어야 함
                # 현재는 근사치로 판단
                potential_block1_end = block1.ended_at or block1.started_at
                if b2.started_at <= potential_block1_end + date.resolution * 10:  # 10일 이내
                    block2 = b2
                    break

        if block2:
            b2_gain_str = f"+{block2.peak_gain_ratio:.2f}%" if block2.peak_gain_ratio else "N/A"
            b2_duration_str = f"{block2.duration_days}일" if block2.duration_days else "진행중"

            print(f"    └─ Block2 #{block2.block2_id[:8]}...")
            print(f"         시작: {block2.started_at} | 종료: {block2.ended_at or '진행중'} ({b2_duration_str})")
            print(f"         진입가: {block2.entry_close:,.0f}원 | 최고가: {block2.peak_price:,.0f}원" if block2.peak_price else "")
            print(f"         수익률: {b2_gain_str} | 종료사유: {block2.exit_reason or '-'}")

            # 연결된 Block3 찾기
            block3 = None
            for b3 in block3_list:
                if b3.prev_block2_id and b3.started_at > block2.started_at:
                    potential_block2_end = block2.ended_at or block2.started_at
                    if b3.started_at <= potential_block2_end + date.resolution * 10:
                        block3 = b3
                        break

            if block3:
                b3_gain_str = f"+{block3.peak_gain_ratio:.2f}%" if block3.peak_gain_ratio else "N/A"
                b3_duration_str = f"{block3.duration_days}일" if block3.duration_days else "진행중"

                print(f"         └─ Block3 #{block3.block3_id[:8]}...")
                print(f"              시작: {block3.started_at} | 종료: {block3.ended_at or '진행중'} ({b3_duration_str})")
                print(f"              진입가: {block3.entry_close:,.0f}원 | 최고가: {block3.peak_price:,.0f}원" if block3.peak_price else "")
                print(f"              수익률: {b3_gain_str} | 종료사유: {block3.exit_reason or '-'}")

        print()

    # ===================================================================
    # 9. 통계 출력
    # ===================================================================
    print("="*70)
    print("통계")
    print("="*70)
    print()

    # Block1 통계
    if block1_list:
        completed_b1 = [b for b in block1_list if b.status == "completed"]
        active_b1 = [b for b in block1_list if b.status == "active"]

        print(f"Block1 통계:")
        print(f"  - 전체: {len(block1_list)}건")
        print(f"  - 진행중: {len(active_b1)}건")
        print(f"  - 완료: {len(completed_b1)}건")

        if completed_b1:
            gains = [b.peak_gain_ratio for b in completed_b1 if b.peak_gain_ratio]
            if gains:
                print(f"  - 평균 수익률: +{sum(gains)/len(gains):.2f}%")
                print(f"  - 최고 수익률: +{max(gains):.2f}%")
                print(f"  - 최저 수익률: +{min(gains):.2f}%")
        print()

    # Block2 통계
    if block2_list:
        completed_b2 = [b for b in block2_list if b.status == "completed"]
        active_b2 = [b for b in block2_list if b.status == "active"]

        print(f"Block2 통계:")
        print(f"  - 전체: {len(block2_list)}건")
        print(f"  - 진행중: {len(active_b2)}건")
        print(f"  - 완료: {len(completed_b2)}건")

        if completed_b2:
            gains = [b.peak_gain_ratio for b in completed_b2 if b.peak_gain_ratio]
            if gains:
                print(f"  - 평균 수익률: +{sum(gains)/len(gains):.2f}%")
                print(f"  - 최고 수익률: +{max(gains):.2f}%")
                print(f"  - 최저 수익률: +{min(gains):.2f}%")
        print()

    # Block3 통계
    if block3_list:
        completed_b3 = [b for b in block3_list if b.status == "completed"]
        active_b3 = [b for b in block3_list if b.status == "active"]

        print(f"Block3 통계:")
        print(f"  - 전체: {len(block3_list)}건")
        print(f"  - 진행중: {len(active_b3)}건")
        print(f"  - 완료: {len(completed_b3)}건")

        if completed_b3:
            gains = [b.peak_gain_ratio for b in completed_b3 if b.peak_gain_ratio]
            if gains:
                print(f"  - 평균 수익률: +{sum(gains)/len(gains):.2f}%")
                print(f"  - 최고 수익률: +{max(gains):.2f}%")
                print(f"  - 최저 수익률: +{min(gains):.2f}%")
        print()

    print("="*70)
    print("완료!")
    print("="*70)


if __name__ == "__main__":
    main()
