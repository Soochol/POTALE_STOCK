"""
Collector Logger
수집기 통합 로깅 시스템
"""
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn,
    TimeElapsedColumn, TimeRemainingColumn
)
from typing import Optional


class CollectorLogger:
    """수집기 전용 로거"""

    def __init__(self, console: Optional[Console] = None):
        """
        Args:
            console: Rich Console 인스턴스 (없으면 새로 생성)
        """
        self.console = console or Console()

    def log_start(self, message: str):
        """수집 시작 로그"""
        self.console.print(f"\n[cyan]{'='*60}[/cyan]")
        self.console.print(f"[bold cyan]{message}[/bold cyan]")
        self.console.print(f"[cyan]{'='*60}[/cyan]\n")

    def log_success(self, message: str):
        """성공 로그"""
        self.console.print(f"[green]✓[/green] {message}")

    def log_error(self, message: str):
        """에러 로그"""
        self.console.print(f"[red]✗[/red] {message}")

    def log_warning(self, message: str):
        """경고 로그"""
        self.console.print(f"[yellow]![/yellow] {message}")

    def log_info(self, message: str):
        """정보 로그"""
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def log_section(self, step: str, message: str):
        """섹션 로그 (예: [1/3] 증분 수집 계획 수립 중...)"""
        self.console.print(f"\n[bold]{step}[/bold] {message}")

    def create_progress_bar(self):
        """진행률 표시 Progress Bar 생성"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("|"),
            TextColumn("{task.completed}/{task.total} 종목"),
            TextColumn("|"),
            TextColumn("[cyan]{task.fields[records]:,} 레코드[/cyan]"),
            TextColumn("|"),
            TimeElapsedColumn(),
            TextColumn("|"),
            TimeRemainingColumn(),
            console=self.console
        )


# 글로벌 로거 인스턴스
_global_logger: Optional[CollectorLogger] = None


def get_logger() -> CollectorLogger:
    """글로벌 로거 인스턴스 반환"""
    global _global_logger
    if _global_logger is None:
        _global_logger = CollectorLogger()
    return _global_logger
