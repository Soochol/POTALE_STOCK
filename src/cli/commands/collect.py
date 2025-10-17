"""Collect command - Data collection operations"""

import typer
from datetime import date, datetime
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.ui.panels import create_config_panel, create_completion_panel
from src.cli.ui.progress import create_collection_progress, create_simple_progress
from src.cli.ui.tables import create_ticker_list_table

app = typer.Typer(help="📊 Collect stock market data from Naver Finance")
console = Console()


@app.command("stocks")
def collect_stocks(
    all: bool = typer.Option(False, "--all", help="Collect all tickers (4,189 stocks)"),
    tickers: Optional[str] = typer.Option(None, "--tickers", help="Specific tickers (comma-separated, e.g., 005930,000660)"),
    from_date: str = typer.Option(..., "--from", help="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = typer.Option(None, "--to", help="End date (YYYY-MM-DD, default: today)"),
    investor: bool = typer.Option(False, "--investor", help="Include investor trading data"),
    resume: bool = typer.Option(False, "--resume", help="Resume interrupted collection"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    db: str = typer.Option("data/database/stock_data.db", "--db", help="Database path"),
):
    """
    Collect stock price data with hybrid mode (adjusted price + volume)

    Examples:

        # Collect all stocks from 2020
        potale collect stocks --all --from 2020-01-01

        # Collect specific stocks
        potale collect stocks --tickers 005930,000660 --from 2024-01-01

        # Resume interrupted collection
        potale collect stocks --all --from 2020-01-01 --resume
    """

    # Validate inputs
    if not all and not tickers:
        console.print("[red]Error:[/red] Either --all or --tickers must be specified")
        raise typer.Exit(1)

    # Parse dates
    try:
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid date format: {from_date}. Use YYYY-MM-DD")
        raise typer.Exit(1)

    # Set default to_date
    if to_date is None:
        to_date_obj = date.today()
    else:
        try:
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid date format: {to_date}. Use YYYY-MM-DD")
            raise typer.Exit(1)

    # Display configuration
    config_panel = create_config_panel(all, tickers, from_date_obj, to_date_obj, investor, resume)
    console.print(config_panel)

    # Confirmation
    if not yes:
        if not Confirm.ask("Continue with this configuration?", default=True):
            console.print("[yellow]Aborted by user[/yellow]")
            raise typer.Exit(0)

    console.print()

    try:
        # Initialize database
        from src.infrastructure.database.connection import DatabaseConnection
        from src.infrastructure.collectors.bulk_collector import BulkCollector

        db_conn = DatabaseConnection(db)

        # Initialize database tables if needed
        if not Path(db).exists():
            console.print(f"[cyan]Creating database:[/cyan] {db}")
            db_conn.create_tables()

        collector = BulkCollector(db_conn, use_hybrid=True)

        # Get ticker list
        if all:
            with create_simple_progress("[cyan]Loading ticker list...", total=None) as progress:
                task = progress.add_task("Loading ticker list...", total=None)
                from src.infrastructure.utils.naver_ticker_list import get_all_tickers
                ticker_list = get_all_tickers()
                progress.update(task, completed=100)

            console.print(f"[green]OK[/green] Loaded {len(ticker_list):,} tickers\n")
        else:
            ticker_list = [t.strip() for t in tickers.split(',')]
            console.print(f"[cyan]Collecting {len(ticker_list)} tickers...[/cyan]\n")

        # Run collection with Rich Progress
        stats = create_collection_progress(
            collector,
            ticker_list,
            from_date_obj,
            to_date_obj,
            collect_investor=investor
        )

        # Display completion panel
        console.print()
        completion_panel = create_completion_panel(stats)
        console.print(completion_panel)

    except KeyboardInterrupt:
        console.print("\n[yellow]WARNING Collection interrupted by user[/yellow]")
        console.print("[dim]Resume with: potale collect stocks --resume[/dim]")
        raise typer.Exit(130)

    except Exception as e:
        console.print(f"\n[red]X Error:[/red] {e}")
        if "--debug" in sys.argv:
            console.print_exception()
        raise typer.Exit(1)


@app.command("tickers")
def collect_tickers(
    save: bool = typer.Option(True, "--save/--no-save", help="Save to CSV file"),
):
    """
    Collect and display all available ticker codes

    This command fetches the complete list of tradeable stocks from Naver Finance.
    """

    try:
        with create_simple_progress("[cyan]Collecting tickers from Naver Finance...", total=None) as progress:
            task = progress.add_task("Collecting tickers...", total=None)

            from src.infrastructure.utils.naver_ticker_list import get_naver_ticker_list

            kospi_tickers = get_naver_ticker_list('KOSPI')
            kosdaq_tickers = get_naver_ticker_list('KOSDAQ')

            progress.update(task, completed=100)

        # Display table
        table = create_ticker_list_table(kospi_tickers, kosdaq_tickers, limit=10)
        console.print()
        console.print(table)

        # Save to CSV if requested
        if save:
            import csv
            output_file = "data/naver_ticker_list.csv"

            Path("data").mkdir(exist_ok=True)

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ticker', 'market'])

                for ticker in kospi_tickers:
                    writer.writerow([ticker, 'KOSPI'])
                for ticker in kosdaq_tickers:
                    writer.writerow([ticker, 'KOSDAQ'])

            console.print(f"\n[green]OK[/green] Saved to: {output_file}")

    except Exception as e:
        console.print(f"\n[red]X Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("resume")
def collect_resume(
    db: str = typer.Option("data/database/stock_data.db", "--db", help="Database path"),
):
    """
    Resume interrupted collection

    This will check the collection progress and resume from the last completed ticker.
    """

    console.print("[yellow]> Resume functionality[/yellow]")
    console.print("[dim]This feature requires collection progress tracking in the database.[/dim]")
    console.print("[dim]Please use: potale collect stocks --resume[/dim]")
