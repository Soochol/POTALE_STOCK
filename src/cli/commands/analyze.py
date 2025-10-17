"""Analyze command - Data analysis operations"""

import typer
from rich.console import Console
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.ui.tables import create_summary_table

app = typer.Typer(help="📈 Analyze collected stock data")
console = Console()


@app.command("summary")
def analyze_summary(
    db: str = typer.Option("data/database/stock_data.db", "--db", help="Database path"),
):
    """
    Show summary statistics of collected data

    Displays overview of:
    - Total records
    - Date range
    - Stock coverage
    - Data completeness
    """

    try:
        from src.infrastructure.database.connection import DatabaseConnection
        from src.infrastructure.database.models import StockPrice, StockInfo, InvestorTrading

        if not Path(db).exists():
            console.print(f"[red]X Error:[/red] Database not found: {db}")
            raise typer.Exit(1)

        db_conn = DatabaseConnection(db)
        session = db_conn.get_session()

        console.print("[cyan]Analyzing collected data...[/cyan]\n")

        # Gather statistics
        summary = {}

        # Stock info
        total_stocks = session.query(StockInfo).count()
        summary["Total Stocks"] = total_stocks

        # Stock price
        total_price_records = session.query(StockPrice).count()
        summary["Price Records"] = total_price_records

        # Investor trading
        total_investor_records = session.query(InvestorTrading).count()
        summary["Investor Records"] = total_investor_records

        # Date range
        if total_price_records > 0:
            from sqlalchemy import func
            min_date = session.query(func.min(StockPrice.date)).scalar()
            max_date = session.query(func.max(StockPrice.date)).scalar()
            summary["First Date"] = str(min_date)
            summary["Last Date"] = str(max_date)

            # Trading days
            trading_days = session.query(StockPrice.date).distinct().count()
            summary["Trading Days"] = trading_days

        # Average records per stock
        if total_stocks > 0:
            avg_records = total_price_records / total_stocks
            summary["Avg Records/Stock"] = f"{avg_records:.1f}"

        # Database size
        if Path(db).exists():
            size_bytes = Path(db).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            summary["Database Size"] = f"{size_mb:.2f} MB"

        session.close()

        # Display
        table = create_summary_table(summary)
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]X Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("ticker")
def analyze_ticker(
    ticker: str = typer.Argument(..., help="Ticker code (e.g., 005930)"),
    db: str = typer.Option("data/database/stock_data.db", "--db", help="Database path"),
):
    """
    Analyze specific ticker data

    Example:
        potale analyze ticker 005930
    """

    try:
        from src.infrastructure.database.connection import DatabaseConnection
        from src.infrastructure.database.models import StockPrice, StockInfo

        if not Path(db).exists():
            console.print(f"[red]X Error:[/red] Database not found: {db}")
            raise typer.Exit(1)

        db_conn = DatabaseConnection(db)
        session = db_conn.get_session()

        # Get stock info
        stock_info = session.query(StockInfo).filter(StockInfo.ticker == ticker).first()

        if not stock_info:
            console.print(f"[yellow]WARNING No info found for ticker {ticker}[/yellow]")
            session.close()
            raise typer.Exit(0)

        # Get price records
        records = session.query(StockPrice).filter(StockPrice.ticker == ticker).order_by(StockPrice.date).all()

        if not records:
            console.print(f"[yellow]WARNING No price data for ticker {ticker}[/yellow]")
            session.close()
            raise typer.Exit(0)

        console.print(f"\n[bold cyan]{stock_info.name} ({ticker})[/bold cyan]\n")

        # Statistics
        summary = {}
        summary["Name"] = stock_info.name
        summary["Market"] = stock_info.market or "N/A"
        summary["Total Records"] = len(records)

        dates = [r.date for r in records]
        summary["First Date"] = str(min(dates))
        summary["Last Date"] = str(max(dates))

        prices = [r.adj_close for r in records if r.adj_close]
        if prices:
            summary["Highest Price"] = f"{max(prices):,.0f}"
            summary["Lowest Price"] = f"{min(prices):,.0f}"
            summary["Latest Price"] = f"{prices[-1]:,.0f}"

        volumes = [r.adj_volume for r in records if r.adj_volume]
        if volumes:
            avg_volume = sum(volumes) / len(volumes)
            summary["Avg Volume"] = f"{avg_volume:,.0f}"

        session.close()

        # Display
        table = create_summary_table(summary)
        console.print(table)

    except Exception as e:
        console.print(f"\n[red]X Error:[/red] {e}")
        raise typer.Exit(1)
