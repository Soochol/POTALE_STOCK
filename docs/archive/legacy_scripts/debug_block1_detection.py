"""
Debug script to analyze why 2020-04-14 wasn't detected as Block1 Seed
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

from src.infrastructure.database.connection import get_db_connection
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.preset.seed_condition_preset_repository import SeedConditionPresetRepository
from src.domain.entities.conditions.block_conditions import Block1Condition
from src.application.services.checkers.block1_checker import Block1Checker
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.common.utils import get_previous_trading_day_stock

console = Console(width=140)

def main():
    """Check Block1 conditions for 2020-04-14"""

    db = get_db_connection()
    stock_repo = SqliteStockRepository(db)
    preset_repo = SeedConditionPresetRepository(db)

    # Load preset
    seed_condition = preset_repo.load("default_seed")
    if not seed_condition:
        console.print("[red]FAILED - Preset 'default_seed' not found[/red]")
        return

    # Load stock data for ticker 025980
    ticker = "025980"
    from_date = date(2020, 1, 1)
    to_date = date(2020, 12, 31)

    console.print(f"\n[cyan]Loading stock data for {ticker} from {from_date} to {to_date}...[/cyan]")
    all_stocks = stock_repo.get_stock_data(ticker, from_date, to_date)

    if not all_stocks:
        console.print("[red]FAILED - No stock data found[/red]")
        return

    console.print(f"[green]OK - Loaded {len(all_stocks)} trading days[/green]\n")

    # Calculate indicators
    console.print("[cyan]Calculating indicators...[/cyan]")
    calculator = Block1IndicatorCalculator()
    all_stocks = calculator.calculate(
        stocks=all_stocks,
        ma_periods=[60],  # MA60
        volume_days=[120],  # 120일 신고거래량
        new_high_days=None
    )
    console.print(f"[green]OK - Indicators calculated for {len(all_stocks)} days[/green]\n")

    # Create Block1 condition
    block1_condition = Block1Condition(
        base=seed_condition.base
    )

    # Test dates
    test_dates = [
        date(2020, 4, 14),
        date(2020, 4, 16),
    ]

    checker = Block1Checker()

    console.print("[bold]Block1 Condition Parameters:[/bold]")
    table = Table(show_header=True, box=None)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_row("entry_surge_rate", f"{seed_condition.base.block1_entry_surge_rate}%")
    table.add_row("entry_ma_period", f"{seed_condition.base.block1_entry_ma_period}")
    table.add_row("entry_max_deviation_ratio", f"{seed_condition.base.block1_entry_max_deviation_ratio}%")
    table.add_row("entry_min_trading_value", f"{seed_condition.base.block1_entry_min_trading_value}억")
    table.add_row("entry_volume_spike_ratio", f"{seed_condition.base.block1_entry_volume_spike_ratio}%")
    table.add_row("entry_volume_high_days", f"{seed_condition.base.block1_entry_volume_high_days}")
    table.add_row("entry_price_high_days", f"{seed_condition.base.block1_entry_price_high_days}")
    table.add_row("min_start_interval_days", f"{seed_condition.base.block1_min_start_interval_days}")
    console.print(table)

    # Check each test date
    for test_date in test_dates:
        stock = next((s for s in all_stocks if s.date == test_date), None)
        if not stock:
            console.print(f"\n[red]FAILED - No data for {test_date}[/red]")
            continue

        console.print(f"\n{'='*100}")
        console.print(f"[bold yellow]Testing {test_date}[/bold yellow]")
        console.print(f"{'='*100}")

        # Check if has indicators
        if not hasattr(stock, 'indicators'):
            console.print("[red]FAILED - No indicators calculated[/red]")
            continue

        indicators = stock.indicators

        # Display stock data
        console.print(f"\n[bold]Stock Data:[/bold]")
        console.print(f"  Open: {stock.open:,.0f}, High: {stock.high:,.0f}, Low: {stock.low:,.0f}, Close: {stock.close:,.0f}")
        console.print(f"  Volume: {stock.volume:,}")
        console.print(f"  Rate: {indicators.get('rate', 0):.2f}%")

        # MA60
        ma_key = f'MA_{seed_condition.base.block1_entry_ma_period}'
        ma_value = indicators.get(ma_key)
        ma_display = f"{ma_value:,.0f}" if ma_value is not None else "N/A"
        console.print(f"  {ma_key}: {ma_display}")

        # Deviation
        deviation_key = f'deviation_{seed_condition.base.block1_entry_ma_period}'
        deviation = indicators.get(deviation_key, 100)
        console.print(f"  Deviation: {deviation:.1f}")

        # Trading value
        trading_value = indicators.get('trading_value_100m', 0)
        console.print(f"  Trading Value: {trading_value:,.0f}억")

        # Check previous trading day
        prev_stock = get_previous_trading_day_stock(stock.date, all_stocks)
        if prev_stock:
            console.print(f"\n  Previous Trading Day: {prev_stock.date}")
            console.print(f"  Prev Volume: {prev_stock.volume:,}")
            volume_ratio_required = seed_condition.base.block1_entry_volume_spike_ratio
            volume_ratio_actual = (stock.volume / prev_stock.volume * 100) if prev_stock.volume > 0 else 0
            console.print(f"  Volume Spike Ratio: {volume_ratio_actual:.1f}% (required: {volume_ratio_required}%)")
        else:
            console.print(f"\n  Previous Trading Day: NOT FOUND")

        # Manual condition checks
        console.print(f"\n[bold]Manual Condition Checks:[/bold]")

        # 1. Surge rate
        rate = indicators.get('rate', 0)
        surge_pass = rate >= seed_condition.base.block1_entry_surge_rate
        console.print(f"  [1] Surge Rate: {rate:.2f}% >= {seed_condition.base.block1_entry_surge_rate}% : {'PASS' if surge_pass else 'FAIL'}")

        # 2. MA check
        if seed_condition.base.block1_entry_ma_period:
            ma_pass = ma_value is not None and stock.high >= ma_value
            ma_val_display = f"{ma_value:,.0f}" if ma_value is not None else "N/A"
            console.print(f"  [2] MA Check: high({stock.high:,.0f}) >= {ma_key}({ma_val_display}) : {'PASS' if ma_pass else 'FAIL'}")
        else:
            console.print(f"  [2] MA Check: SKIPPED (ma_period is None)")

        # 3. Deviation
        if seed_condition.base.block1_entry_max_deviation_ratio is not None:
            dev_pass = deviation <= seed_condition.base.block1_entry_max_deviation_ratio
            console.print(f"  [3] Deviation: {deviation:.1f} <= {seed_condition.base.block1_entry_max_deviation_ratio} : {'PASS' if dev_pass else 'FAIL'}")

        # 4. Trading value
        if seed_condition.base.block1_entry_min_trading_value is not None:
            tv_pass = trading_value >= seed_condition.base.block1_entry_min_trading_value
            console.print(f"  [4] Trading Value: {trading_value:,.0f}억 >= {seed_condition.base.block1_entry_min_trading_value}억 : {'PASS' if tv_pass else 'FAIL'}")

        # 5. Volume high days
        if seed_condition.base.block1_entry_volume_high_days is not None:
            field_name = f'is_volume_high_{seed_condition.base.block1_entry_volume_high_days}d'
            is_volume_high = indicators.get(field_name, False)
            console.print(f"  [5] Volume High Days: {is_volume_high} : {'PASS' if is_volume_high else 'FAIL'}")
        else:
            console.print(f"  [5] Volume High Days: SKIPPED (None)")

        # 6. Volume spike ratio
        if seed_condition.base.block1_entry_volume_spike_ratio is not None:
            if prev_stock and prev_stock.volume > 0:
                vol_pass = stock.volume >= prev_stock.volume * (seed_condition.base.block1_entry_volume_spike_ratio / 100.0)
                console.print(f"  [6] Volume Spike: {volume_ratio_actual:.1f}% >= {seed_condition.base.block1_entry_volume_spike_ratio}% : {'PASS' if vol_pass else 'FAIL'}")
            else:
                console.print(f"  [6] Volume Spike: FAIL (no prev or zero volume)")

        # 7. Price high days
        if seed_condition.base.block1_entry_price_high_days is not None:
            field_name = f'is_new_high_{seed_condition.base.block1_entry_price_high_days}d'
            is_new_high = indicators.get(field_name, False)
            console.print(f"  [7] Price High Days: {is_new_high} : {'PASS' if is_new_high else 'FAIL'}")
        else:
            console.print(f"  [7] Price High Days: SKIPPED (None)")

        # Check result with Block1Checker
        console.print(f"\n[bold]Running Block1Checker.check_entry()...[/bold]")
        result = checker.check_entry(
            condition=block1_condition,
            stock=stock,
            all_stocks=all_stocks
        )

        if result:
            console.print(f"\n[bold green]OK - {test_date} WOULD BE DETECTED[/bold green]")
        else:
            console.print(f"\n[bold red]FAILED - {test_date} NOT DETECTED[/bold red]")

if __name__ == "__main__":
    main()
