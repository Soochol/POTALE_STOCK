"""
Preset 데이터를 YAML 파일에서 읽어서 DB에 업데이트

사용법:
    python update_presets_from_yaml.py                    # 모든 preset 업데이트
    python update_presets_from_yaml.py --seed-only        # Seed 조건만 업데이트
    python update_presets_from_yaml.py --redetect-only    # 재탐지 조건만 업데이트
    python update_presets_from_yaml.py --dry-run          # 실제 저장 없이 미리보기만
"""

import sys
import os
import yaml
import argparse
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.preset.seed_condition_preset_repository import (
    SeedConditionPresetRepository,
)
from src.infrastructure.repositories.preset.redetection_condition_preset_repository import (
    RedetectionConditionPresetRepository,
)
from src.domain.entities.conditions.seed_condition import SeedCondition
from src.domain.entities.conditions.redetection_condition import RedetectionCondition
from src.domain.entities.conditions.base_entry_condition import (
    BaseEntryCondition,
    Block1ExitConditionType,
)


def load_yaml_file(file_path: str) -> dict:
    """YAML 파일 로드"""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_table_header(title: str, width: int = 100):
    """테이블 헤더 출력"""
    print()
    print("╔" + "═" * (width - 2) + "╗")
    print("║" + title.center(width - 2) + "║")
    print("╚" + "═" * (width - 2) + "╝")
    print()


