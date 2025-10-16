"""
Investor Trading Collector
투자자별 거래 데이터 수집기
"""
from datetime import datetime, date
from typing import Optional, List
import time
import pandas as pd
from pykrx import stock
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from ...database.models import InvestorTrading, CollectionProgress
from ..base_collector import BaseCollector, CollectionResult


class InvestorTradingCollector(BaseCollector):
    """투자자별 거래 데이터 수집기"""

    def __init__(self, repository, delay: float = 0.1):
        """
        Args:
            repository: Repository 인스턴스
            delay: API 호출 간 지연 시간 (초)
        """
        super().__init__(delay)
        self.repository = repository

    def collect(self, target_date: date, market: str = "ALL") -> CollectionResult:
        """
        데이터 수집 실행 (BaseCollector의 추상 메소드 구현)

        Args:
            target_date: 수집 대상 날짜
            market: 시장 구분

        Returns:
            CollectionResult
        """
        return self.collect_by_date(target_date, market)

    def collect_by_date(
        self,
        target_date: date,
        market: str = "ALL"
    ) -> CollectionResult:
        """
        특정 날짜의 모든 종목 투자자 거래 데이터 수집

        Args:
            target_date: 수집 대상 날짜
            market: 시장 구분 ("KOSPI", "KOSDAQ", "ALL")

        Returns:
            CollectionResult: 수집 결과
        """
        started_at = datetime.now()

        try:
            # 날짜 형식 변환
            date_str = target_date.strftime("%Y%m%d")

            print(f"[{date_str}] Collecting investor trading data for {market}...")

            # PyKRX API 호출 - 날짜별 투자자 거래 데이터
            # 이 API는 한 번에 모든 종목의 데이터를 가져옴 (효율적!)
            df = stock.get_market_net_purchases_of_equities(
                date_str,
                date_str,
                market=market
            )

            if df is None or df.empty:
                return CollectionResult(
                    success=False,
                    record_count=0,
                    error_message=f"No data available for {date_str}",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # 데이터 변환
            records = self._transform_dataframe(df, target_date)

            # DB 저장 (bulk upsert)
            record_count = self._bulk_upsert(records)

            # 진행상황 업데이트
            self._update_progress(
                collection_type="investor_trading",
                target_date=target_date,
                status="completed",
                record_count=record_count
            )

            print(f"[{date_str}] Saved {record_count} records")

            return CollectionResult(
                success=True,
                record_count=record_count,
                started_at=started_at,
                completed_at=datetime.now()
            )

        except Exception as e:
            error_msg = f"Error collecting data for {target_date}: {str(e)}"
            print(f"[ERROR] {error_msg}")

            # 진행상황 업데이트 (실패)
            self._update_progress(
                collection_type="investor_trading",
                target_date=target_date,
                status="failed",
                error_message=str(e)
            )

            return CollectionResult(
                success=False,
                record_count=0,
                error_message=error_msg,
                started_at=started_at,
                completed_at=datetime.now()
            )

    def _transform_dataframe(self, df: pd.DataFrame, target_date: date) -> List[dict]:
        """
        PyKRX DataFrame을 DB 레코드 형식으로 변환

        Args:
            df: PyKRX에서 반환된 DataFrame
            target_date: 대상 날짜

        Returns:
            List[dict]: DB 레코드 리스트
        """
        records = []

        # DataFrame의 인덱스가 ticker임
        for ticker in df.index:
            row = df.loc[ticker]

            record = {
                'ticker': ticker,
                'date': target_date,
                'institution_net_buy': int(row.get('기관', 0)) if pd.notna(row.get('기관', 0)) else 0,
                'foreign_net_buy': int(row.get('외국인', 0)) if pd.notna(row.get('외국인', 0)) else 0,
                'individual_net_buy': int(row.get('개인', 0)) if pd.notna(row.get('개인', 0)) else 0,
                'created_at': datetime.now()
            }

            records.append(record)

        return records

    def _bulk_upsert(self, records: List[dict]) -> int:
        """
        대량 upsert (insert or update)

        Args:
            records: 저장할 레코드 리스트

        Returns:
            int: 저장된 레코드 수
        """
        if not records:
            return 0

        with self.repository.db.session_scope() as session:
            # SQLite의 INSERT OR REPLACE 사용
            stmt = insert(InvestorTrading).values(records)

            # on_conflict_do_update: ticker + date가 이미 존재하면 업데이트
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'date'],
                set_={
                    'institution_net_buy': stmt.excluded.institution_net_buy,
                    'foreign_net_buy': stmt.excluded.foreign_net_buy,
                    'individual_net_buy': stmt.excluded.individual_net_buy,
                    'created_at': stmt.excluded.created_at
                }
            )

            session.execute(stmt)
            session.commit()

        return len(records)

    def _update_progress(
        self,
        collection_type: str,
        target_date: date,
        status: str,
        record_count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        수집 진행상황 업데이트

        Args:
            collection_type: 수집 타입
            target_date: 대상 날짜
            status: 상태 (pending, in_progress, completed, failed)
            record_count: 수집된 레코드 수
            error_message: 에러 메시지
        """
        with self.repository.db.session_scope() as session:
            # 기존 진행상황 조회
            progress = session.query(CollectionProgress).filter_by(
                collection_type=collection_type,
                target_date=target_date
            ).first()

            if progress:
                # 업데이트
                progress.status = status
                progress.record_count = record_count
                progress.error_message = error_message
                progress.updated_at = datetime.now()

                if status == "in_progress" and not progress.started_at:
                    progress.started_at = datetime.now()
                elif status in ["completed", "failed"]:
                    progress.completed_at = datetime.now()
            else:
                # 신규 생성
                progress = CollectionProgress(
                    collection_type=collection_type,
                    target_date=target_date,
                    status=status,
                    record_count=record_count,
                    error_message=error_message,
                    started_at=datetime.now() if status == "in_progress" else None,
                    completed_at=datetime.now() if status in ["completed", "failed"] else None
                )
                session.add(progress)

            session.commit()

    def collect_date_range(
        self,
        start_date: date,
        end_date: date,
        market: str = "ALL",
        delay: float = 0.1
    ) -> CollectionResult:
        """
        날짜 범위의 투자자 거래 데이터 수집

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            market: 시장 구분
            delay: API 호출 간 지연 시간 (초)

        Returns:
            CollectionResult: 전체 수집 결과
        """
        started_at = datetime.now()
        total_records = 0
        failed_dates = []

        # 날짜 범위 생성
        from datetime import timedelta

        current_date = start_date
        dates = []

        while current_date <= end_date:
            dates.append(current_date)
            current_date = current_date + timedelta(days=1)

        print(f"\nCollecting investor trading data from {start_date} to {end_date}")
        print(f"Total dates: {len(dates)}")

        for i, target_date in enumerate(dates, 1):
            print(f"\nProgress: {i}/{len(dates)} ({i/len(dates)*100:.1f}%)")

            result = self.collect_by_date(target_date, market)

            if result.success:
                total_records += result.record_count
            else:
                failed_dates.append(target_date)

            # API 요청 제한을 위한 지연
            if i < len(dates):
                time.sleep(delay)

        # 최종 결과
        success = len(failed_dates) == 0
        error_msg = None if success else f"Failed dates: {failed_dates}"

        return CollectionResult(
            success=success,
            record_count=total_records,
            error_message=error_msg,
            started_at=started_at,
            completed_at=datetime.now()
        )
