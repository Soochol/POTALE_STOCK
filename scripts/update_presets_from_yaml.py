"""
Preset 데이터를 YAML 파일에서 읽어서 DB에 업데이트

사용법:
    python update_presets_from_yaml.py                    # 모든 preset 업데이트
    python update_presets_from_yaml.py --seed-only        # Seed 조건만 업데이트
    python update_presets_from_yaml.py --redetect-only    # 재탐지 조건만 업데이트
    python update_presets_from_yaml.py --dry-run          # 실제 저장 없이 미리보기만
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from loguru import logger
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == "win32":
    # 콘솔 코드페이지를 UTF-8로 설정
    os.system("chcp 65001 > nul")
    # 표준 출력/에러를 UTF-8로 재설정
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Loguru 설정
logger.remove()  # 기본 핸들러 제거
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

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
    """
    YAML 파일 로드

    Args:
        file_path: YAML 파일 경로

    Returns:
        YAML 파일 내용
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_table_header(title: str, width: int = 100) -> None:
    """
    테이블 헤더 출력

    Args:
        title: 테이블 제목
        width: 테이블 너비 (기본값: 100)
    """
    print()
    print("╔" + "═" * (width - 2) + "╗")
    print("║" + title.center(width - 2) + "║")
    print("╚" + "═" * (width - 2) + "╝")
    print()


