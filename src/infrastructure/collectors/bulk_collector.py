"""
Bulk Collector - 대량 데이터 수집기
네이버 금융에서 모든 종목의 데이터를 체계적으로 수집
"""
import time
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .naver.naver_investor_collector import NaverInvestorCollector
from .naver.naver_price_collector import NaverPriceCollector
from .naver.naver_hybrid_collector import NaverHybridCollector
from ..database.connection import DatabaseConnection
from ..database.models import CollectionProgress


@dataclass
class BulkCollectionStats:
    """대량 수집 통계"""
    total_tickers: int = 0
    completed_tickers: int = 0
    failed_tickers: int = 0
    total_records: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def print_summary(self):
        """통계 요약 출력"""
        if not self.started_at:
            return

        elapsed = (self.completed_at or datetime.now()) - self.started_at
        elapsed_seconds = elapsed.total_seconds()

        print(f"""
========================================
      Bulk Collection Statistics
========================================
 Total Tickers:     {self.total_tickers:>10}
 Completed:         {self.completed_tickers:>10}
 Failed:            {self.failed_tickers:>10}
 Total Records:     {self.total_records:>10}
 Time Elapsed:      {elapsed_seconds/3600:>10.1f}h
 Average Speed:     {self.total_records/elapsed_seconds if elapsed_seconds > 0 else 0:>10.0f} rec/s
========================================
        """)


