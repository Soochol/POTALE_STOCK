"""
Peak Price 재계산 스크립트

DB에 저장된 잘못된 peak_price를 실제 차트 데이터로부터 재계산하여 수정합니다.
verify_peak_prices.py에서 발견된 불일치 문제를 해결하는 스크립트입니다.
"""
import sys
from pathlib import Path
from datetime import date
from typing import Tuple, List, Dict
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseConnection

DEFAULT_DB_PATH = 'data/database/stock_data.db'


class PeakPriceRecalculator:
    """Peak Price 재계산 클래스"""

    def __init__(self, db_path: str):
        """
        초기화

        Args:
            db_path: 데이터베이스 경로
        """
        self.db = DatabaseConnection(db_path)

    def get_actual_peak(
        self,
        ticker: str,
        from_date: date,
        to_date: date
    ) -> Tuple[float, date, int]:
        """
        실제 차트에서 최고가와 최고거래량 조회

        Args:
            ticker: 종목 코드
            from_date: 시작일
            to_date: 종료일

        Returns:
            (최고가, 최고가 날짜, 최고거래량) 튜플
        """
        with self.db.session_scope() as session:
            # 최고가 조회
            query_price = text("""
                SELECT high, date
                FROM stock_price
                WHERE ticker = :ticker
                  AND date >= :from_date
                  AND date <= :to_date
                ORDER BY high DESC
                LIMIT 1
            """)

            result_price = session.execute(
                query_price,
                {
                    'ticker': ticker,
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat()
                }
            ).fetchone()

            if not result_price:
                return None, None, None

            peak_price = float(result_price[0])
            peak_date = date.fromisoformat(result_price[1])

            # 최고거래량 조회
            query_volume = text("""
                SELECT volume
                FROM stock_price
                WHERE ticker = :ticker
                  AND date >= :from_date
                  AND date <= :to_date
                ORDER BY volume DESC
                LIMIT 1
            """)

            result_volume = session.execute(
                query_volume,
                {
                    'ticker': ticker,
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat()
                }
            ).fetchone()

            peak_volume = int(result_volume[0]) if result_volume else 0

            return peak_price, peak_date, peak_volume

    def recalculate_block1(
        self,
        ticker: str = None,
        dry_run: bool = True
    ) -> Dict:
        """
        Block1의 peak_price, peak_date, peak_volume 재계산

        Args:
            ticker: 특정 종목만 처리 (None이면 전체)
            dry_run: True면 실제 업데이트 안 함

        Returns:
            처리 결과 통계
        """
        with self.db.session_scope() as session:
            # Block1 조회 (completed 블록만)
            query = text("""
                SELECT block1_id, ticker, started_at, ended_at,
                       peak_price, peak_date, peak_volume
                FROM block1_detection
                WHERE status = 'completed'
                  AND ended_at IS NOT NULL
            """ + (" AND ticker = :ticker" if ticker else ""))

            params = {'ticker': ticker} if ticker else {}
            blocks = session.execute(query, params).fetchall()

            print(f"총 {len(blocks)}개 Block1 블록 처리 중...")
            print()

            updated_count = 0
            error_count = 0
            unchanged_count = 0

            for block in blocks:
                block1_id = block[0]
                ticker = block[1]
                started_at = date.fromisoformat(block[2])
                ended_at = date.fromisoformat(block[3])
                db_peak_price = float(block[4]) if block[4] else None
                db_peak_date = date.fromisoformat(block[5]) if block[5] else None
                db_peak_volume = int(block[6]) if block[6] else None

                # 실제 peak 계산
                actual_peak_price, actual_peak_date, actual_peak_volume = self.get_actual_peak(
                    ticker, started_at, ended_at
                )

                if actual_peak_price is None:
                    print(f"  [ERROR] Block1 #{block1_id}: 데이터 없음")
                    error_count += 1
                    continue

                # 불일치 체크 (가격만 체크, 0.01 허용 오차)
                if abs(db_peak_price - actual_peak_price) > 0.01:
                    diff_pct = ((actual_peak_price - db_peak_price) / db_peak_price) * 100
                    print(f"  [UPDATE] Block1 #{block1_id}")
                    print(f"           Period: {started_at} ~ {ended_at}")
                    print(f"           Peak Price:  {db_peak_price:>12,.0f} → {actual_peak_price:>12,.0f} ({diff_pct:+.2f}%)")
                    print(f"           Peak Date:   {db_peak_date} → {actual_peak_date}")
                    print(f"           Peak Volume: {db_peak_volume:>12,} → {actual_peak_volume:>12,}")
                    print()

                    if not dry_run:
                        # DB 업데이트
                        update_query = text("""
                            UPDATE block1_detection
                            SET peak_price = :peak_price,
                                peak_date = :peak_date,
                                peak_volume = :peak_volume
                            WHERE block1_id = :block1_id
                        """)

                        session.execute(
                            update_query,
                            {
                                'block1_id': block1_id,
                                'peak_price': actual_peak_price,
                                'peak_date': actual_peak_date.isoformat(),
                                'peak_volume': actual_peak_volume
                            }
                        )

                    updated_count += 1
                else:
                    unchanged_count += 1

            if not dry_run:
                session.commit()

        return {
            'total': len(blocks),
            'updated': updated_count,
            'unchanged': unchanged_count,
            'errors': error_count
        }

    def recalculate_block2(
        self,
        ticker: str = None,
        dry_run: bool = True
    ) -> Dict:
        """
        Block2의 peak_price, peak_date, peak_volume 재계산

        Args:
            ticker: 특정 종목만 처리 (None이면 전체)
            dry_run: True면 실제 업데이트 안 함

        Returns:
            처리 결과 통계
        """
        with self.db.session_scope() as session:
            query = text("""
                SELECT block2_id, ticker, started_at, ended_at,
                       peak_price, peak_date, peak_volume
                FROM block2_detection
                WHERE status = 'completed'
                  AND ended_at IS NOT NULL
            """ + (" AND ticker = :ticker" if ticker else ""))

            params = {'ticker': ticker} if ticker else {}
            blocks = session.execute(query, params).fetchall()

            print(f"총 {len(blocks)}개 Block2 블록 처리 중...")
            print()

            updated_count = 0
            error_count = 0
            unchanged_count = 0

            for block in blocks:
                block2_id = block[0]
                ticker = block[1]
                started_at = date.fromisoformat(block[2])
                ended_at = date.fromisoformat(block[3])
                db_peak_price = float(block[4]) if block[4] else None
                db_peak_date = date.fromisoformat(block[5]) if block[5] else None
                db_peak_volume = int(block[6]) if block[6] else None

                actual_peak_price, actual_peak_date, actual_peak_volume = self.get_actual_peak(
                    ticker, started_at, ended_at
                )

                if actual_peak_price is None:
                    print(f"  [ERROR] Block2 #{block2_id}: 데이터 없음")
                    error_count += 1
                    continue

                if abs(db_peak_price - actual_peak_price) > 0.01:
                    diff_pct = ((actual_peak_price - db_peak_price) / db_peak_price) * 100
                    print(f"  [UPDATE] Block2 #{block2_id}")
                    print(f"           Period: {started_at} ~ {ended_at}")
                    print(f"           Peak Price:  {db_peak_price:>12,.0f} → {actual_peak_price:>12,.0f} ({diff_pct:+.2f}%)")
                    print(f"           Peak Date:   {db_peak_date} → {actual_peak_date}")
                    print(f"           Peak Volume: {db_peak_volume:>12,} → {actual_peak_volume:>12,}")
                    print()

                    if not dry_run:
                        update_query = text("""
                            UPDATE block2_detection
                            SET peak_price = :peak_price,
                                peak_date = :peak_date,
                                peak_volume = :peak_volume
                            WHERE block2_id = :block2_id
                        """)

                        session.execute(
                            update_query,
                            {
                                'block2_id': block2_id,
                                'peak_price': actual_peak_price,
                                'peak_date': actual_peak_date.isoformat(),
                                'peak_volume': actual_peak_volume
                            }
                        )

                    updated_count += 1
                else:
                    unchanged_count += 1

            if not dry_run:
                session.commit()

        return {
            'total': len(blocks),
            'updated': updated_count,
            'unchanged': unchanged_count,
            'errors': error_count
        }

    def recalculate_block3(
        self,
        ticker: str = None,
        dry_run: bool = True
    ) -> Dict:
        """
        Block3의 peak_price, peak_date, peak_volume 재계산

        Args:
            ticker: 특정 종목만 처리 (None이면 전체)
            dry_run: True면 실제 업데이트 안 함

        Returns:
            처리 결과 통계
        """
        with self.db.session_scope() as session:
            query = text("""
                SELECT block3_id, ticker, started_at, ended_at,
                       peak_price, peak_date, peak_volume
                FROM block3_detection
                WHERE status = 'completed'
                  AND ended_at IS NOT NULL
            """ + (" AND ticker = :ticker" if ticker else ""))

            params = {'ticker': ticker} if ticker else {}
            blocks = session.execute(query, params).fetchall()

            print(f"총 {len(blocks)}개 Block3 블록 처리 중...")
            print()

            updated_count = 0
            error_count = 0
            unchanged_count = 0

            for block in blocks:
                block3_id = block[0]
                ticker = block[1]
                started_at = date.fromisoformat(block[2])
                ended_at = date.fromisoformat(block[3])
                db_peak_price = float(block[4]) if block[4] else None
                db_peak_date = date.fromisoformat(block[5]) if block[5] else None
                db_peak_volume = int(block[6]) if block[6] else None

                actual_peak_price, actual_peak_date, actual_peak_volume = self.get_actual_peak(
                    ticker, started_at, ended_at
                )

                if actual_peak_price is None:
                    print(f"  [ERROR] Block3 #{block3_id}: 데이터 없음")
                    error_count += 1
                    continue

                if abs(db_peak_price - actual_peak_price) > 0.01:
                    diff_pct = ((actual_peak_price - db_peak_price) / db_peak_price) * 100
                    print(f"  [UPDATE] Block3 #{block3_id}")
                    print(f"           Period: {started_at} ~ {ended_at}")
                    print(f"           Peak Price:  {db_peak_price:>12,.0f} → {actual_peak_price:>12,.0f} ({diff_pct:+.2f}%)")
                    print(f"           Peak Date:   {db_peak_date} → {actual_peak_date}")
                    print(f"           Peak Volume: {db_peak_volume:>12,} → {actual_peak_volume:>12,}")
                    print()

                    if not dry_run:
                        update_query = text("""
                            UPDATE block3_detection
                            SET peak_price = :peak_price,
                                peak_date = :peak_date,
                                peak_volume = :peak_volume
                            WHERE block3_id = :block3_id
                        """)

                        session.execute(
                            update_query,
                            {
                                'block3_id': block3_id,
                                'peak_price': actual_peak_price,
                                'peak_date': actual_peak_date.isoformat(),
                                'peak_volume': actual_peak_volume
                            }
                        )

                    updated_count += 1
                else:
                    unchanged_count += 1

            if not dry_run:
                session.commit()

        return {
            'total': len(blocks),
            'updated': updated_count,
            'unchanged': unchanged_count,
            'errors': error_count
        }

    def recalculate_block4(
        self,
        ticker: str = None,
        dry_run: bool = True
    ) -> Dict:
        """
        Block4의 peak_price, peak_date, peak_volume 재계산

        Args:
            ticker: 특정 종목만 처리 (None이면 전체)
            dry_run: True면 실제 업데이트 안 함

        Returns:
            처리 결과 통계
        """
        with self.db.session_scope() as session:
            query = text("""
                SELECT block4_id, ticker, started_at, ended_at,
                       peak_price, peak_date, peak_volume
                FROM block4_detection
                WHERE status = 'completed'
                  AND ended_at IS NOT NULL
            """ + (" AND ticker = :ticker" if ticker else ""))

            params = {'ticker': ticker} if ticker else {}
            blocks = session.execute(query, params).fetchall()

            print(f"총 {len(blocks)}개 Block4 블록 처리 중...")
            print()

            updated_count = 0
            error_count = 0
            unchanged_count = 0

            for block in blocks:
                block4_id = block[0]
                ticker = block[1]
                started_at = date.fromisoformat(block[2])
                ended_at = date.fromisoformat(block[3])
                db_peak_price = float(block[4]) if block[4] else None
                db_peak_date = date.fromisoformat(block[5]) if block[5] else None
                db_peak_volume = int(block[6]) if block[6] else None

                actual_peak_price, actual_peak_date, actual_peak_volume = self.get_actual_peak(
                    ticker, started_at, ended_at
                )

                if actual_peak_price is None:
                    print(f"  [ERROR] Block4 #{block4_id}: 데이터 없음")
                    error_count += 1
                    continue

                if abs(db_peak_price - actual_peak_price) > 0.01:
                    diff_pct = ((actual_peak_price - db_peak_price) / db_peak_price) * 100
                    print(f"  [UPDATE] Block4 #{block4_id}")
                    print(f"           Period: {started_at} ~ {ended_at}")
                    print(f"           Peak Price:  {db_peak_price:>12,.0f} → {actual_peak_price:>12,.0f} ({diff_pct:+.2f}%)")
                    print(f"           Peak Date:   {db_peak_date} → {actual_peak_date}")
                    print(f"           Peak Volume: {db_peak_volume:>12,} → {actual_peak_volume:>12,}")
                    print()

                    if not dry_run:
                        update_query = text("""
                            UPDATE block4_detection
                            SET peak_price = :peak_price,
                                peak_date = :peak_date,
                                peak_volume = :peak_volume
                            WHERE block4_id = :block4_id
                        """)

                        session.execute(
                            update_query,
                            {
                                'block4_id': block4_id,
                                'peak_price': actual_peak_price,
                                'peak_date': actual_peak_date.isoformat(),
                                'peak_volume': actual_peak_volume
                            }
                        )

                    updated_count += 1
                else:
                    unchanged_count += 1

            if not dry_run:
                session.commit()

        return {
            'total': len(blocks),
            'updated': updated_count,
            'unchanged': unchanged_count,
            'errors': error_count
        }


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Peak Price 재계산 스크립트')
    parser.add_argument(
        '--ticker',
        type=str,
        help='특정 종목만 처리 (예: 025980)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='실제로 DB에 반영 (기본: dry-run)'
    )
    parser.add_argument(
        '--db',
        type=str,
        default=DEFAULT_DB_PATH,
        help=f'데이터베이스 경로 (기본: {DEFAULT_DB_PATH})'
    )

    args = parser.parse_args()

    separator = "=" * 80
    print(separator)
    print("Peak Price 재계산 스크립트")
    print(separator)
    print()

    if args.apply:
        print("[APPLY MODE] 실제 DB에 반영합니다!")
    else:
        print("[DRY-RUN MODE] 변경 사항을 미리 확인합니다.")
        print("실제 반영하려면 --apply 옵션을 사용하세요.")
    print()

    recalculator = PeakPriceRecalculator(args.db)

    # Block1 재계산
    print(separator)
    print("Block1 재계산 시작")
    print(separator)
    result1 = recalculator.recalculate_block1(
        ticker=args.ticker,
        dry_run=not args.apply
    )
    print(f"Block1 결과: {result1['updated']}개 업데이트, "
          f"{result1['unchanged']}개 정상, {result1['errors']}개 오류")
    print()

    # Block2 재계산
    print(separator)
    print("Block2 재계산 시작")
    print(separator)
    result2 = recalculator.recalculate_block2(
        ticker=args.ticker,
        dry_run=not args.apply
    )
    print(f"Block2 결과: {result2['updated']}개 업데이트, "
          f"{result2['unchanged']}개 정상, {result2['errors']}개 오류")
    print()

    # Block3 재계산
    print(separator)
    print("Block3 재계산 시작")
    print(separator)
    result3 = recalculator.recalculate_block3(
        ticker=args.ticker,
        dry_run=not args.apply
    )
    print(f"Block3 결과: {result3['updated']}개 업데이트, "
          f"{result3['unchanged']}개 정상, {result3['errors']}개 오류")
    print()

    # Block4 재계산
    print(separator)
    print("Block4 재계산 시작")
    print(separator)
    result4 = recalculator.recalculate_block4(
        ticker=args.ticker,
        dry_run=not args.apply
    )
    print(f"Block4 결과: {result4['updated']}개 업데이트, "
          f"{result4['unchanged']}개 정상, {result4['errors']}개 오류")
    print()

    # 전체 요약
    print(separator)
    print("전체 요약")
    print(separator)
    total_blocks = result1['total'] + result2['total'] + result3['total'] + result4['total']
    total_updated = result1['updated'] + result2['updated'] + result3['updated'] + result4['updated']
    total_unchanged = result1['unchanged'] + result2['unchanged'] + result3['unchanged'] + result4['unchanged']
    total_errors = result1['errors'] + result2['errors'] + result3['errors'] + result4['errors']

    print(f"총 블록 수: {total_blocks:,}")
    print(f"  - 업데이트: {total_updated:,}")
    print(f"  - 정상: {total_unchanged:,}")
    print(f"  - 오류: {total_errors:,}")
    print()

    if not args.apply and total_updated > 0:
        print("실제로 반영하려면 --apply 옵션을 사용하세요:")
        if args.ticker:
            print(f"    python scripts/maintenance/recalculate_peak_prices.py --ticker {args.ticker} --apply")
        else:
            print("    python scripts/maintenance/recalculate_peak_prices.py --apply")

    print(separator)


if __name__ == '__main__':
    main()
