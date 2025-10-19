"""
Collection Data Types
수집 관련 데이터 타입 정의
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict


@dataclass
class CollectionResult:
    """기본 수집 결과"""
    success: bool
    record_count: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """소요 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class AsyncCollectionResult:
    """비동기 수집 결과 (가격 + 투자자 데이터)"""
    ticker: str
    success: bool
    price_record_count: int
    investor_record_count: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """소요 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def total_records(self) -> int:
        """총 레코드 수 (가격 + 투자자)"""
        return self.price_record_count + self.investor_record_count


@dataclass
class CollectionStats:
    """대량 수집 통계"""
    total_tickers: int = 0
    completed_tickers: int = 0
    failed_tickers: int = 0
    skipped_tickers: int = 0
    total_records: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_ticker_list: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """소요 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def records_per_second(self) -> float:
        """초당 레코드 수"""
        if self.duration_seconds > 0:
            return self.total_records / self.duration_seconds
        return 0.0

    def print_summary(self):
        """통계 요약 출력"""
        if not self.started_at:
            return

        elapsed = self.duration_seconds

        print(f"""
{'='*80}
      대량 수집 통계
{'='*80}
 전체 종목:         {self.total_tickers:>10,}개
 성공:              {self.completed_tickers:>10,}개
 실패:              {self.failed_tickers:>10,}개
 건너뛰기:          {self.skipped_tickers:>10,}개 (이미 최신)
 총 레코드:         {self.total_records:>10,}개
 소요 시간:         {elapsed/3600:>10.2f}시간 ({elapsed/60:.1f}분)
 평균 속도:         {self.records_per_second:>10.0f} rec/s
{'='*80}
        """)

        if self.failed_ticker_list:
            print(f"\n실패한 종목 ({len(self.failed_ticker_list)}개):")
            for ticker in self.failed_ticker_list[:10]:
                error_msg = self.errors.get(ticker, "Unknown error")
                print(f"  - {ticker}: {error_msg}")
            if len(self.failed_ticker_list) > 10:
                print(f"  ... 외 {len(self.failed_ticker_list) - 10}개")


@dataclass
class CollectionPlan:
    """종목별 수집 계획"""
    ticker: str
    fromdate: date
    todate: date
    is_full_collection: bool  # True: 전체 수집, False: 증분 수집
    existing_latest_date: Optional[date] = None
    estimated_days: int = 0

    def __post_init__(self):
        """예상 수집 일수 계산"""
        if self.fromdate and self.todate:
            # 실제 날짜 차이 (거래일은 약 70%)
            total_days = (self.todate - self.fromdate).days + 1
            self.estimated_days = int(total_days * 0.7)
