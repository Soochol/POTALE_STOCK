"""Rich Panel components for beautiful CLI output"""

from rich.panel import Panel
from rich.text import Text
from datetime import date, datetime, timedelta


def estimate_time(ticker_count, from_date, to_date=None):
    """Estimate collection time"""
    if isinstance(ticker_count, str):
        ticker_count = 4189  # All tickers

    if to_date is None:
        to_date = date.today()

    days = (to_date - from_date).days
    # Assume ~2-3 seconds per ticker per year of data
    years = days / 365
    seconds = ticker_count * years * 2.5

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def estimate_records(ticker_count, from_date, to_date=None):
    """Estimate number of records"""
    if isinstance(ticker_count, str):
        ticker_count = 4189

    if to_date is None:
        to_date = date.today()

    days = (to_date - from_date).days
    # Assume 70% trading days
    trading_days = int(days * 0.7)

    return ticker_count * trading_days


def create_config_panel(all_tickers, ticker_str, from_date, to_date, investor, resume):
    """Create collection configuration panel"""

    if all_tickers:
        ticker_info = "All (4,189 stocks)"
        ticker_count = 4189
    else:
        tickers = ticker_str.split(',') if ticker_str else []
        ticker_info = f"{len(tickers)} stocks"
        ticker_count = len(tickers)

    to_date_str = str(to_date) if to_date else "today"

    content = f"""[bold cyan]Collection Configuration[/bold cyan]

[yellow]Target:[/yellow]
  - Tickers: {ticker_info}
  - Period: {from_date} ~ {to_date_str}
  - Mode: [cyan]Hybrid[/cyan] (Adjusted Price + Volume)

[yellow]Options:[/yellow]
  - Investor Data: {'[green]OK Yes[/green]' if investor else '[dim]X No[/dim]'}
  - Resume: {'[green]OK Yes[/green]' if resume else '[dim]X No[/dim]'}

[yellow]Estimated:[/yellow]
  - Time: [cyan]~{estimate_time(ticker_count, from_date, to_date)}[/cyan]
  - Records: [cyan]~{estimate_records(ticker_count, from_date, to_date):,}[/cyan]
"""

    return Panel(content, title="[bold]POTALE Stock Collector[/bold]", border_style="cyan", padding=(1, 2))


def create_completion_panel(stats):
    """Create collection completion panel"""

    success = stats.get('success', 0)
    failed = stats.get('failed', 0)
    records = stats.get('records', 0)
    elapsed = stats.get('elapsed', '0m')
    speed = stats.get('speed', 0)

    content = f"""[bold green]OK Collection Complete[/bold green]

[yellow]Summary:[/yellow]
  - Success: [green]{success:,}[/green] tickers
  - Failed: [red]{failed:,}[/red] tickers
  - Total Records: [cyan]{records:,}[/cyan]
  - Time Elapsed: [cyan]{elapsed}[/cyan]
  - Average Speed: [cyan]{speed:.1f}[/cyan] rec/s

[yellow]Next Steps:[/yellow]
  - Validate data: [cyan]potale validate all[/cyan]
  - View summary: [cyan]potale analyze summary[/cyan]
"""

    if failed > 0:
        content += "\n[yellow]WARNING Some tickers failed. Check logs for details.[/yellow]"

    return Panel(content, title="[bold]OK Complete[/bold]", border_style="green", padding=(1, 2))


def create_error_panel(ticker, error_message, suggestions=None):
    """Create error panel"""

    content = f"""[bold red]X Error[/bold red]

Failed to collect data for [cyan]{ticker}[/cyan]

[yellow]Error:[/yellow]
{error_message}
"""

    if suggestions:
        content += f"\n[yellow]Suggestions:[/yellow]\n"
        for suggestion in suggestions:
            content += f"  - {suggestion}\n"

    return Panel(content, title="[bold]X Error[/bold]", border_style="red", padding=(1, 2))


def create_welcome_panel():
    """Create welcome panel"""

    content = """[bold cyan]POTALE Stock Data Collector[/bold cyan]

Professional Korean stock market data collection tool
100% Naver Finance | Hybrid Mode | 4,189 Stocks

[dim]Use --help for more information[/dim]
"""

    return Panel(content, border_style="cyan", padding=(1, 2))
