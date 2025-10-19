"""
Block1 조건 프리셋을 DB에 저장하는 스크립트
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from src.infrastructure.repositories.block1_condition_preset_repository import Block1ConditionPresetRepository
from src.infrastructure.database.connection import DatabaseConnection

def save_standard_condition():
    """표준 조건 저장 (BLOCK_DETECTION.md)"""
    condition = Block1Condition(
        entry_surge_rate=8.0,
        entry_ma_period=120,
        high_above_ma=True,
        max_deviation_ratio=120.0,
        min_trading_value=300.0,
        volume_high_months=24,
        volume_spike_ratio=400.0,
        price_high_months=2,
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=60,
        cooldown_days=120
    )

    description = """
    BLOCK_DETECTION.md 표준 조건
    - 엄격한 조건으로 확실한 대박 기회만 포착
    - MA120 장기 추세 확인
    - 24개월 신고거래량 (매우 희귀)
    - 전날 거래량 4배 급증
    - 2개월 신고가
    - 120일 쿨다운
    """

    return condition, description


def save_custom_condition():
    """Custom 조건 저장 (완화된 조건)"""
    condition = Block1Condition(
        entry_surge_rate=8.0,
        entry_ma_period=120,
        high_above_ma=True,
        max_deviation_ratio=150.0,
        min_trading_value=300.0,
        volume_high_months=3,
        volume_spike_ratio=300.0,
        price_high_months=1,
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=60,
        cooldown_days=60
    )

    description = """
    Custom 완화 조건 (MA120 + 60일 쿨다운)
    - MA120으로 장기 추세 확인
    - 이격도 150% (완화)
    - 3개월 신고거래량 (단기)
    - 전날 거래량 3배
    - 1개월 신고가
    - 60일 쿨다운 (빠른 재진입)
    - 평균 수익률: +41.36%
    - 최고 수익률: +153.20%
    """

    return condition, description


def save_aggressive_condition():
    """Aggressive 조건 저장 (더 완화)"""
    condition = Block1Condition(
        entry_surge_rate=5.0,  # 5% 상승
        entry_ma_period=60,  # MA60
        high_above_ma=True,
        max_deviation_ratio=200.0,  # 매우 완화
        min_trading_value=100.0,  # 100억
        volume_high_months=1,  # 1개월 신고거래량
        volume_spike_ratio=200.0,  # 2배
        price_high_months=1,  # 1개월 신고가
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=20,  # MA20으로 빠른 종료
        cooldown_days=30  # 30일 쿨다운
    )

    description = """
    Aggressive 조건 (매우 완화)
    - MA60 단기 추세
    - 등락률 5% (낮은 진입 기준)
    - 이격도 200% (매우 완화)
    - 거래대금 100억
    - 1개월 신고거래량
    - 전날 거래량 2배
    - 30일 짧은 쿨다운
    - 더 많은 기회 포착 목적
    """

    return condition, description


def main():
    print("="*70)
    print("Block1 조건 프리셋 저장")
    print("="*70)
    print()

    # DB 연결
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)
    repo = Block1ConditionPresetRepository(db_conn)

    # 1. Standard 조건 저장
    print("[1/3] Standard 조건 저장 중...")
    condition, desc = save_standard_condition()
    preset = repo.save("standard", condition, desc.strip())
    print(f"  [OK] 저장 완료: {preset.name}")
    print()

    # 2. Custom 조건 저장
    print("[2/3] Custom 조건 저장 중...")
    condition, desc = save_custom_condition()
    preset = repo.save("custom", condition, desc.strip())
    print(f"  [OK] 저장 완료: {preset.name}")
    print()

    # 3. Aggressive 조건 저장
    print("[3/3] Aggressive 조건 저장 중...")
    condition, desc = save_aggressive_condition()
    preset = repo.save("aggressive", condition, desc.strip())
    print(f"  [OK] 저장 완료: {preset.name}")
    print()

    # 저장된 조건 목록 출력
    print("="*70)
    print("저장된 조건 프리셋 목록")
    print("="*70)

    presets = repo.list_all()
    for i, preset in enumerate(presets, 1):
        print(f"\n[{i}] {preset.name}")
        print(f"    MA Period: {preset.entry_ma_period}")
        print(f"    Cooldown: {preset.cooldown_days}일")
        print(f"    Rate Threshold: {preset.entry_surge_rate}%")
        print(f"    Deviation: {preset.max_deviation_ratio}%")
        print(f"    Volume Months: {preset.volume_high_months}개월")
        print(f"    Prev Volume: {preset.volume_spike_ratio}%")
        print(f"    New High: {preset.price_high_months}개월")
        if preset.description:
            print(f"    설명: {preset.description[:100]}...")

    print()
    print("="*70)
    print(f"총 {len(presets)}개 조건 프리셋 저장 완료!")
    print("="*70)


if __name__ == "__main__":
    main()
