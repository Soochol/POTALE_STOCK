"""
Base Collector - 데이터 수집기 베이스 클래스
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from rich.console import Console

console = Console()


@dataclass
class CollectionResult:
    """데이터 수집 결과"""
    success: bool
    record_count: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """소요 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class BaseCollector(ABC):
    """데이터 수집기 베이스 클래스"""

    def __init__(self, delay: float = 0.1):
        """
        Args:
            delay: API 호출 간 대기 시간 (초)
        """
        self.delay = delay
        self.console = Console()

    @abstractmethod
    def collect(self, *args, **kwargs) -> CollectionResult:
        """
        데이터 수집 실행

        Returns:
            CollectionResult
        """
        pass

    def _log_start(self, message: str):
        """수집 시작 로그"""
        self.console.print(f"\n[cyan]{'='*60}[/cyan]")
        self.console.print(f"[bold cyan]{message}[/bold cyan]")
        self.console.print(f"[cyan]{'='*60}[/cyan]\n")

    def _log_success(self, message: str):
        """성공 로그"""
        self.console.print(f"[green]✓[/green] {message}")

    def _log_error(self, message: str):
        """에러 로그"""
        self.console.print(f"[red]✗[/red] {message}")

    def _log_warning(self, message: str):
        """경고 로그"""
        self.console.print(f"[yellow]![/yellow] {message}")
