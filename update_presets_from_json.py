"""
Preset 데이터를 JSON 파일에서 읽어서 DB에 업데이트

사용법:
    python update_presets_from_json.py                    # 모든 preset 업데이트
    python update_presets_from_json.py --seed-only        # Seed 조건만 업데이트
    python update_presets_from_json.py --redetect-only    # 재탐지 조건만 업데이트
    python update_presets_from_json.py --dry-run          # 실제 저장 없이 미리보기만
"""
import json
import argparse
from pathlib import Path
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.seed_condition_preset_repository import SeedConditionPresetRepository
from src.infrastructure.repositories.redetection_condition_preset_repository import RedetectionConditionPresetRepository
from src.domain.entities.seed_condition import SeedCondition
from src.domain.entities.redetection_condition import RedetectionCondition
from src.domain.entities.base_entry_condition import BaseEntryCondition


def load_json_file(file_path: str) -> dict:
    """JSON 파일 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_seed_conditions(db: DatabaseConnection, json_data: dict, dry_run: bool = False):
    """Seed 조건 업데이트 (블록별 섹션 구조 지원)"""
    print("=" * 70)
    print("Seed Condition Presets 업데이트")
    print("=" * 70)

    repo = SeedConditionPresetRepository(db)

    for name, preset_data in json_data.items():
        print(f"\n[{name}]")
        print(f"  설명: {preset_data.get('description', 'N/A')}")

        # 새 구조: block1, block2, block3, block4 섹션이 있는 경우
        if 'block1' in preset_data:
            block1 = preset_data['block1']
            block2 = preset_data['block2']
            block3 = preset_data['block3']
            block4 = preset_data['block4']

            print(f"\n  Block1 조건:")
            print(f"    진입 등락률: {block1['entry_surge_rate']}%")
            print(f"    진입 MA: {block1['entry_ma_period']}일")
            print(f"    종료 MA: {block1['exit_ma_period']}일")

            print(f"\n  Block2 조건:")
            print(f"    진입 등락률: {block2['entry_surge_rate']}% (Block1과 {'동일' if block1['entry_surge_rate'] == block2['entry_surge_rate'] else '다름'})")
            print(f"    거래량 비율: {block2['volume_ratio']}%")
            print(f"    저가 마진: {block2['low_price_margin']}%")

            print(f"\n  Block3 조건:")
            print(f"    진입 등락률: {block3['entry_surge_rate']}%")
            print(f"    거래량 비율: {block3['volume_ratio']}%")

            print(f"\n  Block4 조건:")
            print(f"    진입 등락률: {block4['entry_surge_rate']}%")
            print(f"    거래량 비율: {block4['volume_ratio']}%")

            if not dry_run:
                # Block1 기본 조건 생성
                base = BaseEntryCondition(
                    block1_entry_surge_rate=block1['entry_surge_rate'],
                    block1_entry_ma_period=block1['entry_ma_period'],
                    block1_entry_high_above_ma=block1['entry_high_above_ma'],
                    block1_entry_max_deviation_ratio=block1['entry_max_deviation_ratio'],
                    block1_entry_min_trading_value=block1['entry_min_trading_value'],
                    block1_entry_volume_high_months=block1['entry_volume_high_months'],
                    block1_entry_volume_spike_ratio=block1['entry_volume_spike_ratio'],
                    block1_entry_price_high_months=block1['entry_price_high_months'],
                    block1_exit_ma_period=block1['exit_ma_period'],
                    block1_cooldown_days=block1['cooldown_days']
                )

                condition = SeedCondition(
                    base=base,
                    block2_volume_ratio=block2['volume_ratio'],
                    block2_low_price_margin=block2['low_price_margin'],
                    block2_min_candles_after_block1=block2['min_candles_after_block1'],
                    block3_volume_ratio=block3['volume_ratio'],
                    block3_low_price_margin=block3['low_price_margin'],
                    block3_min_candles_after_block2=block3['min_candles_after_block2'],
                    block4_volume_ratio=block4['volume_ratio'],
                    block4_low_price_margin=block4['low_price_margin'],
                    block4_min_candles_after_block3=block4['min_candles_after_block3'],
                    # Block2 전용 파라미터 (Optional)
                    block2_entry_surge_rate=block2.get('entry_surge_rate'),
                    block2_entry_ma_period=block2.get('entry_ma_period'),
                    block2_entry_high_above_ma=block2.get('entry_high_above_ma'),
                    block2_entry_max_deviation_ratio=block2.get('entry_max_deviation_ratio'),
                    block2_entry_min_trading_value=block2.get('entry_min_trading_value'),
                    block2_entry_volume_high_months=block2.get('entry_volume_high_months'),
                    block2_entry_volume_spike_ratio=block2.get('entry_volume_spike_ratio'),
                    block2_entry_price_high_months=block2.get('entry_price_high_months'),
                    block2_exit_ma_period=block2.get('exit_ma_period'),
                    block2_cooldown_days=block2.get('cooldown_days'),
                    # Block3 전용 파라미터 (Optional)
                    block3_entry_surge_rate=block3.get('entry_surge_rate'),
                    block3_entry_ma_period=block3.get('entry_ma_period'),
                    block3_entry_high_above_ma=block3.get('entry_high_above_ma'),
                    block3_entry_max_deviation_ratio=block3.get('entry_max_deviation_ratio'),
                    block3_entry_min_trading_value=block3.get('entry_min_trading_value'),
                    block3_entry_volume_high_months=block3.get('entry_volume_high_months'),
                    block3_entry_volume_spike_ratio=block3.get('entry_volume_spike_ratio'),
                    block3_entry_price_high_months=block3.get('entry_price_high_months'),
                    block3_exit_ma_period=block3.get('exit_ma_period'),
                    block3_cooldown_days=block3.get('cooldown_days'),
                    # Block4 전용 파라미터 (Optional)
                    block4_entry_surge_rate=block4.get('entry_surge_rate'),
                    block4_entry_ma_period=block4.get('entry_ma_period'),
                    block4_entry_high_above_ma=block4.get('entry_high_above_ma'),
                    block4_entry_max_deviation_ratio=block4.get('entry_max_deviation_ratio'),
                    block4_entry_min_trading_value=block4.get('entry_min_trading_value'),
                    block4_entry_volume_high_months=block4.get('entry_volume_high_months'),
                    block4_entry_volume_spike_ratio=block4.get('entry_volume_spike_ratio'),
                    block4_entry_price_high_months=block4.get('entry_price_high_months'),
                    block4_exit_ma_period=block4.get('exit_ma_period'),
                    block4_cooldown_days=block4.get('cooldown_days')
                )

                repo.save(name, condition, preset_data.get('description', ''))
                print(f"\n  [OK] DB 저장 완료")
            else:
                print(f"\n  [DRY RUN] 저장 건너뜀")

        # 구 구조: flat 구조 (하위 호환성)
        else:
            print(f"  [경고] 구 형식 JSON 구조 감지 - 블록별 섹션 구조로 업데이트 권장")
            print(f"  진입 등락률: {preset_data['entry_surge_rate']}%")
            print(f"  진입 MA: {preset_data['entry_ma_period']}일")
            # ... 구 형식 처리 생략 (필요 시 유지)


def update_redetection_conditions(db: DatabaseConnection, json_data: dict, dry_run: bool = False):
    """재탐지 조건 업데이트 (블록별 섹션 구조 지원)"""
    print("\n" + "=" * 70)
    print("Redetection Condition Presets 업데이트")
    print("=" * 70)

    repo = RedetectionConditionPresetRepository(db)

    for name, preset_data in json_data.items():
        print(f"\n[{name}]")
        print(f"  설명: {preset_data.get('description', 'N/A')}")

        # 새 구조: block1, block2, block3, block4 섹션이 있는 경우
        if 'block1' in preset_data:
            block1 = preset_data['block1']
            block2 = preset_data['block2']
            block3 = preset_data['block3']
            block4 = preset_data['block4']

            print(f"\n  Block1 조건:")
            print(f"    진입 등락률: {block1['entry_surge_rate']}%")
            print(f"    진입 MA: {block1['entry_ma_period']}일")
            print(f"    종료 MA: {block1['exit_ma_period']}일")
            print(f"    가격 Tolerance: {block1['tolerance_pct']}%")

            print(f"\n  Block2 조건:")
            print(f"    진입 등락률: {block2['entry_surge_rate']}% (Block1과 {'동일' if block1['entry_surge_rate'] == block2['entry_surge_rate'] else '다름'})")
            print(f"    거래량 비율: {block2['volume_ratio']}%")
            print(f"    저가 마진: {block2['low_price_margin']}%")
            print(f"    가격 Tolerance: {block2['tolerance_pct']}%")

            print(f"\n  Block3 조건:")
            print(f"    진입 등락률: {block3['entry_surge_rate']}%")
            print(f"    거래량 비율: {block3['volume_ratio']}%")
            print(f"    가격 Tolerance: {block3['tolerance_pct']}%")

            print(f"\n  Block4 조건:")
            print(f"    진입 등락률: {block4['entry_surge_rate']}%")
            print(f"    거래량 비율: {block4['volume_ratio']}%")
            print(f"    가격 Tolerance: {block4['tolerance_pct']}%")

            if not dry_run:
                # Block1 기본 조건 생성
                base = BaseEntryCondition(
                    block1_entry_surge_rate=block1['entry_surge_rate'],
                    block1_entry_ma_period=block1['entry_ma_period'],
                    block1_entry_high_above_ma=block1['entry_high_above_ma'],
                    block1_entry_max_deviation_ratio=block1['entry_max_deviation_ratio'],
                    block1_entry_min_trading_value=block1['entry_min_trading_value'],
                    block1_entry_volume_high_months=block1['entry_volume_high_months'],
                    block1_entry_volume_spike_ratio=block1['entry_volume_spike_ratio'],
                    block1_entry_price_high_months=block1['entry_price_high_months'],
                    block1_exit_ma_period=block1['exit_ma_period'],
                    block1_cooldown_days=block1['cooldown_days']
                )

                condition = RedetectionCondition(
                    base=base,
                    block1_tolerance_pct=block1['tolerance_pct'],
                    block2_tolerance_pct=block2['tolerance_pct'],
                    block3_tolerance_pct=block3['tolerance_pct'],
                    block4_tolerance_pct=block4['tolerance_pct'],
                    block2_volume_ratio=block2['volume_ratio'],
                    block2_low_price_margin=block2['low_price_margin'],
                    block2_min_candles_after_block1=block2['min_candles_after_block1'],
                    block3_volume_ratio=block3['volume_ratio'],
                    block3_low_price_margin=block3['low_price_margin'],
                    block3_min_candles_after_block2=block3['min_candles_after_block2'],
                    block4_volume_ratio=block4['volume_ratio'],
                    block4_low_price_margin=block4['low_price_margin'],
                    block4_min_candles_after_block3=block4['min_candles_after_block3'],
                    # Block2 전용 파라미터 (Optional)
                    block2_entry_surge_rate=block2.get('entry_surge_rate'),
                    block2_entry_ma_period=block2.get('entry_ma_period'),
                    block2_entry_high_above_ma=block2.get('entry_high_above_ma'),
                    block2_entry_max_deviation_ratio=block2.get('entry_max_deviation_ratio'),
                    block2_entry_min_trading_value=block2.get('entry_min_trading_value'),
                    block2_entry_volume_high_months=block2.get('entry_volume_high_months'),
                    block2_entry_volume_spike_ratio=block2.get('entry_volume_spike_ratio'),
                    block2_entry_price_high_months=block2.get('entry_price_high_months'),
                    block2_exit_ma_period=block2.get('exit_ma_period'),
                    block2_cooldown_days=block2.get('cooldown_days'),
                    # Block3 전용 파라미터 (Optional)
                    block3_entry_surge_rate=block3.get('entry_surge_rate'),
                    block3_entry_ma_period=block3.get('entry_ma_period'),
                    block3_entry_high_above_ma=block3.get('entry_high_above_ma'),
                    block3_entry_max_deviation_ratio=block3.get('entry_max_deviation_ratio'),
                    block3_entry_min_trading_value=block3.get('entry_min_trading_value'),
                    block3_entry_volume_high_months=block3.get('entry_volume_high_months'),
                    block3_entry_volume_spike_ratio=block3.get('entry_volume_spike_ratio'),
                    block3_entry_price_high_months=block3.get('entry_price_high_months'),
                    block3_exit_ma_period=block3.get('exit_ma_period'),
                    block3_cooldown_days=block3.get('cooldown_days'),
                    # Block4 전용 파라미터 (Optional)
                    block4_entry_surge_rate=block4.get('entry_surge_rate'),
                    block4_entry_ma_period=block4.get('entry_ma_period'),
                    block4_entry_high_above_ma=block4.get('entry_high_above_ma'),
                    block4_entry_max_deviation_ratio=block4.get('entry_max_deviation_ratio'),
                    block4_entry_min_trading_value=block4.get('entry_min_trading_value'),
                    block4_entry_volume_high_months=block4.get('entry_volume_high_months'),
                    block4_entry_volume_spike_ratio=block4.get('entry_volume_spike_ratio'),
                    block4_entry_price_high_months=block4.get('entry_price_high_months'),
                    block4_exit_ma_period=block4.get('exit_ma_period'),
                    block4_cooldown_days=block4.get('cooldown_days')
                )

                repo.save(name, condition, preset_data.get('description', ''))
                print(f"\n  [OK] DB 저장 완료")
            else:
                print(f"\n  [DRY RUN] 저장 건너뜀")

        # 구 구조: flat 구조 (하위 호환성)
        else:
            print(f"  [경고] 구 형식 JSON 구조 감지 - 블록별 섹션 구조로 업데이트 권장")
            print(f"  진입 등락률: {preset_data['entry_surge_rate']}%")
            print(f"  진입 MA: {preset_data['entry_ma_period']}일")
            # ... 구 형식 처리 생략 (필요 시 유지)


def main():
    parser = argparse.ArgumentParser(description='JSON 파일에서 Preset 데이터를 읽어 DB 업데이트')
    parser.add_argument('--seed-only', action='store_true', help='Seed 조건만 업데이트')
    parser.add_argument('--redetect-only', action='store_true', help='재탐지 조건만 업데이트')
    parser.add_argument('--dry-run', action='store_true', help='실제 저장 없이 미리보기만')
    parser.add_argument('--seed-file', default='presets/seed_conditions.json', help='Seed 조건 JSON 파일 경로')
    parser.add_argument('--redetect-file', default='presets/redetection_conditions.json', help='재탐지 조건 JSON 파일 경로')

    args = parser.parse_args()

    # DB 연결
    db = DatabaseConnection("data/database/stock_data.db")

    if args.dry_run:
        print("\n[!] DRY RUN 모드: 실제로 DB에 저장하지 않습니다.\n")

    # Seed 조건 업데이트
    if not args.redetect_only:
        if Path(args.seed_file).exists():
            seed_data = load_json_file(args.seed_file)
            update_seed_conditions(db, seed_data, args.dry_run)
        else:
            print(f"[!] 파일을 찾을 수 없습니다: {args.seed_file}")

    # 재탐지 조건 업데이트
    if not args.seed_only:
        if Path(args.redetect_file).exists():
            redetect_data = load_json_file(args.redetect_file)
            update_redetection_conditions(db, redetect_data, args.dry_run)
        else:
            print(f"[!] 파일을 찾을 수 없습니다: {args.redetect_file}")

    print("\n" + "=" * 70)
    if args.dry_run:
        print("DRY RUN 완료! (실제 저장은 하지 않았습니다)")
    else:
        print("[OK] Preset 업데이트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
