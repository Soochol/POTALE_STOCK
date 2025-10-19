"""
Async Unified Collector
비동기 통합 데이터 수집기 (가격 + 투자자 데이터)

Architecture:
- 종목별 순차 수집: 가격 → 투자자 (Rate Limiting 회피)
- 종목간 병렬 수집: 10-20개 종목 동시 처리
"""
import asyncio
import aiohttp
from datetime import date, datetime
from typing import List, Dict, Optional

from .async_collectors.price_collector import AsyncPriceCollector
from .async_collectors.investor_collector import AsyncInvestorCollector
from ..common.types import AsyncCollectionResult
from ..common.config import DEFAULT_CONFIG
from ...database.models import StockPrice, InvestorTrading
from sqlalchemy.dialects.sqlite import insert


class AsyncUnifiedCollector:
    """
    비동기 통합 데이터 수집기

    주요 특징:
    - 종목별 순차 수집 (price → investor) - Rate Limiting 회피
    - 종목간 병렬 수집 - 성능 최적화
    - asyncio + aiohttp로 비동기 HTTP 요청
    - Semaphore로 동시 요청 수 제어
    - 큐 기반 비동기 DB 저장
    """

    def __init__(
        self,
        db_connection=None,
        delay: float = DEFAULT_CONFIG.default_delay,
        concurrency: int = DEFAULT_CONFIG.default_concurrency,
        max_retries: int = DEFAULT_CONFIG.retry.max_retries,
        timeout: int = DEFAULT_CONFIG.http.total_timeout
    ):
        """
        Args:
            db_connection: DatabaseConnection 인스턴스
            delay: 요청 간 최소 대기 시간 (초)
            concurrency: 동시 요청 수 제한
            max_retries: 최대 재시도 횟수
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.db_connection = db_connection
        self.delay = delay
        self.concurrency = concurrency
        self.max_retries = max_retries
        self.timeout = timeout

        # 개별 수집기 초기화
        self.price_collector = AsyncPriceCollector(delay=delay)
        self.investor_collector = AsyncInvestorCollector(delay=delay)

        # 동시성 제어
        self.semaphore = asyncio.Semaphore(concurrency)

        # DB 저장 큐
        self.write_queue = None  # asyncio.Queue (runtime에 생성)
        self.writer_task = None

    async def collect_batch(
        self,
        tickers: List[str],
        fromdate: date,
        todate: date,
        collect_investor: bool = False,
        progress_callback=None
    ) -> List[AsyncCollectionResult]:
        """
        여러 종목을 비동기로 배치 수집

        Args:
            tickers: 종목 코드 리스트
            fromdate: 시작 날짜
            todate: 종료 날짜
            collect_investor: 투자자 데이터 수집 여부
            progress_callback: 진행 상황 콜백 함수 (optional)

        Returns:
            AsyncCollectionResult 리스트
        """
        if not tickers:
            return []

        # DB 저장 큐 및 writer 시작
        self.write_queue = asyncio.Queue()
        self.writer_task = asyncio.create_task(self._db_writer())

        # HTTP 세션 생성 (config 사용)
        http_config = DEFAULT_CONFIG.http
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(
            limit=http_config.total_limit,
            limit_per_host=http_config.per_host_limit,
            ttl_dns_cache=http_config.dns_ttl,
            enable_cleanup_closed=http_config.enable_cleanup,
            force_close=http_config.force_close
        )

        async with aiohttp.ClientSession(
            timeout=timeout_config,
            connector=connector
        ) as session:
            # 각 종목별 수집 태스크 생성
            tasks = [
                self._collect_one_ticker(
                    session, ticker, fromdate, todate,
                    collect_investor, progress_callback
                )
                for ticker in tickers
            ]

            # 모든 태스크 실행 (예외 발생 시에도 계속 진행)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 예외를 AsyncCollectionResult로 변환
            final_results = []
            for ticker, result in zip(tickers, results):
                if isinstance(result, Exception):
                    final_results.append(AsyncCollectionResult(
                        ticker=ticker,
                        success=False,
                        price_record_count=0,
                        investor_record_count=0,
                        error_message=str(result),
                        started_at=datetime.now(),
                        completed_at=datetime.now()
                    ))
                else:
                    final_results.append(result)

        # DB writer 종료 대기
        await self.write_queue.put(None)  # 종료 신호
        await self.writer_task

        return final_results

    async def _collect_one_ticker(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        fromdate: date,
        todate: date,
        collect_investor: bool,
        progress_callback=None
    ) -> AsyncCollectionResult:
        """
        단일 종목 수집 (재시도 포함)

        순차 수집:
        1. 가격 데이터 (price)
        2. 투자자 데이터 (investor) - collect_investor=True인 경우

        Args:
            session: aiohttp 세션
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜
            collect_investor: 투자자 데이터 수집 여부
            progress_callback: 진행 콜백

        Returns:
            AsyncCollectionResult
        """
        for attempt in range(self.max_retries):
            try:
                # Semaphore로 동시 요청 수 제어
                async with self.semaphore:
                    result = await self._collect_ticker_impl(
                        session, ticker, fromdate, todate, collect_investor
                    )
                    result.retry_count = attempt

                    if progress_callback:
                        await progress_callback(ticker, result)

                    return result

            except Exception as e:
                if attempt < self.max_retries - 1:
                    # 지수 백오프 (1초, 2초, 4초...)
                    wait_time = (2 ** attempt) * 1.0
                    await asyncio.sleep(wait_time)
                    print(f"  [Retry {attempt + 1}/{self.max_retries}] {ticker}: {str(e)}")
                else:
                    # 최종 실패
                    return AsyncCollectionResult(
                        ticker=ticker,
                        success=False,
                        price_record_count=0,
                        investor_record_count=0,
                        error_message=f"Failed after {self.max_retries} retries: {str(e)}",
                        started_at=datetime.now(),
                        completed_at=datetime.now(),
                        retry_count=attempt + 1
                    )

    async def _collect_ticker_impl(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        fromdate: date,
        todate: date,
        collect_investor: bool
    ) -> AsyncCollectionResult:
        """
        단일 종목 수집 실제 구현 (순차: 가격 → 투자자)

        Args:
            session: aiohttp 세션
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜
            collect_investor: 투자자 데이터 수집 여부

        Returns:
            AsyncCollectionResult
        """
        started_at = datetime.now()
        price_count = 0
        investor_count = 0
        error_messages = []

        # 1. 가격 데이터 수집
        price_result = await self.price_collector.collect(
            session, ticker, fromdate, todate
        )

        if price_result['success'] and price_result['records']:
            price_count = len(price_result['records'])
            await self.write_queue.put(('price', price_result['records']))
        elif price_result['error']:
            error_messages.append(f"Price: {price_result['error']}")

        # 2. 투자자 데이터 수집 (순차, collect_investor=True인 경우만)
        if collect_investor:
            investor_result = await self.investor_collector.collect(
                session, ticker, fromdate, todate
            )

            if investor_result['success'] and investor_result['records']:
                investor_count = len(investor_result['records'])
                await self.write_queue.put(('investor', investor_result['records']))
            elif investor_result['error']:
                error_messages.append(f"Investor: {investor_result['error']}")

        completed_at = datetime.now()

        return AsyncCollectionResult(
            ticker=ticker,
            success=True if (price_count > 0 or investor_count > 0) else False,
            price_record_count=price_count,
            investor_record_count=investor_count,
            error_message='; '.join(error_messages) if error_messages else None,
            started_at=started_at,
            completed_at=completed_at
        )

    async def _db_writer(self):
        """
        DB 저장 worker (큐 기반 배치 저장)
        """
        if not self.db_connection:
            # DB 연결이 없으면 skip
            while True:
                item = await self.write_queue.get()
                if item is None:
                    break
            return

        session = self.db_connection.get_session()

        try:
            while True:
                # 큐에서 레코드 배치 수집
                batch = []
                timeout_seconds = DEFAULT_CONFIG.db_flush_timeout

                # 최대 db_batch_size개 또는 timeout 대기
                for _ in range(DEFAULT_CONFIG.db_batch_size):
                    try:
                        item = await asyncio.wait_for(
                            self.write_queue.get(),
                            timeout=timeout_seconds
                        )

                        if item is None:  # 종료 신호
                            if batch:
                                self._flush_batch(session, batch)
                            return

                        batch.append(item)

                    except asyncio.TimeoutError:
                        break

                # 배치 저장
                if batch:
                    self._flush_batch(session, batch)

        except Exception as e:
            print(f"[Error] DB writer error: {e}")
            session.rollback()

        finally:
            session.close()

    def _flush_batch(self, session, batch: List[tuple]):
        """
        배치를 DB에 저장

        Args:
            session: DB 세션
            batch: (table_type, records) 튜플 리스트
        """
        # 타입별로 그룹핑
        price_records = []
        investor_records = []

        for table_type, records in batch:
            if table_type == 'price':
                price_records.extend(records)
            elif table_type == 'investor':
                investor_records.extend(records)

        # Price 데이터 저장
        if price_records:
            self._bulk_upsert_price(session, price_records)

        # Investor 데이터 저장
        if investor_records:
            self._bulk_upsert_investor(session, investor_records)

    def _bulk_upsert_price(self, session, records: List[Dict]):
        """
        StockPrice 대량 upsert (INSERT OR REPLACE)

        Args:
            session: DB 세션
            records: 레코드 리스트
        """
        if not records:
            return

        try:
            stmt = insert(StockPrice).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'date'],
                set_={
                    'open': stmt.excluded.open,
                    'high': stmt.excluded.high,
                    'low': stmt.excluded.low,
                    'close': stmt.excluded.close,
                    'volume': stmt.excluded.volume,
                    'trading_value': stmt.excluded.trading_value,
                    'adjustment_ratio': stmt.excluded.adjustment_ratio,
                    'raw_close': stmt.excluded.raw_close,
                    'raw_volume': stmt.excluded.raw_volume,
                    'created_at': stmt.excluded.created_at
                }
            )

            session.execute(stmt)
            session.commit()

        except Exception as e:
            session.rollback()
            print(f"[Error] Bulk upsert price failed: {e}")
            raise

    def _bulk_upsert_investor(self, session, records: List[Dict]):
        """
        InvestorTrading 대량 upsert (INSERT OR REPLACE)

        Args:
            session: DB 세션
            records: 레코드 리스트
        """
        if not records:
            return

        try:
            stmt = insert(InvestorTrading).values(records)
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

        except Exception as e:
            session.rollback()
            print(f"[Error] Bulk upsert investor failed: {e}")
            raise
