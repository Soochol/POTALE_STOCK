"""
Block1~6 조건 비교 콘솔 시각화

YAML 파일에서 Seed/Redetection 조건을 읽어서 콘솔에 Rich하게 표시합니다.

사용법:
    python scripts/visualization/show_block_conditions.py
    python scripts/visualization/show_block_conditions.py --seed-only
    python scripts/visualization/show_block_conditions.py --redetect-only
    python scripts/visualization/show_block_conditions.py --diff-only
    python scripts/visualization/show_block_conditions.py --compact
"""

import argparse
import io
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == "win32":
    # 콘솔 코드페이지를 UTF-8로 설정
    os.system("chcp 65001 > nul")
    # 표준 출력/에러를 UTF-8로 재설정
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 기본 경로
DEFAULT_SEED_FILE = "presets/seed_conditions.yaml"
DEFAULT_REDETECT_FILE = "presets/redetection_conditions.yaml"


def load_yaml(file_path: str) -> Dict:
    """YAML 파일 로드"""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_value_color(value: Optional[float], param_type: str) -> str:
    """
    값에 따라 색상 결정

    Args:
        value: 파라미터 값
        param_type: 파라미터 타입 (surge_rate, volume_ratio, margin, etc.)

    Returns:
        Rich 색상 코드
    """
    if value is None:
        return "dim"

    # entry_surge_rate: 높을수록 엄격 (빨강)
    if param_type == "surge_rate":
        if value >= 15:
            return "red"
        elif value >= 10:
            return "yellow"
        else:
            return "green"

    # volume_ratio: 높을수록 엄격 (빨강)
    elif param_type == "volume_ratio":
        if value >= 50:
            return "red"
        elif value >= 20:
            return "yellow"
        else:
            return "green"

    # low_price_margin: 높을수록 완화 (초록)
    elif param_type == "margin":
        if value >= 10:
            return "green"
        elif value >= 5:
            return "yellow"
        else:
            return "red"

    return "white"


def format_value(value, unit: str = "", na_text: str = "-") -> str:
    """값 포맷팅"""
    if value is None:
        return f"[dim]{na_text}[/dim]"

    if unit == "%":
        return f"{value:.1f}%"
    elif unit == "일":
        return f"{value}일"
    elif unit == "억":
        return f"{value:.0f}억"
    elif unit == "개":
        return f"{value}개"
    elif unit == "bool":
        return "true" if value else "false"
    else:
        return str(value)


def format_colored_value(value, param_type: str, unit: str = "", na_text: str = "-") -> str:
    """색상이 적용된 값 포맷팅"""
    if value is None:
        return f"[dim]{na_text}[/dim]"

    color = get_value_color(value, param_type)
    formatted = format_value(value, unit)
    return f"[{color}]{formatted}[/{color}]"


