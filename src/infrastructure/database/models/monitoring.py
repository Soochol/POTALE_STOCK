"""
Data Collection Monitoring Models
데이터 수집 로그 및 품질 관리 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Index

from .base import Base


class DataCollectionLog(Base):
    """데이터 수집 로그 테이블"""
    __tablename__ = 'data_collection_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_type = Column(String(50), nullable=False, comment='수집 타입 (price, market_data, etc)')
    ticker = Column(String(10), comment='종목코드 (전체 수집시 NULL)')
    start_date = Column(Date, comment='수집 시작일')
    end_date = Column(Date, comment='수집 종료일')

    status = Column(String(20), nullable=False, comment='상태 (success, failed, partial)')
    record_count = Column(Integer, default=0, comment='수집된 레코드 수')
    error_message = Column(String(500), comment='에러 메시지')

    started_at = Column(DateTime, nullable=False, comment='수집 시작 시각')
    completed_at = Column(DateTime, comment='수집 완료 시각')
    duration_seconds = Column(Float, comment='소요 시간(초)')

    # 인덱스
    __table_args__ = (
        Index('ix_collection_log_date', 'started_at'),
        Index('ix_collection_log_ticker', 'ticker'),
    )

    def __repr__(self):
        return f"<DataCollectionLog(type={self.collection_type}, ticker={self.ticker}, status={self.status})>"


class CollectionProgress(Base):
    """수집 진행 상황 추적 테이블"""
    __tablename__ = 'collection_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_type = Column(String(50), nullable=False, comment='수집 타입 (price, market_data, investor_trading, etc)')
    target_date = Column(Date, nullable=False, comment='수집 대상 날짜')
    status = Column(String(20), default='pending', comment='상태 (pending, in_progress, completed, failed)')

    ticker = Column(String(10), comment='종목코드 (개별 수집 시)')
    record_count = Column(Integer, default=0, comment='수집된 레코드 수')
    error_message = Column(String(500), comment='에러 메시지')

    started_at = Column(DateTime, comment='수집 시작 시각')
    completed_at = Column(DateTime, comment='수집 완료 시각')
    retry_count = Column(Integer, default=0, comment='재시도 횟수')

    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_collection_progress_type_date', 'collection_type', 'target_date', unique=True),
        Index('ix_collection_progress_status', 'status'),
        Index('ix_collection_progress_date', 'target_date'),
    )

    def __repr__(self):
        return f"<CollectionProgress(type={self.collection_type}, date={self.target_date}, status={self.status})>"


class DataQualityCheck(Base):
    """데이터 품질 체크 테이블"""
    __tablename__ = 'data_quality_check'

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False, comment='테이블명')
    check_date = Column(Date, nullable=False, comment='체크 날짜')
    check_type = Column(String(50), nullable=False, comment='체크 타입 (missing_data, duplicate, outlier, etc)')

    status = Column(String(20), nullable=False, comment='상태 (pass, warning, fail)')
    issue_count = Column(Integer, default=0, comment='발견된 이슈 수')
    details = Column(String(1000), comment='상세 내용 (JSON 형식)')

    checked_at = Column(DateTime, default=datetime.now, comment='체크 시각')

    # 인덱스
    __table_args__ = (
        Index('ix_data_quality_table_date', 'table_name', 'check_date'),
        Index('ix_data_quality_status', 'status'),
    )

    def __repr__(self):
        return f"<DataQualityCheck(table={self.table_name}, date={self.check_date}, status={self.status})>"
