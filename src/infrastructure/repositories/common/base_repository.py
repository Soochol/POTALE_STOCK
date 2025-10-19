"""
Base Repository Classes
공통 Repository 베이스 클래스
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Type
from datetime import date, datetime
from sqlalchemy.orm import Session

from ...database.connection import DatabaseConnection


# Type Variables
EntityType = TypeVar('EntityType')
ModelType = TypeVar('ModelType')


class BaseDetectionRepository(ABC, Generic[EntityType, ModelType]):
    """
    블록 탐지 결과 Repository 베이스 클래스
    Block1/2/3 Repository의 공통 로직을 제공
    """

    def __init__(self, db_connection: DatabaseConnection, model_class: Type[ModelType]):
        self.db = db_connection
        self.model_class = model_class

    @abstractmethod
    def _entity_to_model(self, entity: EntityType) -> ModelType:
        """엔티티를 DB 모델로 변환 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    def _model_to_entity(self, model: ModelType) -> EntityType:
        """DB 모델을 엔티티로 변환 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    def _get_block_id(self, entity: EntityType) -> str:
        """엔티티에서 block_id 추출 (block1_id, block2_id, block3_id)"""
        pass

    @abstractmethod
    def _get_model_block_id_field(self):
        """모델의 block_id 필드 반환 (Block1DetectionModel.block1_id 등)"""
        pass

    def save(self, detection: EntityType) -> EntityType:
        """
        블록 탐지 결과 저장 (공통 로직)

        Args:
            detection: 블록 탐지 결과 엔티티

        Returns:
            저장된 블록 탐지 결과
        """
        with self.db.session_scope() as session:
            # 엔티티를 모델로 변환
            model = self._entity_to_model(detection)
            block_id = self._get_block_id(detection)

            # 기존 데이터 확인
            existing = session.query(self.model_class).filter(
                self._get_model_block_id_field() == block_id
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

    def find_by_id(self, block_id: str) -> Optional[EntityType]:
        """
        block_id로 블록 조회

        Args:
            block_id: 블록 고유 ID

        Returns:
            블록 탐지 결과 또는 None
        """
        with self.db.session_scope() as session:
            model = session.query(self.model_class).filter(
                self._get_model_block_id_field() == block_id
            ).first()

            if model:
                return self._model_to_entity(model)
            return None

    def find_by_ticker(
        self,
        ticker: str,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[EntityType]:
        """
        종목코드로 블록 리스트 조회

        Args:
            ticker: 종목코드
            status: 상태 필터 ("active", "completed", None)
            from_date: 시작일 필터
            to_date: 종료일 필터

        Returns:
            블록 탐지 결과 리스트
        """
        with self.db.session_scope() as session:
            query = session.query(self.model_class).filter(
                self.model_class.ticker == ticker
            )

            if status:
                query = query.filter(self.model_class.status == status)

            if from_date:
                query = query.filter(self.model_class.started_at >= from_date)

            if to_date:
                query = query.filter(self.model_class.started_at <= to_date)

            models = query.order_by(self.model_class.started_at).all()

            return [self._model_to_entity(model) for model in models]

    def find_active_by_ticker(self, ticker: str) -> List[EntityType]:
        """
        종목의 활성 블록 조회

        Args:
            ticker: 종목코드

        Returns:
            활성 블록 리스트
        """
        return self.find_by_ticker(ticker, status="active")

    def update_status(
        self,
        block_id: str,
        status: str,
        ended_at: Optional[date] = None,
        exit_reason: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        블록 상태 업데이트

        Args:
            block_id: 블록 고유 ID
            status: 새 상태
            ended_at: 종료일
            exit_reason: 종료 사유
            **kwargs: 추가 필드 (exit_price, duration_days 등)

        Returns:
            업데이트 성공 여부
        """
        with self.db.session_scope() as session:
            model = session.query(self.model_class).filter(
                self._get_model_block_id_field() == block_id
            ).first()

            if not model:
                return False

            model.status = status
            if ended_at:
                model.ended_at = ended_at
            if exit_reason:
                model.exit_reason = exit_reason

            # 추가 필드 업데이트
            for key, value in kwargs.items():
                if hasattr(model, key) and value is not None:
                    setattr(model, key, value)

            session.commit()
            return True

    def update_peak(self, block_id: str, **kwargs) -> bool:
        """
        블록 최고가/거래량 업데이트

        Args:
            block_id: 블록 고유 ID
            **kwargs: peak_price, peak_date, peak_gain_ratio, peak_volume 등

        Returns:
            업데이트 성공 여부
        """
        with self.db.session_scope() as session:
            model = session.query(self.model_class).filter(
                self._get_model_block_id_field() == block_id
            ).first()

            if not model:
                return False

            # 필드 업데이트
            for key, value in kwargs.items():
                if hasattr(model, key) and value is not None:
                    setattr(model, key, value)

            session.commit()
            return True

    def delete(self, block_id: str) -> bool:
        """
        블록 삭제

        Args:
            block_id: 블록 고유 ID

        Returns:
            삭제 성공 여부
        """
        with self.db.session_scope() as session:
            model = session.query(self.model_class).filter(
                self._get_model_block_id_field() == block_id
            ).first()

            if not model:
                return False

            session.delete(model)
            session.commit()
            return True


class BaseConditionPresetRepository(ABC):
    """
    조건 프리셋 Repository 베이스 클래스
    Block1/2/3 Condition Preset Repository의 공통 로직
    """

    def __init__(self, db_connection: DatabaseConnection, model_class: Type):
        self.db = db_connection
        self.model_class = model_class

    @abstractmethod
    def _condition_to_dict(self, condition) -> dict:
        """조건 엔티티를 딕셔너리로 변환 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    def _dict_to_condition(self, data: dict):
        """딕셔너리를 조건 엔티티로 변환 (서브클래스에서 구현)"""
        pass

    def exists(self, name: str) -> bool:
        """
        프리셋 존재 여부 확인

        Args:
            name: 프리셋 이름

        Returns:
            존재 여부
        """
        with self.db.session_scope() as session:
            count = session.query(self.model_class).filter_by(
                name=name,
                is_active=1
            ).count()
            return count > 0

    def delete(self, name: str) -> bool:
        """
        프리셋 삭제 (Soft Delete)

        Args:
            name: 프리셋 이름

        Returns:
            삭제 성공 여부
        """
        with self.db.session_scope() as session:
            preset = session.query(self.model_class).filter_by(name=name).first()

            if not preset:
                return False

            preset.is_active = 0
            preset.updated_at = datetime.now()

            session.commit()
            return True

    def list_all(self, active_only: bool = True) -> List[dict]:
        """
        모든 프리셋 조회

        Args:
            active_only: True이면 활성 프리셋만, False면 모두

        Returns:
            프리셋 정보 리스트
        """
        with self.db.session_scope() as session:
            query = session.query(self.model_class)

            if active_only:
                query = query.filter_by(is_active=1)

            presets = query.order_by(self.model_class.name).all()

            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'is_active': p.is_active,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at,
                    **self._preset_to_dict(p)
                }
                for p in presets
            ]

    def _preset_to_dict(self, preset) -> dict:
        """
        Preset 모델을 딕셔너리로 변환 (list_all에서 사용)
        서브클래스에서 오버라이드 가능
        """
        return {}
