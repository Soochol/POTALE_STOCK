"""Config command - Configuration management"""

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage configuration settings")
console = Console()


@app.command("show")
def config_show():
    """
    Show current configuration

    Displays:
    - Database path
    - Default settings
    - Environment info
    """

    table = Table(title="Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="cyan", width=30)
    table.add_column("Value", style="white")

    # Default settings
    table.add_row("Database Path", "data/database/stock_data.db")
    table.add_row("Collection Mode", "Hybrid (Adjusted Price + Volume)")
    table.add_row("Data Source", "100% Naver Finance")
    table.add_row("API Delay", "0.2 seconds")
    table.add_row("Total Tickers", "4,189 (KOSPI + KOSDAQ)")

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Configuration file support coming soon[/dim]")


@app.command("init")
def config_init():
    """
    Initialize configuration

    Creates default configuration file
    """

    console.print("[yellow]> Config initialization[/yellow]")
    console.print("[dim]This feature will be implemented soon[/dim]")
    console.print("[dim]For now, use command-line options[/dim]")
