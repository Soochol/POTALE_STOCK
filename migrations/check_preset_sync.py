"""
JSON Preset 파일과 DB 데이터 동기화 확인

presets/seed_conditions.json, presets/redetection_conditions.json과
DB의 seed_condition_preset, redetection_condition_preset 테이블 데이터를 비교합니다.
"""
import json
from pathlib import Path
from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def load_json_presets():
    """JSON 파일에서 preset 로드"""
    seed_path = Path("presets/seed_conditions.json")
    redetect_path = Path("presets/redetection_conditions.json")

    with open(seed_path, 'r', encoding='utf-8') as f:
        seed_presets = json.load(f)

    with open(redetect_path, 'r', encoding='utf-8') as f:
        redetect_presets = json.load(f)

    return seed_presets, redetect_presets


def load_db_presets():
    """DB에서 preset 로드"""
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    seed_db = {}
    redetect_db = {}

    with db_conn.session_scope() as session:
        # Seed presets
        result = session.execute(text("SELECT * FROM seed_condition_preset"))
        columns = result.keys()
        for row in result:
            row_dict = dict(zip(columns, row))
            seed_db[row_dict['name']] = row_dict

        # Redetection presets
        result = session.execute(text("SELECT * FROM redetection_condition_preset"))
        columns = result.keys()
        for row in result:
            row_dict = dict(zip(columns, row))
            redetect_db[row_dict['name']] = row_dict

    return seed_db, redetect_db


def compare_seed_preset(name, json_data, db_data):
    """Seed preset 비교"""
    print(f"\n{'='*80}")
    print(f"[Seed Preset] {name}")
    print(f"{'='*80}")

    if name not in db_data:
        print(f"[ERROR] DB에 '{name}' preset이 없습니다!")
        return False

    db_row = db_data[name]
    all_match = True

    # Block1 필드 비교
    block1 = json_data['block1']
    comparisons = [
        ('block1_entry_surge_rate', block1.get('entry_surge_rate')),
        ('block1_entry_ma_period', block1.get('entry_ma_period')),
        ('block1_entry_high_above_ma', 1 if block1.get('entry_high_above_ma') else 0),
        ('block1_entry_max_deviation_ratio', block1.get('entry_max_deviation_ratio')),
        ('block1_entry_min_trading_value', block1.get('entry_min_trading_value')),
        ('block1_entry_volume_high_months', block1.get('entry_volume_high_months')),
        ('block1_entry_volume_spike_ratio', block1.get('entry_volume_spike_ratio')),
        ('block1_entry_price_high_months', block1.get('entry_price_high_months')),
        ('block1_exit_ma_period', block1.get('exit_ma_period')),
        ('block1_cooldown_days', block1.get('cooldown_days')),
    ]

    print("\n[Block1 필드]")
    for db_field, json_value in comparisons:
        db_value = db_row.get(db_field)
        match = (db_value == json_value)
        symbol = "[OK]" if match else "[DIFF]"
        print(f"  {symbol} {db_field}: DB={db_value}, JSON={json_value}")
        if not match:
            all_match = False

    # Block2/3/4 필드 비교
    for block_num in [2, 3, 4]:
        block_key = f'block{block_num}'
        if block_key not in json_data:
            continue

        block = json_data[block_key]
        print(f"\n[Block{block_num} 필드]")

        # Block별 고유 필드
        comparisons = [
            (f'block{block_num}_entry_surge_rate', block.get('entry_surge_rate')),
            (f'block{block_num}_entry_ma_period', block.get('entry_ma_period')),
            (f'block{block_num}_entry_high_above_ma', 1 if block.get('entry_high_above_ma') else 0 if block.get('entry_high_above_ma') is False else None),
            (f'block{block_num}_exit_ma_period', block.get('exit_ma_period')),
            (f'block{block_num}_cooldown_days', block.get('cooldown_days')),
            (f'block{block_num}_volume_ratio', block.get('volume_ratio')),
            (f'block{block_num}_low_price_margin', block.get('low_price_margin')),
            (f'block{block_num}_min_candles_after_block{block_num-1}', block.get('min_candles_after_prev')),
        ]

        for db_field, json_value in comparisons:
            db_value = db_row.get(db_field)
            match = (db_value == json_value)
            symbol = "[OK]" if match else "[DIFF]"
            print(f"  {symbol} {db_field}: DB={db_value}, JSON={json_value}")
            if not match:
                all_match = False

    return all_match