def print_conditions_table(block1: dict, block2: dict, block3: dict, block4: dict, condition_type: str = "seed"):
    """조건을 상세 테이블 형식으로 출력 (모든 항목)"""

    # 테이블 1: 주요 진입 조건
    print("┌" + "─" * 98 + "┐")
    print("│" + " 주요 진입 조건".center(98) + "│")
    print("├" + "─" * 14 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 32 + "┤")
    print("│" + " 항목".center(14) + "│" + " Block1".center(12) + "│" + " Block2".center(12) +
          "│" + " Block3".center(12) + "│" + " Block4".center(12) + "│" + " 설명".center(32) + "│")
    print("├" + "─" * 14 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 32 + "┤")

    # 등락률
    print("│" + " 등락률".center(14) + "│" +
          f"{block1['entry_surge_rate']:>6.1f}%".center(12) + "│" +
          f"{block2.get('entry_surge_rate', block1['entry_surge_rate']):>6.1f}%".center(12) + "│" +
          f"{block3.get('entry_surge_rate', block1['entry_surge_rate']):>6.1f}%".center(12) + "│" +
          f"{block4.get('entry_surge_rate', 2.0):>6.1f}%".center(12) + "│" +
          " 진입 조건 (당일 등락률)".ljust(32) + "│")

    # 거래량 비율
    print("│" + " 거래량 비율".center(14) + "│" +
          "  -".center(12) + "│" +
          f"{block2['volume_ratio']:>6.1f}%".center(12) + "│" +
          f"{block3['volume_ratio']:>6.1f}%".center(12) + "│" +
          f"{block4['volume_ratio']:>6.1f}%".center(12) + "│" +
          " 이전 블록 최고 거래량 대비".ljust(32) + "│")

    # 저가 마진
    print("│" + " 저가 마진".center(14) + "│" +
          "  -".center(12) + "│" +
          f"{block2['low_price_margin']:>6.1f}%".center(12) + "│" +
          f"{block3['low_price_margin']:>6.1f}%".center(12) + "│" +
          f"{block4['low_price_margin']:>6.1f}%".center(12) + "│" +
          " 이전 블록 최고가 대비 마진".ljust(32) + "│")

    # MA 기간
    print("│" + " MA 기간".center(14) + "│" +
          f"{block1['entry_ma_period']:>4d}일".center(12) + "│" +
          f"{block2.get('entry_ma_period', block1['entry_ma_period']):>4d}일".center(12) + "│" +
          f"{block3.get('entry_ma_period', block1['entry_ma_period']):>4d}일".center(12) + "│" +
          f"{block4.get('entry_ma_period', 60):>4d}일".center(12) + "│" +
          " 진입 조건 이동평균선 기간".ljust(32) + "│")

    # 고가 > MA
    print("│" + " 고가 > MA".center(14) + "│" +
          ("   예".center(12) if block1.get('entry_high_above_ma', True) else "  아니오".center(12)) + "│" +
          ("   예".center(12) if block2.get('entry_high_above_ma', True) else "  아니오".center(12)) + "│" +
          ("   예".center(12) if block3.get('entry_high_above_ma', True) else "  아니오".center(12)) + "│" +
          ("   예".center(12) if block4.get('entry_high_above_ma', True) else "  아니오".center(12)) + "│" +
          " 고가가 MA 상회 필수".ljust(32) + "│")

    # 최소 캔들
    print("│" + " 최소 캔들".center(14) + "│" +
          "  -".center(12) + "│" +
          f"{block2['min_candles_after_block1']:>4d}개".center(12) + "│" +
          f"{block3['min_candles_after_block2']:>4d}개".center(12) + "│" +
          f"{block4['min_candles_after_block3']:>4d}개".center(12) + "│" +
          " 이전 블록 시작 후 최소".ljust(32) + "│")

    # 최대 캔들 (선택적)
    def format_max_candles(val):
        return f"{val:>4d}개" if val is not None else "  제한없음"

    print("│" + " 최대 캔들".center(14) + "│" +
          "  -".center(12) + "│" +
          format_max_candles(block2.get('max_candles_after_block1')).center(12) + "│" +
          format_max_candles(block3.get('max_candles_after_block2')).center(12) + "│" +
          format_max_candles(block4.get('max_candles_after_block3')).center(12) + "│" +
          " 이전 블록 시작 후 최대".ljust(32) + "│")

    print("└" + "─" * 14 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 32 + "┘")
    print()

    # 테이블 2: 상세 진입 조건
    print("┌" + "─" * 98 + "┐")
    print("│" + " 상세 진입 조건".center(98) + "│")
    print("├" + "─" * 14 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 32 + "┤")
    print("│" + " 항목".center(14) + "│" + " Block1".center(12) + "│" + " Block2".center(12) +
          "│" + " Block3".center(12) + "│" + " Block4".center(12) + "│" + " 설명".center(32) + "│")
    print("├" + "─" * 14 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 32 + "┤")

    # 이격도
    print("│" + " 이격도".center(14) + "│" +
          f"{block1['entry_max_deviation_ratio']:>6.1f}%".center(12) + "│" +
          f"{block2.get('entry_max_deviation_ratio', block1['entry_max_deviation_ratio']):>6.1f}%".center(12) + "│" +
          f"{block3.get('entry_max_deviation_ratio', block1['entry_max_deviation_ratio']):>6.1f}%".center(12) + "│" +
          f"{block4.get('entry_max_deviation_ratio', 105.0):>6.1f}%".center(12) + "│" +
          " 최대 이격도".ljust(32) + "│")

    # 거래대금
    print("│" + " 거래대금".center(14) + "│" +
          f"{block1['entry_min_trading_value']:>5.0f}억".center(12) + "│" +
          f"{block2.get('entry_min_trading_value', block1['entry_min_trading_value']):>5.0f}억".center(12) + "│" +
          f"{block3.get('entry_min_trading_value', block1['entry_min_trading_value']):>5.0f}억".center(12) + "│" +
          f"{block4.get('entry_min_trading_value', 150.0):>5.0f}억".center(12) + "│" +
          " 최소 거래대금".ljust(32) + "│")

    # 신고 거래량
    def format_months(val):
        return f"{val:>3d}개월" if val is not None else "  비활성화"

    print("│" + " 신고 거래량".center(14) + "│" +
          format_months(block1['entry_volume_high_months']).center(12) + "│" +
          format_months(block2.get('entry_volume_high_months', block1['entry_volume_high_months'])).center(12) + "│" +
          format_months(block3.get('entry_volume_high_months', block1['entry_volume_high_months'])).center(12) + "│" +
          format_months(block4.get('entry_volume_high_months', 3)).center(12) + "│" +
          " N개월 신고 거래량".ljust(32) + "│")

    # 거래량 급증
    print("│" + " 거래량 급증".center(14) + "│" +
          f"{block1['entry_volume_spike_ratio']:>6.1f}%".center(12) + "│" +
          f"{block2.get('entry_volume_spike_ratio', block1['entry_volume_spike_ratio']):>6.1f}%".center(12) + "│" +
          f"{block3.get('entry_volume_spike_ratio', block1['entry_volume_spike_ratio']):>6.1f}%".center(12) + "│" +
          f"{block4.get('entry_volume_spike_ratio', 150.0):>6.1f}%".center(12) + "│" +
          " 전일 거래량 대비".ljust(32) + "│")

    # 신고가
    print("│" + " 신고가".center(14) + "│" +
          format_months(block1['entry_price_high_months']).center(12) + "│" +
          format_months(block2.get('entry_price_high_months', block1['entry_price_high_months'])).center(12) + "│" +
          format_months(block3.get('entry_price_high_months', block1['entry_price_high_months'])).center(12) + "│" +
          format_months(block4.get('entry_price_high_months', 1)).center(12) + "│" +
          " N개월 신고가".ljust(32) + "│")

    print("└" + "─" * 14 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 32 + "┘")
    print()

    # 테이블 3: 종료 조건
    print("┌" + "─" * 98 + "┐")
    print("│" + " 종료 조건".center(98) + "│")
    print("├" + "─" * 14 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 32 + "┤")
    print("│" + " 항목".center(14) + "│" + " Block1".center(12) + "│" + " Block2".center(12) +
          "│" + " Block3".center(12) + "│" + " Block4".center(12) + "│" + " 설명".center(32) + "│")
    print("├" + "─" * 14 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 32 + "┤")

    # 종료 타입
    exit_types = {"ma_break": "MA돌파", "three_line_reversal": "삼선전환", "body_middle": "몸통중간"}
    print("│" + " 종료 타입".center(14) + "│" +
          exit_types.get(block1.get('exit_condition_type', 'ma_break'), 'MA돌파').center(12) + "│" +
          exit_types.get(block2.get('exit_condition_type', 'ma_break'), 'MA돌파').center(12) + "│" +
          exit_types.get(block3.get('exit_condition_type', 'ma_break'), 'MA돌파').center(12) + "│" +
          exit_types.get(block4.get('exit_condition_type', 'ma_break'), 'MA돌파').center(12) + "│" +
          " 종료 조건 방식".ljust(32) + "│")

    # 종료 MA
    print("│" + " 종료 MA".center(14) + "│" +
          f"{block1['exit_ma_period']:>4d}일".center(12) + "│" +
          f"{block2.get('exit_ma_period', block1['exit_ma_period']):>4d}일".center(12) + "│" +
          f"{block3.get('exit_ma_period', block1['exit_ma_period']):>4d}일".center(12) + "│" +
          f"{block4.get('exit_ma_period', 60):>4d}일".center(12) + "│" +
          " 종료용 이동평균선".ljust(32) + "│")

    # 쿨다운
    print("│" + " 쿨다운".center(14) + "│" +
          f"{block1['cooldown_days']:>4d}일".center(12) + "│" +
          f"{block2.get('cooldown_days', block1['cooldown_days']):>4d}일".center(12) + "│" +
          f"{block3.get('cooldown_days', block1['cooldown_days']):>4d}일".center(12) + "│" +
          f"{block4.get('cooldown_days', 20):>4d}일".center(12) + "│" +
          " 재진입 대기 기간".ljust(32) + "│")

    print("└" + "─" * 14 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 32 + "┘")
    print()

    # 테이블 4: 재탐지 전용 (Tolerance)
    if condition_type == "redetection":
        print("┌" + "─" * 98 + "┐")
        print("│" + " 재탐지 전용 조건".center(98) + "│")
        print("├" + "─" * 14 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 32 + "┤")
        print("│" + " 항목".center(14) + "│" + " Block1".center(12) + "│" + " Block2".center(12) +
              "│" + " Block3".center(12) + "│" + " Block4".center(12) + "│" + " 설명".center(32) + "│")
        print("├" + "─" * 14 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 32 + "┤")

        # Tolerance
        print("│" + " Tolerance".center(14) + "│" +
              f"{block1.get('tolerance_pct', 0):>6.1f}%".center(12) + "│" +
              f"{block2.get('tolerance_pct', 0):>6.1f}%".center(12) + "│" +
              f"{block3.get('tolerance_pct', 0):>6.1f}%".center(12) + "│" +
              f"{block4.get('tolerance_pct', 0):>6.1f}%".center(12) + "│" +
              " 재탐지 가격 범위 (±)".ljust(32) + "│")

        print("└" + "─" * 14 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 32 + "┘")
        print()