def print_conditions_table(
    block1: dict,
    block2: dict,
    block3: dict,
    block4: dict,
    condition_type: str = "seed",
) -> None:
    """
    조건을 상세 테이블 형식으로 출력 (모든 항목) - Rich Table 사용

    Args:
        block1: Block1 조건 딕셔너리
        block2: Block2 조건 딕셔너리
        block3: Block3 조건 딕셔너리
        block4: Block4 조건 딕셔너리
        condition_type: 조건 타입 ("seed" 또는 "redetection")
    """

    console = Console()

    # 설명 텍스트 (조건 타입에 따라 다름)
    volume_ratio_desc = (
        "시드 블록 최고 거래량 대비"
        if condition_type == "redetection"
        else "이전 블록 최고 거래량 대비"
    )
    low_price_desc = (
        "시드 블록 최고가 대비 마진"
        if condition_type == "redetection"
        else "이전 블록 최고가 대비 마진"
    )

    # Helper: 값에 따라 색상 적용
    def color_value(text, numeric_val, threshold_high=None, threshold_low=None):
        """높을수록 엄격한 값은 빨강, 낮을수록 완화된 값은 초록"""
        if threshold_high and numeric_val >= threshold_high:
            return f"[red]{text}[/red]"
        elif threshold_low and numeric_val <= threshold_low:
            return f"[green]{text}[/green]"
        else:
            return f"[yellow]{text}[/yellow]"

    # 테이블 1: 주요 진입 조건
    table1 = Table(
        title="주요 진입 조건",
        show_header=True,
        header_style="bold magenta",
        title_style="bold cyan",
        box=box.ROUNDED  # 더 부드러운 박스 스타일
    )
    table1.add_column(
        "변수명", justify="left", style="bold cyan", no_wrap=True, width=18
    )
    table1.add_column("Block1", justify="center", width=12)
    table1.add_column("Block2", justify="center", width=12)
    table1.add_column("Block3", justify="center", width=12)
    table1.add_column("Block4", justify="center", width=12)
    table1.add_column("설명", justify="left", width=32)

    # 등락률 (높을수록 엄격 = 빨강, 낮을수록 완화 = 초록)
    b1_surge = block1['entry_surge_rate']
    b2_surge = block2.get('entry_surge_rate', block1['entry_surge_rate'])
    b3_surge = block3.get('entry_surge_rate', block1['entry_surge_rate'])
    b4_surge = block4.get('entry_surge_rate', 2.0)

    table1.add_row(
        "entry_surge_rate",
        color_value(
            f"{b1_surge:.1f}%", b1_surge, threshold_high=15, threshold_low=8
        ),
        color_value(
            f"{b2_surge:.1f}%", b2_surge, threshold_high=15, threshold_low=8
        ),
        color_value(
            f"{b3_surge:.1f}%", b3_surge, threshold_high=15, threshold_low=8
        ),
        color_value(
            f"{b4_surge:.1f}%", b4_surge, threshold_high=15, threshold_low=8
        ),
        "진입 조건 (당일 등락률)",
    )

    # 거래량 비율 (낮을수록 엄격 = 빨강)
    b2_vol = block2['volume_ratio']
    b3_vol = block3['volume_ratio']
    b4_vol = block4['volume_ratio']

    table1.add_row(
        "volume_ratio",
        "[dim]-[/dim]",
        color_value(f"{b2_vol:.1f}%", b2_vol, threshold_low=10),
        color_value(f"{b3_vol:.1f}%", b3_vol, threshold_low=10),
        color_value(f"{b4_vol:.1f}%", b4_vol, threshold_low=10),
        volume_ratio_desc,
    )

    # 저가 마진 (높을수록 완화 = 초록)
    b2_margin = block2['low_price_margin']
    b3_margin = block3['low_price_margin']
    b4_margin = block4['low_price_margin']

    table1.add_row(
        "low_price_margin",
        "[dim]-[/dim]",
        color_value(f"{b2_margin:.1f}%", b2_margin, threshold_low=5),
        color_value(f"{b3_margin:.1f}%", b3_margin, threshold_low=5),
        color_value(f"{b4_margin:.1f}%", b4_margin, threshold_low=5),
        low_price_desc,
    )

    # MA 기간
    table1.add_row(
        "entry_ma_period",
        f"{block1['entry_ma_period']}일",
        f"{block2.get('entry_ma_period', block1['entry_ma_period'])}일",
        f"{block3.get('entry_ma_period', block1['entry_ma_period'])}일",
        f"{block4.get('entry_ma_period', 60)}일",
        "진입 조건 이동평균선 기간"
    )

    # 최소/최대 캔들 (Seed 전용)
    if condition_type == "seed":
        table1.add_row(
            "min_candles",
            "-",
            f"{block2['min_candles_after_block1']}개",
            f"{block3['min_candles_after_block2']}개",
            f"{block4['min_candles_after_block3']}개",
            "이전 블록 시작 후 최소"
        )

        def format_max_candles(val):
            return f"{val}개" if val is not None else "제한없음"

        table1.add_row(
            "max_candles",
            "-",
            format_max_candles(block2.get('max_candles_after_block1')),
            format_max_candles(block3.get('max_candles_after_block2')),
            format_max_candles(block4.get('max_candles_after_block3')),
            "이전 블록 시작 후 최대"
        )

    console.print(table1)
    print()  # 빈 줄

    # 테이블 2: 상세 진입 조건
    table2 = Table(
        title="상세 진입 조건",
        show_header=True,
        header_style="bold magenta",
        title_style="bold cyan",
        box=box.ROUNDED
    )
    table2.add_column(
        "변수명", justify="left", style="bold cyan", no_wrap=True, width=18
    )
    table2.add_column("Block1", justify="center", width=12)
    table2.add_column("Block2", justify="center", width=12)
    table2.add_column("Block3", justify="center", width=12)
    table2.add_column("Block4", justify="center", width=12)
    table2.add_column("설명", justify="left", width=32)

    # 이격도
    default_deviation = block1.get('entry_max_deviation_ratio', 500.0)
    table2.add_row(
        "max_deviation",
        f"{default_deviation:.1f}%",
        f"{block2.get('entry_max_deviation_ratio', default_deviation):.1f}%",
        f"{block3.get('entry_max_deviation_ratio', default_deviation):.1f}%",
        f"{block4.get('entry_max_deviation_ratio', 500.0):.1f}%",
        "최대 이격도",
    )

    # 거래대금
    default_trading = block1.get('entry_min_trading_value', 0.0)
    table2.add_row(
        "min_trading",
        f"{default_trading:.0f}억",
        f"{block2.get('entry_min_trading_value', default_trading):.0f}억",
        f"{block3.get('entry_min_trading_value', default_trading):.0f}억",
        f"{block4.get('entry_min_trading_value', 0.0):.0f}억",
        "최소 거래대금",
    )

    # 신고 거래량
    def format_days(val):
        """일수 포맷팅"""
        return (
            f"[yellow]{val}일[/yellow]"
            if val is not None
            else "[dim]비활성화[/dim]"
        )

    table2.add_row(
        "volume_high",
        format_days(block1.get('entry_volume_high_days')),
        format_days(block2.get('entry_volume_high_days')),
        format_days(block3.get('entry_volume_high_days')),
        format_days(block4.get('entry_volume_high_days')),
        "N일 신고 거래량 (달력 기준)"
    )

    # 거래량 급증
    default_spike = block1.get('entry_volume_spike_ratio', 0.0)
    table2.add_row(
        "volume_spike",
        f"{default_spike:.1f}%",
        f"{block2.get('entry_volume_spike_ratio', default_spike):.1f}%",
        f"{block3.get('entry_volume_spike_ratio', default_spike):.1f}%",
        f"{block4.get('entry_volume_spike_ratio', 0.0):.1f}%",
        "전일 거래량 대비",
    )

    # 신고가
    table2.add_row(
        "price_high",
        format_days(block1.get('entry_price_high_days')),
        format_days(block2.get('entry_price_high_days')),
        format_days(block3.get('entry_price_high_days')),
        format_days(block4.get('entry_price_high_days')),
        "N일 신고가 (달력 기준)"
    )

    console.print(table2)
    print()  # 빈 줄

    # 테이블 3: 종료 조건
    table3 = Table(
        title="종료 조건",
        show_header=True,
        header_style="bold magenta",
        title_style="bold cyan",
        box=box.ROUNDED
    )
    table3.add_column(
        "변수명", justify="left", style="bold cyan", no_wrap=True, width=18
    )
    table3.add_column("Block1", justify="center", width=12)
    table3.add_column("Block2", justify="center", width=12)
    table3.add_column("Block3", justify="center", width=12)
    table3.add_column("Block4", justify="center", width=12)
    table3.add_column("설명", justify="left", width=32)

    # 종료 타입
    def format_exit_type(block):
        """종료 타입 포맷팅"""
        exit_type = block.get('exit_condition_type', 'ma_break')
        return "MA돌파" if exit_type == 'ma_break' else exit_type

    table3.add_row(
        "exit_type",
        format_exit_type(block1),
        format_exit_type(block2),
        format_exit_type(block3),
        format_exit_type(block4),
        "종료 조건 방식",
    )

    # 종료 MA
    table3.add_row(
        "exit_ma",
        f"{block1.get('exit_ma_period', 60)}일",
        f"{block2.get('exit_ma_period', block1.get('exit_ma_period', 60))}일",
        f"{block3.get('exit_ma_period', block1.get('exit_ma_period', 60))}일",
        f"{block4.get('exit_ma_period', 60)}일",
        "종료용 이동평균선"
    )

    # 쿨다운
    table3.add_row(
        "cooldown",
        f"{block1.get('cooldown_days', 20)}일",
        f"{block2.get('cooldown_days', block1.get('cooldown_days', 20))}일",
        f"{block3.get('cooldown_days', block1.get('cooldown_days', 20))}일",
        f"{block4.get('cooldown_days', 20)}일",
        "재진입 대기 기간"
    )

    console.print(table3)

    # 재탐지 전용 테이블 (재탐지 모드일 때만)
    if condition_type == "redetection":
        print()  # 빈 줄
        table4 = Table(
            title="재탐지 전용 조건",
            show_header=True,
            header_style="bold magenta",
            title_style="bold cyan",
            box=box.ROUNDED
        )
        table4.add_column(
            "변수명", justify="left", style="bold cyan", no_wrap=True, width=18
        )
        table4.add_column("Block1", justify="center", width=12)
        table4.add_column("Block2", justify="center", width=12)
        table4.add_column("Block3", justify="center", width=12)
        table4.add_column("Block4", justify="center", width=12)
        table4.add_column("설명", justify="left", width=32)

        # Tolerance
        table4.add_row(
            "tolerance_pct",
            f"{block1.get('tolerance_pct', 10.0):.1f}%",
            f"{block2.get('tolerance_pct', 10.0):.1f}%",
            f"{block3.get('tolerance_pct', 10.0):.1f}%",
            f"{block4.get('tolerance_pct', 10.0):.1f}%",
            "자기 Seed 블록 가격 기준 (±)"
        )

        # 재탐지 최소 기간 (Seed 발생일 기준)
        table4.add_row(
            "redetection_min_days",
            f"{block1.get('redetection_min_days_after_seed', 0)}일",
            f"{block2.get('redetection_min_days_after_seed', 0)}일",
            f"{block3.get('redetection_min_days_after_seed', 0)}일",
            f"{block4.get('redetection_min_days_after_seed', 0)}일",
            "각 Seed 발생일 + 최소일수"
        )

        # 재탐지 최대 기간 (Seed 발생일 기준)
        table4.add_row(
            "redetection_max_days",
            f"{block1.get('redetection_max_days_after_seed', 1825)}일",
            f"{block2.get('redetection_max_days_after_seed', 1825)}일",
            f"{block3.get('redetection_max_days_after_seed', 1825)}일",
            f"{block4.get('redetection_max_days_after_seed', 1825)}일",
            "각 Seed 발생일 + 최대일수 (5년=1825일)"
        )

        console.print(table4)

