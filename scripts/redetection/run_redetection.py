"""
Automated Redetection Script

Seed pattern을 기반으로 유사 패턴을 DTW로 재탐지
"""
import argparse
import sys
from pathlib import Path
from datetime import date, datetime
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_pattern_redetector import DynamicPatternRedetector
from src.domain.entities.conditions import ExpressionEngine
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.seed_pattern_repository_impl import SeedPatternRepositoryImpl
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl


class AutomatedRedetection:
    """자동화된 Redetection 시스템"""

    def __init__(self, db_path: str = "data/database/stock_data.db"):
        """
        Args:
            db_path: Database file path
        """
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        self.session = Session()

        self.stock_repo = SqliteStockRepository(self.session)
        self.seed_pattern_repo = SeedPatternRepositoryImpl(self.session)
        self.detection_repo = DynamicBlockRepositoryImpl(self.session)
        self.block_graph_loader = BlockGraphLoader()
        self.expression_engine = ExpressionEngine()

    def run_redetection(
        self,
        redetection_yaml: str,
        seed_pattern_name: Optional[str] = None,
        ticker: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        similarity_method: str = "dtw",
        save_results: bool = True
    ) -> dict:
        """
        Redetection 실행

        Args:
            redetection_yaml: Redetection YAML file path
            seed_pattern_name: Specific seed pattern name (None = all active)
            ticker: Stock ticker (None = use seed pattern's ticker)
            from_date: Start date for historical data
            to_date: End date for historical data
            similarity_method: "range" or "dtw"
            save_results: Save redetections to DB

        Returns:
            Summary dict
        """
        print(f"\n{'='*70}")
        print(f"🔄 Automated Redetection Pipeline")
        print(f"{'='*70}")

        # Load redetection graph
        print(f"📋 Loading redetection graph: {redetection_yaml}")
        redetection_graph = self.block_graph_loader.load_from_file(redetection_yaml)

        if redetection_graph.pattern_type != "redetection":
            raise ValueError(
                f"YAML must have pattern_type='redetection', got '{redetection_graph.pattern_type}'"
            )

        print(f"   ✅ Loaded (similarity_method={similarity_method})")

        # Load seed patterns
        if seed_pattern_name:
            seed_pattern = self.seed_pattern_repo.find_by_name(seed_pattern_name)
            if not seed_pattern:
                raise ValueError(f"Seed pattern '{seed_pattern_name}' not found")
            seed_patterns = [seed_pattern]
        else:
            seed_patterns = self.seed_pattern_repo.find_active_patterns()

        print(f"🌱 Found {len(seed_patterns)} seed pattern(s)")

        # Run redetection for each seed
        all_results = []

        for idx, seed in enumerate(seed_patterns, 1):
            print(f"\n{'-'*70}")
            print(f"🔍 Redetecting from seed {idx}/{len(seed_patterns)}: {seed.pattern_name}")
            print(f"{'-'*70}")

            try:
                result = self._redetect_from_seed(
                    redetection_graph=redetection_graph,
                    seed_pattern=seed,
                    ticker=ticker or seed.ticker,
                    from_date=from_date,
                    to_date=to_date,
                    similarity_method=similarity_method,
                    save_results=save_results
                )
                all_results.append(result)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        # Aggregate summary
        summary = self._create_summary(all_results)

        print(f"\n{'='*70}")
        print(f"✅ Redetection Complete!")
        print(f"{'='*70}")
        print(f"   Total seeds processed: {summary['total_seeds']}")
        print(f"   Total redetections found: {summary['total_redetections']}")
        print(f"   Average similarity: {summary['avg_similarity']:.3f}")
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        print(f"{'='*70}\n")

        return summary

    def _redetect_from_seed(
        self,
        redetection_graph,
        seed_pattern,
        ticker: str,
        from_date: Optional[date],
        to_date: Optional[date],
        similarity_method: str,
        save_results: bool
    ) -> dict:
        """Single seed pattern redetection"""

        # Load historical stock data
        print(f"📊 Loading stock data for {ticker}...")
        stocks = self.stock_repo.find_by_ticker_and_date_range(
            ticker=ticker,
            start_date=from_date,
            end_date=to_date
        )

        if not stocks:
            print(f"   ⚠️  No stock data found")
            return {"seed": seed_pattern.pattern_name, "redetections": [], "error": "No data"}

        print(f"   Found {len(stocks)} candles")

        # Initialize redetector
        redetector = DynamicPatternRedetector(
            redetection_graph,
            self.expression_engine
        )

        # Override similarity method if needed
        redetector.similarity_calculator.method = similarity_method

        # Run redetection
        print(f"🔄 Running redetection (method={similarity_method})...")
        redetections = redetector.redetect_patterns(
            seed_pattern=seed_pattern,
            ticker=ticker,
            stocks=stocks,
            start_date=from_date,
            end_date=to_date
        )

        print(f"   Found {len(redetections)} redetections")

        # Get summary
        summary = redetector.get_redetection_summary(redetections)

        print(f"   Average similarity: {summary.get('avg_similarity', 0.0):.3f}")
        print(f"   Date range: {summary.get('date_range', 'N/A')}")

        # Save to DB
        if save_results and redetections:
            print(f"💾 Saving {len(redetections)} redetections to DB...")

            saved_count = 0
            for detection in redetections:
                try:
                    self.detection_repo.save(detection)
                    saved_count += 1
                except Exception as e:
                    print(f"   ⚠️  Failed to save: {e}")

            self.session.commit()
            print(f"   ✅ Saved {saved_count} redetections")

        return {
            "seed": seed_pattern.pattern_name,
            "ticker": ticker,
            "redetections": redetections,
            "summary": summary
        }

    def _create_summary(self, results: List[dict]) -> dict:
        """Aggregate summary from all results"""
        total_seeds = len(results)
        total_redetections = sum(len(r.get("redetections", [])) for r in results)

        similarities = []
        for r in results:
            summary = r.get("summary", {})
            if summary.get("avg_similarity"):
                similarities.append(summary["avg_similarity"])

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        success_rate = (len(similarities) / total_seeds * 100) if total_seeds > 0 else 0.0

        return {
            "total_seeds": total_seeds,
            "total_redetections": total_redetections,
            "avg_similarity": avg_similarity,
            "success_rate": success_rate,
            "results": results
        }

    def close(self):
        """Close session"""
        self.session.close()


def main():
    parser = argparse.ArgumentParser(description="Run automated redetection")
    parser.add_argument("--redetection-yaml", required=True, help="Redetection YAML file")
    parser.add_argument("--seed-pattern", help="Specific seed pattern name")
    parser.add_argument("--ticker", help="Stock ticker (default: seed pattern's ticker)")
    parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--method", choices=["range", "dtw"], default="dtw",
                        help="Similarity method")
    parser.add_argument("--no-save", action="store_true", help="Don't save to DB (dry run)")
    parser.add_argument("--db", default="data/database/stock_data.db", help="Database path")

    args = parser.parse_args()

    # Parse dates
    from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date() if args.from_date else None
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date() if args.to_date else None

    # Run redetection
    redetection = AutomatedRedetection(db_path=args.db)

    try:
        summary = redetection.run_redetection(
            redetection_yaml=args.redetection_yaml,
            seed_pattern_name=args.seed_pattern,
            ticker=args.ticker,
            from_date=from_date,
            to_date=to_date,
            similarity_method=args.method,
            save_results=not args.no_save
        )

        return 0 if summary["total_redetections"] > 0 else 1

    finally:
        redetection.close()


if __name__ == "__main__":
    sys.exit(main())
