"""
Async Bulk Collector - 비동기 대량 데이터 수집 오케스트레이터

Features:
- 비동기 병렬 수집 (10-20 종목 동시)
- 증분 수집 통합
- 배치 처리 (메모리 관리)
- 실시간 진행률 추적
- 자동 재시도 및 에러 처리
"""
import asyncio
import gc
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict

from .common.types import CollectionStats, CollectionPlan, AsyncCollectionResult
from .common.config import DEFAULT_CONFIG
from .common.logger import get_logger
from .common.batch_processor import BatchProcessor
from .naver.async_unified_collector import AsyncUnifiedCollector
from .incremental_collector import IncrementalCollector
from ..database.connection import DatabaseConnection

# Backward compatibility alias
AsyncBulkCollectionStats = CollectionStats


class AsyncBulkCollector:
    """
    비동기 대량 데이터 수집 오케스트레이터

    Features:
    - 비동기 병렬 수집으로 속도 향상 (4-5배)
    - 증분 수집으로 불필요한 수집 제거
    - 배치 처리로 메모리 관리
    - 실시간 진행률 표시
    """

    def __init__(
        self,
        db_connection: DatabaseConnection,
        concurrency: int = DEFAULT_CONFIG.default_concurrency,
        delay: float = DEFAULT_CONFIG.default_delay,
        batch_size: int = DEFAULT_CONFIG.default_batch_size,
        use_incremental: bool = True
    ):
        """
        Args:
            db_connection: 데이터베이스 연결
            concurrency: 동시 수집 종목 수
            delay: 요청 간 대기 시간 (초)
            batch_size: 배치 크기 (메모리 관리용)
            use_incremental: 증분 수집 사용 여부
        """
        self.db = db_connection
        self.concurrency = concurrency
        self.delay = delay
        self.batch_size = batch_size
        self.use_incremental = use_incremental

        # 증분 수집기
        self.incremental_collector = IncrementalCollector(db_connection)

        # 비동기 수집기
        self.async_collector = AsyncUnifiedCollector(
            db_connection=db_connection,
            delay=delay,
            concurrency=concurrency
        )

        # 통계
        self.stats = CollectionStats()

        # 로거
        self.logger = get_logger()

        # 배치 프로세서
        self.batch_processor = BatchProcessor(batch_size=batch_size)

    async def collect_all_stocks_async(
        self,
        tickers: List[str],
        fromdate: date,
        todate: date,
        collect_investor: bool = False,
        force_full: bool = False,
        save_failed_to_file: bool = True
    ) -> AsyncBulkCollectionStats:
        """
        모든 종목을 비동기로 수집

        Args:
            tickers: 종목 코드 리스트
            fromdate: 시작 날짜
            todate: 종료 날짜
            collect_investor: 투자자 데이터 수집 여부
            force_full: 전체 재수집 강제
            save_failed_to_file: 실패한 종목을 파일로 저장

        Returns:
            AsyncBulkCollectionStats
        """
        self.collect_investor = collect_investor
        self.stats = AsyncBulkCollectionStats(
            total_tickers=len(tickers),
            started_at=datetime.now()
        )

        print(f"\n{'='*80}")
        print(f"비동기 대량 데이터 수집 시작")
        print(f"{'='*80}")
        print(f"종목 수:        {len(tickers):,}개")
        print(f"기간:           {fromdate} ~ {todate}")
        print(f"동시 수집:      {self.concurrency}개 종목")
        print(f"배치 크기:      {self.batch_size}개")
        print(f"증분 수집:      {'활성화' if self.use_incremental and not force_full else '비활성화'}")
        print(f"투자자 데이터:  {'수집함' if collect_investor else '수집 안 함'}")
        print(f"{'='*80}\n")

        # 1. 증분 수집 계획 수립
        if self.use_incremental and not force_full:
            print("[1/3] 증분 수집 계획 수립 중...")
            plans = self.incremental_collector.get_collection_plan(
                tickers, fromdate, todate, force_full=False
            )

            # 계획 요약 출력
            self.incremental_collector.print_collection_summary(plans, len(tickers))

            # 건너뛴 종목 수 계산
            self.stats.skipped_tickers = len(tickers) - len(plans)
        else:
            # 증분 수집 비활성화 → 모든 종목 전체 수집
            plans = [
                CollectionPlan(
                    ticker=ticker,
                    fromdate=fromdate,
                    todate=todate,
                    is_full_collection=True
                )
                for ticker in tickers
            ]

        if not plans:
            print("\n[green]모든 종목이 이미 최신 상태입니다![/green]")
            self.stats.completed_at = datetime.now()
            return self.stats

        # 2. 배치별로 비동기 수집
        self.logger.log_section("[2/3]", f"비동기 수집 시작 ({len(plans)}개 종목, 배치 크기: {self.batch_size})...")

        total_batches = (len(plans) + self.batch_size - 1) // self.batch_size

        # Rich Progress Bar 설정 (logger에서 생성)
        with self.logger.create_progress_bar() as progress:
            task_id = progress.add_task(
                "[cyan]데이터 수집 중",
                total=len(plans),
                records=0
            )

            for batch_idx in range(0, len(plans), self.batch_size):
                batch_plans = plans[batch_idx:batch_idx + self.batch_size]
                batch_num = (batch_idx // self.batch_size) + 1

                # 비동기 수집 실행
                results = await self._collect_batch_async(batch_plans)

                # 통계 업데이트
                self._update_stats(results)

                # Progress Bar 업데이트
                progress.update(
                    task_id,
                    advance=len(batch_plans),
                    records=self.stats.total_records
                )

                # 메모리 정리
                gc.collect()

        # 3. 실패한 종목 재시도
        if self.stats.failed_ticker_list:
            print(f"\n[3/3] 실패한 종목 재시도 ({len(self.stats.failed_ticker_list)}개)...")
            await self._retry_failed_tickers(fromdate, todate)

        # 완료
        self.stats.completed_at = datetime.now()

        print(f"\n{'='*80}")
        print(f"비동기 대량 수집 완료!")
        print(f"{'='*80}")
        self.stats.print_summary()

        # 실패한 종목 파일 저장
        if save_failed_to_file and self.stats.failed_ticker_list:
            self._save_failed_tickers_to_file()

        return self.stats

    async def _collect_batch_async(
        self,
        plans: List[CollectionPlan]
    ) -> List[AsyncCollectionResult]:
        """
        배치 비동기 수집

        Args:
            plans: 수집 계획 리스트

        Returns:
            AsyncCollectionResult 리스트
        """
        # 계획을 ticker, fromdate, todate 리스트로 변환
        tickers = [p.ticker for p in plans]
        fromdate = plans[0].fromdate if plans else date.today()
        todate = plans[0].todate if plans else date.today()

        # 각 플랜별 날짜가 다를 수 있으므로, 개별 수집
        # (증분 수집 시 종목마다 fromdate가 다름)
        async def collect_one_plan(plan: CollectionPlan):
            # 단일 종목을 배치로 수집 (실제로는 1개)
            results = await self.async_collector.collect_batch(
                [plan.ticker],
                plan.fromdate,
                plan.todate,
                collect_investor=self.collect_investor,
                progress_callback=None
            )
            return results[0] if results else None

        # 모든 플랜을 병렬 수집
        tasks = [collect_one_plan(plan) for plan in plans]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외를 AsyncCollectionResult로 변환
        final_results = []
        for plan, result in zip(plans, results):
            if isinstance(result, Exception):
                final_results.append(AsyncCollectionResult(
                    ticker=plan.ticker,
                    success=False,
                    record_count=0,
                    error_message=str(result),
                    started_at=datetime.now(),
                    completed_at=datetime.now()
                ))
            elif result is not None:
                final_results.append(result)

        return final_results

    def _update_stats(self, results: List[AsyncCollectionResult]):
        """
        통계 업데이트

        Args:
            results: 수집 결과 리스트
        """
        for result in results:
            if result.success:
                self.stats.completed_tickers += 1
                # AsyncUnifiedCollector의 결과는 price_record_count + investor_record_count
                self.stats.total_records += result.price_record_count + result.investor_record_count
            else:
                self.stats.failed_tickers += 1
                self.stats.failed_ticker_list.append(result.ticker)
                self.stats.errors[result.ticker] = result.error_message or "Unknown error"

    def _print_progress(self):
        """진행률 출력"""
        total_processed = self.stats.completed_tickers + self.stats.failed_tickers
        total_target = self.stats.total_tickers - self.stats.skipped_tickers

        if total_target == 0:
            progress_pct = 100.0
        else:
            progress_pct = (total_processed / total_target) * 100

        elapsed = (datetime.now() - self.stats.started_at).total_seconds()
        if total_processed > 0:
            eta_seconds = (elapsed / total_processed) * (total_target - total_processed)
            eta_minutes = eta_seconds / 60
        else:
            eta_minutes = 0

        print(f"    진행: {progress_pct:>5.1f}% | "
              f"완료: {self.stats.completed_tickers:>5}/{total_target} | "
              f"레코드: {self.stats.total_records:>8,}개 | "
              f"ETA: {eta_minutes:>5.1f}분")

    async def _retry_failed_tickers(self, fromdate: date, todate: date):
        """
        실패한 종목 재시도

        Args:
            fromdate: 시작 날짜
            todate: 종료 날짜
        """
        if not self.stats.failed_ticker_list:
            return

        retry_plans = [
            CollectionPlan(
                ticker=ticker,
                fromdate=fromdate,
                todate=todate,
                is_full_collection=True
            )
            for ticker in self.stats.failed_ticker_list
        ]

        # 통계 초기화 (재시도용)
        original_failed = self.stats.failed_ticker_list.copy()
        self.stats.failed_ticker_list = []
        self.stats.failed_tickers = 0

        # 재시도
        results = await self._collect_batch_async(retry_plans)

        # 여전히 실패한 종목만 다시 추가
        for result in results:
            if not result.success:
                self.stats.failed_ticker_list.append(result.ticker)
                self.stats.failed_tickers += 1

        # 재시도 성공한 종목 수
        retry_success = len(original_failed) - len(self.stats.failed_ticker_list)
        if retry_success > 0:
            print(f"  재시도 성공: {retry_success}개")

    def _save_failed_tickers_to_file(self):
        """실패한 종목을 파일로 저장"""
        if not self.stats.failed_ticker_list:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"failed_tickers_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 실패한 종목 리스트 ({len(self.stats.failed_ticker_list)}개)\n")
                f.write(f"# 생성 시간: {datetime.now()}\n\n")

                for ticker in self.stats.failed_ticker_list:
                    error_msg = self.stats.errors.get(ticker, "Unknown error")
                    f.write(f"{ticker}\t{error_msg}\n")

            print(f"\n[yellow]실패한 종목 리스트 저장됨: {filename}[/yellow]")

        except Exception as e:
            print(f"[red]실패한 종목 파일 저장 실패: {e}[/red]")

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
            검증 결과
        """
        return self.incremental_collector.validate_collection(tickers, fromdate, todate)


# 헬퍼 함수: 동기 함수에서 비동기 수집 실행
def run_async_collection(
    db_connection: DatabaseConnection,
    tickers: List[str],
    fromdate: date,
    todate: date,
    concurrency: int = 10,
    collect_investor: bool = False,
    use_incremental: bool = True,
    force_full: bool = False
) -> AsyncBulkCollectionStats:
    """
    동기 함수에서 비동기 수집 실행 (asyncio.run 래퍼)

    Args:
        db_connection: 데이터베이스 연결
        tickers: 종목 코드 리스트
        fromdate: 시작 날짜
        todate: 종료 날짜
        concurrency: 동시 수집 종목 수
        collect_investor: 투자자 데이터 수집 여부
        use_incremental: 증분 수집 사용
        force_full: 전체 재수집 강제

    Returns:
        AsyncBulkCollectionStats
    """
    collector = AsyncBulkCollector(
        db_connection=db_connection,
        concurrency=concurrency,
        use_incremental=use_incremental
    )

    # asyncio.run()으로 비동기 함수 실행
    stats = asyncio.run(
        collector.collect_all_stocks_async(
            tickers=tickers,
            fromdate=fromdate,
            todate=todate,
            collect_investor=collect_investor,
            force_full=force_full
        )
    )

    return stats
