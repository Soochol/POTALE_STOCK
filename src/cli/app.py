"""
POTALE CLI Application
Main Typer app with all command groups
"""

import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.commands import collect, validate, analyze, config
from src.cli.ui.panels import create_welcome_panel

app = typer.Typer(
    name="potale",
    help="[bold cyan]POTALE Stock Data Collector[/bold cyan] - Professional Korean stock market data collection",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()

# Register command groups
app.add_typer(collect.app, name="collect", help="Collect stock market data")
app.add_typer(validate.app, name="validate", help="Validate collected data")
app.add_typer(analyze.app, name="analyze", help="Analyze stock data")
app.add_typer(config.app, name="config", help="Manage configuration")


@app.command()
def version():
    """Show version information"""

    from src.cli import __version__

    content = f"""[bold cyan]POTALE Stock Data Collector[/bold cyan]

[yellow]Version:[/yellow] {__version__}
[yellow]Data Source:[/yellow] 100% Naver Finance
[yellow]Collection Mode:[/yellow] Hybrid (Adjusted Price + Volume)
[yellow]Total Stocks:[/yellow] 4,189 (KOSPI + KOSDAQ)

[dim]https://github.com/yourusername/POTALE_STOCK[/dim]
"""

    panel = Panel(content, title="[bold]Version Info[/bold]", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(panel)


@app.command()
def doctor():
    """Check system environment and dependencies"""

    from rich.table import Table

    console.print("\n[cyan]Checking system environment...[/cyan]\n")

    checks = []

    # Python version
    import platform
    python_version = platform.python_version()
    checks.append(("Python Version", python_version, True, ""))

    # Required packages
    packages = [
        "pandas",
        "requests",
        "beautifulsoup4",
        "rich",
        "typer",
        "sqlalchemy",
    ]

    for package in packages:
        try:
            __import__(package)
            checks.append((f"Package: {package}", "Installed", True, ""))
        except ImportError:
            checks.append((f"Package: {package}", "Missing", False, f"Install with: pip install {package}"))

    # Database
    db_path = Path("data/database/stock_data.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        checks.append(("Database", f"Found ({size_mb:.2f} MB)", True, ""))
    else:
        checks.append(("Database", "Not found", False, "Run: potale collect stocks to create"))

    # Display results
    table = Table(title="System Check", show_header=True, header_style="bold cyan")
    table.add_column("Item", style="cyan", width=25)
    table.add_column("Status", style="white", width=20)
    table.add_column("Note", style="dim")

    for item, status, passed, note in checks:
        if passed:
            status_str = f"[green]OK {status}[/green]"
        else:
            status_str = f"[red]X {status}[/red]"

        table.add_row(item, status_str, note)

    console.print(table)

    # Summary
    passed_count = sum(1 for _, _, passed, _ in checks if passed)
    total_count = len(checks)

    console.print()
    if passed_count == total_count:
        console.print(f"[green]OK All checks passed ({passed_count}/{total_count})[/green]")
    else:
        console.print(f"[yellow]WARNING {total_count - passed_count} check(s) failed ({passed_count}/{total_count})[/yellow]")
    console.print()


@app.command()
def info():
    """Show project information"""

    content = """[bold cyan]POTALE Stock Data Collector[/bold cyan]

Professional tool for collecting Korean stock market data from Naver Finance.

[yellow]Features:[/yellow]
  - 100% Naver Finance based (no pykrx dependency)
  - Hybrid collection: Adjusted price + Adjusted volume
  - 4,189 stocks (KOSPI 2,387 + KOSDAQ 1,802)
  - Resume interrupted collections
  - Data validation and analysis
  - Rich CLI with progress bars

[yellow]Quick Start:[/yellow]
  [cyan]potale collect stocks --all --from 2020-01-01[/cyan]
  [cyan]potale validate all[/cyan]
  [cyan]potale analyze summary[/cyan]

[yellow]Documentation:[/yellow]
  [dim]See README.md for more information[/dim]
"""

    panel = Panel(content, title="[bold]Project Info[/bold]", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(panel)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    POTALE Stock Data Collector

    Professional tool for Korean stock market data collection
    """
    if ctx.invoked_subcommand is None:
        welcome = create_welcome_panel()
        console.print()
        console.print(welcome)
        console.print()
        console.print("[dim]Use --help for more information[/dim]")
        console.print()
