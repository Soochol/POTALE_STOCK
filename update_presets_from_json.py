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


def load_json_file(file_path: str) -> dict:
    """JSON 파일 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_seed_conditions(db: DatabaseConnection, json_data: dict, dry_run: bool = False):
    """Seed 조건 업데이트"""
    print("=" * 70)
    print("Seed Condition Presets 업데이트")
    print("=" * 70)

    repo = SeedConditionPresetRepository(db)

    for name, data in json_data.items():
        print(f"\n[{name}]")
        print(f"  설명: {data.get('description', 'N/A')}")
        print(f"  진입 등락률: {data['entry_surge_rate']}%")
        print(f"  진입 MA: {data['entry_ma_period']}일")
        print(f"  고가 >= MA: {data['entry_high_above_ma']}")
        print(f"  이격도: {data['entry_max_deviation_ratio']}%")
        print(f"  거래대금: {data['entry_min_trading_value']}억")
        print(f"  신고거래량 기간: {data['entry_volume_high_months']}개월")
        print(f"  전날 대비 거래량: {data['entry_volume_spike_ratio']}%")
        print(f"  신고가 기간: {data['entry_price_high_months']}개월")
        print(f"  종료 MA: {data['exit_ma_period']}일")
        print(f"  Cooldown: {data['cooldown_days']}일")
        print(f"  Block2 거래량 비율: {data['block2_volume_ratio']}%")
        print(f"  Block2 저가 마진: {data['block2_low_price_margin']}%")
        print(f"  Block2 최소 캔들: {data['block2_min_candles_after_block1']}")
        print(f"  Block3 거래량 비율: {data['block3_volume_ratio']}%")
        print(f"  Block3 저가 마진: {data['block3_low_price_margin']}%")
        print(f"  Block3 최소 캔들: {data['block3_min_candles_after_block2']}")

        if not dry_run:
            condition = SeedCondition(
                entry_surge_rate=data['entry_surge_rate'],
                entry_ma_period=data['entry_ma_period'],
                entry_high_above_ma=data['entry_high_above_ma'],
                entry_max_deviation_ratio=data['entry_max_deviation_ratio'],
                entry_min_trading_value=data['entry_min_trading_value'],
                entry_volume_high_months=data['entry_volume_high_months'],
                entry_volume_spike_ratio=data['entry_volume_spike_ratio'],
                entry_price_high_months=data['entry_price_high_months'],
                exit_ma_period=data['exit_ma_period'],
                cooldown_days=data['cooldown_days'],
                block2_volume_ratio=data['block2_volume_ratio'],
                block2_low_price_margin=data['block2_low_price_margin'],
                block2_min_candles_after_block1=data['block2_min_candles_after_block1'],
                block3_volume_ratio=data['block3_volume_ratio'],
                block3_low_price_margin=data['block3_low_price_margin'],
                block3_min_candles_after_block2=data['block3_min_candles_after_block2']
            )

            repo.save(name, condition, data.get('description', ''))
            print(f"  [OK] DB 저장 완료")
        else:
            print(f"  [DRY RUN] 저장 건너뜀")


def update_redetection_conditions(db: DatabaseConnection, json_data: dict, dry_run: bool = False):
    """재탐지 조건 업데이트"""
    print("\n" + "=" * 70)
    print("Redetection Condition Presets 업데이트")
    print("=" * 70)

    repo = RedetectionConditionPresetRepository(db)

    for name, data in json_data.items():
        print(f"\n[{name}]")
        print(f"  설명: {data.get('description', 'N/A')}")
        print(f"  진입 등락률: {data['entry_surge_rate']}%")
        print(f"  진입 MA: {data['entry_ma_period']}일")
        print(f"  고가 >= MA: {data['entry_high_above_ma']}")
        print(f"  이격도: {data['entry_max_deviation_ratio']}%")
        print(f"  거래대금: {data['entry_min_trading_value']}억")
        print(f"  신고거래량 기간: {data['entry_volume_high_months']}개월")
        print(f"  전날 대비 거래량: {data['entry_volume_spike_ratio']}%")
        print(f"  신고가 기간: {data['entry_price_high_months']}개월")
        print(f"  종료 MA: {data['exit_ma_period']}일")
        print(f"  Cooldown: {data['cooldown_days']}일")
        print(f"  Block1 가격 Tolerance: {data['block1_tolerance_pct']}%")
        print(f"  Block2 가격 Tolerance: {data['block2_tolerance_pct']}%")
        print(f"  Block3 가격 Tolerance: {data['block3_tolerance_pct']}%")
        print(f"  Block2 거래량 비율: {data['block2_volume_ratio']}%")
        print(f"  Block2 저가 마진: {data['block2_low_price_margin']}%")
        print(f"  Block2 최소 캔들: {data['block2_min_candles_after_block1']}")
        print(f"  Block3 거래량 비율: {data['block3_volume_ratio']}%")
        print(f"  Block3 저가 마진: {data['block3_low_price_margin']}%")
        print(f"  Block3 최소 캔들: {data['block3_min_candles_after_block2']}")

        if not dry_run:
            condition = RedetectionCondition(
                entry_surge_rate=data['entry_surge_rate'],
                entry_ma_period=data['entry_ma_period'],
                entry_high_above_ma=data['entry_high_above_ma'],
                entry_max_deviation_ratio=data['entry_max_deviation_ratio'],
                entry_min_trading_value=data['entry_min_trading_value'],
                entry_volume_high_months=data['entry_volume_high_months'],
                entry_volume_spike_ratio=data['entry_volume_spike_ratio'],
                entry_price_high_months=data['entry_price_high_months'],
                exit_ma_period=data['exit_ma_period'],
                cooldown_days=data['cooldown_days'],
                block1_tolerance_pct=data['block1_tolerance_pct'],
                block2_tolerance_pct=data['block2_tolerance_pct'],
                block3_tolerance_pct=data['block3_tolerance_pct'],
                block2_volume_ratio=data['block2_volume_ratio'],
                block2_low_price_margin=data['block2_low_price_margin'],
                block2_min_candles_after_block1=data['block2_min_candles_after_block1'],
                block3_volume_ratio=data['block3_volume_ratio'],
                block3_low_price_margin=data['block3_low_price_margin'],
                block3_min_candles_after_block2=data['block3_min_candles_after_block2']
            )

            repo.save(name, condition, data.get('description', ''))
            print(f"  [OK] DB 저장 완료")
        else:
            print(f"  [DRY RUN] 저장 건너뜀")


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
