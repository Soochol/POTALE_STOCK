"""
Block4 Detection Entity - 블록4 탐지 결과 엔티티
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Block4Detection:
    """블록4 탐지 결과"""

    # 기본 정보 (필수 필드)
    ticker: str
    condition_name: str  # 조건 프리셋 이름 (예: "아난티_2015-2025")
    started_at: date

    # 기본 정보 (기본값 있는 필드)
    block4_id: str = ""  # 블록4 고유 ID (UUID, __post_init__에서 생성)
    ended_at: Optional[date] = None
    status: str = "active"  # active, completed

    # 진입 정보
    entry_close: float = 0.0  # 진입일 종가
    entry_rate: Optional[float] = None  # 진입일 등락률

    # 직전 블록3 정보
    prev_block3_id: Optional[int] = None  # 참조한 블록3의 ID
    prev_block3_peak_price: Optional[float] = None  # 블록3 최고가
    prev_block3_peak_volume: Optional[int] = None  # 블록3 최고 거래량

    # 블록4 최고가 추적
    peak_price: Optional[float] = None  # 블록4 기간 중 최고가
    peak_date: Optional[date] = None  # 최고가 달성일
    peak_gain_ratio: Optional[float] = None  # 최고가 상승률 (%)
    peak_volume: Optional[int] = None  # 블록4 기간 중 최고 거래량

    # 종료 정보
    duration_days: Optional[int] = None  # 지속 기간
    exit_reason: Optional[str] = None  # 종료 사유 (ma_break, three_line_reversal, body_middle)

    # 메타데이터
    id: Optional[int] = None  # DB ID

    def __post_init__(self):
        """유효성 검사 및 UUID 생성"""
        import uuid

        # UUID 생성
        if not self.block4_id:
            self.block4_id = str(uuid.uuid4())

        if self.status not in ["active", "completed"]:
            raise ValueError("status는 'active' 또는 'completed'여야 합니다")

        if self.entry_close <= 0:
            raise ValueError("진입 종가는 0보다 커야 합니다")

    def update_peak(self, price: float, current_date: date, volume: int):
        """최고가 갱신"""
        if self.peak_price is None or price > self.peak_price:
            self.peak_price = price
            self.peak_date = current_date
            self.peak_gain_ratio = ((price - self.entry_close) / self.entry_close) * 100

        if self.peak_volume is None or volume > self.peak_volume:
            self.peak_volume = volume

    def complete(self, end_date: date, exit_reason: str):
        """블록4 종료"""
        self.ended_at = end_date
        self.status = "completed"
        self.exit_reason = exit_reason
        self.duration_days = (end_date - self.started_at).days + 1

    def __repr__(self):
        return (
            f"<Block4Detection("
            f"ticker={self.ticker}, "
            f"started={self.started_at}, "
            f"status={self.status}, "
            f"peak_gain={self.peak_gain_ratio:.2f}% if self.peak_gain_ratio else 'N/A'"
            f")>"
        )
