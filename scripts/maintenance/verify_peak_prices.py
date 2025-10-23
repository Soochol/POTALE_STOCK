"""
Peak Price 검증 스크립트

모든 블록의 peak_price가 실제 범위 최고점과 일치하는지 검증

사용법:
    python scripts/maintenance/verify_peak_prices.py --ticker 025980
    python scripts/maintenance/verify_peak_prices.py --all
    python scripts/maintenance/verify_peak_prices.py --ticker 025980 --verbose
"""
import argparse
import sys
from pathlib import Path
from datetime import date, timedelta
from typing import List, Dict, Tuple

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseConnection
from sqlalchemy import text


class PeakPriceVerifier:
    """Peak Price 검증기"""

    def __init__(self, db_path: str):
        self.db = DatabaseConnection(db_path)

    def get_actual_max_high(
        self,
        ticker: str,
        from_date: date,
        to_date: date
    ) -> Tuple[float, date]:
        """
        기간 내 실제 최고가 및 날짜 조회

        Returns:
            (최고가, 최고가 날짜)
        """
        with self.db.session_scope() as session:
            query = text("""
                SELECT high, date
                FROM stock_price
                WHERE ticker = :ticker
                AND date >= :from_date
                AND date <= :to_date
                ORDER BY high DESC
                LIMIT 1
            """)
            result = session.execute(
                query,
                {
                    'ticker': ticker,
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat()
                }
            ).fetchone()

            if result:
                return float(result[0]), date.fromisoformat(result[1])
            return 0.0, None

    def verify_block1(self, ticker: str = None) -> List[Dict]:
        """Block1 peak_price 검증"""
        with self.db.session_scope() as session:
            query_str = """
                SELECT id, block1_id, ticker, started_at, ended_at,
                       peak_price, peak_date, status
                FROM block1_detection
                WHERE ended_at IS NOT NULL
            """
            params = {}

            if ticker:
                query_str += " AND ticker = :ticker"
                params['ticker'] = ticker

            query_str += " ORDER BY started_at"

            blocks = session.execute(text(query_str), params).fetchall()

        mismatches = []

        for block in blocks:
            block_id, block1_id, ticker, started_at, ended_at, peak_price, peak_date, status = block

            started_at = date.fromisoformat(started_at)
            ended_at = date.fromisoformat(ended_at)
            peak_date_db = date.fromisoformat(peak_date) if peak_date else None

            # 실제 최고가 계산
            actual_high, actual_date = self.get_actual_max_high(
                ticker,
                started_at,
                ended_at
            )

            # 불일치 확인
            if abs(actual_high - peak_price) > 0.01:  # 부동소수점 오차 허용
                mismatches.append({
                    'block_type': 'Block1',
                    'block_id': block1_id,
                    'ticker': ticker,
                    'started_at': started_at,
                    'ended_at': ended_at,
                    'db_peak_price': peak_price,
                    'db_peak_date': peak_date_db,
                    'actual_peak_price': actual_high,
                    'actual_peak_date': actual_date,
                    'diff': actual_high - peak_price,
                    'diff_pct': ((actual_high - peak_price) / peak_price * 100) if peak_price > 0 else 0
                })

        return mismatches

    def verify_block2(self, ticker: str = None) -> List[Dict]:
        """Block2 peak_price 검증"""
        with self.db.session_scope() as session:
            query_str = """
                SELECT id, block2_id, ticker, started_at, ended_at,
                       peak_price, peak_date, status
                FROM block2_detection
                WHERE ended_at IS NOT NULL
            """
            params = {}

            if ticker:
                query_str += " AND ticker = :ticker"
                params['ticker'] = ticker

            query_str += " ORDER BY started_at"

            blocks = session.execute(text(query_str), params).fetchall()

        mismatches = []

        for block in blocks:
            block_id, block2_id, ticker, started_at, ended_at, peak_price, peak_date, status = block

            started_at = date.fromisoformat(started_at)
            ended_at = date.fromisoformat(ended_at)
            peak_date_db = date.fromisoformat(peak_date) if peak_date else None

            # 실제 최고가 계산
            actual_high, actual_date = self.get_actual_max_high(
                ticker,
                started_at,
                ended_at
            )

            # 불일치 확인
            if abs(actual_high - peak_price) > 0.01:
                mismatches.append({
                    'block_type': 'Block2',
                    'block_id': block2_id,
                    'ticker': ticker,
                    'started_at': started_at,
                    'ended_at': ended_at,
                    'db_peak_price': peak_price,
                    'db_peak_date': peak_date_db,
                    'actual_peak_price': actual_high,
                    'actual_peak_date': actual_date,
                    'diff': actual_high - peak_price,
                    'diff_pct': ((actual_high - peak_price) / peak_price * 100) if peak_price > 0 else 0
                })

        return mismatches

    def verify_block3(self, ticker: str = None) -> List[Dict]:
        """Block3 peak_price 검증"""
        with self.db.session_scope() as session:
            query_str = """
                SELECT id, block3_id, ticker, started_at, ended_at,
                       peak_price, peak_date, status
                FROM block3_detection
                WHERE ended_at IS NOT NULL
            """
            params = {}

            if ticker:
                query_str += " AND ticker = :ticker"
                params['ticker'] = ticker

            query_str += " ORDER BY started_at"

            blocks = session.execute(text(query_str), params).fetchall()

        mismatches = []

        for block in blocks:
            block_id, block3_id, ticker, started_at, ended_at, peak_price, peak_date, status = block

            started_at = date.fromisoformat(started_at)
            ended_at = date.fromisoformat(ended_at)
            peak_date_db = date.fromisoformat(peak_date) if peak_date else None

            # 실제 최고가 계산
            actual_high, actual_date = self.get_actual_max_high(
                ticker,
                started_at,
                ended_at
            )

            # 불일치 확인
            if abs(actual_high - peak_price) > 0.01:
                mismatches.append({
                    'block_type': 'Block3',
                    'block_id': block3_id,
                    'ticker': ticker,
                    'started_at': started_at,
                    'ended_at': ended_at,
                    'db_peak_price': peak_price,
                    'db_peak_date': peak_date_db,
                    'actual_peak_price': actual_high,
                    'actual_peak_date': actual_date,
                    'diff': actual_high - peak_price,
                    'diff_pct': ((actual_high - peak_price) / peak_price * 100) if peak_price > 0 else 0
                })

        return mismatches

    def verify_all_blocks(self, ticker: str = None) -> Dict[str, List[Dict]]:
        """모든 블록 타입 검증"""
        return {
            'block1': self.verify_block1(ticker),
            'block2': self.verify_block2(ticker),
            'block3': self.verify_block3(ticker),
        }


