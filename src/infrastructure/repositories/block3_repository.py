"""
Block3 Repository - 블록3 탐지 결과 저장/조회 Repository
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from ...domain.entities.block3_detection import Block3Detection as Block3DetectionEntity
from ..database.models import Block3Detection as Block3DetectionModel
from ..database.connection import DatabaseConnection
import uuid


class Block3Repository:
    """블록3 탐지 결과 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def save(self, detection: Block3DetectionEntity) -> Block3DetectionEntity:
        """
        블록3 탐지 결과 저장

        Args:
            detection: 블록3 탐지 결과 엔티티

        Returns:
            저장된 블록3 탐지 결과
        """
        session = self.db.get_session()

        try:
            # block3_id 자동 생성 (없는 경우)
            if not hasattr(detection, 'block3_id') or not detection.block3_id:
                detection.block3_id = str(uuid.uuid4())

            # 엔티티를 모델로 변환
            model = self._entity_to_model(detection)

            # 기존 데이터 확인 (block3_id로)
            existing = session.query(Block3DetectionModel).filter(
                Block3DetectionModel.block3_id == detection.block3_id
            ).first()

            if existing:
                # 업데이트
                for key, value in model.__dict__.items():
                    if key != '_sa_instance_state' and key != 'id':
                        setattr(existing, key, value)
            else:
                # 신규 삽입
                session.add(model)

            session.commit()

            # 저장된 ID 반영
            if not existing:
                detection.id = model.id

            return detection

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to save Block3Detection: {e}")

        finally:
            session.close()

    def find_by_id(self, block3_id: str) -> Optional[Block3DetectionEntity]:
        """
        block3_id로 블록3 조회

        Args:
            block3_id: 블록3 고유 ID

        Returns:
            블록3 탐지 결과 또는 None
        """
        session = self.db.get_session()

        try:
            model = session.query(Block3DetectionModel).filter(
                Block3DetectionModel.block3_id == block3_id
            ).first()

            if model:
                return self._model_to_entity(model)
            return None

        finally:
            session.close()

    def find_by_ticker(
        self,
        ticker: str,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Block3DetectionEntity]:
        """
        종목코드로 블록3 리스트 조회

        Args:
            ticker: 종목코드
            status: 상태 필터 ("active", "completed", None)
            from_date: 시작일 필터
            to_date: 종료일 필터

        Returns:
            블록3 탐지 결과 리스트
        """
        session = self.db.get_session()

        try:
            query = session.query(Block3DetectionModel).filter(
                Block3DetectionModel.ticker == ticker
            )

            if status:
                query = query.filter(Block3DetectionModel.status == status)

            if from_date:
                query = query.filter(Block3DetectionModel.started_at >= from_date)

            if to_date:
                query = query.filter(Block3DetectionModel.started_at <= to_date)

            models = query.order_by(Block3DetectionModel.started_at).all()

            return [self._model_to_entity(model) for model in models]

        finally:
            session.close()

    def find_active_by_ticker(self, ticker: str) -> List[Block3DetectionEntity]:
        """
        종목의 활성 블록3 조회

        Args:
            ticker: 종목코드

        Returns:
            활성 블록3 리스트
        """
        return self.find_by_ticker(ticker, status="active")

    def update_status(
        self,
        block3_id: str,
        status: str,
        ended_at: Optional[date] = None,
        exit_reason: Optional[str] = None
    ) -> bool:
        """
        블록3 상태 업데이트

        Args:
            block3_id: 블록3 고유 ID
            status: 새 상태
            ended_at: 종료일
            exit_reason: 종료 사유

        Returns:
            업데이트 성공 여부
        """
        session = self.db.get_session()

        try:
            model = session.query(Block3DetectionModel).filter(
                Block3DetectionModel.block3_id == block3_id
            ).first()

            if not model:
                return False

            model.status = status
            if ended_at:
                model.ended_at = ended_at
                model.duration_days = (ended_at - model.started_at).days + 1
            if exit_reason:
                model.exit_reason = exit_reason

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to update Block3Detection status: {e}")

        finally:
            session.close()

    def update_peak(
        self,
        block3_id: str,
        peak_price: float,
        peak_date: date,
        peak_gain_ratio: float,
        peak_volume: int
    ) -> bool:
        """
        블록3 최고가/거래량 업데이트

        Args:
            block3_id: 블록3 고유 ID
            peak_price: 최고가
            peak_date: 최고가 달성일
            peak_gain_ratio: 최고가 상승률
            peak_volume: 최고 거래량

        Returns:
            업데이트 성공 여부
        """
        session = self.db.get_session()

        try:
            model = session.query(Block3DetectionModel).filter(
                Block3DetectionModel.block3_id == block3_id
            ).first()

            if not model:
                return False

            model.peak_price = peak_price
            model.peak_date = peak_date
            model.peak_gain_ratio = peak_gain_ratio
            model.peak_volume = peak_volume

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to update Block3Detection peak: {e}")

        finally:
            session.close()

    def delete(self, block3_id: str) -> bool:
        """
        블록3 삭제

        Args:
            block3_id: 블록3 고유 ID

        Returns:
            삭제 성공 여부
        """
        session = self.db.get_session()

        try:
            model = session.query(Block3DetectionModel).filter(
                Block3DetectionModel.block3_id == block3_id
            ).first()

            if not model:
                return False

            session.delete(model)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to delete Block3Detection: {e}")

        finally:
            session.close()

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
