"""Validate command - Data validation operations"""

import typer
from rich.console import Console
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.ui.tables import create_validation_table

app = typer.Typer(help="Validate collected data quality")
console = Console()


@app.command("all")
def validate_all(
    db: str = typer.Option("data/database/stock_data.db", "--db", help="Database path"),
):
    """
    Validate all collected data

    Performs comprehensive data quality checks:
    - NULL value detection
    - Duplicate record detection
    - Data completeness
    - Date range validation
    """

    try:
        from src.infrastructure.database.connection import DatabaseConnection
        from src.infrastructure.database.models import StockPrice, StockInfo

        if not Path(db).exists():
            console.print(f"[red]X Error:[/red] Database not found: {db}")
            raise typer.Exit(1)

        db_conn = DatabaseConnection(db)
        session = db_conn.get_session()

        console.print("[cyan]Running validation checks...[/cyan]\n")

        results = {}

        # Check 1: Record count
        total_records = session.query(StockPrice).count()
        total_stocks = session.query(StockInfo).count()

        results["Total Records"] = {
            "passed": total_records > 0,
            "details": f"{total_records:,} price records, {total_stocks:,} stocks"
        }

        # Check 2: NULL values
        null_close = session.query(StockPrice).filter(
            (StockPrice.adj_close == None) | (StockPrice.adj_volume == None)
        ).count()

        results["NULL Values"] = {
            "passed": null_close == 0,
            "details": f"{null_close} records with NULL close/volume" if null_close > 0 else "No NULL values"
        }

        # Check 3: Zero prices
        zero_prices = session.query(StockPrice).filter(StockPrice.adj_close == 0).count()

        results["Zero Prices"] = {
            "passed": zero_prices == 0,
            "details": f"{zero_prices} records with zero price" if zero_prices > 0 else "No zero prices"
        }

        # Check 4: Duplicates
        from sqlalchemy import func
        duplicates = session.query(
            StockPrice.ticker,
            StockPrice.date,
            func.count().label('count')
        ).group_by(
            StockPrice.ticker,
            StockPrice.date
        ).having(
            func.count() > 1
        ).count()

        results["Duplicates"] = {
            "passed": duplicates == 0,
            "details": f"{duplicates} duplicate records" if duplicates > 0 else "No duplicates"
        }

        # Check 5: Date range
        if total_records > 0:
            from sqlalchemy import func
            min_date = session.query(func.min(StockPrice.date)).scalar()
            max_date = session.query(func.max(StockPrice.date)).scalar()

            results["Date Range"] = {
                "passed": True,
                "details": f"{min_date} to {max_date}"
            }

        session.close()

        # Display results
        table = create_validation_table(results)
        console.print(table)

        # Summary
        passed = sum(1 for r in results.values() if r['passed'])
        total = len(results)

        console.print()
        if passed == total:
            console.print(f"[green]All checks passed ({passed}/{total})[/green]")
        else:
            console.print(f"[yellow]WARNING {total - passed} check(s) failed ({passed}/{total})[/yellow]")

    except Exception as e:
        console.print(f"\n[red]X Error:[/red] {e}")
        if "--debug" in sys.argv:
            console.print_exception()
        raise typer.Exit(1)


@app.command("ticker")
def validate_ticker(
    ticker: str = typer.Argument(..., help="Ticker code (e.g., 005930)"),
    db: str = typer.Option("data/database/stock_data.db", "--db", help="Database path"),
):
    """
    Validate data for a specific ticker

    Example:
        potale validate ticker 005930
    """

    try:
        from src.infrastructure.database.connection import DatabaseConnection
        from src.infrastructure.database.models import StockPrice

        if not Path(db).exists():
            console.print(f"[red]X Error:[/red] Database not found: {db}")
            raise typer.Exit(1)

        db_conn = DatabaseConnection(db)
        session = db_conn.get_session()

        # Get ticker data
        records = session.query(StockPrice).filter(StockPrice.ticker == ticker).all()

        if not records:
            console.print(f"[yellow]WARNING No data found for ticker {ticker}[/yellow]")
            session.close()
            raise typer.Exit(0)

        # Validation
        console.print(f"\n[cyan]Validating {ticker}...[/cyan]\n")

        results = {}

        results["Record Count"] = {
            "passed": len(records) > 0,
            "details": f"{len(records):,} records"
        }

        # Check for NULL values
        null_count = sum(1 for r in records if r.adj_close is None or r.adj_volume is None)
        results["NULL Values"] = {
            "passed": null_count == 0,
            "details": f"{null_count} NULL values" if null_count > 0 else "No NULL values"
        }

        # Check for zero prices
        zero_count = sum(1 for r in records if r.adj_close == 0)
        results["Zero Prices"] = {
            "passed": zero_count == 0,
            "details": f"{zero_count} zero prices" if zero_count > 0 else "No zero prices"
        }

        # Date range
        dates = [r.date for r in records]
        results["Date Range"] = {
            "passed": True,
            "details": f"{min(dates)} to {max(dates)}"
        }

        session.close()

        # Display
        table = create_validation_table(results)
        console.print(table)

        passed = sum(1 for r in results.values() if r['passed'])
        total = len(results)

        console.print()
        if passed == total:
            console.print(f"[green]All checks passed ({passed}/{total})[/green]")
        else:
            console.print(f"[yellow]WARNING {total - passed} check(s) failed[/yellow]")

    except Exception as e:
        console.print(f"\n[red]X Error:[/red] {e}")
        raise typer.Exit(1)
