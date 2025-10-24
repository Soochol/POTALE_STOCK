"""Rich Progress components for collection tracking"""

from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    TaskProgressColumn
)
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from datetime import datetime, date

console = Console()


def create_stats_table(stats):
    """Create statistics table"""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", justify="right")
    table.add_column(style="white")

    success = stats.get('success', 0)
    failed = stats.get('failed', 0)
    records = stats.get('records', 0)
    speed = stats.get('speed', 0)

    table.add_row("Success:", f"[green]{success}[/green]")
    table.add_row("Failed:", f"[red]{failed}[/red]")
    table.add_row("Records:", f"{records:,}")
    table.add_row("Speed:", f"{speed:.1f} rec/s")

    return table


def create_collection_progress(collector, tickers, from_date, to_date, collect_investor=False):
    """
    Create Rich progress display for bulk collection

    Args:
        collector: BulkCollector instance
        tickers: List of ticker codes
        from_date: Start date
        to_date: End date
        collect_investor: Whether to collect investor data

    Returns:
        Dictionary with collection statistics
    """

    # Progress bars
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("-"),
        TimeElapsedColumn(),
        TextColumn("<"),
        TimeRemainingColumn(),
    )

    # Tasks
    overall_task = progress.add_task(
        "[cyan]Overall Progress",
        total=len(tickers)
    )
    current_task = progress.add_task(
        "[green]Current: Initializing...",
        total=100
    )

    # Stats
    stats = {
        'success': 0,
        'failed': 0,
        'records': 0,
        'speed': 0,
        'start_time': datetime.now()
    }

    # Layout
    layout = Layout()
    layout.split_column(
        Layout(name="progress", size=5),
        Layout(name="stats", size=7),
    )

    layout["progress"].update(progress)
    layout["stats"].update(Panel(create_stats_table(stats), title="Statistics", border_style="cyan"))

    # Live display
    with Live(layout, console=console, refresh_per_second=4):
        for idx, ticker in enumerate(tickers):
            try:
                # Update current task description
                progress.update(
                    current_task,
                    completed=0,
                    description=f"[green]Current: {ticker}"
                )

                # Collect price data
                result = collector.price_collector.collect(ticker, from_date, to_date)

                if result.success:
                    stats['success'] += 1
                    stats['records'] += result.record_count
                else:
                    stats['failed'] += 1

                # Update progress
                progress.advance(overall_task, 1)
                progress.update(current_task, completed=100)

                # Calculate speed
                elapsed = (datetime.now() - stats['start_time']).total_seconds()
                if elapsed > 0:
                    stats['speed'] = stats['records'] / elapsed

                # Update stats panel
                layout["stats"].update(Panel(
                    create_stats_table(stats),
                    title="Statistics",
                    border_style="cyan"
                ))

            except KeyboardInterrupt:
                progress.stop()
                console.print("\n[yellow]WARNING Collection interrupted by user[/yellow]")
                break

            except Exception as e:
                stats['failed'] += 1
                progress.advance(overall_task, 1)

    # Calculate final elapsed time
    elapsed = datetime.now() - stats['start_time']
    hours = int(elapsed.total_seconds() // 3600)
    minutes = int((elapsed.total_seconds() % 3600) // 60)
    seconds = int(elapsed.total_seconds() % 60)

    if hours > 0:
        stats['elapsed'] = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        stats['elapsed'] = f"{minutes}m {seconds}s"
    else:
        stats['elapsed'] = f"{seconds}s"

    return stats


def create_simple_progress(description, total=None):
    """Create simple progress spinner for quick tasks"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    )