class BulkCollector:
    """
    대량 데이터 수집기

    네이버 금융에서 모든 종목의 데이터를 수집합니다.
    - 종목별 순차 수집 (네이버 금융의 한계)
    - 진행 상황 추적 및 재개 기능
    - 자동 재시도 및 에러 처리
    """

    def __init__(self, db_connection: DatabaseConnection, delay: float = 0.2, use_hybrid: bool = True):
        """
        Args:
            db_connection: 데이터베이스 연결
            delay: API 호출 간 대기 시간 (초) - 네이버는 0.2초 권장
            use_hybrid: 하이브리드 수집기 사용 여부 (수정주가+수정거래량)
        """
        self.db = db_connection
        self.delay = delay
        self.use_hybrid = use_hybrid

        # 개별 수집기들
        if use_hybrid:
            # NaverHybridCollector: 수정주가 + 수정거래량
            self.price_collector = NaverHybridCollector(db_connection, delay)
        else:
            # NaverPriceCollector: 원본 주가 (레거시)
            self.price_collector = NaverPriceCollector(db_connection, delay)

        self.investor_collector = NaverInvestorCollector(db_connection, delay)

        # 통계
        self.stats = BulkCollectionStats()

    def collect_all_stocks(
        self,
        tickers: List[str],
        fromdate: date,
        todate: date,
        collect_price: bool = True,
        collect_investor: bool = True,
        resume: bool = False
    ) -> BulkCollectionStats:
        """
        모든 종목의 데이터를 수집

        Args:
            tickers: 종목 코드 리스트
            fromdate: 시작 날짜
            todate: 종료 날짜
            collect_price: 주가 데이터 수집 여부
            collect_investor: 투자자 거래 데이터 수집 여부
            resume: 중단된 작업 재개 여부

        Returns:
            BulkCollectionStats: 수집 통계
        """
        self.stats = BulkCollectionStats(
            total_tickers=len(tickers),
            started_at=datetime.now()
        )

        print(f"\n{'='*80}")
        print(f"대량 데이터 수집 시작")
        print(f"{'='*80}")
        print(f"종목 수: {len(tickers):,}개")
        print(f"기간: {fromdate} ~ {todate}")
        print(f"수집 방식: {'하이브리드 (수정주가+수정거래량)' if self.use_hybrid else '일반 (원본 주가)'}")
        print(f"수집 항목: ", end="")
        items = []
        if collect_price:
            items.append("주가" if not self.use_hybrid else "주가(수정)")
        if collect_investor:
            items.append("투자자거래")
        print(", ".join(items))
        print(f"{'='*80}\n")

        # 재개 시 완료된 종목 건너뛰기
        if resume:
            completed_tickers = self._get_completed_tickers(fromdate, todate)
            tickers = [t for t in tickers if t not in completed_tickers]
            print(f"[Resume] {len(completed_tickers)}개 종목 이미 완료, {len(tickers)}개 종목 남음\n")

        # 종목별 수집
        for idx, ticker in enumerate(tickers, 1):
            print(f"\n[{idx}/{len(tickers)}] {ticker} 수집 중...")

            try:
                ticker_records = 0

                # 주가 데이터 수집
                if collect_price:
                    result = self.price_collector.collect(ticker, fromdate, todate)
                    if result.success:
                        ticker_records += result.record_count
                        if self.use_hybrid:
                            print(f"  [OK] Price (Hybrid): {result.record_count} records (수정주가+수정거래량)")
                        else:
                            print(f"  [OK] Price: {result.record_count} records")
                    else:
                        print(f"  [FAIL] Price collection failed: {result.error_message}")

                # 투자자 거래 데이터 수집
                if collect_investor:
                    result = self.investor_collector.collect(ticker, fromdate, todate)
                    if result.success:
                        ticker_records += result.record_count
                        print(f"  [OK] Investor: {result.record_count} records")
                    else:
                        print(f"  [FAIL] Investor collection failed: {result.error_message}")

                # 통계 업데이트
                self.stats.completed_tickers += 1
                self.stats.total_records += ticker_records

                # 진행률 표시
                progress_pct = (idx / len(tickers)) * 100
                elapsed = datetime.now() - self.stats.started_at
                eta = self._calculate_eta(idx, len(tickers), elapsed)

                print(f"  진행률: {progress_pct:.1f}% | "
                      f"완료: {self.stats.completed_tickers}/{len(tickers)} | "
                      f"레코드: {self.stats.total_records:,}개 | "
                      f"ETA: {eta}")

            except KeyboardInterrupt:
                print(f"\n\n사용자가 중단했습니다.")
                print(f"재개하려면: --resume 옵션 사용")
                break

            except Exception as e:
                print(f"  [FAIL] {ticker} collection failed: {e}")
                self.stats.failed_tickers += 1
                self._log_error(ticker, fromdate, todate, str(e))

        # 완료
        self.stats.completed_at = datetime.now()

        print(f"\n{'='*80}")
        print(f"대량 수집 완료")
        print(f"{'='*80}")
        self.stats.print_summary()

        return self.stats

    def collect_ticker_with_retry(
        self,
        ticker: str,
        fromdate: date,
        todate: date,
        collect_price: bool = True,
        collect_investor: bool = True,
        max_retries: int = 3
    ) -> Tuple[int, List[str]]:
        """
        단일 종목 수집 (재시도 포함)

        Args:
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜
            collect_price: 주가 수집 여부
            collect_investor: 투자자 거래 수집 여부
            max_retries: 최대 재시도 횟수

        Returns:
            (레코드 수, 에러 메시지 리스트)
        """
        total_records = 0
        errors = []

        # 주가 데이터
        if collect_price:
            for attempt in range(max_retries):
                try:
                    result = self.price_collector.collect(ticker, fromdate, todate)
                    if result.success:
                        total_records += result.record_count
                        break
                    else:
                        errors.append(f"주가: {result.error_message}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # 지수 백오프
                except Exception as e:
                    errors.append(f"주가: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)

        # 투자자 거래 데이터
        if collect_investor:
            for attempt in range(max_retries):
                try:
                    result = self.investor_collector.collect(ticker, fromdate, todate)
                    if result.success:
                        total_records += result.record_count
                        break
                    else:
                        errors.append(f"투자자거래: {result.error_message}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                except Exception as e:
                    errors.append(f"투자자거래: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)

        return total_records, errors

    def _get_completed_tickers(self, fromdate: date, todate: date) -> List[str]:
        """
        이미 수집 완료된 종목 리스트 조회

        Args:
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            완료된 종목 코드 리스트
        """
        session = self.db.get_session()

        try:
            # CollectionProgress에서 완료된 종목 조회
            completed = session.query(CollectionProgress).filter(
                CollectionProgress.status == 'completed',
                CollectionProgress.target_date == fromdate
            ).all()

            # collection_type에서 ticker 추출
            # 예: "stock_price_005930" -> "005930"
            tickers = []
            for progress in completed:
                parts = progress.collection_type.split('_')
                if len(parts) >= 3:
                    ticker = parts[-1]
                    tickers.append(ticker)

            return list(set(tickers))

        finally:
            session.close()

    def _calculate_eta(self, current: int, total: int, elapsed: timedelta) -> str:
        """
        완료 예상 시간 계산

        Args:
            current: 현재 진행 수
            total: 전체 수
            elapsed: 경과 시간

        Returns:
            ETA 문자열 (예: "2시간 30분")
        """
        if current == 0:
            return "계산 중..."

        avg_time_per_item = elapsed.total_seconds() / current
        remaining_items = total - current
        remaining_seconds = avg_time_per_item * remaining_items

        hours = int(remaining_seconds // 3600)
        minutes = int((remaining_seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}시간 {minutes}분"
        else:
            return f"{minutes}분"

    def _log_error(self, ticker: str, fromdate: date, todate: date, error: str):
        """
        에러 로깅

        Args:
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜
            error: 에러 메시지
        """
        session = self.db.get_session()

        try:
            # CollectionProgress에 실패 기록
            progress = CollectionProgress(
                collection_type=f"bulk_{ticker}",
                target_date=fromdate,
                status='failed',
                record_count=0,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                error_message=error,
                retry_count=1
            )
            session.add(progress)
            session.commit()

        except Exception as e:
            print(f"[Warning] Failed to log error: {e}")
            session.rollback()

        finally:
            session.close()

    def get_ticker_list_from_db(self) -> List[str]:
        """
        DB에서 종목 리스트 조회

        Returns:
            종목 코드 리스트
        """
        session = self.db.get_session()

        try:
            from ..database.models import StockInfo

            stocks = session.query(StockInfo.ticker).filter(
                StockInfo.is_active == True
            ).all()

            return [stock.ticker for stock in stocks]

        except Exception as e:
            print(f"[Warning] Failed to get ticker list from DB: {e}")
            return []

        finally:
            session.close()

    def validate_collection(
        self,
        tickers: List[str],
        fromdate: date,
        todate: date
    ) -> Dict[str, any]:
        """
        수집 완료 후 데이터 검증

        Args:
            tickers: 종목 코드 리스트
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            검증 결과 딕셔너리
        """
        session = self.db.get_session()

        try:
            from ..database.models import StockPrice, InvestorTrading

            results = {
                'total_tickers': len(tickers),
                'missing_tickers': [],
                'incomplete_tickers': [],
                'date_range': (fromdate, todate),
                'expected_days': (todate - fromdate).days + 1
            }

            # 거래일 수 계산 (주말 제외, 대략 70%)
            expected_records = int(results['expected_days'] * 0.7)

            for ticker in tickers:
                # 주가 데이터 확인
                price_count = session.query(StockPrice).filter(
                    StockPrice.ticker == ticker,
                    StockPrice.date >= fromdate,
                    StockPrice.date <= todate
                ).count()

                # 투자자 거래 데이터 확인
                investor_count = session.query(InvestorTrading).filter(
                    InvestorTrading.ticker == ticker,
                    InvestorTrading.date >= fromdate,
                    InvestorTrading.date <= todate
                ).count()

                if price_count == 0 and investor_count == 0:
                    results['missing_tickers'].append(ticker)
                elif price_count < expected_records * 0.5 or investor_count < expected_records * 0.5:
                    results['incomplete_tickers'].append(ticker)

            return results

        finally:
            session.close()
