"""
Test script for Highlight-Centric Detection

Simple validation script for Phase 3B.
"""

import sys
import logging
from pathlib import Path
from datetime import date

# Configure logging - reduce noise
logging.basicConfig(level=logging.WARNING)  # Only show warnings and errors

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.application.use_cases.highlight_centric_detector import HighlightCentricDetector
from src.application.services.highlight_detector import HighlightDetector
from src.application.services.support_resistance_analyzer import SupportResistanceAnalyzer
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.domain.entities.conditions import ExpressionEngine, function_registry
from src.infrastructure.database.connection import get_db_connection
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.highlight_centric_pattern_repository_impl import HighlightCentricPatternRepositoryImpl

print("=" * 70)
print("Highlight-Centric Detection Test - Ananti (025980)")
print("=" * 70)

# 1. Connect to database
print("\n1. Connecting to database...")
db_connection = get_db_connection("data/database/stock_data.db")
session = db_connection.get_session()

# 2. Load YAML configuration
print("2. Loading YAML configuration...")
loader = BlockGraphLoader()
block_graph = loader.load_from_file("presets/examples/ananti_validation.yaml")
print(f"   Loaded: {len(block_graph.nodes)} nodes, {len(block_graph.edges)} edges")

# 3. Load stock data
print("3. Loading Ananti stock data...")
stock_repo = SqliteStockRepository(session)
# Load extra data: 60 days before scan period for backward scan + 1125 days after for forward scan
stocks = stock_repo.get_stock_data(
    ticker="025980",
    start_date=date(2020, 2, 1),  # 60 days before April
    end_date=date(2024, 12, 31)    # Through end of 2024 for forward scan
)
print(f"   Loaded: {len(stocks)} candles")

# 4. Calculate indicators
print("4. Calculating indicators...")
indicator_calc = Block1IndicatorCalculator()
stocks = indicator_calc.calculate(stocks)
print("   OK")

# 5. Initialize detection components
print("5. Initializing detection components...")
expression_engine = ExpressionEngine(function_registry)
highlight_detector = HighlightDetector(expression_engine)
sr_analyzer = SupportResistanceAnalyzer(tolerance_pct=2.0)
dynamic_block_detector = DynamicBlockDetector(
    block_graph=block_graph,
    expression_engine=expression_engine
)

# 6. Initialize HighlightCentricDetector
print("6. Initializing HighlightCentricDetector...")
hc_detector = HighlightCentricDetector(
    block_graph=block_graph,
    highlight_detector=highlight_detector,
    support_resistance_analyzer=sr_analyzer,
    dynamic_block_detector=dynamic_block_detector,
    expression_engine=expression_engine
)
print("   OK")

# 7. Detect patterns
print("\n7. Detecting highlight-centric patterns...")
print(f"   Scan period: 2020-04-01 to 2020-05-31")
print(f"   Backward scan: 30 days")
print(f"   Forward scan: 1125 days (4.5 years)")
print()

patterns = hc_detector.detect_patterns(
    ticker="025980",
    stocks=stocks,
    scan_from=date(2020, 4, 1),
    scan_to=date(2020, 5, 31),
    backward_days=30,
    forward_days=1125
)

print(f"\n[OK] Detection completed: {len(patterns)} pattern(s) found")

# 8. Display results
if patterns:
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern.pattern_id}")
        print(f"  Ticker: {pattern.ticker}")
        print(f"  Status: {pattern.status.value}")
        print(f"  Highlight block: {pattern.highlight_block.block_id} (started: {pattern.highlight_block.started_at})")
        print(f"  Root block: {pattern.root_block.block_id} (started: {pattern.root_block.started_at})")
        print(f"  Is highlight root: {pattern.is_highlight_root()}")

        if pattern.backward_scan_result:
            bsr = pattern.backward_scan_result
            print(f"  Backward scan:")
            print(f"    - Found stronger root: {bsr.found_stronger_root}")
            if bsr.found_stronger_root:
                print(f"    - Peak price ratio: {bsr.peak_price_ratio:.2f}x")
            print(f"    - Lookback days: {bsr.lookback_days}")

        print(f"  Forward blocks: {len(pattern.forward_blocks)}")
        if pattern.forward_blocks:
            print(f"    - First: {pattern.forward_blocks[0].block_id} ({pattern.forward_blocks[0].started_at})")
            print(f"    - Last: {pattern.forward_blocks[-1].block_id} ({pattern.forward_blocks[-1].started_at})")

        print(f"  Pattern duration: {pattern.get_pattern_duration_days()} days")
        print(f"  Has S/R analysis: {pattern.has_sr_analysis()}")

        print(f"  Spot count: {pattern.get_highlight_spot_count()}")

    # 9. Save to database (auto-skip for testing)
    print("\n9. Skipping database save (test mode)")

else:
    print("\n[WARNING] No patterns found")

# 10. Cleanup
print("\n10. Cleaning up...")
session.close()
print("   Session closed")

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
