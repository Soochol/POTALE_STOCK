"""
프리셋 로더 스크립트

YAML 파일에서 프리셋을 읽어 DB에 저장합니다.
"""
import sys
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import get_db_connection
from src.infrastructure.repositories.preset.seed_condition_preset_repository import SeedConditionPresetRepository
from src.infrastructure.repositories.preset.redetection_condition_preset_repository import RedetectionConditionPresetRepository
from src.domain.entities.conditions.seed_condition import SeedCondition
from src.domain.entities.conditions.redetection_condition import RedetectionCondition
from src.domain.entities.conditions.base_entry_condition import BaseEntryCondition, Block1ExitConditionType


def load_yaml_file(filepath: str) -> dict:
    """YAML 파일 로드"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def convert_exit_type(exit_type_str: str) -> Block1ExitConditionType:
    """문자열을 Block1ExitConditionType Enum으로 변환"""
    if not exit_type_str:
        return None

    if exit_type_str == 'ma_break':
        return Block1ExitConditionType.MA_BREAK
    elif exit_type_str == 'three_line_reversal':
        return Block1ExitConditionType.THREE_LINE_REVERSAL
    elif exit_type_str == 'body_middle':
        return Block1ExitConditionType.BODY_MIDDLE
    else:
        return None


def create_base_entry_condition(block_data: dict) -> BaseEntryCondition:
    """블록 데이터에서 BaseEntryCondition 생성"""
    exit_type = convert_exit_type(block_data.get('exit_condition_type'))

    return BaseEntryCondition(
        block1_entry_surge_rate=block_data.get('entry_surge_rate'),
        block1_entry_ma_period=block_data.get('entry_ma_period'),
        block1_entry_high_above_ma=block_data.get('entry_high_above_ma'),
        block1_entry_max_deviation_ratio=block_data.get('entry_max_deviation_ratio'),
        block1_entry_min_trading_value=block_data.get('entry_min_trading_value'),
        block1_entry_volume_high_months=block_data.get('entry_volume_high_months'),
        block1_entry_volume_spike_ratio=block_data.get('entry_volume_spike_ratio'),
        block1_entry_price_high_months=block_data.get('entry_price_high_months'),
        block1_exit_condition_type=exit_type if exit_type else Block1ExitConditionType.MA_BREAK,
        block1_exit_ma_period=block_data.get('exit_ma_period'),
        block1_min_start_interval_days=block_data.get('min_start_interval_days', 120)
    )


def create_seed_condition(preset_name: str, preset_data: dict) -> SeedCondition:
    """Seed 조건 생성"""
    block1_data = preset_data['block1']
    block2_data = preset_data['block2']
    block3_data = preset_data['block3']
    block4_data = preset_data['block4']

    return SeedCondition(
        base=create_base_entry_condition(block1_data),
        # Block2 조건
        block2_volume_ratio=block2_data.get('volume_ratio', 15.0),
        block2_low_price_margin=block2_data.get('low_price_margin', 10.0),
        block2_min_candles_after_block1=block2_data.get('min_candles_after_block1', 4),
        block2_max_candles_after_block1=block2_data.get('max_candles_after_block1'),
        block2_entry_surge_rate=block2_data.get('entry_surge_rate'),
        block2_entry_ma_period=block2_data.get('entry_ma_period'),
        block2_entry_high_above_ma=block2_data.get('entry_high_above_ma'),
        block2_entry_max_deviation_ratio=block2_data.get('entry_max_deviation_ratio'),
        block2_entry_min_trading_value=block2_data.get('entry_min_trading_value'),
        block2_entry_volume_high_months=block2_data.get('entry_volume_high_months'),
        block2_entry_volume_spike_ratio=block2_data.get('entry_volume_spike_ratio'),
        block2_entry_price_high_months=block2_data.get('entry_price_high_months'),
        block2_exit_condition_type=convert_exit_type(block2_data.get('exit_condition_type')),
        block2_exit_ma_period=block2_data.get('exit_ma_period'),
        block2_min_start_interval_days=block2_data.get('min_start_interval_days'),
        # Block3 조건
        block3_volume_ratio=block3_data.get('volume_ratio', 15.0),
        block3_low_price_margin=block3_data.get('low_price_margin', 10.0),
        block3_min_candles_after_block2=block3_data.get('min_candles_after_block2', 4),
        block3_max_candles_after_block2=block3_data.get('max_candles_after_block2'),
        block3_entry_surge_rate=block3_data.get('entry_surge_rate'),
        block3_entry_ma_period=block3_data.get('entry_ma_period'),
        block3_entry_high_above_ma=block3_data.get('entry_high_above_ma'),
        block3_entry_max_deviation_ratio=block3_data.get('entry_max_deviation_ratio'),
        block3_entry_min_trading_value=block3_data.get('entry_min_trading_value'),
        block3_entry_volume_high_months=block3_data.get('entry_volume_high_months'),
        block3_entry_volume_spike_ratio=block3_data.get('entry_volume_spike_ratio'),
        block3_entry_price_high_months=block3_data.get('entry_price_high_months'),
        block3_exit_condition_type=convert_exit_type(block3_data.get('exit_condition_type')),
        block3_exit_ma_period=block3_data.get('exit_ma_period'),
        block3_min_start_interval_days=block3_data.get('min_start_interval_days'),
        # Block4 조건
        block4_volume_ratio=block4_data.get('volume_ratio', 20.0),
        block4_low_price_margin=block4_data.get('low_price_margin', 10.0),
        block4_min_candles_after_block3=block4_data.get('min_candles_after_block3', 4),
        block4_max_candles_after_block3=block4_data.get('max_candles_after_block3'),
        block4_entry_surge_rate=block4_data.get('entry_surge_rate'),
        block4_entry_ma_period=block4_data.get('entry_ma_period'),
        block4_entry_high_above_ma=block4_data.get('entry_high_above_ma'),
        block4_entry_max_deviation_ratio=block4_data.get('entry_max_deviation_ratio'),
        block4_entry_min_trading_value=block4_data.get('entry_min_trading_value'),
        block4_entry_volume_high_months=block4_data.get('entry_volume_high_months'),
        block4_entry_volume_spike_ratio=block4_data.get('entry_volume_spike_ratio'),
        block4_entry_price_high_months=block4_data.get('entry_price_high_months'),
        block4_exit_condition_type=convert_exit_type(block4_data.get('exit_condition_type')),
        block4_exit_ma_period=block4_data.get('exit_ma_period'),
        block4_min_start_interval_days=block4_data.get('min_start_interval_days')
    )


def create_redetection_condition(preset_name: str, preset_data: dict) -> RedetectionCondition:
    """재탐지 조건 생성"""
    block1_data = preset_data['block1']
    block2_data = preset_data['block2']
    block3_data = preset_data['block3']
    block4_data = preset_data['block4']

    return RedetectionCondition(
        base=create_base_entry_condition(block1_data),
        block1_tolerance_pct=block1_data.get('tolerance_pct', 10.0),
        # Block2 조건
        block2_volume_ratio=block2_data.get('volume_ratio', 15.0),
        block2_low_price_margin=block2_data.get('low_price_margin', 10.0),
        block2_min_candles_after_block1=block2_data.get('min_candles_after_block1', 4),
        block2_max_candles_after_block1=block2_data.get('max_candles_after_block1'),
        block2_tolerance_pct=block2_data.get('tolerance_pct', 15.0),
        block2_entry_surge_rate=block2_data.get('entry_surge_rate'),
        block2_entry_ma_period=block2_data.get('entry_ma_period'),
        block2_entry_high_above_ma=block2_data.get('entry_high_above_ma'),
        block2_entry_max_deviation_ratio=block2_data.get('entry_max_deviation_ratio'),
        block2_entry_min_trading_value=block2_data.get('entry_min_trading_value'),
        block2_entry_volume_high_months=block2_data.get('entry_volume_high_months'),
        block2_entry_volume_spike_ratio=block2_data.get('entry_volume_spike_ratio'),
        block2_entry_price_high_months=block2_data.get('entry_price_high_months'),
        block2_exit_condition_type=convert_exit_type(block2_data.get('exit_condition_type')),
        block2_exit_ma_period=block2_data.get('exit_ma_period'),
        block2_min_start_interval_days=block2_data.get('min_start_interval_days'),
        # Block3 조건
        block3_volume_ratio=block3_data.get('volume_ratio', 15.0),
        block3_low_price_margin=block3_data.get('low_price_margin', 10.0),
        block3_min_candles_after_block2=block3_data.get('min_candles_after_block2', 4),
        block3_max_candles_after_block2=block3_data.get('max_candles_after_block2'),
        block3_tolerance_pct=block3_data.get('tolerance_pct', 20.0),
        block3_entry_surge_rate=block3_data.get('entry_surge_rate'),
        block3_entry_ma_period=block3_data.get('entry_ma_period'),
        block3_entry_high_above_ma=block3_data.get('entry_high_above_ma'),
        block3_entry_max_deviation_ratio=block3_data.get('entry_max_deviation_ratio'),
        block3_entry_min_trading_value=block3_data.get('entry_min_trading_value'),
        block3_entry_volume_high_months=block3_data.get('entry_volume_high_months'),
        block3_entry_volume_spike_ratio=block3_data.get('entry_volume_spike_ratio'),
        block3_entry_price_high_months=block3_data.get('entry_price_high_months'),
        block3_exit_condition_type=convert_exit_type(block3_data.get('exit_condition_type')),
        block3_exit_ma_period=block3_data.get('exit_ma_period'),
        block3_min_start_interval_days=block3_data.get('min_start_interval_days'),
        # Block4 조건
        block4_volume_ratio=block4_data.get('volume_ratio', 20.0),
        block4_low_price_margin=block4_data.get('low_price_margin', 10.0),
        block4_min_candles_after_block3=block4_data.get('min_candles_after_block3', 4),
        block4_max_candles_after_block3=block4_data.get('max_candles_after_block3'),
        block4_tolerance_pct=block4_data.get('tolerance_pct', 25.0),
        block4_entry_surge_rate=block4_data.get('entry_surge_rate'),
        block4_entry_ma_period=block4_data.get('entry_ma_period'),
        block4_entry_high_above_ma=block4_data.get('entry_high_above_ma'),
        block4_entry_max_deviation_ratio=block4_data.get('entry_max_deviation_ratio'),
        block4_entry_min_trading_value=block4_data.get('entry_min_trading_value'),
        block4_entry_volume_high_months=block4_data.get('entry_volume_high_months'),
        block4_entry_volume_spike_ratio=block4_data.get('entry_volume_spike_ratio'),
        block4_entry_price_high_months=block4_data.get('entry_price_high_months'),
        block4_exit_condition_type=convert_exit_type(block4_data.get('exit_condition_type')),
        block4_exit_ma_period=block4_data.get('exit_ma_period'),
        block4_min_start_interval_days=block4_data.get('min_start_interval_days')
    )


def main():
    """메인 함수"""
    print("=" * 80)
    print("프리셋 로더")
    print("=" * 80)
    print()

    # DB 연결
    db_path = 'data/database/stock_data.db'
    print(f"DB 연결 중... {db_path}")
    db = get_db_connection(db_path)
    print("   OK\n")

    # Repository 초기화
    seed_repo = SeedConditionPresetRepository(db)
    redetect_repo = RedetectionConditionPresetRepository(db)

    # Seed 조건 로드
    print("Seed 조건 로드 중...")
    seed_yaml = load_yaml_file('presets/seed_conditions.yaml')

    for preset_name, preset_data in seed_yaml.items():
        try:
            seed_condition = create_seed_condition(preset_name, preset_data)
            seed_repo.save(preset_name, seed_condition)
            print(f"   OK {preset_name}")
        except Exception as e:
            print(f"   ERROR {preset_name}: {e}")

    print()

    # 재탐지 조건 로드
    print("재탐지 조건 로드 중...")
    redetect_yaml = load_yaml_file('presets/redetection_conditions.yaml')

    for preset_name, preset_data in redetect_yaml.items():
        try:
            redetect_condition = create_redetection_condition(preset_name, preset_data)
            redetect_repo.save(preset_name, redetect_condition)
            print(f"   OK {preset_name}")
        except Exception as e:
            print(f"   ERROR {preset_name}: {e}")

    print()
    print("=" * 80)
    print("완료!")
    print("=" * 80)


if __name__ == '__main__':
    main()
