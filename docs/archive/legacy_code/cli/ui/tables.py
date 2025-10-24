"""Rich Table components for data display"""

from rich.table import Table
from rich.console import Console

console = Console()


def create_ticker_list_table(kospi_tickers, kosdaq_tickers, limit=10):
    """Create ticker list table"""

    table = Table(title="Available Tickers", show_header=True, header_style="bold cyan")

    table.add_column("Market", style="cyan", width=10)
    table.add_column("Count", justify="right", style="green", width=10)
    table.add_column("Sample (first 10)", style="white")

    # KOSPI
    kospi_sample = ", ".join(kospi_tickers[:limit])
    table.add_row("KOSPI", f"{len(kospi_tickers):,}", kospi_sample)

    # KOSDAQ
    kosdaq_sample = ", ".join(kosdaq_tickers[:limit])
    table.add_row("KOSDAQ", f"{len(kosdaq_tickers):,}", kosdaq_sample)

    # Total
    total = len(kospi_tickers) + len(kosdaq_tickers)
    table.add_row("[bold]Total[/bold]", f"[bold]{total:,}[/bold]", "")

    return table


def create_validation_table(results):
    """Create validation results table"""

    table = Table(title="Validation Results", show_header=True, header_style="bold cyan")

    table.add_column("Check", style="cyan", width=30)
    table.add_column("Status", justify="center", width=12)
    table.add_column("Details", style="white")

    for check_name, result in results.items():
        if result.get('passed', False):
            status = "[green]OK Pass[/green]"
        else:
            status = "[red]X Fail[/red]"

        details = result.get('details', '')
        table.add_row(check_name, status, details)

    return table


def create_summary_table(summary):
    """Create collection summary table"""

    table = Table(title="Collection Summary", show_header=True, header_style="bold cyan")

    table.add_column("Item", style="cyan", width=30)
    table.add_column("Value", justify="right", style="green", width=20)

    for key, value in summary.items():
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                formatted_value = f"{value:,.2f}"
            else:
                formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)

        table.add_row(key, formatted_value)

    return table


def create_ticker_status_table(ticker_statuses):
    """Create ticker collection status table"""

    table = Table(title="Ticker Status", show_header=True, header_style="bold cyan")

    table.add_column("Ticker", style="cyan", width=10)
    table.add_column("Name", style="white", width=20)
    table.add_column("Status", justify="center", width=12)
    table.add_column("Records", justify="right", width=10)
    table.add_column("Time", justify="right", width=10)

    for status in ticker_statuses[:20]:  # Limit to 20 for display
        ticker = status.get('ticker', '')
        name = status.get('name', 'N/A')
        state = status.get('status', 'unknown')
        records = status.get('records', 0)
        time = status.get('time', '-')

        if state == 'completed':
            status_str = "[green]OK Done[/green]"
        elif state == 'running':
            status_str = "[yellow]> Live[/yellow]"
        elif state == 'failed':
            status_str = "[red]X Fail[/red]"
        else:
            status_str = "[dim]Wait[/dim]"

        table.add_row(ticker, name, status_str, f"{records:,}", time)

    if len(ticker_statuses) > 20:
        table.caption = f"[dim]Showing 20 of {len(ticker_statuses)} tickers[/dim]"

    return table
