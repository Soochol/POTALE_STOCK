"""
Block Detection Models
블록1/2/3/4 탐지 결과 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Float, String, Date, DateTime, Index, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Block1Detection(Base):
    """블록1 탐지 결과 테이블"""
    __tablename__ = 'block1_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block1_id = Column(String(50), unique=True, nullable=False, comment='블록1 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록1 시작일')
    ended_at = Column(Date, comment='블록1 종료일')

    # 진입 시점 OHLC 가격
    entry_open = Column(Float, nullable=False, comment='시작일 시가')
    entry_high = Column(Float, nullable=False, comment='시작일 고가')
    entry_low = Column(Float, nullable=False, comment='시작일 저가')
    entry_close = Column(Float, nullable=False, comment='시작일 종가')

    # 진입 시점 거래 정보
    entry_volume = Column(BigInteger, nullable=False, comment='시작일 거래량')
    entry_trading_value = Column(Float, comment='시작일 거래대금 (억)')

    # 진입 시점 기술적 지표
    entry_ma_value = Column(Float, comment='시작일 이동평균선 값')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')
    entry_deviation = Column(Float, comment='시작일 이격도 (%)')

    # 블록1 기간 중 최고가 추적
    peak_price = Column(Float, comment='블록1 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')
    peak_volume = Column(BigInteger, comment='블록1 기간 중 최고 거래량')

    # 종료 정보
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle)')
    exit_price = Column(Float, comment='종료일 종가')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    pattern = relationship("BlockPattern", back_populates="block1_detections", foreign_keys=[pattern_id])

    # 인덱스 및 제약조건
    __table_args__ = (
        # 인덱스
        Index('ix_block1_ticker_started', 'ticker', 'started_at'),
        Index('ix_block1_status', 'status'),
        Index('ix_block1_started', 'started_at'),
        Index('ix_block1_id', 'block1_id', unique=True),
        Index('ix_block1_pattern', 'pattern_id'),
        Index('ix_block1_detection_type', 'detection_type'),
        Index('ix_block1_pattern_condition', 'pattern_id', 'condition_name'),
        Index('ix_block1_status_started', 'status', 'started_at'),
        # 제약조건
        CheckConstraint('entry_high >= entry_low', name='ck_block1_high_low'),
        CheckConstraint('entry_high >= entry_close', name='ck_block1_high_close'),
        CheckConstraint('entry_close >= entry_low', name='ck_block1_close_low'),
        CheckConstraint('entry_open > 0', name='ck_block1_open_positive'),
        CheckConstraint('entry_high > 0', name='ck_block1_high_positive'),
        CheckConstraint('entry_low > 0', name='ck_block1_low_positive'),
        CheckConstraint('entry_close > 0', name='ck_block1_close_positive'),
        CheckConstraint('entry_volume >= 0', name='ck_block1_volume_nonnegative'),
        CheckConstraint("ended_at IS NULL OR started_at <= ended_at", name='ck_block1_dates_valid'),
    )

    def __repr__(self):
        return f"<Block1Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"


class Block2Detection(Base):
    """블록2 탐지 결과 테이블"""
    __tablename__ = 'block2_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block2_id = Column(String(50), unique=True, nullable=False, comment='블록2 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록2 시작일')
    ended_at = Column(Date, comment='블록2 종료일')

    # 진입 정보
    entry_close = Column(Float, nullable=False, comment='시작일 종가')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')

    # 직전 블록1 정보
    prev_block1_id = Column(Integer, ForeignKey('block1_detection.id'), comment='참조한 블록1 ID')
    prev_block1_peak_price = Column(Float, comment='블록1 최고가')
    prev_block1_peak_volume = Column(BigInteger, comment='블록1 최고 거래량')

    # 블록2 기간 중 최고가/거래량 추적
    peak_price = Column(Float, comment='블록2 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')
    peak_gain_ratio = Column(Float, comment='최고가 상승률 (%)')
    peak_volume = Column(BigInteger, comment='블록2 기간 중 최고 거래량')

    # 종료 정보
    duration_days = Column(Integer, comment='지속 기간 (일)')
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle, block3_started)')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    prev_block1 = relationship("Block1Detection", foreign_keys=[prev_block1_id])
    pattern = relationship("BlockPattern", back_populates="block2_detections", foreign_keys=[pattern_id])

    # 인덱스 및 제약조건
    __table_args__ = (
        # 인덱스
        Index('ix_block2_ticker_started', 'ticker', 'started_at'),
        Index('ix_block2_status', 'status'),
        Index('ix_block2_started', 'started_at'),
        Index('ix_block2_id', 'block2_id', unique=True),
        Index('ix_block2_prev_block1', 'prev_block1_id'),
        Index('ix_block2_pattern', 'pattern_id'),
        Index('ix_block2_detection_type', 'detection_type'),
        Index('ix_block2_pattern_condition', 'pattern_id', 'condition_name'),
        Index('ix_block2_status_started', 'status', 'started_at'),
        # 제약조건
        CheckConstraint('entry_close > 0', name='ck_block2_close_positive'),
        CheckConstraint("ended_at IS NULL OR started_at <= ended_at", name='ck_block2_dates_valid'),
        CheckConstraint('peak_price IS NULL OR peak_price >= entry_close', name='ck_block2_peak_valid'),
    )

    def __repr__(self):
        return f"<Block2Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"


class Block3Detection(Base):
    """블록3 탐지 결과 테이블"""
    __tablename__ = 'block3_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block3_id = Column(String(50), unique=True, nullable=False, comment='블록3 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록3 시작일')
    ended_at = Column(Date, comment='블록3 종료일')

    # 진입 정보
    entry_close = Column(Float, nullable=False, comment='시작일 종가')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')

    # 직전 블록2 정보
    prev_block2_id = Column(Integer, ForeignKey('block2_detection.id'), comment='참조한 블록2 ID')
    prev_block2_peak_price = Column(Float, comment='블록2 최고가')
    prev_block2_peak_volume = Column(BigInteger, comment='블록2 최고 거래량')

    # 블록3 기간 중 최고가/거래량 추적
    peak_price = Column(Float, comment='블록3 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')
    peak_gain_ratio = Column(Float, comment='최고가 상승률 (%)')
    peak_volume = Column(BigInteger, comment='블록3 기간 중 최고 거래량')

    # 종료 정보
    duration_days = Column(Integer, comment='지속 기간 (일)')
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle)')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    prev_block2 = relationship("Block2Detection", foreign_keys=[prev_block2_id])
    pattern = relationship("BlockPattern", back_populates="block3_detections", foreign_keys=[pattern_id])

    # 인덱스 및 제약조건
    __table_args__ = (
        # 인덱스
        Index('ix_block3_ticker_started', 'ticker', 'started_at'),
        Index('ix_block3_status', 'status'),
        Index('ix_block3_started', 'started_at'),
        Index('ix_block3_id', 'block3_id', unique=True),
        Index('ix_block3_prev_block2', 'prev_block2_id'),
        Index('ix_block3_pattern', 'pattern_id'),
        Index('ix_block3_detection_type', 'detection_type'),
        Index('ix_block3_pattern_condition', 'pattern_id', 'condition_name'),
        Index('ix_block3_status_started', 'status', 'started_at'),
        # 제약조건
        CheckConstraint('entry_close > 0', name='ck_block3_close_positive'),
        CheckConstraint("ended_at IS NULL OR started_at <= ended_at", name='ck_block3_dates_valid'),
        CheckConstraint('peak_price IS NULL OR peak_price >= entry_close', name='ck_block3_peak_valid'),
    )

    def __repr__(self):
        return f"<Block3Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"


class Block4Detection(Base):
    """블록4 탐지 결과 테이블"""
    __tablename__ = 'block4_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block4_id = Column(String(50), unique=True, nullable=False, comment='블록4 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록4 시작일')
    ended_at = Column(Date, comment='블록4 종료일')

    # 진입 정보
    entry_close = Column(Float, nullable=False, comment='시작일 종가')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')

    # 직전 블록3 정보
    prev_block3_id = Column(Integer, ForeignKey('block3_detection.id'), comment='참조한 블록3 ID')
    prev_block3_peak_price = Column(Float, comment='블록3 최고가')
    prev_block3_peak_volume = Column(BigInteger, comment='블록3 최고 거래량')

    # 블록4 기간 중 최고가/거래량 추적
    peak_price = Column(Float, comment='블록4 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')
    peak_gain_ratio = Column(Float, comment='최고가 상승률 (%)')
    peak_volume = Column(BigInteger, comment='블록4 기간 중 최고 거래량')

    # 종료 정보
    duration_days = Column(Integer, comment='지속 기간 (일)')
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle)')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    prev_block3 = relationship("Block3Detection", foreign_keys=[prev_block3_id])
    pattern = relationship("BlockPattern", back_populates="block4_detections", foreign_keys=[pattern_id])

    # 인덱스 및 제약조건
    __table_args__ = (
        # 인덱스
        Index('ix_block4_ticker_started', 'ticker', 'started_at'),
        Index('ix_block4_status', 'status'),
        Index('ix_block4_started', 'started_at'),
        Index('ix_block4_id', 'block4_id', unique=True),
        Index('ix_block4_prev_block3', 'prev_block3_id'),
        Index('ix_block4_pattern', 'pattern_id'),
        Index('ix_block4_detection_type', 'detection_type'),
        Index('ix_block4_pattern_condition', 'pattern_id', 'condition_name'),
        Index('ix_block4_status_started', 'status', 'started_at'),
        # 제약조건
        CheckConstraint('entry_close > 0', name='ck_block4_close_positive'),
        CheckConstraint("ended_at IS NULL OR started_at <= ended_at", name='ck_block4_dates_valid'),
        CheckConstraint('peak_price IS NULL OR peak_price >= entry_close', name='ck_block4_peak_valid'),
    )

    def __repr__(self):
        return f"<Block4Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"
