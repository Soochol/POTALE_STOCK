"""
Block1/2/3 조건 프리셋 저장 스크립트

Block1, Block2, Block3 조건을 DB에 저장합니다.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from src.domain.entities.block2_condition import Block2Condition
from src.domain.entities.block3_condition import Block3Condition
from src.infrastructure.repositories.block1_condition_preset_repository import Block1ConditionPresetRepository
from src.infrastructure.repositories.block2_condition_preset_repository import Block2ConditionPresetRepository
from src.infrastructure.repositories.block3_condition_preset_repository import Block3ConditionPresetRepository
from src.infrastructure.database.connection import DatabaseConnection


def save_standard_conditions():
    """Standard 조건 저장 (엄격한 조건)"""
    print("[1/3] Standard 조건 저장 중...")

    # Block1 Standard 조건
    block1_cond = Block1Condition(
        entry_surge_rate=10.0,
        entry_ma_period=20,
        max_deviation_ratio=120.0,
        min_trading_value=100.0,
        volume_high_months=6,
        volume_spike_ratio=400.0,
        price_high_months=2,
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=60,
        cooldown_days=120
    )

    block1_preset_name = block1_preset_repo.save(
        name="standard",
        condition=block1_cond,
        description="표준 조건 (엄격): 10% 급등, 6개월 신고거래량, 400% 거래량 급증"
    )
    print(f"  [OK] Block1 Standard 저장 완료: {block1_preset_name}")

    # Block2 Standard 조건
    block2_cond = Block2Condition(
        block1_condition=block1_cond,
        block_volume_ratio=20.0,
        low_price_margin=15.0,
        cooldown_days=60,
        min_candles_after_block1=5
    )

    block2_preset_name = block2_preset_repo.save(
        name="standard",
        condition=block2_cond,
        block1_preset_name="standard",
        description="표준 조건: Block1 거래량 20%, 저가 마진 15%"
    )
    print(f"  [OK] Block2 Standard 저장 완료: {block2_preset_name}")

    # Block3 Standard 조건
    block3_cond = Block3Condition(
        block2_condition=block2_cond,
        block_volume_ratio=20.0,
        low_price_margin=15.0,
        min_candles_after_block2=5
    )

    block3_preset_name = block3_preset_repo.save(
        name="standard",
        condition=block3_cond,
        block2_preset_name="standard",
        description="표준 조건: Block2 거래량 20%, 저가 마진 15%"
    )
    print(f"  [OK] Block3 Standard 저장 완료: {block3_preset_name}")
    print()


def save_custom_conditions():
    """Custom 조건 저장 (완화된 조건)"""
    print("[2/3] Custom 조건 저장 중...")

    # Block1 Custom 조건
    block1_cond = Block1Condition(
        entry_surge_rate=8.0,
        entry_ma_period=120,
        max_deviation_ratio=150.0,
        min_trading_value=300.0,
        volume_high_months=12,
        volume_spike_ratio=300.0,
        price_high_months=1,
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=60,
        cooldown_days=20
    )

    block1_preset_name = block1_preset_repo.save(
        name="custom",
        condition=block1_cond,
        description="커스텀 조건 (완화): 8% 급등, 12개월 신고거래량, 300% 거래량 급증"
    )
    print(f"  [OK] Block1 Custom 저장 완료: {block1_preset_name}")

    # Block2 Custom 조건
    block2_cond = Block2Condition(
        block1_condition=block1_cond,
        block_volume_ratio=15.0,
        low_price_margin=10.0,
        cooldown_days=20,
        min_candles_after_block1=4
    )

    block2_preset_name = block2_preset_repo.save(
        name="custom",
        condition=block2_cond,
        block1_preset_name="custom",
        description="커스텀 조건: Block1 거래량 15%, 저가 마진 10%"
    )
    print(f"  [OK] Block2 Custom 저장 완료: {block2_preset_name}")

    # Block3 Custom 조건
    block3_cond = Block3Condition(
        block2_condition=block2_cond,
        block_volume_ratio=15.0,
        low_price_margin=10.0,
        min_candles_after_block2=4
    )

    block3_preset_name = block3_preset_repo.save(
        name="custom",
        condition=block3_cond,
        block2_preset_name="custom",
        description="커스텀 조건: Block2 거래량 15%, 저가 마진 10%"
    )
    print(f"  [OK] Block3 Custom 저장 완료: {block3_preset_name}")
    print()


def save_aggressive_conditions():
    """Aggressive 조건 저장 (매우 완화된 조건)"""
    print("[3/3] Aggressive 조건 저장 중...")

    # Block1 Aggressive 조건
    block1_cond = Block1Condition(
        entry_surge_rate=5.0,
        entry_ma_period=60,
        max_deviation_ratio=200.0,
        min_trading_value=50.0,
        volume_high_months=3,
        volume_spike_ratio=150.0,
        price_high_months=1,
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=20,
        cooldown_days=10
    )

    block1_preset_name = block1_preset_repo.save(
        name="aggressive",
        condition=block1_cond,
        description="공격적 조건 (완화): 5% 급등, 3개월 신고거래량, 150% 거래량 급증"
    )
    print(f"  [OK] Block1 Aggressive 저장 완료: {block1_preset_name}")

    # Block2 Aggressive 조건
    block2_cond = Block2Condition(
        block1_condition=block1_cond,
        block_volume_ratio=10.0,
        low_price_margin=-20.0,  # Block1 최고가의 80%까지 허용
        cooldown_days=10,
        min_candles_after_block1=2
    )

    block2_preset_name = block2_preset_repo.save(
        name="aggressive",
        condition=block2_cond,
        block1_preset_name="aggressive",
        description="공격적 조건: Block1 거래량 10%, 저가 마진 -20% (Block1 최고가의 80%)"
    )
    print(f"  [OK] Block2 Aggressive 저장 완료: {block2_preset_name}")

    # Block3 Aggressive 조건
    block3_cond = Block3Condition(
        block2_condition=block2_cond,
        block_volume_ratio=10.0,
        low_price_margin=-20.0,
        min_candles_after_block2=2
    )

    block3_preset_name = block3_preset_repo.save(
        name="aggressive",
        condition=block3_cond,
        block2_preset_name="aggressive",
        description="공격적 조건: Block2 거래량 10%, 저가 마진 -20%"
    )
    print(f"  [OK] Block3 Aggressive 저장 완료: {block3_preset_name}")
    print()


def main():
    """메인 함수"""
    global block1_preset_repo, block2_preset_repo, block3_preset_repo

    print("="*70)
    print("Block1/2/3 조건 프리셋 저장")
    print("="*70)
    print()

    # DB 연결
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    # 테이블 생성 (없으면 생성)
    db_conn.create_tables()

    # Repository 초기화
    block1_preset_repo = Block1ConditionPresetRepository(db_conn)
    block2_preset_repo = Block2ConditionPresetRepository(db_conn)
    block3_preset_repo = Block3ConditionPresetRepository(db_conn)

    print("Repository 초기화 완료")
    print()

    # 조건 저장
    try:
        save_standard_conditions()
        save_custom_conditions()
        save_aggressive_conditions()

        print("="*70)
        print("모든 조건 저장 완료!")
        print("="*70)
        print()

        # 저장된 조건 확인
        print("저장된 Block1 프리셋:")
        for preset in block1_preset_repo.list_all():
            # Block1는 객체를 반환
            print(f"  - {preset.name}: {preset.description}")
        print()

        print("저장된 Block2 프리셋:")
        for preset in block2_preset_repo.list_all():
            # Block2/3는 dict를 반환
            print(f"  - {preset['name']}: {preset['description']}")
        print()

        print("저장된 Block3 프리셋:")
        for preset in block3_preset_repo.list_all():
            print(f"  - {preset['name']}: {preset['description']}")
        print()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_conn.close()


if __name__ == "__main__":
    main()