def create_seed_table(data: Dict, compact: bool = False) -> Table:
    """Seed 조건 테이블 생성"""
    table = Table(
        title="[bold cyan]Seed Conditions[/bold cyan] (엄격한 조건)",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        title_style="bold cyan",
    )

    # 컬럼 추가
    table.add_column("Parameter", justify="left", style="bold", no_wrap=True, width=25)
    for i in range(1, 7):
        table.add_column(f"Block{i}", justify="center", width=10)

    preset = data["default_seed"]
    blocks = [preset[f"block{i}"] for i in range(1, 7)]

    # 진입 조건 섹션
    table.add_row("[bold yellow]진입 조건[/bold yellow]", "", "", "", "", "", "")

    # entry_surge_rate
    row = ["entry_surge_rate"]
    row.append(format_colored_value(blocks[0]["entry_surge_rate"], "surge_rate", "%"))
    for i in range(1, 6):
        val = blocks[i].get("entry_surge_rate", blocks[0]["entry_surge_rate"])
        row.append(format_colored_value(val, "surge_rate", "%"))
    table.add_row(*row)

    if not compact:
        # entry_ma_period
        row = ["entry_ma_period"]
        for block in blocks:
            val = block.get("entry_ma_period")
            row.append(format_value(val, "일"))
        table.add_row(*row)

        # entry_min_trading_value
        row = ["entry_min_trading"]
        for block in blocks:
            val = block.get("entry_min_trading_value")
            row.append(format_value(val, "억"))
        table.add_row(*row)

        # entry_volume_spike_ratio
        row = ["volume_spike"]
        for block in blocks:
            val = block.get("entry_volume_spike_ratio")
            row.append(format_value(val, "%"))
        table.add_row(*row)

    # 추가 조건 섹션
    table.add_row("[bold yellow]추가 조건[/bold yellow] (이전 블록 기준)", "", "", "", "", "", "")

    # volume_ratio
    row = ["volume_ratio"]
    row.append("[dim]N/A[/dim]")
    for i in range(1, 6):
        val = blocks[i].get("volume_ratio")
        row.append(format_colored_value(val, "volume_ratio", "%"))
    table.add_row(*row)

    # low_price_margin
    row = ["low_price_margin"]
    row.append("[dim]N/A[/dim]")
    for i in range(1, 6):
        val = blocks[i].get("low_price_margin")
        row.append(format_colored_value(val, "margin", "%"))
    table.add_row(*row)

    if not compact:
        # min_candles
        row = ["min_candles"]
        row.append("[dim]N/A[/dim]")
        for i in range(1, 6):
            val = blocks[i].get(f"min_candles_after_block{i}")
            row.append(format_value(val, "개"))
        table.add_row(*row)

        # max_candles
        row = ["max_candles"]
        row.append("[dim]N/A[/dim]")
        for i in range(1, 6):
            val = blocks[i].get(f"max_candles_after_block{i}")
            row.append(format_value(val, "개", "무제한"))
        table.add_row(*row)

    # 종료 조건 섹션
    if not compact:
        table.add_row("[bold yellow]종료 조건[/bold yellow]", "", "", "", "", "", "")

        # exit_ma_period
        row = ["exit_ma_period"]
        for block in blocks:
            val = block.get("exit_ma_period")
            row.append(format_value(val, "일"))
        table.add_row(*row)

        # auto_exit_on_next_block
        row = ["auto_exit_next"]
        for block in blocks:
            val = block.get("auto_exit_on_next_block")
            row.append(format_value(val, "bool"))
        table.add_row(*row)

        # min_start_interval_days
        row = ["min_start_interval"]
        for block in blocks:
            val = block.get("min_start_interval_days")
            row.append(format_value(val, "일"))
        table.add_row(*row)

    return table


def create_redetection_table(data: Dict, compact: bool = False) -> Table:
    """Redetection 조건 테이블 생성"""
    table = Table(
        title="[bold green]Redetection Conditions[/bold green] (완화된 조건)",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        title_style="bold green",
    )

    # 컬럼 추가
    table.add_column("Parameter", justify="left", style="bold", no_wrap=True, width=25)
    for i in range(1, 7):
        table.add_column(f"Block{i}", justify="center", width=10)

    preset = data["default_redetect"]
    blocks = [preset[f"block{i}"] for i in range(1, 7)]

    # 진입 조건 섹션
    table.add_row("[bold yellow]진입 조건[/bold yellow]", "", "", "", "", "", "")

    # entry_surge_rate
    row = ["entry_surge_rate"]
    row.append(format_colored_value(blocks[0]["entry_surge_rate"], "surge_rate", "%"))
    for i in range(1, 6):
        val = blocks[i].get("entry_surge_rate", blocks[0]["entry_surge_rate"])
        row.append(format_colored_value(val, "surge_rate", "%"))
    table.add_row(*row)

    if not compact:
        # entry_ma_period
        row = ["entry_ma_period"]
        for block in blocks:
            val = block.get("entry_ma_period")
            row.append(format_value(val, "일"))
        table.add_row(*row)

        # entry_min_trading_value
        row = ["entry_min_trading"]
        for block in blocks:
            val = block.get("entry_min_trading_value")
            row.append(format_value(val, "억"))
        table.add_row(*row)

    # 추가 조건 섹션
    table.add_row("[bold yellow]추가 조건[/bold yellow] (시드 블록 기준)", "", "", "", "", "", "")

    # volume_ratio
    row = ["volume_ratio"]
    row.append("[dim]N/A[/dim]")
    for i in range(1, 6):
        val = blocks[i].get("volume_ratio")
        row.append(format_colored_value(val, "volume_ratio", "%"))
    table.add_row(*row)

    # low_price_margin
    row = ["low_price_margin"]
    row.append("[dim]N/A[/dim]")
    for i in range(1, 6):
        val = blocks[i].get("low_price_margin")
        row.append(format_colored_value(val, "margin", "%"))
    table.add_row(*row)

    # 재탐지 전용 조건
    table.add_row("[bold yellow]재탐지 전용[/bold yellow]", "", "", "", "", "", "")

    # tolerance_pct
    row = ["tolerance_pct"]
    for block in blocks:
        val = block.get("tolerance_pct")
        row.append(format_value(val, "%"))
    table.add_row(*row)

    if not compact:
        # redetection_min_days_after_seed
        row = ["redetect_min_days"]
        for block in blocks:
            val = block.get("redetection_min_days_after_seed")
            row.append(format_value(val, "일"))
        table.add_row(*row)

        # redetection_max_days_after_seed
        row = ["redetect_max_days"]
        for block in blocks:
            val = block.get("redetection_max_days_after_seed")
            row.append(format_value(val, "일"))
        table.add_row(*row)

    return table