def print_summary(results: Dict[str, List[Dict]], verbose: bool = False):
    """검증 결과 요약 출력"""
    print("\n" + "=" * 80)
    print("Peak Price 검증 결과")
    print("=" * 80)

    total_mismatches = 0

    for block_type, mismatches in results.items():
        print(f"\n{block_type.upper()}: {len(mismatches)}개 불일치")
        total_mismatches += len(mismatches)

        if verbose and mismatches:
            print("\n상세 내역:")
            print("-" * 80)
            for i, mismatch in enumerate(mismatches, 1):
                print(f"\n[{i}] {mismatch['block_id']} ({mismatch['ticker']})")
                print(f"    기간: {mismatch['started_at']} ~ {mismatch['ended_at']}")
                print(f"    DB peak_price: {mismatch['db_peak_price']:,.0f} ({mismatch['db_peak_date']})")
                print(f"    실제 최고가: {mismatch['actual_peak_price']:,.0f} ({mismatch['actual_peak_date']})")
                print(f"    차이: {mismatch['diff']:+,.0f} ({mismatch['diff_pct']:+.2f}%)")

    print("\n" + "=" * 80)
    print(f"총 불일치: {total_mismatches}개")
    print("=" * 80 + "\n")

    return total_mismatches


def main():
    parser = argparse.ArgumentParser(
        description="Block Peak Price 검증"
    )
    parser.add_argument(
        "--ticker",
        help="검증할 종목 코드 (예: 025980)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="모든 종목 검증"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 출력"
    )
    parser.add_argument(
        "--db",
        default="data/database/stock_data.db",
        help="데이터베이스 경로"
    )

    args = parser.parse_args()

    if not args.ticker and not args.all:
        print("[ERROR] --ticker 또는 --all 옵션이 필요합니다")
        parser.print_help()
        return 1

    # 검증 실행
    verifier = PeakPriceVerifier(args.db)

    ticker = args.ticker.zfill(6) if args.ticker else None
    results = verifier.verify_all_blocks(ticker)

    # 결과 출력
    total_mismatches = print_summary(results, args.verbose)

    # 종료 코드
    return 0 if total_mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
