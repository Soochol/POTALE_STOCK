"""
JSON Preset 파일과 DB의 이름(preset 목록)만 간단히 비교

presets/seed_conditions.json, presets/redetection_conditions.json과
DB의 seed_condition_preset, redetection_condition_preset 테이블에
같은 이름의 preset들이 있는지 확인합니다.
"""
import json
from pathlib import Path
from sqlalchemy import text
from src.infrastructure.database.connection import DatabaseConnection


def print_table(preset_type, json_names, db_names):
    """테이블 형식으로 preset 비교 출력"""
    print(f"\n[{preset_type}]")
    print("=" * 80)

    # 모든 preset 이름 수집
    all_names = sorted(set(json_names) | set(db_names))

    # 테이블 헤더
    print(f"{'Preset Name':<30} {'JSON':<10} {'DB':<10} {'Status':<15}")
    print("-" * 80)

    # 각 preset별로 출력
    for name in all_names:
        in_json = name in json_names
        in_db = name in db_names

        json_mark = "O" if in_json else "-"
        db_mark = "O" if in_db else "-"

        if in_json and in_db:
            status = "[OK] Both"
        elif in_json:
            status = "[WARN] JSON only"
        else:
            status = "[WARN] DB only"

        print(f"{name:<30} {json_mark:<10} {db_mark:<10} {status:<15}")

    # 요약
    both_count = len(set(json_names) & set(db_names))
    json_only_count = len(set(json_names) - set(db_names))
    db_only_count = len(set(db_names) - set(json_names))

    print("-" * 80)
    print(f"{'Total:':<30} {len(json_names):<10} {len(db_names):<10}")
    print(f"Common: {both_count}, JSON only: {json_only_count}, DB only: {db_only_count}")


def main():
    """메인 실행"""
    print("="*80)
    print("JSON Preset vs DB - 이름 비교 (Table Format)")
    print("="*80)

    # JSON 로드
    with open("presets/seed_conditions.json", 'r', encoding='utf-8') as f:
        seed_json = json.load(f)

    with open("presets/redetection_conditions.json", 'r', encoding='utf-8') as f:
        redetect_json = json.load(f)

    # DB 로드
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    with db_conn.session_scope() as session:
        # Seed preset 이름들
        result = session.execute(text("SELECT name FROM seed_condition_preset"))
        seed_db_names = [row[0] for row in result]

        # Redetection preset 이름들
        result = session.execute(text("SELECT name FROM redetection_condition_preset"))
        redetect_db_names = [row[0] for row in result]

    # Seed 비교 (테이블 형식)
    seed_json_names = list(seed_json.keys())
    print_table("SEED PRESETS", seed_json_names, seed_db_names)

    # Redetection 비교 (테이블 형식)
    redetect_json_names = list(redetect_json.keys())
    print_table("REDETECTION PRESETS", redetect_json_names, redetect_db_names)

    # 최종 요약
    seed_match = (set(seed_json_names) == set(seed_db_names))
    redetect_match = (set(redetect_json_names) == set(redetect_db_names))

    print("\n" + "="*80)
    print("Final Summary")
    print("="*80)
    print(f"Seed presets:        {'[OK] Match' if seed_match else '[DIFF] Mismatch'}")
    print(f"Redetection presets: {'[OK] Match' if redetect_match else '[DIFF] Mismatch'}")

    if seed_match and redetect_match:
        print("\n[OK] All preset names match between JSON and DB!")
    else:
        print("\n[DIFF] Some preset names do not match.")
    print("="*80)


if __name__ == "__main__":
    main()