def compare_redetection_preset(name, json_data, db_data):
    """Redetection preset 비교"""
    print(f"\n{'='*80}")
    print(f"[Redetection Preset] {name}")
    print(f"{'='*80}")

    if name not in db_data:
        print(f"[ERROR] DB에 '{name}' preset이 없습니다!")
        return False

    db_row = db_data[name]
    all_match = True

    # Block1 필드 비교
    block1 = json_data['block1']
    comparisons = [
        ('block1_entry_surge_rate', block1.get('entry_surge_rate')),
        ('block1_entry_ma_period', block1.get('entry_ma_period')),
        ('block1_entry_high_above_ma', 1 if block1.get('entry_high_above_ma') else 0),
        ('block1_exit_ma_period', block1.get('exit_ma_period')),
        ('block1_cooldown_days', block1.get('cooldown_days')),
        ('block1_tolerance_pct', block1.get('tolerance_pct')),
    ]

    print("\n[Block1 필드]")
    for db_field, json_value in comparisons:
        db_value = db_row.get(db_field)
        match = (db_value == json_value)
        symbol = "[OK]" if match else "[DIFF]"
        print(f"  {symbol} {db_field}: DB={db_value}, JSON={json_value}")
        if not match:
            all_match = False

    # Block2/3/4 필드 비교
    for block_num in [2, 3, 4]:
        block_key = f'block{block_num}'
        if block_key not in json_data:
            continue

        block = json_data[block_key]
        print(f"\n[Block{block_num} 필드]")

        comparisons = [
            (f'block{block_num}_tolerance_pct', block.get('tolerance_pct')),
            (f'block{block_num}_entry_surge_rate', block.get('entry_surge_rate')),
            (f'block{block_num}_volume_ratio', block.get('volume_ratio')),
            (f'block{block_num}_low_price_margin', block.get('low_price_margin')),
            (f'block{block_num}_min_candles_after_block{block_num-1}', block.get('min_candles_after_prev')),
        ]

        for db_field, json_value in comparisons:
            db_value = db_row.get(db_field)
            match = (db_value == json_value)
            symbol = "[OK]" if match else "[DIFF]"
            print(f"  {symbol} {db_field}: DB={db_value}, JSON={json_value}")
            if not match:
                all_match = False

    return all_match


def main():
    """메인 실행"""
    print("="*80)
    print("JSON Preset vs DB 데이터 동기화 확인")
    print("="*80)

    # 데이터 로드
    seed_json, redetect_json = load_json_presets()
    seed_db, redetect_db = load_db_presets()

    print(f"\n[파일 로드 완료]")
    print(f"  Seed JSON: {list(seed_json.keys())}")
    print(f"  Seed DB: {list(seed_db.keys())}")
    print(f"  Redetection JSON: {list(redetect_json.keys())}")
    print(f"  Redetection DB: {list(redetect_db.keys())}")

    all_results = []

    # Seed presets 비교
    print("\n" + "="*80)
    print("SEED PRESETS 비교")
    print("="*80)
    for name in seed_json:
        result = compare_seed_preset(name, seed_json[name], seed_db)
        all_results.append((f"Seed: {name}", result))

    # Redetection presets 비교
    print("\n" + "="*80)
    print("REDETECTION PRESETS 비교")
    print("="*80)
    for name in redetect_json:
        result = compare_redetection_preset(name, redetect_json[name], redetect_db)
        all_results.append((f"Redetection: {name}", result))

    # 최종 요약
    print("\n" + "="*80)
    print("최종 요약")
    print("="*80)
    for name, result in all_results:
        symbol = "[OK]" if result else "[DIFF]"
        print(f"{symbol} {name}: {'일치' if result else '불일치'}")

    all_match = all(result for _, result in all_results)
    print("\n" + "="*80)
    if all_match:
        print("[OK] 모든 preset이 JSON과 DB에서 일치합니다!")
    else:
        print("[DIFF] 일부 preset이 불일치합니다. 위 내용을 확인하세요.")
    print("="*80)


if __name__ == "__main__":
    main()
