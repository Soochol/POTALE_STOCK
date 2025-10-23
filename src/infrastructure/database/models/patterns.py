"""
Block Pattern Models
블록 패턴 재탐지 시스템 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class BlockPattern(Base):
    """블록 패턴 (재탐지 시스템)"""
    __tablename__ = 'block_pattern'

    pattern_id = Column(Integer, primary_key=True, autoincrement=True, comment='패턴 고유 ID')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # Seed 참조
    seed_block1_id = Column(String(50), ForeignKey('block1_detection.block1_id'), nullable=False, comment='Block1 Seed ID')
    seed_block2_id = Column(String(50), ForeignKey('block2_detection.block2_id'), nullable=False, comment='Block2 Seed ID')
    seed_block3_id = Column(String(50), ForeignKey('block3_detection.block3_id'), nullable=False, comment='Block3 Seed ID')

    # 재탐지 기간
    redetection_start = Column(Date, nullable=False, comment='재탐지 시작일 (Block1 Seed 시작일)')
    redetection_end = Column(Date, nullable=False, comment='재탐지 종료일 (시작일 + 5년)')

    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, comment='패턴 생성일시')

    # 관계 설정
    stock_info = relationship("StockInfo")
    seed_block1 = relationship("Block1Detection", foreign_keys=[seed_block1_id])
    seed_block2 = relationship("Block2Detection", foreign_keys=[seed_block2_id])
    seed_block3 = relationship("Block3Detection", foreign_keys=[seed_block3_id])

    block1_detections = relationship("Block1Detection", back_populates="pattern", foreign_keys="Block1Detection.pattern_id")
    block2_detections = relationship("Block2Detection", back_populates="pattern", foreign_keys="Block2Detection.pattern_id")
    block3_detections = relationship("Block3Detection", back_populates="pattern", foreign_keys="Block3Detection.pattern_id")
    block4_detections = relationship("Block4Detection", back_populates="pattern", foreign_keys="Block4Detection.pattern_id")
    block5_detections = relationship("Block5Detection", back_populates="pattern", foreign_keys="Block5Detection.pattern_id")
    block6_detections = relationship("Block6Detection", back_populates="pattern", foreign_keys="Block6Detection.pattern_id")

    # 인덱스
    __table_args__ = (
        Index('ix_block_pattern_ticker', 'ticker'),
        Index('ix_block_pattern_created', 'created_at'),
        Index('ix_block_pattern_redetection_period', 'redetection_start', 'redetection_end'),
    )

    def __repr__(self):
        return f"<BlockPattern(pattern_id={self.pattern_id}, ticker={self.ticker}, start={self.redetection_start})>"
