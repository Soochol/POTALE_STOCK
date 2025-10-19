"""
Block1 Repository - 블록1 탐지 결과 저장/조회 Repository
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from ...domain.entities.block1_detection import Block1Detection as Block1DetectionEntity
from ..database.models import Block1Detection as Block1DetectionModel
from ..database.connection import DatabaseConnection


class Block1Repository:
    """블록1 탐지 결과 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def save(self, detection: Block1DetectionEntity) -> Block1DetectionEntity:
        """
        블록1 탐지 결과 저장

        Args:
            detection: 블록1 탐지 결과 엔티티

        Returns:
            저장된 블록1 탐지 결과
        """
        session = self.db.get_session()

        try:
            # 엔티티를 모델로 변환
            model = self._entity_to_model(detection)

            # 기존 데이터 확인 (block1_id로)
            existing = session.query(Block1DetectionModel).filter(
                Block1DetectionModel.block1_id == detection.block1_id
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
            raise Exception(f"Failed to save Block1Detection: {e}")

        finally:
            session.close()

    def find_by_id(self, block1_id: str) -> Optional[Block1DetectionEntity]:
        """
        block1_id로 블록1 조회

        Args:
            block1_id: 블록1 고유 ID

        Returns:
            블록1 탐지 결과 또는 None
        """
        session = self.db.get_session()

        try:
            model = session.query(Block1DetectionModel).filter(
                Block1DetectionModel.block1_id == block1_id
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
    ) -> List[Block1DetectionEntity]:
        """
        종목코드로 블록1 리스트 조회

        Args:
            ticker: 종목코드
            status: 상태 필터 ("active", "completed", None)
            from_date: 시작일 필터
            to_date: 종료일 필터

        Returns:
            블록1 탐지 결과 리스트
        """
        session = self.db.get_session()

        try:
            query = session.query(Block1DetectionModel).filter(
                Block1DetectionModel.ticker == ticker
            )

            if status:
                query = query.filter(Block1DetectionModel.status == status)

            if from_date:
                query = query.filter(Block1DetectionModel.started_at >= from_date)

            if to_date:
                query = query.filter(Block1DetectionModel.started_at <= to_date)

            models = query.order_by(Block1DetectionModel.started_at).all()

            return [self._model_to_entity(model) for model in models]

        finally:
            session.close()

    def find_active_by_ticker(self, ticker: str) -> List[Block1DetectionEntity]:
        """
        종목의 활성 블록1 조회

        Args:
            ticker: 종목코드

        Returns:
            활성 블록1 리스트
        """
        return self.find_by_ticker(ticker, status="active")

    def update_status(
        self,
        block1_id: str,
        status: str,
        ended_at: Optional[date] = None,
        exit_reason: Optional[str] = None,
        exit_price: Optional[float] = None
    ) -> bool:
        """
        블록1 상태 업데이트

        Args:
            block1_id: 블록1 고유 ID
            status: 새 상태
            ended_at: 종료일
            exit_reason: 종료 사유
            exit_price: 종료 가격

        Returns:
            업데이트 성공 여부
        """
        session = self.db.get_session()

        try:
            model = session.query(Block1DetectionModel).filter(
                Block1DetectionModel.block1_id == block1_id
            ).first()

            if not model:
                return False

            model.status = status
            if ended_at:
                model.ended_at = ended_at
            if exit_reason:
                model.exit_reason = exit_reason
            if exit_price:
                model.exit_price = exit_price

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to update Block1Detection status: {e}")

        finally:
            session.close()

    def delete(self, block1_id: str) -> bool:
        """
        블록1 삭제

        Args:
            block1_id: 블록1 고유 ID

        Returns:
            삭제 성공 여부
        """
        session = self.db.get_session()

        try:
            model = session.query(Block1DetectionModel).filter(
                Block1DetectionModel.block1_id == block1_id
            ).first()

            if not model:
                return False

            session.delete(model)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to delete Block1Detection: {e}")

        finally:
            session.close()

    def update_peak(
        self,
        block1_id: str,
        peak_price: float,
        peak_date: date
    ) -> bool:
        """
        블록1 최고가 업데이트

        Args:
            block1_id: 블록1 고유 ID
            peak_price: 최고가
            peak_date: 최고가 달성일

        Returns:
            업데이트 성공 여부
        """
        session = self.db.get_session()

        try:
            model = session.query(Block1DetectionModel).filter(
                Block1DetectionModel.block1_id == block1_id
            ).first()

            if not model:
                return False

            model.peak_price = peak_price
            model.peak_date = peak_date

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to update Block1Detection peak: {e}")

        finally:
            session.close()

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
            exit_reason=entity.exit_reason,
            exit_price=entity.exit_price,
            condition_name=entity.condition_name
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
            entry_trading_value=model.entry_trading_value or 0.0,
            entry_ma_value=model.entry_ma_value,
            entry_rate=model.entry_rate,
            entry_deviation=model.entry_deviation,
            peak_price=model.peak_price,
            peak_date=model.peak_date,
            exit_reason=model.exit_reason,
            exit_price=model.exit_price,
            condition_name=model.condition_name,
            created_at=model.created_at.date() if model.created_at else None
        )
