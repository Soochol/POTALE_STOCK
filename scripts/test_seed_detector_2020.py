"""
Test PatternSeedDetector directly for 2020-04-14
"""
import sys
from pathlib import Path
from datetime import date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console

from src.infrastructure.database.connection import get_db_connection
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.preset.seed_condition_preset_repository import SeedConditionPresetRepository
from src.application.services.detectors.pattern_seed_detector import PatternSeedDetector
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator

console = Console()

def main():
    db = get_db_connection()
    stock_repo = SqliteStockRepository(db)
    preset_repo = SeedConditionPresetRepository(db)

    # Load data
    ticker = "025980"
    stocks = stock_repo.get_stock_data(ticker, date(2015, 1, 1), date.today())
    console.print(f"Loaded {len(stocks)} stocks")

    # Load preset
    seed_condition = preset_repo.load("default_seed")
    console.print(f"Loaded preset: {seed_condition.base.block1_entry_volume_high_days}")

    # Calculate indicators
    calculator = Block1IndicatorCalculator()

    # Collect all MA periods and volume_days
    ma_periods = [60] if seed_condition.base.block1_entry_ma_period else []
    volume_days = [120] if seed_condition.base.block1_entry_volume_high_days else []

    stocks = calculator.calculate(
        stocks=stocks,
        ma_periods=ma_periods,
        volume_days=volume_days,
        new_high_days=None
    )
    console.print(f"Calculated indicators")

    # Find Block1 seeds
    detector = PatternSeedDetector()
    block1_seeds = detector.find_all_block1_seeds(stocks, seed_condition)

    console.print(f"\n[bold]Found {len(block1_seeds)} Block1 Seeds:[/bold]")
    for seed in block1_seeds:
        console.print(f"  {seed.started_at}: {seed.entry_close:,.0f}원")

    # Check if 2020-04-14 is in the list
    target_date = date(2020, 4, 14)
    found = any(s.started_at == target_date for s in block1_seeds)

    if found:
        console.print(f"\n[green]✓ 2020-04-14 IS in the seed list![/green]")
    else:
        console.print(f"\n[red]✗ 2020-04-14 is NOT in the seed list[/red]")

        # Check nearby dates
        nearby = [s for s in block1_seeds if s.started_at >= date(2020, 3, 1) and s.started_at <= date(2020, 5, 31)]
        if nearby:
            console.print(f"\nNearby seeds in Mar-May 2020:")
            for s in nearby:
                console.print(f"  {s.started_at}: {s.entry_close:,.0f}원")
        else:
            console.print(f"\nNo seeds found in Mar-May 2020")

if __name__ == "__main__":
    main()
