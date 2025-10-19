"""
패턴 재탐지 시스템 기본 프리셋 저장

Seed 조건과 Redetection 조건 프리셋을 DB에 저장합니다.
"""
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.seed_condition_preset_repository import SeedConditionPresetRepository
from src.infrastructure.repositories.redetection_condition_preset_repository import RedetectionConditionPresetRepository
from src.domain.entities.seed_condition import SeedCondition
from src.domain.entities.redetection_condition import RedetectionCondition
from src.domain.entities.block1_condition import Block1ExitConditionType


def save_seed_presets():
    """Seed 조건 프리셋 저장"""
    print("=" * 70)
    print("Seed 조건 프리셋 저장")
    print("=" * 70)

    db = DatabaseConnection("data/database/stock_data.db")
    repo = SeedConditionPresetRepository(db)

    presets = [
        {
            "name": "aggressive_seed",
            "description": "공격적 Seed 탐지 (엄격한 조건)",
            "condition": SeedCondition(
                entry_surge_rate=8.0,
                entry_ma_period=120,
                high_above_ma=True,
                max_deviation_ratio=120.0,
                min_trading_value=300.0,
                volume_high_months=12,
                volume_spike_ratio=400.0,
                price_high_months=2,
                exit_condition_type=Block1ExitConditionType.MA_BREAK,
                exit_ma_period=60,
                cooldown_days=20,
                block2_volume_ratio=15.0,
                block2_low_price_margin=10.0,
                block2_min_candles_after_block1=4,
                block3_volume_ratio=15.0,
                block3_low_price_margin=10.0,
                block3_min_candles_after_block2=4
            )
        },
        {
            "name": "standard_seed",
            "description": "표준 Seed 탐지 (중간 조건)",
            "condition": SeedCondition(
                entry_surge_rate=6.0,
                entry_ma_period=120,
                high_above_ma=True,
                max_deviation_ratio=130.0,
                min_trading_value=200.0,
                volume_high_months=12,
                volume_spike_ratio=300.0,
                price_high_months=2,
                exit_condition_type=Block1ExitConditionType.MA_BREAK,
                exit_ma_period=60,
                cooldown_days=20,
                block2_volume_ratio=15.0,
                block2_low_price_margin=10.0,
                block2_min_candles_after_block1=4,
                block3_volume_ratio=15.0,
                block3_low_price_margin=10.0,
                block3_min_candles_after_block2=4
            )
        },
        {
            "name": "conservative_seed",
            "description": "보수적 Seed 탐지 (완화 조건)",
            "condition": SeedCondition(
                entry_surge_rate=5.0,
                entry_ma_period=120,
                high_above_ma=True,
                max_deviation_ratio=140.0,
                min_trading_value=100.0,
                volume_high_months=6,
                volume_spike_ratio=250.0,
                price_high_months=2,
                exit_condition_type=Block1ExitConditionType.MA_BREAK,
                exit_ma_period=60,
                cooldown_days=20,
                block2_volume_ratio=15.0,
                block2_low_price_margin=10.0,
                block2_min_candles_after_block1=4,
                block3_volume_ratio=15.0,
                block3_low_price_margin=10.0,
                block3_min_candles_after_block2=4
            )
        }
    ]

    for preset in presets:
        try:
            repo.save(
                name=preset["name"],
                condition=preset["condition"],
                description=preset["description"]
            )
            print(f"[OK] {preset['name']}: {preset['description']}")
        except Exception as e:
            print(f"[ERR] {preset['name']}: {e}")

    print("\n" + "=" * 70)


