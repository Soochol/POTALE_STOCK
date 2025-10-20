"""
Preset 데이터를 YAML 파일에서 읽어서 DB에 업데이트 (상세 버전)

사용법:
    python update_presets_from_yaml_detailed.py                    # 모든 preset 업데이트
    python update_presets_from_yaml_detailed.py --seed-only        # Seed 조건만 업데이트
    python update_presets_from_yaml_detailed.py --redetect-only    # 재탐지 조건만 업데이트
    python update_presets_from_yaml_detailed.py --dry-run          # 실제 저장 없이 미리보기만
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


def print_conditions_table_detailed(block1: dict, block2: dict, block3: dict, block4: dict, condition_type: str = "seed"):
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
          " 이전 블록 시작 후 필요".ljust(32) + "│")

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
    print("│" + " 신고 거래량".center(14) + "│" +
          f"{block1['entry_volume_high_months']:>3d}개월".center(12) + "│" +
          f"{block2.get('entry_volume_high_months', block1['entry_volume_high_months']):>3d}개월".center(12) + "│" +
          f"{block3.get('entry_volume_high_months', block1['entry_volume_high_months']):>3d}개월".center(12) + "│" +
          f"{block4.get('entry_volume_high_months', 3):>3d}개월".center(12) + "│" +
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
          f"{block1['entry_price_high_months']:>3d}개월".center(12) + "│" +
          f"{block2.get('entry_price_high_months', block1['entry_price_high_months']):>3d}개월".center(12) + "│" +
          f"{block3.get('entry_price_high_months', block1['entry_price_high_months']):>3d}개월".center(12) + "│" +
          f"{block4.get('entry_price_high_months', 1):>3d}개월".center(12) + "│" +
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


print("새 파일 생성 완료!")
