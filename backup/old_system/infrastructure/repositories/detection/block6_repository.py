"""
Block6 Repository - 블록6 탐지 결과 저장/조회 Repository
"""
import uuid
from typing import Optional, List
from sqlalchemy.orm import joinedload
from datetime import date
from ....domain.entities import Block6Detection as Block6DetectionEntity
from ...database.models import Block6Detection as Block6DetectionModel
from ...database.connection import DatabaseConnection
from ..common import BaseDetectionRepository, UUIDMixin, DurationCalculatorMixin


class Block6Repository(
    BaseDetectionRepository[Block6DetectionEntity, Block6DetectionModel],
    UUIDMixin,
    DurationCalculatorMixin
):
    """블록6 탐지 결과 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, Block6DetectionModel)

    def save(self, detection: Block6DetectionEntity) -> Block6DetectionEntity:
        """
        블록6 탐지 결과 저장 (block6_id 자동 생성 포함)

        Args:
            detection: 블록6 탐지 결과 엔티티

        Returns:
            저장된 블록6 탐지 결과
        """
        # block6_id 자동 생성 (Mixin 사용)
        self.ensure_block_id(detection, 'block6_id')
        return super().save(detection)

    def _get_block_id(self, entity: Block6DetectionEntity) -> str:
        """엔티티에서 block6_id 추출"""
        return getattr(entity, 'block6_id', self.generate_uuid())

    def _get_model_block_id_field(self):
        """모델의 block6_id 필드 반환"""
        return Block6DetectionModel.block6_id

    def update_status(
        self,
        block6_id: str,
        status: str,
        ended_at: Optional[date] = None,
        exit_reason: Optional[str] = None
    ) -> bool:
        """
        블록6 상태 업데이트 (duration_days 자동 계산)

        Args:
            block6_id: 블록6 고유 ID
            status: 새 상태
            ended_at: 종료일
            exit_reason: 종료 사유

        Returns:
            업데이트 성공 여부
        """
        # duration_days 계산 (Mixin 사용)
        duration_days = None
        if ended_at:
            with self.db.session_scope() as session:
                duration_days = self.calculate_duration_days(
                    session,
                    Block6DetectionModel,
                    Block6DetectionModel.block6_id,
                    block6_id,
                    ended_at
                )

        return super().update_status(
            block6_id, status, ended_at, exit_reason,
            duration_days=duration_days
        )

    def _entity_to_model(self, entity: Block6DetectionEntity) -> Block6DetectionModel:
        """엔티티를 DB 모델로 변환"""
        return Block6DetectionModel(
            block6_id=getattr(entity, 'block6_id', str(uuid.uuid4())),
            ticker=entity.ticker,
            status=entity.status,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            entry_close=entity.entry_close,
            entry_rate=entity.entry_rate,
            prev_block5_id=entity.prev_block5_id,
            prev_block5_peak_price=entity.prev_block5_peak_price,
            prev_block5_peak_volume=entity.prev_block5_peak_volume,
            peak_price=entity.peak_price,
            peak_date=entity.peak_date,
            peak_gain_ratio=entity.peak_gain_ratio,
            peak_volume=entity.peak_volume,
            duration_days=entity.duration_days,
            exit_reason=entity.exit_reason,
            condition_name=entity.condition_name,
            pattern_id=entity.pattern_id,
            detection_type=entity.detection_type
        )

    def find_by_pattern_and_condition(
        self,
        pattern_id: int,
        condition_name: str
    ) -> List[Block6DetectionEntity]:
        """
        특정 패턴의 특정 조건(seed/redetection) Block6 조회

        Args:
            pattern_id: 패턴 ID
            condition_name: 조건 이름 ('seed' 또는 'redetection')

        Returns:
            Block6Detection 엔티티 리스트
        """
        with self.db.session_scope() as session:
            models = session.query(Block6DetectionModel)\
                .options(joinedload(Block6DetectionModel.stock_info))\
                .filter(
                    Block6DetectionModel.pattern_id == pattern_id,
                    Block6DetectionModel.condition_name == condition_name
                ).order_by(Block6DetectionModel.started_at).all()

            return [self._model_to_entity(model) for model in models]

    def _model_to_entity(self, model: Block6DetectionModel) -> Block6DetectionEntity:
        """DB 모델을 엔티티로 변환"""
        entity = Block6DetectionEntity(
            ticker=model.ticker,
            condition_name=model.condition_name or "",
            started_at=model.started_at,
            ended_at=model.ended_at,
            status=model.status,
            entry_close=model.entry_close,
            entry_rate=model.entry_rate,
            prev_block_id=model.prev_block5_id,
            prev_block_peak_price=model.prev_block5_peak_price,
            prev_block_peak_volume=model.prev_block5_peak_volume,
            peak_price=model.peak_price,
            peak_date=model.peak_date,
            peak_gain_ratio=model.peak_gain_ratio,
            peak_volume=model.peak_volume,
            duration_days=model.duration_days,
            exit_reason=model.exit_reason,
            pattern_id=model.pattern_id,
            detection_type=model.detection_type,
            created_at=model.created_at,
            id=model.id
        )
        # block6_id 추가
        entity.block6_id = model.block6_id
        return entity
