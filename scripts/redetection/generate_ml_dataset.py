"""
ML Dataset Generation from Redetections

Redetection 결과를 ML training dataset으로 변환
"""
import argparse
import sys
import csv
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl
from src.infrastructure.repositories.seed_pattern_repository_impl import SeedPatternRepositoryImpl


class MLDatasetGenerator:
    """ML Dataset 생성기"""

    def __init__(self, db_path: str = "data/database/stock_data.db"):
        """
        Args:
            db_path: Database file path
        """
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        self.session = Session()

        self.detection_repo = DynamicBlockRepositoryImpl(self.session)
        self.seed_pattern_repo = SeedPatternRepositoryImpl(self.session)

    def generate_block_labels(
        self,
        output_csv: str,
        condition_name: str = "redetection",
        min_similarity: float = 0.7
    ) -> int:
        """
        Block labels CSV 생성

        Format: ticker,block_type,sequence,started_at,ended_at,similarity_score

        Args:
            output_csv: Output CSV file path
            condition_name: Condition name to filter
            min_similarity: Minimum similarity score

        Returns:
            Number of labels generated
        """
        print(f"\n{'='*60}")
        print(f"📊 Generating ML Dataset (Block Labels)")
        print(f"{'='*60}")

        # Query redetections
        print(f"🔍 Querying redetections (condition='{condition_name}')...")

        # TODO: Need to add query method for redetections
        # For now, create sample structure
        labels = []

        # Get all seed patterns
        seeds = self.seed_pattern_repo.find_active_patterns()
        print(f"   Found {len(seeds)} seed patterns")

        for seed in seeds:
            ticker = seed.ticker

            # Extract labels from block_features
            for seq_idx, feature in enumerate(seed.block_features, 1):
                label = {
                    "ticker": ticker,
                    "block_type": feature.block_type,
                    "sequence": seq_idx,
                    "started_at": feature.started_at.isoformat(),
                    "ended_at": feature.ended_at.isoformat() if feature.ended_at else "",
                    "peak_price": feature.peak_price,
                    "peak_volume": feature.peak_volume,
                    "duration": feature.duration_candles,
                    "similarity_score": 1.0,  # Seed pattern = perfect score
                    "source": f"seed:{seed.pattern_name}"
                }
                labels.append(label)

        # Filter by similarity
        filtered_labels = [l for l in labels if l["similarity_score"] >= min_similarity]

        print(f"   Total labels: {len(labels)}")
        print(f"   After similarity filter (>={min_similarity}): {len(filtered_labels)}")

        # Write to CSV
        print(f"💾 Writing to CSV: {output_csv}")

        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)

        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            if filtered_labels:
                fieldnames = list(filtered_labels[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered_labels)

        print(f"   ✅ Wrote {len(filtered_labels)} labels")

        return len(filtered_labels)

    def generate_summary_report(
        self,
        output_file: str
    ) -> Dict[str, Any]:
        """
        요약 리포트 생성

        Args:
            output_file: Output report file path

        Returns:
            Summary dict
        """
        print(f"\n{'='*60}")
        print(f"📈 Generating Summary Report")
        print(f"{'='*60}")

        # Count seeds
        seeds = self.seed_pattern_repo.find_active_patterns()

        # Aggregate statistics
        total_blocks = sum(len(seed.block_features) for seed in seeds)

        tickers = set(seed.ticker for seed in seeds)

        block_type_counts = {}
        for seed in seeds:
            for feature in seed.block_features:
                block_type = feature.block_type
                block_type_counts[block_type] = block_type_counts.get(block_type, 0) + 1

        summary = {
            "total_seed_patterns": len(seeds),
            "total_blocks": total_blocks,
            "unique_tickers": len(tickers),
            "tickers": sorted(tickers),
            "block_type_distribution": block_type_counts,
            "avg_blocks_per_pattern": total_blocks / len(seeds) if seeds else 0
        }

        # Write report
        print(f"💾 Writing report: {output_file}")

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ML Dataset Summary Report\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Total Seed Patterns: {summary['total_seed_patterns']}\n")
            f.write(f"Total Blocks: {summary['total_blocks']}\n")
            f.write(f"Unique Tickers: {summary['unique_tickers']}\n")
            f.write(f"Avg Blocks/Pattern: {summary['avg_blocks_per_pattern']:.2f}\n\n")

            f.write("Block Type Distribution:\n")
            for block_type, count in sorted(summary['block_type_distribution'].items()):
                f.write(f"  Block{block_type}: {count}\n")

            f.write("\nTickers:\n")
            for ticker in summary['tickers']:
                f.write(f"  {ticker}\n")

        print(f"   ✅ Report saved")

        print(f"\n📊 Summary:")
        print(f"   Seed patterns: {summary['total_seed_patterns']}")
        print(f"   Total blocks: {summary['total_blocks']}")
        print(f"   Unique tickers: {summary['unique_tickers']}")

        return summary

    def close(self):
        """Close session"""
        self.session.close()


def main():
    parser = argparse.ArgumentParser(description="Generate ML dataset from redetections")
    parser.add_argument("--output-csv", default="data/ml/block_labels.csv",
                        help="Output CSV file path")
    parser.add_argument("--output-report", default="data/ml/dataset_report.txt",
                        help="Output report file path")
    parser.add_argument("--min-similarity", type=float, default=0.7,
                        help="Minimum similarity score")
    parser.add_argument("--db", default="data/database/stock_data.db", help="Database path")

    args = parser.parse_args()

    # Generate dataset
    generator = MLDatasetGenerator(db_path=args.db)

    try:
        # Generate labels
        label_count = generator.generate_block_labels(
            output_csv=args.output_csv,
            min_similarity=args.min_similarity
        )

        # Generate report
        summary = generator.generate_summary_report(
            output_file=args.output_report
        )

        print(f"\n{'='*60}")
        print(f"✅ ML Dataset Generation Complete!")
        print(f"   Labels CSV: {args.output_csv}")
        print(f"   Report: {args.output_report}")
        print(f"{'='*60}\n")

        return 0 if label_count > 0 else 1

    finally:
        generator.close()


if __name__ == "__main__":
    sys.exit(main())
