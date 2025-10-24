"""
Seed Pattern ORM Model

SQLAlchemy ORM model for seed_pattern table
"""
from sqlalchemy import Column, Integer, String, Date, Text, JSON, Index
from src.infrastructure.database.models.base import Base


class SeedPatternModel(Base):
    """
    Seed Pattern 테이블

    고품질 seed detection 결과 저장
    """
    __tablename__ = 'seed_pattern'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    pattern_name = Column(String(100), nullable=False, unique=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    yaml_config_path = Column(String(500), nullable=False)
    detection_date = Column(Date, nullable=False, index=True)

    # Block features (JSON)
    block_features = Column(JSON, nullable=False)

    # Pattern shape (JSON)
    price_shape = Column(JSON, nullable=False)
    volume_shape = Column(JSON, nullable=False)

    # 상태
    status = Column(String(20), nullable=False, default='active', index=True)

    # 추가 정보
    description = Column(Text, nullable=True)
    custom_metadata = Column(JSON, nullable=False, default=dict)

    # 복합 인덱스
    __table_args__ = (
        Index('idx_ticker_detection_date', 'ticker', 'detection_date'),
        Index('idx_ticker_status', 'ticker', 'status'),
    )

    def __repr__(self) -> str:
        return (
            f"<SeedPatternModel(id={self.id}, "
            f"name='{self.pattern_name}', "
            f"ticker='{self.ticker}', "
            f"status='{self.status}')>"
        )
