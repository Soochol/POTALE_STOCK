"""
DynamicBlockRepository 구현체
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from src.domain.repositories.dynamic_block_repository import DynamicBlockRepository
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus, RedetectionEvent
from src.infrastructure.database.models.dynamic_block_detection_model import DynamicBlockDetectionModel


class DynamicBlockRepositoryImpl(DynamicBlockRepository):
    """
    DynamicBlockRepository의 SQLAlchemy 구현체
    """

    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy 세션
        """
        self.session = session

    def save(self, detection: DynamicBlockDetection) -> DynamicBlockDetection:
        """블록 저장 (생성 또는 업데이트)"""
        if detection.id is None:
            # 새 레코드 생성
            model = self._to_model(detection)
            self.session.add(model)
            self.session.flush()  # ID 할당
            detection.id = model.id
        else:
            # 기존 레코드 업데이트
            model = self.session.query(DynamicBlockDetectionModel).filter_by(
                id=detection.id
            ).first()

            if model:
                self._update_model(model, detection)
            else:
                # 모델이 없으면 새로 생성
                model = self._to_model(detection)
                self.session.add(model)
                self.session.flush()
                detection.id = model.id

        self.session.commit()
        return detection

    def save_all(self, detections: List[DynamicBlockDetection]) -> List[DynamicBlockDetection]:
        """여러 블록 일괄 저장"""
        saved_detections = []
        for detection in detections:
            saved = self.save(detection)
            saved_detections.append(saved)
        return saved_detections

    def find_by_id(self, detection_id: int) -> Optional[DynamicBlockDetection]:
        """ID로 블록 조회"""
        model = self.session.query(DynamicBlockDetectionModel).filter_by(
            id=detection_id
        ).first()

        if model:
            return self._to_entity(model)
        return None

    def find_by_ticker(
        self,
        ticker: str,
        condition_name: Optional[str] = None,
        block_type: Optional[int] = None
    ) -> List[DynamicBlockDetection]:
        """종목 코드로 블록 조회"""
        query = self.session.query(DynamicBlockDetectionModel).filter_by(ticker=ticker)

        if condition_name:
            query = query.filter_by(condition_name=condition_name)

        if block_type is not None:
            query = query.filter_by(block_type=block_type)

        models = query.order_by(DynamicBlockDetectionModel.started_at).all()
        return [self._to_entity(m) for m in models]

    def find_active_blocks(
        self,
        ticker: str,
        block_id: Optional[str] = None
    ) -> List[DynamicBlockDetection]:
        """진행 중인 블록 조회"""
        query = self.session.query(DynamicBlockDetectionModel).filter_by(
            ticker=ticker,
            status=BlockStatus.ACTIVE.value
        )

        if block_id:
            query = query.filter_by(block_id=block_id)

        models = query.order_by(DynamicBlockDetectionModel.started_at).all()
        return [self._to_entity(m) for m in models]

    def find_by_pattern_id(self, pattern_id: int) -> List[DynamicBlockDetection]:
        """패턴 ID로 블록 조회"""
        models = self.session.query(DynamicBlockDetectionModel).filter_by(
            pattern_id=pattern_id
        ).order_by(DynamicBlockDetectionModel.block_type).all()

        return [self._to_entity(m) for m in models]

    def find_by_date_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        block_type: Optional[int] = None
    ) -> List[DynamicBlockDetection]:
        """날짜 범위로 블록 조회"""
        query = self.session.query(DynamicBlockDetectionModel).filter(
            DynamicBlockDetectionModel.ticker == ticker,
            DynamicBlockDetectionModel.started_at >= start_date,
            DynamicBlockDetectionModel.started_at <= end_date
        )

        if block_type is not None:
            query = query.filter_by(block_type=block_type)

        models = query.order_by(DynamicBlockDetectionModel.started_at).all()
        return [self._to_entity(m) for m in models]

    def delete_by_id(self, detection_id: int) -> bool:
        """ID로 블록 삭제"""
        result = self.session.query(DynamicBlockDetectionModel).filter_by(
            id=detection_id
        ).delete()

        self.session.commit()
        return result > 0

    def delete_by_ticker(self, ticker: str, condition_name: Optional[str] = None) -> int:
        """종목의 블록 삭제"""
        query = self.session.query(DynamicBlockDetectionModel).filter_by(ticker=ticker)

        if condition_name:
            query = query.filter_by(condition_name=condition_name)

        count = query.delete()
        self.session.commit()
        return count

    # ========== Private Helper Methods ==========

    def _to_model(self, entity: DynamicBlockDetection) -> DynamicBlockDetectionModel:
        """Entity → ORM Model 변환"""
        # Metadata에 redetections 추가 (NEW - 2025-10-25)
        metadata = entity.metadata.copy()
        if entity.redetections:
            metadata['redetections'] = [redet.to_dict() for redet in entity.redetections]

        return DynamicBlockDetectionModel(
            id=entity.id,
            block_id=entity.block_id,
            block_type=entity.block_type,
            ticker=entity.ticker,
            pattern_id=entity.pattern_id,
            condition_name=entity.condition_name,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            status=entity.status.value,
            peak_price=entity.peak_price,
            peak_volume=entity.peak_volume,
            peak_date=entity.peak_date,
            parent_blocks=entity.parent_blocks,
            custom_metadata=metadata
        )

    def _update_model(self, model: DynamicBlockDetectionModel, entity: DynamicBlockDetection) -> None:
        """기존 모델 업데이트"""
        # Metadata에 redetections 추가 (NEW - 2025-10-25)
        metadata = entity.metadata.copy()
        if entity.redetections:
            metadata['redetections'] = [redet.to_dict() for redet in entity.redetections]

        model.block_id = entity.block_id
        model.block_type = entity.block_type
        model.ticker = entity.ticker
        model.pattern_id = entity.pattern_id
        model.condition_name = entity.condition_name
        model.started_at = entity.started_at
        model.ended_at = entity.ended_at
        model.status = entity.status.value
        model.peak_price = entity.peak_price
        model.peak_volume = entity.peak_volume
        model.peak_date = entity.peak_date
        model.parent_blocks = entity.parent_blocks
        model.custom_metadata = metadata

    def _to_entity(self, model: DynamicBlockDetectionModel) -> DynamicBlockDetection:
        """ORM Model → Entity 변환"""
        # Metadata에서 redetections 추출 (NEW - 2025-10-25)
        metadata = model.custom_metadata or {}
        redetections = []

        if 'redetections' in metadata:
            redetections_data = metadata.pop('redetections')  # metadata에서 제거
            redetections = [
                RedetectionEvent.from_dict(redet_dict)
                for redet_dict in redetections_data
            ]

        return DynamicBlockDetection(
            id=model.id,
            block_id=model.block_id,
            block_type=model.block_type,
            ticker=model.ticker,
            pattern_id=model.pattern_id,
            condition_name=model.condition_name,
            started_at=model.started_at,
            ended_at=model.ended_at,
            status=BlockStatus(model.status),
            peak_price=model.peak_price,
            peak_volume=model.peak_volume,
            peak_date=model.peak_date,
            parent_blocks=model.parent_blocks or [],
            redetections=redetections,
            metadata=metadata
        )
