"""
Full Automated Pipeline

Seed Detection → Redetection → ML Dataset Generation
전체 파이프라인 자동 실행
"""
import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime


class PipelineOrchestrator:
    """전체 파이프라인 오케스트레이션"""

    def __init__(self, verbose: bool = True):
        """
        Args:
            verbose: Print detailed output
        """
        self.verbose = verbose
        self.script_dir = Path(__file__).parent
        self.python_exe = sys.executable

    def run_full_pipeline(
        self,
        seed_yaml: str,
        redetection_yaml: str,
        ticker: str,
        from_date: str,
        to_date: str = None,
        max_seed_patterns: int = 10,
        similarity_method: str = "dtw",
        min_similarity: float = 0.7,
        db_path: str = "data/database/stock_data.db"
    ) -> dict:
        """
        전체 파이프라인 실행

        Args:
            seed_yaml: Seed detection YAML path
            redetection_yaml: Redetection YAML path
            ticker: Stock ticker
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD, optional)
            max_seed_patterns: Max seed patterns to detect
            similarity_method: "range" or "dtw"
            min_similarity: Minimum similarity for ML dataset
            db_path: Database path

        Returns:
            Pipeline summary dict
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n{'='*70}")
        print(f"🚀 FULL AUTOMATED PIPELINE")
        print(f"{'='*70}")
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Ticker: {ticker}")
        print(f"📆 Date Range: {from_date} → {to_date or 'present'}")
        print(f"🔬 Similarity Method: {similarity_method}")
        print(f"{'='*70}\n")

        results = {}

        # Step 1: Seed Detection
        print(f"\n{'#'*70}")
        print(f"# STEP 1: Seed Pattern Detection")
        print(f"{'#'*70}\n")

        seed_result = self._run_seed_detection(
            yaml=seed_yaml,
            ticker=ticker,
            from_date=from_date,
            to_date=to_date,
            max_patterns=max_seed_patterns,
            db=db_path
        )

        results['seed_detection'] = seed_result

        if seed_result['returncode'] != 0:
            print(f"\n❌ Seed detection failed!")
            return results

        print(f"\n✅ Seed detection completed")

        # Step 2: Redetection
        print(f"\n{'#'*70}")
        print(f"# STEP 2: Redetection with {similarity_method.upper()}")
        print(f"{'#'*70}\n")

        redetection_result = self._run_redetection(
            redetection_yaml=redetection_yaml,
            ticker=ticker,
            from_date=from_date,
            to_date=to_date,
            method=similarity_method,
            db=db_path
        )

        results['redetection'] = redetection_result

        if redetection_result['returncode'] != 0:
            print(f"\n⚠️  Redetection completed with warnings")

        print(f"\n✅ Redetection completed")

        # Step 3: ML Dataset Generation
        print(f"\n{'#'*70}")
        print(f"# STEP 3: ML Dataset Generation")
        print(f"{'#'*70}\n")

        output_csv = f"data/ml/block_labels_{ticker}_{timestamp}.csv"
        output_report = f"data/ml/report_{ticker}_{timestamp}.txt"

        ml_result = self._run_ml_dataset_generation(
            output_csv=output_csv,
            output_report=output_report,
            min_similarity=min_similarity,
            db=db_path
        )

        results['ml_dataset'] = ml_result

        if ml_result['returncode'] != 0:
            print(f"\n⚠️  ML dataset generation completed with warnings")

        print(f"\n✅ ML dataset generation completed")

        # Final Summary
        print(f"\n{'='*70}")
        print(f"🎉 PIPELINE COMPLETE!")
        print(f"{'='*70}")
        print(f"📅 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📂 Output Files:")
        print(f"   ML Labels: {output_csv}")
        print(f"   Report: {output_report}")
        print(f"{'='*70}\n")

        results['status'] = 'success'
        results['timestamp'] = timestamp

        return results

    def _run_seed_detection(
        self,
        yaml: str,
        ticker: str,
        from_date: str,
        to_date: str,
        max_patterns: int,
        db: str
    ) -> dict:
        """Run seed detection script"""

        script = self.script_dir / "detect_seed_patterns.py"
        cmd = [
            self.python_exe,
            str(script),
            "--yaml", yaml,
            "--ticker", ticker,
            "--from-date", from_date,
            "--max-patterns", str(max_patterns),
            "--db", db
        ]

        if to_date:
            cmd.extend(["--to-date", to_date])

        print(f"🔧 Command: {' '.join(cmd)}\n")

        result = subprocess.run(cmd, capture_output=not self.verbose)

        return {
            'returncode': result.returncode,
            'cmd': ' '.join(cmd)
        }

    def _run_redetection(
        self,
        redetection_yaml: str,
        ticker: str,
        from_date: str,
        to_date: str,
        method: str,
        db: str
    ) -> dict:
        """Run redetection script"""

        script = self.script_dir / "run_redetection.py"
        cmd = [
            self.python_exe,
            str(script),
            "--redetection-yaml", redetection_yaml,
            "--ticker", ticker,
            "--from-date", from_date,
            "--method", method,
            "--db", db
        ]

        if to_date:
            cmd.extend(["--to-date", to_date])

        print(f"🔧 Command: {' '.join(cmd)}\n")

        result = subprocess.run(cmd, capture_output=not self.verbose)

        return {
            'returncode': result.returncode,
            'cmd': ' '.join(cmd)
        }

    def _run_ml_dataset_generation(
        self,
        output_csv: str,
        output_report: str,
        min_similarity: float,
        db: str
    ) -> dict:
        """Run ML dataset generation script"""

        script = self.script_dir / "generate_ml_dataset.py"
        cmd = [
            self.python_exe,
            str(script),
            "--output-csv", output_csv,
            "--output-report", output_report,
            "--min-similarity", str(min_similarity),
            "--db", db
        ]

        print(f"🔧 Command: {' '.join(cmd)}\n")

        result = subprocess.run(cmd, capture_output=not self.verbose)

        return {
            'returncode': result.returncode,
            'cmd': ' '.join(cmd)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Run full automated pipeline: Seed → Redetection → ML Dataset"
    )

    # Required arguments
    parser.add_argument("--seed-yaml", required=True, help="Seed detection YAML")
    parser.add_argument("--redetection-yaml", required=True, help="Redetection YAML")
    parser.add_argument("--ticker", required=True, help="Stock ticker")
    parser.add_argument("--from-date", required=True, help="Start date (YYYY-MM-DD)")

    # Optional arguments
    parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-seed-patterns", type=int, default=10,
                        help="Max seed patterns to detect")
    parser.add_argument("--method", choices=["range", "dtw"], default="dtw",
                        help="Similarity method")
    parser.add_argument("--min-similarity", type=float, default=0.7,
                        help="Min similarity for ML dataset")
    parser.add_argument("--db", default="data/database/stock_data.db", help="Database path")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    # Run pipeline
    orchestrator = PipelineOrchestrator(verbose=not args.quiet)

    try:
        results = orchestrator.run_full_pipeline(
            seed_yaml=args.seed_yaml,
            redetection_yaml=args.redetection_yaml,
            ticker=args.ticker,
            from_date=args.from_date,
            to_date=args.to_date,
            max_seed_patterns=args.max_seed_patterns,
            similarity_method=args.method,
            min_similarity=args.min_similarity,
            db_path=args.db
        )

        return 0 if results.get('status') == 'success' else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        return 130

    except Exception as e:
        print(f"\n\n❌ Pipeline failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
