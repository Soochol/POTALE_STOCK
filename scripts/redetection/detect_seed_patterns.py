"""
Automated Seed Pattern Detection Script (CLI Wrapper)

Thin wrapper that calls DetectSeedPatternsUseCase
Clean Architecture: scripts는 진입점일 뿐, 비즈니스 로직은 src/application/use_cases/에 있음
"""
import argparse
import sys
from pathlib import Path
from datetime import date

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.application.use_cases.seed_detection import DetectSeedPatternsUseCase


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Detect high-quality seed patterns with strict conditions'
    )

    parser.add_argument(
        '--yaml',
        type=str,
        required=True,
        help='Seed detection YAML file path'
    )

    parser.add_argument(
        '--ticker',
        type=str,
        required=True,
        help='Stock ticker'
    )

    parser.add_argument(
        '--from-date',
        type=str,
        default='2015-01-01',
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--to-date',
        type=str,
        default=None,
        help='End date (YYYY-MM-DD), default: today'
    )

    parser.add_argument(
        '--max-patterns',
        type=int,
        default=10,
        help='Maximum number of seed patterns to save'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='data/database/stock_data.db',
        help='Database path'
    )

    return parser.parse_args()


def main():
    """Main entry point - thin wrapper"""
    args = parse_args()

    # Parse dates
    from_date = date.fromisoformat(args.from_date) if args.from_date else None
    to_date = date.fromisoformat(args.to_date) if args.to_date else None

    # Create use case (dependency injection)
    use_case = DetectSeedPatternsUseCase(db_path=args.db)

    # Execute use case
    try:
        seed_patterns = use_case.execute(
            yaml_path=args.yaml,
            ticker=args.ticker,
            from_date=from_date,
            to_date=to_date,
            max_patterns=args.max_patterns
        )

        # Print summary
        print(f"\n{'='*60}")
        print(f"✅ Seed Detection Complete!")
        print(f"   Total patterns saved: {len(seed_patterns)}")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
