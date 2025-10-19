"""
Incremental Collector - 증분 수집 로직
이미 수집된 데이터는 건너뛰고, 최신 데이터만 수집
"""
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional

from .common.types import CollectionPlan
from .common.logger import get_logger
from ..database.connection import DatabaseConnection
from ..database.queries import (
    get_latest_dates_bulk,
    get_date_range_bulk,
    get_tickers_without_data,
    get_tickers_needing_update
)


class IncrementalCollector:
    """
    증분 수집 관리자

    Features:
    - 각 종목의 최신 날짜 자동 확인
    - 이미 수집된 데이터는 건너뛰기
    - 신규 종목은 전체 수집
    - 기존 종목은 최신일+1부터 수집
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Args:
            db_connection: 데이터베이스 연결
        """
        self.db = db_connection
        self.logger = get_logger()

    def get_collection_plan(
        self,
        tickers: List[str],
        fromdate: date,
        todate: date,
        force_full: bool = False
    ) -> List[CollectionPlan]:
        """
        종목별 수집 계획 수립

        Args:
            tickers: 종목 코드 리스트
            fromdate: 요청 시작 날짜
            todate: 요청 종료 날짜
            force_full: True면 모든 종목을 전체 수집 (증분 무시)

        Returns:
            CollectionPlan 리스트 (수집이 필요한 종목만)

        Example:
            >>> plans = collector.get_collection_plan(
            ...     ['005930', '000660'],
            ...     date(2024, 1, 1),
            ...     date(2024, 12, 31)
            ... )
            >>> for plan in plans:
            ...     print(f"{plan.ticker}: {plan.fromdate} ~ {plan.todate}")
        """
        if not tickers:
            return []

        session = self.db.get_session()
        try:
            # 1. 모든 종목의 최신 날짜 조회 (단일 쿼리)
            latest_dates = get_latest_dates_bulk(session, tickers)

            # 2. 수집 계획 수립
            plans = []

            for ticker in tickers:
                latest_date = latest_dates.get(ticker)

                # 전체 재수집 강제
                if force_full:
                    plan = CollectionPlan(
                        ticker=ticker,
                        fromdate=fromdate,
                        todate=todate,
                        is_full_collection=True,
                        existing_latest_date=latest_date
                    )
                    plans.append(plan)
                    continue

                # 데이터가 없는 신규 종목 → 전체 수집
                if latest_date is None:
                    plan = CollectionPlan(
                        ticker=ticker,
                        fromdate=fromdate,
                        todate=todate,
                        is_full_collection=True,
                        existing_latest_date=None
                    )
                    plans.append(plan)

                # 이미 최신 데이터 보유 → 건너뛰기
                elif latest_date >= todate:
                    # Skip silently (already up-to-date)
                    continue

                # 증분 수집 (최신일+1 ~ todate)
                else:
                    incremental_from = latest_date + timedelta(days=1)

                    # 증분 수집 범위가 요청 범위보다 이전이면 조정
                    if incremental_from < fromdate:
                        incremental_from = fromdate

                    plan = CollectionPlan(
                        ticker=ticker,
                        fromdate=incremental_from,
                        todate=todate,
                        is_full_collection=False,
                        existing_latest_date=latest_date
                    )
                    plans.append(plan)

            return plans

        finally:
            session.close()

    def optimize_collection_order(
        self,
        plans: List[CollectionPlan],
        strategy: str = "small_first"
    ) -> List[CollectionPlan]:
        """
        수집 계획 순서 최적화

        Args:
            plans: 수집 계획 리스트
            strategy: 정렬 전략
                - "small_first": 작은 것부터 (증분 우선, 빠른 완료)
                - "large_first": 큰 것부터 (전체 수집 우선)
                - "ticker": 종목코드 순

        Returns:
            정렬된 CollectionPlan 리스트
        """
        if strategy == "small_first":
            # 증분 수집 우선, 예상 일수 작은 순
            return sorted(
                plans,
                key=lambda p: (p.is_full_collection, p.estimated_days)
            )

        elif strategy == "large_first":
            # 전체 수집 우선, 예상 일수 큰 순
            return sorted(
                plans,
                key=lambda p: (not p.is_full_collection, -p.estimated_days)
            )

        elif strategy == "ticker":
            # 종목코드 순
            return sorted(plans, key=lambda p: p.ticker)

        else:
            return plans

    def print_collection_summary(
        self,
        plans: List[CollectionPlan],
        total_tickers: int
    ):
        """
        수집 계획 요약 출력

        Args:
            plans: 수집 계획 리스트
            total_tickers: 전체 종목 수
        """
        if not plans:
            print("\n[green]모든 종목이 이미 최신 상태입니다![/green]")
            return

        # 통계 계산
        full_count = sum(1 for p in plans if p.is_full_collection)
        incremental_count = len(plans) - full_count
        skipped_count = total_tickers - len(plans)
        total_estimated_days = sum(p.estimated_days for p in plans)

        print("\n" + "=" * 80)
        print("[bold cyan]증분 수집 계획 요약[/bold cyan]")
        print("=" * 80)
        print(f"전체 종목 수:        {total_tickers:>10,}개")
        print(f"수집 필요 종목:      {len(plans):>10,}개")
        print(f"  - 전체 수집:       {full_count:>10,}개 (신규 종목)")
        print(f"  - 증분 수집:       {incremental_count:>10,}개 (업데이트)")
        print(f"건너뛰기:            {skipped_count:>10,}개 (이미 최신)")
        print(f"예상 수집량:         {total_estimated_days:>10,} 거래일")
        print("=" * 80 + "\n")

        # 샘플 출력 (처음 5개)
        if len(plans) > 0:
            print("[dim]수집 계획 샘플 (처음 5개):[/dim]")
            for i, plan in enumerate(plans[:5], 1):
                collection_type = "전체" if plan.is_full_collection else "증분"
                print(
                    f"  {i}. {plan.ticker}: "
                    f"{plan.fromdate} ~ {plan.todate} "
                    f"({plan.estimated_days}일, {collection_type})"
                )
            if len(plans) > 5:
                print(f"  ... 외 {len(plans) - 5}개")
            print()

    def get_statistics(self, tickers: List[str]) -> Dict:
        """
        전체 종목의 수집 통계 조회

        Args:
            tickers: 종목 코드 리스트

        Returns:
            통계 딕셔너리
        """
        session = self.db.get_session()
        try:
            # 날짜 범위 조회
            date_ranges = get_date_range_bulk(session, tickers)

            # 통계 계산
            tickers_with_data = sum(
                1 for ticker in tickers
                if date_ranges.get(ticker, (None, None))[0] is not None
            )

            tickers_without_data = len(tickers) - tickers_with_data

            # 전체 최초일/최신일
            all_earliest = None
            all_latest = None

            for ticker in tickers:
                earliest, latest = date_ranges.get(ticker, (None, None))
                if earliest:
                    if all_earliest is None or earliest < all_earliest:
                        all_earliest = earliest
                if latest:
                    if all_latest is None or latest > all_latest:
                        all_latest = latest

            return {
                'total_tickers': len(tickers),
                'tickers_with_data': tickers_with_data,
                'tickers_without_data': tickers_without_data,
                'earliest_date': all_earliest,
                'latest_date': all_latest,
                'date_ranges': date_ranges
            }

        finally:
            session.close()

    def validate_collection(
        self,
        tickers: List[str],
        fromdate: date,
        todate: date
    ) -> Dict:
        """
        수집 완료 후 검증

        Args:
            tickers: 종목 코드 리스트
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            검증 결과 딕셔너리
        """
        session = self.db.get_session()
        try:
            latest_dates = get_latest_dates_bulk(session, tickers)

            # 검증
            up_to_date = []
            needs_update = []
            no_data = []

            for ticker in tickers:
                latest = latest_dates.get(ticker)

                if latest is None:
                    no_data.append(ticker)
                elif latest >= todate:
                    up_to_date.append(ticker)
                else:
                    needs_update.append((ticker, latest))

            return {
                'total': len(tickers),
                'up_to_date': len(up_to_date),
                'needs_update': len(needs_update),
                'no_data': len(no_data),
                'up_to_date_tickers': up_to_date,
                'needs_update_tickers': needs_update,
                'no_data_tickers': no_data
            }

        finally:
            session.close()

    def print_validation_result(self, validation: Dict):
        """
        검증 결과 출력

        Args:
            validation: validate_collection() 결과
        """
        print("\n" + "=" * 80)
        print("[bold cyan]수집 검증 결과[/bold cyan]")
        print("=" * 80)
        print(f"전체 종목:      {validation['total']:>10,}개")
        print(f"[green]최신 상태:      {validation['up_to_date']:>10,}개[/green]")

        if validation['needs_update'] > 0:
            print(f"[yellow]업데이트 필요:  {validation['needs_update']:>10,}개[/yellow]")
            # 샘플 출력
            for ticker, latest in validation['needs_update_tickers'][:5]:
                print(f"  - {ticker}: {latest}")
            if validation['needs_update'] > 5:
                print(f"  ... 외 {validation['needs_update'] - 5}개")

        if validation['no_data'] > 0:
            print(f"[red]데이터 없음:    {validation['no_data']:>10,}개[/red]")
            # 샘플 출력
            for ticker in validation['no_data_tickers'][:5]:
                print(f"  - {ticker}")
            if validation['no_data'] > 5:
                print(f"  ... 외 {validation['no_data'] - 5}개")

        print("=" * 80 + "\n")