def create_ascii_bar_chart(seed_data: Dict, redetect_data: Dict, param: str, title: str, max_val: float = 100.0) -> str:
    """ASCII 막대 차트 생성"""
    lines = []
    lines.append(f"\n[bold cyan]{title}[/bold cyan]")
    lines.append("")

    # Seed 조건
    lines.append("[yellow]Seed:[/yellow]")
    seed_preset = seed_data["default_seed"]
    for i in range(1, 7):
        block = seed_preset[f"block{i}"]

        if i == 1 and param in ["volume_ratio", "low_price_margin"]:
            lines.append(f"  Block{i}: [dim]N/A[/dim]")
            continue

        val = block.get(param)
        if val is None:
            lines.append(f"  Block{i}: [dim]N/A[/dim]")
            continue

        bar_length = int((val / max_val) * 40)
        bar = "■" * bar_length
        color = get_value_color(val, param.replace("entry_", "").replace("_", ""))
        lines.append(f"  Block{i}: [{color}]{bar}[/{color}] {val:.1f}%")

    # Redetection 조건
    lines.append("")
    lines.append("[green]Redetection:[/green]")
    redetect_preset = redetect_data["default_redetect"]
    for i in range(1, 7):
        block = redetect_preset[f"block{i}"]

        if i == 1 and param in ["volume_ratio", "low_price_margin"]:
            lines.append(f"  Block{i}: [dim]N/A[/dim]")
            continue

        val = block.get(param)
        if val is None:
            lines.append(f"  Block{i}: [dim]N/A[/dim]")
            continue

        bar_length = int((val / max_val) * 40)
        bar = "■" * bar_length
        color = get_value_color(val, param.replace("entry_", "").replace("_", ""))
        lines.append(f"  Block{i}: [{color}]{bar}[/{color}] {val:.1f}%")

    return "\n".join(lines)