def update_seed_conditions(
    db: DatabaseConnection, json_data: dict, dry_run: bool = False
) -> None:
    """
    Seed 조건 업데이트 (블록별 섹션 구조 지원)

    Args:
        db: 데이터베이스 연결 객체
        json_data: YAML에서 로드한 조건 데이터
        dry_run: True일 경우 실제 저장하지 않음
    """
    console = Console()
    console.print(
        Panel(
            "[bold cyan]Seed Condition Presets 업데이트[/bold cyan]",
            border_style="cyan",
        )
    )
    print()

    repo = SeedConditionPresetRepository(db)

    for idx, (name, preset_data) in enumerate(json_data.items(), 1):
        logger.info(f"[{idx}/{len(json_data)}] 처리 중: {name}")
        console.print(f"[bold yellow]{name}[/bold yellow] - {preset_data.get('description', 'N/A')}")
        print()

        # 새 구조: block1, block2, block3, block4 섹션이 있는 경우
        if "block1" in preset_data:
            block1 = preset_data["block1"]
            block2 = preset_data["block2"]
            block3 = preset_data["block3"]
            block4 = preset_data["block4"]

            # 테이블 형식으로 출력
            print_conditions_table(
                block1, block2, block3, block4, condition_type="seed"
            )

            if not dry_run:
                # Block1 기본 조건 생성
                base = BaseEntryCondition(
                    block1_entry_surge_rate=block1["entry_surge_rate"],
                    block1_entry_ma_period=block1["entry_ma_period"],
                    block1_entry_max_deviation_ratio=block1[
                        "entry_max_deviation_ratio"
                    ],
                    block1_entry_min_trading_value=block1["entry_min_trading_value"],
                    block1_entry_volume_high_days=block1["entry_volume_high_days"],
                    block1_entry_volume_spike_ratio=block1["entry_volume_spike_ratio"],
                    block1_entry_price_high_days=block1["entry_price_high_days"],
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
                    block2_max_candles_after_block1=block2.get(
                        "max_candles_after_block1"
                    ),
                    block3_volume_ratio=block3["volume_ratio"],
                    block3_low_price_margin=block3["low_price_margin"],
                    block3_min_candles_after_block2=block3["min_candles_after_block2"],
                    block3_max_candles_after_block2=block3.get(
                        "max_candles_after_block2"
                    ),
                    block4_volume_ratio=block4["volume_ratio"],
                    block4_low_price_margin=block4["low_price_margin"],
                    block4_min_candles_after_block3=block4["min_candles_after_block3"],
                    block4_max_candles_after_block3=block4.get(
                        "max_candles_after_block3"
                    ),
                    # Block2 전용 파라미터 (Optional)
                    block2_entry_surge_rate=block2.get("entry_surge_rate"),
                    block2_entry_ma_period=block2.get("entry_ma_period"),
                    block2_entry_max_deviation_ratio=block2.get(
                        "entry_max_deviation_ratio"
                    ),
                    block2_entry_min_trading_value=block2.get(
                        "entry_min_trading_value"
                    ),
                    block2_entry_volume_high_days=block2.get(
                        "entry_volume_high_days"
                    ),
                    block2_entry_volume_spike_ratio=block2.get(
                        "entry_volume_spike_ratio"
                    ),
                    block2_entry_price_high_days=block2.get(
                        "entry_price_high_days"
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
                    block3_entry_max_deviation_ratio=block3.get(
                        "entry_max_deviation_ratio"
                    ),
                    block3_entry_min_trading_value=block3.get(
                        "entry_min_trading_value"
                    ),
                    block3_entry_volume_high_days=block3.get(
                        "entry_volume_high_days"
                    ),
                    block3_entry_volume_spike_ratio=block3.get(
                        "entry_volume_spike_ratio"
                    ),
                    block3_entry_price_high_days=block3.get(
                        "entry_price_high_days"
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
                    block4_entry_max_deviation_ratio=block4.get(
                        "entry_max_deviation_ratio"
                    ),
                    block4_entry_min_trading_value=block4.get(
                        "entry_min_trading_value"
                    ),
                    block4_entry_volume_high_days=block4.get(
                        "entry_volume_high_days"
                    ),
                    block4_entry_volume_spike_ratio=block4.get(
                        "entry_volume_spike_ratio"
                    ),
                    block4_entry_price_high_days=block4.get(
                        "entry_price_high_days"
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
                logger.success(f"DB 저장 완료: {name}")
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
) -> None:
    """
    재탐지 조건 업데이트 (블록별 섹션 구조 지원)

    Args:
        db: 데이터베이스 연결 객체
        json_data: YAML에서 로드한 조건 데이터
        dry_run: True일 경우 실제 저장하지 않음
    """
    console = Console()
    console.print(
        Panel(
            "[bold green]Redetection Condition Presets 업데이트[/bold green]",
            border_style="green",
        )
    )
    print()

    repo = RedetectionConditionPresetRepository(db)

    for idx, (name, preset_data) in enumerate(json_data.items(), 1):
        logger.info(f"[{idx}/{len(json_data)}] 처리 중: {name}")
        console.print(f"[bold yellow]{name}[/bold yellow] - {preset_data.get('description', 'N/A')}")
        print()

        # 새 구조: block1, block2, block3, block4 섹션이 있는 경우
        if "block1" in preset_data:
            block1 = preset_data["block1"]
            block2 = preset_data["block2"]
            block3 = preset_data["block3"]
            block4 = preset_data["block4"]

            # 테이블 형식으로 출력
            print_conditions_table(
                block1, block2, block3, block4, condition_type="redetection"
            )

            if not dry_run:
                # Block1 기본 조건 생성
                base = BaseEntryCondition(
                    block1_entry_surge_rate=block1["entry_surge_rate"],
                    block1_entry_ma_period=block1["entry_ma_period"],
                    block1_entry_max_deviation_ratio=block1[
                        "entry_max_deviation_ratio"
                    ],
                    block1_entry_min_trading_value=block1["entry_min_trading_value"],
                    block1_entry_volume_high_days=block1["entry_volume_high_days"],
                    block1_entry_volume_spike_ratio=block1["entry_volume_spike_ratio"],
                    block1_entry_price_high_days=block1["entry_price_high_days"],
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
                    # 재탐지 기간 범위 (Seed 발생일 기준)
                    block1_redetection_min_days_after_seed=block1["redetection_min_days_after_seed"],
                    block1_redetection_max_days_after_seed=block1["redetection_max_days_after_seed"],
                    block2_redetection_min_days_after_seed=block2["redetection_min_days_after_seed"],
                    block2_redetection_max_days_after_seed=block2["redetection_max_days_after_seed"],
                    block3_redetection_min_days_after_seed=block3["redetection_min_days_after_seed"],
                    block3_redetection_max_days_after_seed=block3["redetection_max_days_after_seed"],
                    block4_redetection_min_days_after_seed=block4["redetection_min_days_after_seed"],
                    block4_redetection_max_days_after_seed=block4["redetection_max_days_after_seed"],
                    block2_volume_ratio=block2["volume_ratio"],
                    block2_low_price_margin=block2["low_price_margin"],
                    block3_volume_ratio=block3["volume_ratio"],
                    block3_low_price_margin=block3["low_price_margin"],
                    block4_volume_ratio=block4["volume_ratio"],
                    block4_low_price_margin=block4["low_price_margin"],
                    # Block2 전용 파라미터 (Optional)
                    block2_entry_surge_rate=block2.get("entry_surge_rate"),
                    block2_entry_ma_period=block2.get("entry_ma_period"),
                    block2_entry_max_deviation_ratio=block2.get(
                        "entry_max_deviation_ratio"
                    ),
                    block2_entry_min_trading_value=block2.get(
                        "entry_min_trading_value"
                    ),
                    block2_entry_volume_high_days=block2.get(
                        "entry_volume_high_days"
                    ),
                    block2_entry_volume_spike_ratio=block2.get(
                        "entry_volume_spike_ratio"
                    ),
                    block2_entry_price_high_days=block2.get(
                        "entry_price_high_days"
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
                    block3_entry_max_deviation_ratio=block3.get(
                        "entry_max_deviation_ratio"
                    ),
                    block3_entry_min_trading_value=block3.get(
                        "entry_min_trading_value"
                    ),
                    block3_entry_volume_high_days=block3.get(
                        "entry_volume_high_days"
                    ),
                    block3_entry_volume_spike_ratio=block3.get(
                        "entry_volume_spike_ratio"
                    ),
                    block3_entry_price_high_days=block3.get(
                        "entry_price_high_days"
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
                    block4_entry_max_deviation_ratio=block4.get(
                        "entry_max_deviation_ratio"
                    ),
                    block4_entry_min_trading_value=block4.get(
                        "entry_min_trading_value"
                    ),
                    block4_entry_volume_high_days=block4.get(
                        "entry_volume_high_days"
                    ),
                    block4_entry_volume_spike_ratio=block4.get(
                        "entry_volume_spike_ratio"
                    ),
                    block4_entry_price_high_days=block4.get(
                        "entry_price_high_days"
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
                logger.success(f"DB 저장 완료: {name}")
                print()
            else:
                print(f"\n  [DRY RUN] 저장 건너뜀")

        # 구 구조: flat 구조 (하위 호환성)
        else:
            print(f"  [경고] 구 형식 JSON 구조 감지 - 블록별 섹션 구조로 업데이트 권장")
            print(f"  진입 등락률: {preset_data['entry_surge_rate']}%")
            print(f"  진입 MA: {preset_data['entry_ma_period']}일")
            # ... 구 형식 처리 생략 (필요 시 유지)


def main() -> None:
    """메인 함수: YAML 파일에서 Preset 데이터를 읽어 DB 업데이트"""
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

    console = Console()

    # DB 연결
    logger.info("데이터베이스 연결 중...")
    db = DatabaseConnection("data/database/stock_data.db")
    logger.success("데이터베이스 연결 완료")
    print()

    if args.dry_run:
        logger.warning("DRY RUN 모드: 실제로 DB에 저장하지 않습니다")
        print()

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
    if args.dry_run:
        console.print(Panel(
            "[bold yellow]DRY RUN 완료![/bold yellow]\n실제 저장은 하지 않았습니다",
            title="완료",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold green]✓ Preset 업데이트 완료![/bold green]",
            title="완료",
            border_style="green"
        ))
    print()


if __name__ == "__main__":
    main()
