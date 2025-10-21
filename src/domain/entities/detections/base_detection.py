"""
Base Detection Entity - 블록 탐지 결과 기본 클래스

Block2/3/4의 공통 로직을 추출한 베이스 클래스
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class BaseBlockDetection:
    """
    Block2/3/4 탐지 결과의 공통 베이스 클래스

    Block1은 필드가 다르므로 별도 클래스로 유지
    Block2/3/4는 구조가 동일하므로 이 베이스를 상속
    """

    # 기본 정보 (필수 필드)
    ticker: str
    condition_name: str  # 조건 프리셋 이름
    started_at: date

    # 기본 정보 (기본값 있는 필드)
    block_id: str = ""  # 고유 ID (UUID, 서브클래스에서 설정)
    ended_at: Optional[date] = None
    status: str = "active"  # active, completed

    # 진입 정보
    entry_close: float = 0.0  # 진입일 종가
    entry_rate: Optional[float] = None  # 진입일 등락률

    # 직전 블록 정보 (서브클래스에서 구체화)
    prev_block_id: Optional[int] = None  # 참조한 이전 블록의 ID
    prev_block_peak_price: Optional[float] = None  # 이전 블록 최고가
    prev_block_peak_volume: Optional[int] = None  # 이전 블록 최고 거래량

    # 현재 블록 최고가 추적
    peak_price: Optional[float] = None  # 기간 중 최고가
    peak_date: Optional[date] = None  # 최고가 달성일
    peak_gain_ratio: Optional[float] = None  # 최고가 상승률 (%)
    peak_volume: Optional[int] = None  # 기간 중 최고 거래량

    # 종료 정보
    duration_days: Optional[int] = None  # 지속 기간
    exit_reason: Optional[str] = None  # 종료 사유

    # 메타데이터
    id: Optional[int] = None  # DB ID
    created_at: Optional[datetime] = None  # 레코드 생성일시

    # 패턴 재탐지 시스템
    pattern_id: Optional[int] = None  # 패턴 ID (재탐지 시스템)
    detection_type: Optional[str] = None  # "seed" or "redetection"

    def __post_init__(self):
        """유효성 검사 (서브클래스에서 UUID 생성)"""
        if self.status not in ["active", "completed"]:
            raise ValueError("status는 'active' 또는 'completed'여야 합니다")

        if self.entry_close <= 0:
            raise ValueError("진입 종가는 0보다 커야 합니다")

    def update_peak(self, price: float, current_date: date, volume: int):
        """최고가 및 최고거래량 갱신"""
        if self.peak_price is None or price > self.peak_price:
            self.peak_price = price
            self.peak_date = current_date
            self.peak_gain_ratio = ((price - self.entry_close) / self.entry_close) * 100

        if self.peak_volume is None or volume > self.peak_volume:
            self.peak_volume = volume

    def complete(self, end_date: date, exit_reason: str):
        """블록 종료"""
        self.ended_at = end_date
        self.status = "completed"
        self.exit_reason = exit_reason
        self.duration_days = (end_date - self.started_at).days + 1

    def _get_block_name(self) -> str:
        """블록 이름 반환 (서브클래스에서 override)"""
        return "BaseBlock"

    def __repr__(self):
        peak_str = f"{self.peak_gain_ratio:.2f}%" if self.peak_gain_ratio else "N/A"
        return (
            f"<{self._get_block_name()}Detection("
            f"ticker={self.ticker}, "
            f"started={self.started_at}, "
            f"status={self.status}, "
            f"peak_gain={peak_str}"
            f")>"
        )
