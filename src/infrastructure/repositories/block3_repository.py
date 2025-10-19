"""
Block3 Repository - 블록3 탐지 결과 저장/조회 Repository
"""
from typing import Optional
from datetime import date
from ...domain.entities.block3_detection import Block3Detection as Block3DetectionEntity
from ..database.models import Block3Detection as Block3DetectionModel
from ..database.connection import DatabaseConnection
from .common import BaseDetectionRepository
import uuid


class Block3Repository(BaseDetectionRepository[Block3DetectionEntity, Block3DetectionModel]):
    """블록3 탐지 결과 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, Block3DetectionModel)

    def save(self, detection: Block3DetectionEntity) -> Block3DetectionEntity:
        """
        블록3 탐지 결과 저장 (block3_id 자동 생성 포함)

        Args:
            detection: 블록3 탐지 결과 엔티티

        Returns:
            저장된 블록3 탐지 결과
        """
        # block3_id 자동 생성 (없는 경우)
        if not hasattr(detection, 'block3_id') or not detection.block3_id:
            detection.block3_id = str(uuid.uuid4())

        return super().save(detection)

    def _get_block_id(self, entity: Block3DetectionEntity) -> str:
        """엔티티에서 block3_id 추출"""
        return getattr(entity, 'block3_id', str(uuid.uuid4()))

    def _get_model_block_id_field(self):
        """모델의 block3_id 필드 반환"""
        return Block3DetectionModel.block3_id

    def update_status(
        self,
        block3_id: str,
        status: str,
        ended_at: Optional[date] = None,
        exit_reason: Optional[str] = None
    ) -> bool:
        """
        블록3 상태 업데이트 (duration_days 자동 계산)

        Args:
            block3_id: 블록3 고유 ID
            status: 새 상태
            ended_at: 종료일
            exit_reason: 종료 사유

        Returns:
            업데이트 성공 여부
        """
        # duration_days 계산 (ended_at 있으면)
        duration_days = None
        if ended_at:
            with self.db.session_scope() as session:
                model = session.query(Block3DetectionModel).filter(
                    Block3DetectionModel.block3_id == block3_id
                ).first()
                if model and model.started_at:
                    duration_days = (ended_at - model.started_at).days + 1

        return super().update_status(
            block3_id, status, ended_at, exit_reason,
            duration_days=duration_days
        )

    def _entity_to_model(self, entity: Block3DetectionEntity) -> Block3DetectionModel:
        """엔티티를 DB 모델로 변환"""
        return Block3DetectionModel(
            block3_id=getattr(entity, 'block3_id', str(uuid.uuid4())),
            ticker=entity.ticker,
            status=entity.status,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            entry_close=entity.entry_close,
            entry_rate=entity.entry_rate,
            prev_block2_id=entity.prev_block2_id,
            prev_block2_peak_price=entity.prev_block2_peak_price,
            prev_block2_peak_volume=entity.prev_block2_peak_volume,
            peak_price=entity.peak_price,
            peak_date=entity.peak_date,
            peak_gain_ratio=entity.peak_gain_ratio,
            peak_volume=entity.peak_volume,
            duration_days=entity.duration_days,
            exit_reason=entity.exit_reason,
            condition_name=entity.condition_name
        )

    def _model_to_entity(self, model: Block3DetectionModel) -> Block3DetectionEntity:
        """DB 모델을 엔티티로 변환"""
        entity = Block3DetectionEntity(
            ticker=model.ticker,
            condition_name=model.condition_name or "",
            started_at=model.started_at,
            ended_at=model.ended_at,
            status=model.status,
            entry_close=model.entry_close,
            entry_rate=model.entry_rate,
            prev_block2_id=model.prev_block2_id,
            prev_block2_peak_price=model.prev_block2_peak_price,
            prev_block2_peak_volume=model.prev_block2_peak_volume,
            peak_price=model.peak_price,
            peak_date=model.peak_date,
            peak_gain_ratio=model.peak_gain_ratio,
            peak_volume=model.peak_volume,
            duration_days=model.duration_days,
            exit_reason=model.exit_reason,
            id=model.id
        )
        # block3_id 추가
        entity.block3_id = model.block3_id
        return entity