def save_redetection_presets():
    """재탐지 조건 프리셋 저장"""
    print("\n" + "=" * 70)
    print("재탐지 조건 프리셋 저장")
    print("=" * 70)

    db = DatabaseConnection("data/database/stock_data.db")
    repo = RedetectionConditionPresetRepository(db)

    presets = [
        {
            "name": "aggressive_redetect",
            "description": "공격적 재탐지 (완화된 조건 + ±10/15/20% tolerance)",
            "condition": RedetectionCondition(
                # 완화된 조건
                entry_surge_rate=5.0,
                entry_ma_period=120,
                high_above_ma=True,
                max_deviation_ratio=120.0,
                min_trading_value=300.0,
                volume_high_months=6,
                volume_spike_ratio=300.0,
                price_high_months=1,
                # Tolerance
                block1_tolerance_pct=10.0,
                block2_tolerance_pct=15.0,
                block3_tolerance_pct=20.0,
                # 종료 조건
                exit_condition_type=Block1ExitConditionType.MA_BREAK,
                exit_ma_period=60,
                cooldown_days=20,
                # Block2/3 조건
                block2_volume_ratio=15.0,
                block2_low_price_margin=10.0,
                block2_min_candles_after_block1=4,
                block3_volume_ratio=15.0,
                block3_low_price_margin=10.0,
                block3_min_candles_after_block2=4
            )
        },
        {
            "name": "standard_redetect",
            "description": "표준 재탐지 (중간 완화 + ±12/17/22% tolerance)",
            "condition": RedetectionCondition(
                entry_surge_rate=4.0,
                entry_ma_period=120,
                high_above_ma=True,
                max_deviation_ratio=130.0,
                min_trading_value=200.0,
                volume_high_months=6,
                volume_spike_ratio=250.0,
                price_high_months=1,
                # Tolerance (더 넓게)
                block1_tolerance_pct=12.0,
                block2_tolerance_pct=17.0,
                block3_tolerance_pct=22.0,
                exit_condition_type=Block1ExitConditionType.MA_BREAK,
                exit_ma_period=60,
                cooldown_days=20,
                block2_volume_ratio=15.0,
                block2_low_price_margin=10.0,
                block2_min_candles_after_block1=4,
                block3_volume_ratio=15.0,
                block3_low_price_margin=10.0,
                block3_min_candles_after_block2=4
            )
        },
        {
            "name": "conservative_redetect",
            "description": "보수적 재탐지 (매우 완화 + ±15/20/25% tolerance)",
            "condition": RedetectionCondition(
                entry_surge_rate=3.0,
                entry_ma_period=120,
                high_above_ma=True,
                max_deviation_ratio=140.0,
                min_trading_value=100.0,
                volume_high_months=3,
                volume_spike_ratio=200.0,
                price_high_months=1,
                # Tolerance (가장 넓게)
                block1_tolerance_pct=15.0,
                block2_tolerance_pct=20.0,
                block3_tolerance_pct=25.0,
                exit_condition_type=Block1ExitConditionType.MA_BREAK,
                exit_ma_period=60,
                cooldown_days=20,
                block2_volume_ratio=15.0,
                block2_low_price_margin=10.0,
                block2_min_candles_after_block1=4,
                block3_volume_ratio=15.0,
                block3_low_price_margin=10.0,
                block3_min_candles_after_block2=4
            )
        }
    ]

    for preset in presets:
        try:
            repo.save(
                name=preset["name"],
                condition=preset["condition"],
                description=preset["description"]
            )
            print(f"[OK] {preset['name']}: {preset['description']}")
        except Exception as e:
            print(f"[ERR] {preset['name']}: {e}")

    print("\n" + "=" * 70)


def test_load_presets():
    """저장된 프리셋 로드 테스트"""
    print("\n" + "=" * 70)
    print("프리셋 로드 테스트")
    print("=" * 70)

    db = DatabaseConnection("data/database/stock_data.db")

    # Seed 프리셋 로드
    print("\n[Seed 프리셋]")
    seed_repo = SeedConditionPresetRepository(db)
    seed_names = seed_repo.list_all()

    for name in seed_names:
        condition = seed_repo.load(name)
        if condition:
            print(f"  [OK] {name}:")
            print(f"       급등률: {condition.entry_surge_rate}%")
            print(f"       거래량: {condition.volume_high_months}개월")
            print(f"       Cooldown: {condition.cooldown_days}일")

    # Redetection 프리셋 로드
    print("\n[재탐지 프리셋]")
    redetect_repo = RedetectionConditionPresetRepository(db)
    redetect_names = redetect_repo.list_all()

    for name in redetect_names:
        condition = redetect_repo.load(name)
        if condition:
            print(f"  [OK] {name}:")
            print(f"       급등률: {condition.entry_surge_rate}% (완화)")
            print(f"       거래량: {condition.volume_high_months}개월 (완화)")
            print(f"       Tolerance: Block1=±{condition.block1_tolerance_pct}%, "
                  f"Block2=±{condition.block2_tolerance_pct}%, "
                  f"Block3=±{condition.block3_tolerance_pct}%")
            print(f"       Cooldown: {condition.cooldown_days}일")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    save_seed_presets()
    save_redetection_presets()
    test_load_presets()

    print("\n" + "=" * 70)
    print("모든 프리셋 저장 완료!")
    print("=" * 70)
