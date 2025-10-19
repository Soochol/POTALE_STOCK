"""
Batch Processor
배치 처리 및 재시도 로직
"""
import asyncio
import gc
from typing import List, Callable, TypeVar, Awaitable
from .types import CollectionPlan, AsyncCollectionResult
from .config import DEFAULT_CONFIG


T = TypeVar('T')


class BatchProcessor:
    """배치 처리 관리자"""

    def __init__(self, batch_size: int = DEFAULT_CONFIG.default_batch_size):
        """
        Args:
            batch_size: 배치 크기
        """
        self.batch_size = batch_size

    async def process_in_batches(
        self,
        items: List[T],
        processor: Callable[[List[T]], Awaitable[List[AsyncCollectionResult]]],
        on_batch_complete: Callable[[int, List[AsyncCollectionResult]], Awaitable[None]] = None
    ) -> List[AsyncCollectionResult]:
        """
        아이템들을 배치로 처리

        Args:
            items: 처리할 아이템 리스트
            processor: 배치 처리 함수 (async)
            on_batch_complete: 배치 완료 시 콜백 (optional)

        Returns:
            모든 결과 리스트
        """
        all_results = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(0, len(items), self.batch_size):
            batch = items[batch_idx:batch_idx + self.batch_size]
            batch_num = (batch_idx // self.batch_size) + 1

            # 배치 처리
            results = await processor(batch)
            all_results.extend(results)

            # 콜백 실행
            if on_batch_complete:
                await on_batch_complete(batch_num, results)

            # 메모리 정리
            gc.collect()

        return all_results


class RetryHandler:
    """재시도 처리 관리자"""

    def __init__(
        self,
        max_retries: int = DEFAULT_CONFIG.retry.max_retries,
        base_delay: float = DEFAULT_CONFIG.retry.base_delay,
        exponential_base: int = DEFAULT_CONFIG.retry.exponential_base
    ):
        """
        Args:
            max_retries: 최대 재시도 횟수
            base_delay: 기본 대기 시간 (초)
            exponential_base: 지수 백오프 베이스
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_base = exponential_base

    def calculate_delay(self, attempt: int) -> float:
        """
        지수 백오프 지연 시간 계산

        Args:
            attempt: 현재 시도 횟수 (0부터 시작)

        Returns:
            대기 시간 (초)
        """
        return (self.exponential_base ** attempt) * self.base_delay

    async def retry_with_backoff(
        self,
        func: Callable[[], Awaitable[T]],
        on_retry: Callable[[int, Exception], None] = None
    ) -> T:
        """
        지수 백오프로 재시도

        Args:
            func: 실행할 async 함수
            on_retry: 재시도 시 콜백 (attempt, exception)

        Returns:
            함수 실행 결과

        Raises:
            마지막 예외 (재시도 모두 실패 시)
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    wait_time = self.calculate_delay(attempt)
                    await asyncio.sleep(wait_time)

                    if on_retry:
                        on_retry(attempt + 1, e)

        # 모든 재시도 실패
        raise last_exception