def update_seed_conditions(
    db: DatabaseConnection, json_data: dict, dry_run: bool = False
):
    """Seed 조건 업데이트 (블록별 섹션 구조 지원)"""
    print_table_header("Seed Condition Presets 업데이트", 100)

    repo = SeedConditionPresetRepository(db)

    for name, preset_data in json_data.items():
        print(f"[{name}] {preset_data.get('description', 'N/A')}")
        print()

        # 새 구조: block1, block2, block3, block4 섹션이 있는 경우
        if "block1" in preset_data:
            block1 = preset_data["block1"]
            block2 = preset_data["block2"]
            block3 = preset_data["block3"]
            block4 = preset_data["block4"]

            # 테이블 형식으로 출력
            print_conditions_table(block1, block2, block3, block4, condition_type="seed")

            if not dry_run:
                # Block1 기본 조건 생성
                base = BaseEntryCondition(
                    block1_entry_surge_rate=block1["entry_surge_rate"],
                    block1_entry_ma_period=block1["entry_ma_period"],
                    block1_entry_high_above_ma=block1["entry_high_above_ma"],
                    block1_entry_max_deviation_ratio=block1[
                        "entry_max_deviation_ratio"
                    ],
                    block1_entry_min_trading_value=block1["entry_min_trading_value"],
                    block1_entry_volume_high_months=block1["entry_volume_high_months"],
                    block1_entry_volume_spike_ratio=block1["entry_volume_spike_ratio"],
                    block1_entry_price_high_months=block1["entry_price_high_months"],
                    block1_exit_condition_type=Block1ExitConditionType(
                        block1.get("exit_condition_type", "ma_break")
                    ),
                    block1_exit_ma_period=block1["exit_ma_period"],
                    block1_cooldown_days=block1["cooldown_days"],
                )

                condition = SeedCondition(
                    base=base,
                    block2_volume_ratio=block2["volume_ratio"],
                    block2_low_price_margin=block2["low_price_margin"],
                    block2_min_candles_after_block1=block2["min_candles_after_block1"],
                    block2_max_candles_after_block1=block2.get("max_candles_after_block1"),
                    block3_volume_ratio=block3["volume_ratio"],
                    block3_low_price_margin=block3["low_price_margin"],
                    block3_min_candles_after_block2=block3["min_candles_after_block2"],
                    block3_max_candles_after_block2=block3.get("max_candles_after_block2"),
                    block4_volume_ratio=block4["volume_ratio"],
                    block4_low_price_margin=block4["low_price_margin"],
                    block4_min_candles_after_block3=block4["min_candles_after_block3"],
                    block4_max_candles_after_block3=block4.get("max_candles_after_block3"),
                    # Block2 전용 파라미터 (Optional)
                    block2_entry_surge_rate=block2.get("entry_surge_rate"),
                    block2_entry_ma_period=block2.get("entry_ma_period"),
                    block2_entry_high_above_ma=block2.get("entry_high_above_ma"),
                    block2_entry_max_deviation_ratio=block2.get(
                        "entry_max_deviation_ratio"
                    ),
                    block2_entry_min_trading_value=block2.get(
                        "entry_min_trading_value"
                    ),
                    block2_entry_volume_high_months=block2.get(
                        "entry_volume_high_months"
                    ),
                    block2_entry_volume_spike_ratio=block2.get(
                        "entry_volume_spike_ratio"
                    ),
                    block2_entry_price_high_months=block2.get(
                        "entry_price_high_months"
                    ),
                    block2_exit_condition_type=(
                        Block1ExitConditionType(block2["exit_condition_type"])
                        if block2.get("exit_condition_type")
                        else None
                    ),
                    block2_exit_ma_period=block2.get("exit_ma_period"),
                    block2_cooldown_days=block2.get("cooldown_days"),
                    # Block3 전용 파라미터 (Optional)
                    block3_entry_surge_rate=block3.get("entry_surge_rate"),
                    block3_entry_ma_period=block3.get("entry_ma_period"),
                    block3_entry_high_above_ma=block3.get("entry_high_above_ma"),
                    block3_entry_max_deviation_ratio=block3.get(
                        "entry_max_deviation_ratio"
                    ),
                    block3_entry_min_trading_value=block3.get(
                        "entry_min_trading_value"
                    ),
                    block3_entry_volume_high_months=block3.get(
                        "entry_volume_high_months"
                    ),
                    block3_entry_volume_spike_ratio=block3.get(
                        "entry_volume_spike_ratio"
                    ),
                    block3_entry_price_high_months=block3.get(
                        "entry_price_high_months"
                    ),
                    block3_exit_condition_type=(
                        Block1ExitConditionType(block3["exit_condition_type"])
                        if block3.get("exit_condition_type")
                        else None
                    ),
                    block3_exit_ma_period=block3.get("exit_ma_period"),
                    block3_cooldown_days=block3.get("cooldown_days"),
                    # Block4 전용 파라미터 (Optional)
                    block4_entry_surge_rate=block4.get("entry_surge_rate"),
                    block4_entry_ma_period=block4.get("entry_ma_period"),
                    block4_entry_high_above_ma=block4.get("entry_high_above_ma"),
                    block4_entry_max_deviation_ratio=block4.get(
                        "entry_max_deviation_ratio"
                    ),
                    block4_entry_min_trading_value=block4.get(
                        "entry_min_trading_value"
                    ),
                    block4_entry_volume_high_months=block4.get(
                        "entry_volume_high_months"
                    ),
                    block4_entry_volume_spike_ratio=block4.get(
                        "entry_volume_spike_ratio"
                    ),
                    block4_entry_price_high_months=block4.get(
                        "entry_price_high_months"
                    ),
                    block4_exit_condition_type=(
                        Block1ExitConditionType(block4["exit_condition_type"])
                        if block4.get("exit_condition_type")
                        else None
                    ),
                    block4_exit_ma_period=block4.get("exit_ma_period"),
                    block4_cooldown_days=block4.get("cooldown_days"),
                )

                repo.save(name, condition, preset_data.get("description", ""))
                print("  ✓ DB 저장 완료")
                print()
            else:
                print(f"\n  [DRY RUN] 저장 건너뜀")

        # 구 구조: flat 구조 (하위 호환성)
        else:
            print(f"  [경고] 구 형식 JSON 구조 감지 - 블록별 섹션 구조로 업데이트 권장")
            print(f"  진입 등락률: {preset_data['entry_surge_rate']}%")
            print(f"  진입 MA: {preset_data['entry_ma_period']}일")
            # ... 구 형식 처리 생략 (필요 시 유지)


