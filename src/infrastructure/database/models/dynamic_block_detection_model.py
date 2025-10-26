"""
DynamicBlockDetection ORM Model
"""

from sqlalchemy import Column, Integer, String, Date, Float, JSON
from .base import Base


class DynamicBlockDetectionModel(Base):
    """
    동적 블록 감지 ORM 모델

    Table: dynamic_block_detection
    """

    __tablename__ = 'dynamic_block_detection'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 블록 정의
    block_id = Column(String(50), nullable=False, index=True)
    block_type = Column(Integer, nullable=False, index=True)

    # 종목 정보
    ticker = Column(String(20), nullable=False, index=True)

    # 패턴 연결
    pattern_id = Column(Integer, nullable=True, index=True)

    # 조건 정보
    condition_name = Column(String(50), nullable=False, index=True)

    # 시간 정보
    started_at = Column(Date, nullable=True, index=True)
    ended_at = Column(Date, nullable=True, index=True)

    # 상태
    status = Column(String(20), nullable=False, index=True)

    # 가격/거래량 정보
    peak_price = Column(Float, nullable=True)
    peak_volume = Column(Integer, nullable=True)
    peak_date = Column(Date, nullable=True)
    prev_close = Column(Float, nullable=True)  # 블록 시작 전일 종가

    # 관계 정보 (JSON)
    parent_blocks = Column(JSON, nullable=False, default=list)

    # Virtual Block System (NEW - 2025-10-26)
    yaml_type = Column(Integer, nullable=False, default=0, index=True)  # YAML 정의 block_type (불변)
    logical_level = Column(Integer, nullable=False, default=0, index=True)  # 실제 급등 순서 (1, 2, 3, ...)
    pattern_sequence = Column(Integer, nullable=False, default=0)  # 패턴 내 생성 순서
    is_virtual = Column(Integer, nullable=False, default=0, index=True)  # 0/1 (Spot으로 스킵된 가상 블록 여부)

    # 메타데이터 (JSON) - 'metadata'는 SQLAlchemy 예약어이므로 'custom_metadata' 사용
    custom_metadata = Column(JSON, nullable=False, default=dict)

    def __repr__(self):
        return (
            f"<DynamicBlockDetectionModel(id={self.id}, block_id='{self.block_id}', "
            f"ticker='{self.ticker}', status='{self.status}')>"
        )
