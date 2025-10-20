"""
Block2 Repository - 블록2 탐지 결과 저장/조회 Repository
"""
from typing import Optional
from datetime import date
from ....domain.entities import Block2Detection as Block2DetectionEntity
from ...database.models import Block2Detection as Block2DetectionModel
from ...database.connection import DatabaseConnection
from ..common import BaseDetectionRepository, UUIDMixin, DurationCalculatorMixin


class Block2Repository(
    BaseDetectionRepository[Block2DetectionEntity, Block2DetectionModel],
    UUIDMixin,
    DurationCalculatorMixin
):
    """블록2 탐지 결과 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, Block2DetectionModel)

    def save(self, detection: Block2DetectionEntity) -> Block2DetectionEntity:
        """
        블록2 탐지 결과 저장 (block2_id 자동 생성 포함)

        Args:
            detection: 블록2 탐지 결과 엔티티

        Returns:
            저장된 블록2 탐지 결과
        """
        # block2_id 자동 생성 (Mixin 사용)
        self.ensure_block_id(detection, 'block2_id')
        return super().save(detection)

    def _get_block_id(self, entity: Block2DetectionEntity) -> str:
        """엔티티에서 block2_id 추출"""
        return getattr(entity, 'block2_id', self.generate_uuid())

    def _get_model_block_id_field(self):
        """모델의 block2_id 필드 반환"""
        return Block2DetectionModel.block2_id

    def find_latest_completed_before(
        self,
        ticker: str,
        before_date: date
    ) -> Optional[Block2DetectionEntity]:
        """
        특정 날짜 이전의 가장 최근 완료된 블록2 조회

        Args:
            ticker: 종목코드
            before_date: 기준 날짜

        Returns:
            블록2 탐지 결과 또는 None
        """
        with self.db.session_scope() as session:
            model = session.query(Block2DetectionModel).filter(
                Block2DetectionModel.ticker == ticker,
                Block2DetectionModel.status == "completed",
                Block2DetectionModel.ended_at < before_date
            ).order_by(
                Block2DetectionModel.ended_at.desc()
            ).first()

            if model:
                return self._model_to_entity(model)
            return None

    def update_status(
        self,
        block2_id: str,
        status: str,
        ended_at: Optional[date] = None,
        exit_reason: Optional[str] = None
    ) -> bool:
        """
        블록2 상태 업데이트 (duration_days 자동 계산)

        Args:
            block2_id: 블록2 고유 ID
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
                    Block2DetectionModel,
                    Block2DetectionModel.block2_id,
                    block2_id,
                    ended_at
                )

        return super().update_status(
            block2_id, status, ended_at, exit_reason,
            duration_days=duration_days
        )

    def _entity_to_model(self, entity: Block2DetectionEntity) -> Block2DetectionModel:
        """엔티티를 DB 모델로 변환"""
        return Block2DetectionModel(
            block2_id=getattr(entity, 'block2_id', str(uuid.uuid4())),
            ticker=entity.ticker,
            status=entity.status,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            entry_close=entity.entry_close,
            entry_rate=entity.entry_rate,
            prev_block1_id=entity.prev_block1_id,
            prev_block1_peak_price=entity.prev_block1_peak_price,
            prev_block1_peak_volume=entity.prev_block1_peak_volume,
            peak_price=entity.peak_price,
            peak_date=entity.peak_date,
            peak_gain_ratio=entity.peak_gain_ratio,
            peak_volume=entity.peak_volume,
            duration_days=entity.duration_days,
            exit_reason=entity.exit_reason,
            condition_name=entity.condition_name
        )

    def _model_to_entity(self, model: Block2DetectionModel) -> Block2DetectionEntity:
        """DB 모델을 엔티티로 변환"""
        entity = Block2DetectionEntity(
            ticker=model.ticker,
            condition_name=model.condition_name or "",
            started_at=model.started_at,
            ended_at=model.ended_at,
            status=model.status,
            entry_close=model.entry_close,
            entry_rate=model.entry_rate,
            prev_block1_id=model.prev_block1_id,
            prev_block1_peak_price=model.prev_block1_peak_price,
            prev_block1_peak_volume=model.prev_block1_peak_volume,
            peak_price=model.peak_price,
            peak_date=model.peak_date,
            peak_gain_ratio=model.peak_gain_ratio,
            peak_volume=model.peak_volume,
            duration_days=model.duration_days,
            exit_reason=model.exit_reason,
            id=model.id
        )
        # block2_id 추가
        entity.block2_id = model.block2_id
        return entity