def update_redetection_conditions(
    db: DatabaseConnection, json_data: dict, dry_run: bool = False
):
    """재탐지 조건 업데이트 (블록별 섹션 구조 지원)"""
    print_table_header("Redetection Condition Presets 업데이트", 100)

    repo = RedetectionConditionPresetRepository(db)

    for name, preset_data in json_data.items():
        print(f"[{name}] {preset_data.get('description', 'N/A')}")
        print()

        # 새 구조: block1, block2, block3, block4 섹션이 있는 경우
        if "block1" in preset_data:
            block1 = preset_data["block1"]
            block2 = preset_data["block2"]
            block3 = preset_data["block3"]
            block4 = preset_data["block4"]

            # 테이블 형식으로 출력
            print_conditions_table(block1, block2, block3, block4, condition_type="redetection")

            if not dry_run:
                # Block1 기본 조건 생성
                base = BaseEntryCondition(
                    block1_entry_surge_rate=block1["entry_surge_rate"],
                    block1_entry_ma_period=block1["entry_ma_period"],
                    block1_entry_high_above_ma=block1["entry_high_above_ma"],
                    block1_entry_max_deviation_ratio=block1[
                        "entry_max_deviation_ratio"
                    ],
                    block1_entry_min_trading_value=block1["entry_min_trading_value"],
                    block1_entry_volume_high_months=block1["entry_volume_high_months"],
                    block1_entry_volume_spike_ratio=block1["entry_volume_spike_ratio"],
                    block1_entry_price_high_months=block1["entry_price_high_months"],
                    block1_exit_condition_type=Block1ExitConditionType(
                        block1.get("exit_condition_type", "ma_break")
                    ),
                    block1_exit_ma_period=block1["exit_ma_period"],
                    block1_cooldown_days=block1["cooldown_days"],
                )

                condition = RedetectionCondition(
                    base=base,
                    block1_tolerance_pct=block1["tolerance_pct"],
                    block2_tolerance_pct=block2["tolerance_pct"],
                    block3_tolerance_pct=block3["tolerance_pct"],
                    block4_tolerance_pct=block4["tolerance_pct"],
                    block2_volume_ratio=block2["volume_ratio"],
                    block2_low_price_margin=block2["low_price_margin"],
                    block2_min_candles_after_block1=block2["min_candles_after_block1"],
                    block2_max_candles_after_block1=block2.get("max_candles_after_block1"),
                    block3_volume_ratio=block3["volume_ratio"],
                    block3_low_price_margin=block3["low_price_margin"],
                    block3_min_candles_after_block2=block3["min_candles_after_block2"],
                    block3_max_candles_after_block2=block3.get("max_candles_after_block2"),
                    block4_volume_ratio=block4["volume_ratio"],
                    block4_low_price_margin=block4["low_price_margin"],
                    block4_min_candles_after_block3=block4["min_candles_after_block3"],
                    block4_max_candles_after_block3=block4.get("max_candles_after_block3"),
                    # Block2 전용 파라미터 (Optional)
                    block2_entry_surge_rate=block2.get("entry_surge_rate"),
                    block2_entry_ma_period=block2.get("entry_ma_period"),
                    block2_entry_high_above_ma=block2.get("entry_high_above_ma"),
                    block2_entry_max_deviation_ratio=block2.get(
                        "entry_max_deviation_ratio"
                    ),
                    block2_entry_min_trading_value=block2.get(
                        "entry_min_trading_value"
                    ),
                    block2_entry_volume_high_months=block2.get(
                        "entry_volume_high_months"
                    ),
                    block2_entry_volume_spike_ratio=block2.get(
                        "entry_volume_spike_ratio"
                    ),
                    block2_entry_price_high_months=block2.get(
                        "entry_price_high_months"
                    ),
                    block2_exit_condition_type=(
                        Block1ExitConditionType(block2["exit_condition_type"])
                        if block2.get("exit_condition_type")
                        else None
                    ),
                    block2_exit_ma_period=block2.get("exit_ma_period"),
                    block2_cooldown_days=block2.get("cooldown_days"),
                    # Block3 전용 파라미터 (Optional)
                    block3_entry_surge_rate=block3.get("entry_surge_rate"),
                    block3_entry_ma_period=block3.get("entry_ma_period"),
                    block3_entry_high_above_ma=block3.get("entry_high_above_ma"),
                    block3_entry_max_deviation_ratio=block3.get(
                        "entry_max_deviation_ratio"
                    ),
                    block3_entry_min_trading_value=block3.get(
                        "entry_min_trading_value"
                    ),
                    block3_entry_volume_high_months=block3.get(
                        "entry_volume_high_months"
                    ),
                    block3_entry_volume_spike_ratio=block3.get(
                        "entry_volume_spike_ratio"
                    ),
                    block3_entry_price_high_months=block3.get(
                        "entry_price_high_months"
                    ),
                    block3_exit_condition_type=(
                        Block1ExitConditionType(block3["exit_condition_type"])
                        if block3.get("exit_condition_type")
                        else None
                    ),
                    block3_exit_ma_period=block3.get("exit_ma_period"),
                    block3_cooldown_days=block3.get("cooldown_days"),
                    # Block4 전용 파라미터 (Optional)
                    block4_entry_surge_rate=block4.get("entry_surge_rate"),
                    block4_entry_ma_period=block4.get("entry_ma_period"),
                    block4_entry_high_above_ma=block4.get("entry_high_above_ma"),
                    block4_entry_max_deviation_ratio=block4.get(
                        "entry_max_deviation_ratio"
                    ),
                    block4_entry_min_trading_value=block4.get(
                        "entry_min_trading_value"
                    ),
                    block4_entry_volume_high_months=block4.get(
                        "entry_volume_high_months"
                    ),
                    block4_entry_volume_spike_ratio=block4.get(
                        "entry_volume_spike_ratio"
                    ),
                    block4_entry_price_high_months=block4.get(
                        "entry_price_high_months"
                    ),
                    block4_exit_condition_type=(
                        Block1ExitConditionType(block4["exit_condition_type"])
                        if block4.get("exit_condition_type")
                        else None
                    ),
                    block4_exit_ma_period=block4.get("exit_ma_period"),
                    block4_cooldown_days=block4.get("cooldown_days"),
                )

                repo.save(name, condition, preset_data.get("description", ""))
                print("  ✓ DB 저장 완료")
                print()
            else:
                print(f"\n  [DRY RUN] 저장 건너뜀")

        # 구 구조: flat 구조 (하위 호환성)
        else:
            print(f"  [경고] 구 형식 JSON 구조 감지 - 블록별 섹션 구조로 업데이트 권장")
            print(f"  진입 등락률: {preset_data['entry_surge_rate']}%")
            print(f"  진입 MA: {preset_data['entry_ma_period']}일")
            # ... 구 형식 처리 생략 (필요 시 유지)


