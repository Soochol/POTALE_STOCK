"""
아난티 Block 탐지 결과 조회 스크립트
DB에서 저장된 모든 Block1/2/3 결과를 조회하여 표시
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.block2_repository import Block2Repository
from src.infrastructure.repositories.block3_repository import Block3Repository
from src.infrastructure.database.connection import DatabaseConnection
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def show_ananti_blocks():
    """아난티 Block 탐지 결과 조회"""

    ticker = "025980"
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    # Repository 초기화
    block1_repo = Block1Repository(db_conn)
    block2_repo = Block2Repository(db_conn)
    block3_repo = Block3Repository(db_conn)

    console.print(Panel.fit(
        f"[bold cyan]아난티({ticker}) Block 탐지 결과[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # ===================================================================
    # Block1 조회
    # ===================================================================
    console.print("[bold]1. Block1 탐지 결과[/bold]")
    console.print("="*80)

    try:
        block1_list = block1_repo.find_by_ticker(ticker)

        if not block1_list:
            console.print("[yellow]Block1 탐지 결과 없음[/yellow]\n")
        else:
            console.print(f"[green]총 {len(block1_list)}건 발견[/green]\n")

            # Block1 테이블
            table = Table(show_header=True, header_style="bold magenta", show_lines=True)
            table.add_column("No", style="cyan", width=4)
            table.add_column("조건명", style="yellow", width=12)
            table.add_column("시작일", style="green", width=12)
            table.add_column("종료일", style="red", width=12)
            table.add_column("상태", style="blue", width=10)
            table.add_column("지속\n(일)", justify="right", width=6)
            table.add_column("진입가\n(원)", justify="right", width=10)
            table.add_column("최고가\n(원)", justify="right", width=10)
            table.add_column("수익률\n(%)", justify="right", style="green bold", width=10)
            table.add_column("종료사유", width=15)

            # 시작일 기준 정렬
            block1_list = sorted(block1_list, key=lambda x: x.started_at)

            for i, block in enumerate(block1_list, 1):
                # 상태 색상
                status_color = "green" if block.status == "active" else "dim"

                # 종료일
                ended_str = str(block.ended_at) if block.ended_at else "-"

                # 지속 기간
                duration_str = str(block.duration_days) if block.duration_days else "-"

                # 진입가
                entry_price = f"{block.entry_close:,.0f}"

                # 최고가
                peak_price = f"{block.peak_price:,.0f}" if block.peak_price else "-"

                # 수익률
                gain_str = f"+{block.peak_gain_ratio:.2f}" if block.peak_gain_ratio else "-"

                # 종료 사유
                exit_reason = block.exit_reason if block.exit_reason else "-"

                table.add_row(
                    str(i),
                    block.condition_name,
                    str(block.started_at),
                    ended_str,
                    f"[{status_color}]{block.status}[/{status_color}]",
                    duration_str,
                    entry_price,
                    peak_price,
                    gain_str,
                    exit_reason
                )

            console.print(table)
            console.print()

            # 통계
            console.print("[bold]Block1 통계:[/bold]")

            # 진행중/완료
            active_count = sum(1 for b in block1_list if b.status == "active")
            completed_count = sum(1 for b in block1_list if b.status == "completed")
            console.print(f"  - 진행중: {active_count}건")
            console.print(f"  - 완료: {completed_count}건")

            # 평균 지속 기간
            durations = [b.duration_days for b in block1_list if b.duration_days]
            if durations:
                avg_duration = sum(durations) / len(durations)
                console.print(f"  - 평균 지속기간: {avg_duration:.1f}일")
                console.print(f"  - 최대 지속기간: {max(durations)}일")
                console.print(f"  - 최소 지속기간: {min(durations)}일")

            # 평균 수익률
            gains = [b.peak_gain_ratio for b in block1_list if b.peak_gain_ratio]
            if gains:
                avg_gain = sum(gains) / len(gains)
                console.print(f"  - 평균 수익률: +{avg_gain:.2f}%")
                console.print(f"  - 최대 수익률: +{max(gains):.2f}%")
                console.print(f"  - 최소 수익률: +{min(gains):.2f}%")

            # 조건별 분포
            from collections import Counter
            condition_counts = Counter(b.condition_name for b in block1_list)
            console.print(f"  - 조건별 분포:")
            for cond, count in condition_counts.items():
                console.print(f"    * {cond}: {count}건")

            # 종료 사유 분포
            exit_reasons = Counter(b.exit_reason for b in block1_list if b.exit_reason)
            if exit_reasons:
                console.print(f"  - 종료 사유:")
                for reason, count in exit_reasons.items():
                    console.print(f"    * {reason}: {count}건")

            console.print()

    except Exception as e:
        console.print(f"[red]Block1 조회 실패: {e}[/red]")
        import traceback
        traceback.print_exc()

    # ===================================================================
    # Block2 조회
    # ===================================================================
    console.print("[bold]2. Block2 탐지 결과[/bold]")
    console.print("="*80)

    try:
        block2_list = block2_repo.find_by_ticker(ticker)

        if not block2_list:
            console.print("[yellow]Block2 탐지 결과 없음[/yellow]\n")
        else:
            console.print(f"[green]총 {len(block2_list)}건 발견[/green]\n")

            # Block2 테이블
            table2 = Table(show_header=True, header_style="bold magenta", show_lines=True)
            table2.add_column("No", style="cyan", width=4)
            table2.add_column("조건명", style="yellow", width=12)
            table2.add_column("시작일", style="green", width=12)
            table2.add_column("종료일", style="red", width=12)
            table2.add_column("상태", style="blue", width=10)
            table2.add_column("지속(일)", justify="right", width=10)

            block2_list = sorted(block2_list, key=lambda x: x.started_at)

            for i, block in enumerate(block2_list, 1):
                status_color = "green" if block.status == "active" else "dim"
                ended_str = str(block.ended_at) if block.ended_at else "-"

                # 지속 기간 계산
                if block.ended_at and block.started_at:
                    duration = (block.ended_at - block.started_at).days
                else:
                    duration = None
                duration_str = str(duration) if duration else "-"

                table2.add_row(
                    str(i),
                    block.condition_name,
                    str(block.started_at),
                    ended_str,
                    f"[{status_color}]{block.status}[/{status_color}]",
                    duration_str
                )

            console.print(table2)
            console.print()

    except Exception as e:
        console.print(f"[red]Block2 조회 실패: {e}[/red]")
        import traceback
        traceback.print_exc()

    # ===================================================================
    # Block3 조회
    # ===================================================================
    console.print("[bold]3. Block3 탐지 결과[/bold]")
    console.print("="*80)

    try:
        block3_list = block3_repo.find_by_ticker(ticker)

        if not block3_list:
            console.print("[yellow]Block3 탐지 결과 없음[/yellow]\n")
        else:
            console.print(f"[green]총 {len(block3_list)}건 발견[/green]\n")

            # Block3 테이블
            table3 = Table(show_header=True, header_style="bold magenta", show_lines=True)
            table3.add_column("No", style="cyan", width=4)
            table3.add_column("조건명", style="yellow", width=12)
            table3.add_column("시작일", style="green", width=12)
            table3.add_column("종료일", style="red", width=12)
            table3.add_column("상태", style="blue", width=10)
            table3.add_column("지속(일)", justify="right", width=10)

            block3_list = sorted(block3_list, key=lambda x: x.started_at)

            for i, block in enumerate(block3_list, 1):
                status_color = "green" if block.status == "active" else "dim"
                ended_str = str(block.ended_at) if block.ended_at else "-"

                # 지속 기간 계산
                if block.ended_at and block.started_at:
                    duration = (block.ended_at - block.started_at).days
                else:
                    duration = None
                duration_str = str(duration) if duration else "-"

                table3.add_row(
                    str(i),
                    block.condition_name,
                    str(block.started_at),
                    ended_str,
                    f"[{status_color}]{block.status}[/{status_color}]",
                    duration_str
                )

            console.print(table3)
            console.print()

    except Exception as e:
        console.print(f"[red]Block3 조회 실패: {e}[/red]")
        import traceback
        traceback.print_exc()

    # ===================================================================
    # 전체 요약
    # ===================================================================
    console.print(Panel.fit(
        "[bold]전체 요약[/bold]\n"
        f"Block1: {len(block1_list) if block1_list else 0}건\n"
        f"Block2: {len(block2_list) if block2_list else 0}건\n"
        f"Block3: {len(block3_list) if block3_list else 0}건",
        border_style="green"
    ))

if __name__ == "__main__":
    show_ananti_blocks()
