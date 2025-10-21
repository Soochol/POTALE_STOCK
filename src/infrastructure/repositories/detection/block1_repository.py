"""
Block1 Repository - 블록1 탐지 결과 저장/조회 Repository
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import joinedload
from ....domain.entities import Block1Detection as Block1DetectionEntity
from ...database.models import Block1Detection as Block1DetectionModel
from ...database.connection import DatabaseConnection
from ..common import BaseDetectionRepository


class Block1Repository(BaseDetectionRepository[Block1DetectionEntity, Block1DetectionModel]):
    """블록1 탐지 결과 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, Block1DetectionModel)

    def _get_block_id(self, entity: Block1DetectionEntity) -> str:
        """엔티티에서 block1_id 추출"""
        return entity.block1_id

    def _get_model_block_id_field(self):
        """모델의 block1_id 필드 반환"""
        return Block1DetectionModel.block1_id

    def _entity_to_model(self, entity: Block1DetectionEntity) -> Block1DetectionModel:
        """엔티티를 DB 모델로 변환"""
        return Block1DetectionModel(
            block1_id=entity.block1_id,
            ticker=entity.ticker,
            status=entity.status,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            entry_open=entity.entry_open,
            entry_high=entity.entry_high,
            entry_low=entity.entry_low,
            entry_close=entity.entry_close,
            entry_volume=entity.entry_volume,
            entry_trading_value=entity.entry_trading_value,
            entry_ma_value=entity.entry_ma_value,
            entry_rate=entity.entry_rate,
            entry_deviation=entity.entry_deviation,
            peak_price=entity.peak_price,
            peak_date=entity.peak_date,
            peak_volume=entity.peak_volume,
            exit_reason=entity.exit_reason,
            exit_price=entity.exit_price,
            condition_name=entity.condition_name,
            pattern_id=entity.pattern_id,
            detection_type=entity.detection_type
        )

    def _model_to_entity(self, model: Block1DetectionModel) -> Block1DetectionEntity:
        """DB 모델을 엔티티로 변환"""
        return Block1DetectionEntity(
            ticker=model.ticker,
            block1_id=model.block1_id,
            status=model.status,
            started_at=model.started_at,
            ended_at=model.ended_at,
            entry_open=model.entry_open,
            entry_high=model.entry_high,
            entry_low=model.entry_low,
            entry_close=model.entry_close,
            entry_volume=model.entry_volume,
            entry_trading_value=model.entry_trading_value,
            entry_ma_value=model.entry_ma_value,
            entry_rate=model.entry_rate,
            entry_deviation=model.entry_deviation,
            peak_price=model.peak_price,
            peak_date=model.peak_date,
            peak_volume=model.peak_volume,
            exit_reason=model.exit_reason,
            exit_price=model.exit_price,
            condition_name=model.condition_name,
            pattern_id=model.pattern_id,
            detection_type=model.detection_type,
            created_at=model.created_at
        )

    def find_by_pattern_and_condition(
        self,
        pattern_id: int,
        condition_name: str
    ) -> List[Block1DetectionEntity]:
        """
        특정 패턴의 특정 조건(seed/redetection) Block1 조회

        Args:
            pattern_id: 패턴 ID
            condition_name: 조건 이름 ('seed' 또는 'redetection')

        Returns:
            Block1Detection 엔티티 리스트
        """
        with self.db.session_scope() as session:
            models = session.query(Block1DetectionModel)\
                .options(joinedload(Block1DetectionModel.stock_info))\
                .filter(
                    Block1DetectionModel.pattern_id == pattern_id,
                    Block1DetectionModel.condition_name == condition_name
                ).order_by(Block1DetectionModel.started_at).all()

            return [self._model_to_entity(model) for model in models]