def main():
    parser = argparse.ArgumentParser(
        description="YAML 파일에서 Preset 데이터를 읽어 DB 업데이트"
    )
    parser.add_argument("--seed-only", action="store_true", help="Seed 조건만 업데이트")
    parser.add_argument(
        "--redetect-only", action="store_true", help="재탐지 조건만 업데이트"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="실제 저장 없이 미리보기만"
    )
    parser.add_argument(
        "--seed-file",
        default="presets/seed_conditions.yaml",
        help="Seed 조건 YAML 파일 경로",
    )
    parser.add_argument(
        "--redetect-file",
        default="presets/redetection_conditions.yaml",
        help="재탐지 조건 YAML 파일 경로",
    )

    args = parser.parse_args()

    # DB 연결
    db = DatabaseConnection("data/database/stock_data.db")

    if args.dry_run:
        print("\n[!] DRY RUN 모드: 실제로 DB에 저장하지 않습니다.\n")

    # Seed 조건 업데이트
    if not args.redetect_only:
        if Path(args.seed_file).exists():
            seed_data = load_yaml_file(args.seed_file)
            update_seed_conditions(db, seed_data, args.dry_run)
        else:
            print(f"[!] 파일을 찾을 수 없습니다: {args.seed_file}")

    # 재탐지 조건 업데이트
    if not args.seed_only:
        if Path(args.redetect_file).exists():
            redetect_data = load_yaml_file(args.redetect_file)
            update_redetection_conditions(db, redetect_data, args.dry_run)
        else:
            print(f"[!] 파일을 찾을 수 없습니다: {args.redetect_file}")

    print()
    print("╔" + "═" * 68 + "╗")
    if args.dry_run:
        print("║" + " DRY RUN 완료! (실제 저장은 하지 않았습니다)".center(68) + "║")
    else:
        print("║" + " ✓ Preset 업데이트 완료!".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()


if __name__ == "__main__":
    main()
