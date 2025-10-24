"""
Block1 Detection Entity - 블록1 탐지 결과 엔티티
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class Block1Detection:
    """
    블록1 탐지 결과 엔티티

    블록1 시작부터 종료까지의 전체 정보를 저장합니다.
    """

    # 필수 필드 (기본값 없음)
    ticker: str  # 종목코드
    started_at: date  # 블록1 시작일
    entry_open: float  # 시작일 시가
    entry_high: float  # 시작일 고가
    entry_low: float  # 시작일 저가
    entry_close: float  # 시작일 종가
    entry_volume: int  # 시작일 거래량
    condition_name: str  # 사용된 조건 이름

    # 기본값 있는 필드
    entry_trading_value: Optional[float] = None  # 시작일 거래대금 (억)
    block1_id: str = ""  # 고유 ID (UUID, __post_init__에서 생성)
    status: str = "active"  # "active" (진행중) or "completed" (종료)
    ended_at: Optional[date] = None  # 블록1 종료일 (진행중이면 None)

    # 진입 시점 기술적 지표
    entry_ma_value: Optional[float] = None  # 시작일 이동평균선 값
    entry_rate: Optional[float] = None  # 시작일 등락률 (%)
    entry_deviation: Optional[float] = None  # 시작일 이격도 (%)

    # 블록1 기간 중 최고가/최고거래량 추적
    peak_price: Optional[float] = None  # 블록1 기간 중 최고가
    peak_date: Optional[date] = None  # 최고가 달성일
    peak_volume: Optional[int] = None  # 블록1 기간 중 최고 거래량

    # 종료 정보
    exit_reason: Optional[str] = None  # 종료 사유 ("ma_break", "three_line_reversal", "body_middle")
    exit_price: Optional[float] = None  # 종료일 종가

    # 메타데이터
    created_at: Optional[datetime] = None  # 레코드 생성일시

    # 패턴 재탐지 시스템 필드
    pattern_id: Optional[int] = None  # 패턴 ID (재탐지 시스템)
    detection_type: Optional[str] = None  # "seed" or "redetection"

    def __post_init__(self):
        """초기화 후 처리"""
        # block1_id가 없으면 UUID 생성
        if not self.block1_id:
            self.block1_id = str(uuid.uuid4())

        # 상태 검증
        if self.status not in ["active", "completed"]:
            raise ValueError(f"Invalid status: {self.status}")

        # 종료된 블록1은 종료일 필수
        if self.status == "completed" and self.ended_at is None:
            raise ValueError("Completed block1 must have ended_at")

    @property
    def duration_days(self) -> Optional[int]:
        """블록1 지속 기간 (일)"""
        if self.ended_at:
            return (self.ended_at - self.started_at).days
        return None

    @property
    def entry_body_middle(self) -> float:
        """시작일 캔들 몸통 중간 가격"""
        return (self.entry_open + self.entry_close) / 2

    def update_peak(self, current_price: float, current_date: date, current_volume: int = None) -> bool:
        """
        최고가 및 최고거래량 갱신

        Args:
            current_price: 현재 가격 (고가)
            current_date: 현재 날짜
            current_volume: 현재 거래량 (선택적)

        Returns:
            갱신 여부 (True: 갱신됨, False: 갱신 안됨)
        """
        updated = False

        # 최고가 갱신
        if self.peak_price is None or current_price > self.peak_price:
            self.peak_price = current_price
            self.peak_date = current_date
            updated = True

        # 최고거래량 갱신
        if current_volume is not None:
            if self.peak_volume is None or current_volume > self.peak_volume:
                self.peak_volume = current_volume
                updated = True

        return updated

    @property
    def peak_gain_ratio(self) -> Optional[float]:
        """진입가 대비 최고가 상승률 (%)"""
        if self.peak_price and self.entry_close > 0:
            return ((self.peak_price - self.entry_close) / self.entry_close) * 100
        return None

    def complete(self, ended_at: date, exit_reason: str, exit_price: float):
        """블록1 종료 처리"""
        self.status = "completed"
        self.ended_at = ended_at
        self.exit_reason = exit_reason
        self.exit_price = exit_price

    def __repr__(self):
        duration = f", {self.duration_days}일" if self.duration_days else ""
        peak_info = f", 최고가: {self.peak_price:,}원" if self.peak_price else ""
        return (f"<Block1Detection(ticker={self.ticker}, "
                f"started={self.started_at}, status={self.status}{duration}{peak_info})>")