def create_diff_table(seed_data: Dict, redetect_data: Dict) -> Table:
    """Seed vs Redetection 차이 분석 테이블"""
    table = Table(
        title="[bold magenta]Seed vs Redetection 주요 차이점[/bold magenta]",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
    )

    table.add_column("Parameter", justify="left", style="bold", width=25)
    table.add_column("Block", justify="center", width=10)
    table.add_column("Seed", justify="center", width=15)
    table.add_column("Redetection", justify="center", width=15)
    table.add_column("차이", justify="center", width=15)

    seed_preset = seed_data["default_seed"]
    redetect_preset = redetect_data["default_redetect"]

    # Block1 entry_surge_rate
    seed_val = seed_preset["block1"]["entry_surge_rate"]
    redetect_val = redetect_preset["block1"]["entry_surge_rate"]
    diff = seed_val - redetect_val
    diff_text = f"{diff:+.1f}%" if diff != 0 else "동일"
    diff_color = "red" if diff > 0 else "green" if diff < 0 else "yellow"
    table.add_row(
        "entry_surge_rate",
        "Block1",
        f"[red]{seed_val:.1f}%[/red]",
        f"[green]{redetect_val:.1f}%[/green]",
        f"[{diff_color}]{diff_text}[/{diff_color}]"
    )

    # Block2 volume_ratio
    seed_val = seed_preset["block2"]["volume_ratio"]
    redetect_val = redetect_preset["block2"]["volume_ratio"]
    diff = seed_val - redetect_val
    diff_text = f"{diff:+.1f}%" if diff != 0 else "동일"
    diff_color = "red" if diff > 0 else "green" if diff < 0 else "yellow"
    table.add_row(
        "volume_ratio",
        "Block2",
        f"[red]{seed_val:.1f}%[/red]",
        f"[green]{redetect_val:.1f}%[/green]",
        f"[{diff_color}]{diff_text}[/{diff_color}]"
    )

    # Redetection 전용: tolerance_pct
    redetect_val = redetect_preset["block1"]["tolerance_pct"]
    table.add_row(
        "tolerance_pct",
        "Block1",
        "[dim]N/A[/dim]",
        f"{redetect_val:.1f}%",
        "[cyan](재탐지 전용)[/cyan]"
    )

    return table


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Block1~6 조건 비교 콘솔 시각화")
    parser.add_argument("--seed-only", action="store_true", help="Seed 조건만 표시")
    parser.add_argument("--redetect-only", action="store_true", help="Redetection 조건만 표시")
    parser.add_argument("--diff-only", action="store_true", help="차이점만 표시")
    parser.add_argument("--compact", action="store_true", help="간략한 버전 (주요 파라미터만)")
    parser.add_argument("--no-bars", action="store_true", help="막대 차트 제외")

    args = parser.parse_args()

    console = Console(width=140)

    # YAML 로드
    seed_data = load_yaml(DEFAULT_SEED_FILE)
    redetect_data = load_yaml(DEFAULT_REDETECT_FILE)

    # 타이틀
    console.print()
    console.print(Panel(
        "[bold cyan]Block1~6 Conditions Comparison[/bold cyan]\n"
        "[dim]Seed vs Redetection 조건 비교[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()

    # Seed 테이블
    if not args.redetect_only and not args.diff_only:
        seed_table = create_seed_table(seed_data, args.compact)
        console.print(seed_table)
        console.print()

    # Redetection 테이블
    if not args.seed_only and not args.diff_only:
        redetect_table = create_redetection_table(redetect_data, args.compact)
        console.print(redetect_table)
        console.print()

    # 막대 차트
    if not args.no_bars and not args.diff_only and not args.compact:
        console.print(Panel(
            "[bold yellow]주요 파라미터 막대 차트[/bold yellow]",
            border_style="yellow"
        ))

        # entry_surge_rate
        bar1 = create_ascii_bar_chart(
            seed_data, redetect_data,
            "entry_surge_rate",
            "entry_surge_rate (등락률 %)",
            max_val=20.0
        )
        console.print(bar1)
        console.print()

        # volume_ratio
        bar2 = create_ascii_bar_chart(
            seed_data, redetect_data,
            "volume_ratio",
            "volume_ratio (이전 블록 대비 거래량 %)",
            max_val=100.0
        )
        console.print(bar2)
        console.print()

        # low_price_margin
        bar3 = create_ascii_bar_chart(
            seed_data, redetect_data,
            "low_price_margin",
            "low_price_margin (이전 블록 최고가 대비 마진 %)",
            max_val=15.0
        )
        console.print(bar3)
        console.print()

    # 차이 분석
    if not args.seed_only and not args.redetect_only:
        diff_table = create_diff_table(seed_data, redetect_data)
        console.print(diff_table)
        console.print()

    # 요약 패널
    console.print(Panel(
        "[bold green]✓ 시각화 완료![/bold green]\n\n"
        "[dim]옵션:[/dim]\n"
        "  --seed-only      : Seed 조건만\n"
        "  --redetect-only  : Redetection 조건만\n"
        "  --diff-only      : 차이점만\n"
        "  --compact        : 간략 버전\n"
        "  --no-bars        : 막대 차트 제외",
        title="완료",
        border_style="green"
    ))
    console.print()


if __name__ == "__main__":
    main()
