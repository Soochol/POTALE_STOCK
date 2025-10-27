"""
Database model for Highlight-Centric Pattern
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class HighlightCentricPatternModel(Base):
    """
    SQLAlchemy model for highlight-centric patterns.

    Stores patterns discovered via highlight-first detection approach.
    """

    __tablename__ = 'highlight_centric_pattern'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Pattern identity
    pattern_id = Column(String(50), unique=True, nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)

    # Block references (FKs to dynamic_block_detection)
    highlight_block_id = Column(
        Integer,
        ForeignKey('dynamic_block_detection.id'),
        nullable=False
    )
    root_block_id = Column(
        Integer,
        ForeignKey('dynamic_block_detection.id'),
        nullable=False
    )

    # Backward scan metadata
    found_stronger_root = Column(Boolean, default=False, nullable=False)
    backward_lookback_days = Column(Integer, default=30, nullable=False)
    peak_price_ratio = Column(Integer, default=100, nullable=False)  # Stored as int (1.20 → 120)

    # Forward scan metadata
    forward_scan_days = Column(Integer, default=1125, nullable=False)
    forward_block_count = Column(Integer, default=0, nullable=False)

    # Support/resistance analysis (JSON stored as Text)
    sr_analysis = Column(Text, nullable=True)  # JSON string

    # Lifecycle
    status = Column(String(20), default='active', nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    highlight_block = relationship(
        'DynamicBlockDetectionModel',
        foreign_keys=[highlight_block_id],
        backref='highlight_patterns'
    )
    root_block = relationship(
        'DynamicBlockDetectionModel',
        foreign_keys=[root_block_id],
        backref='root_patterns'
    )

    def __repr__(self):
        return (
            f"<HighlightCentricPattern(id={self.id}, "
            f"pattern_id='{self.pattern_id}', "
            f"ticker='{self.ticker}', "
            f"status='{self.status}')>"
        )


# Index definitions for fast queries
from sqlalchemy import Index

# Composite index for ticker + created_at (common query pattern)
Index(
    'idx_hcp_ticker_created',
    HighlightCentricPatternModel.ticker,
    HighlightCentricPatternModel.created_at
)

# Index for status filtering
Index(
    'idx_hcp_status',
    HighlightCentricPatternModel.status
)

# Composite index for ticker + status (common filter combination)
Index(
    'idx_hcp_ticker_status',
    HighlightCentricPatternModel.ticker,
    HighlightCentricPatternModel.status
)
