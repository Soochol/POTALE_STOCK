"""
Seed Pattern Repository Implementation

SQLAlchemy 기반 Seed Pattern 저장소 구현
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.domain.repositories.seed_pattern_repository import SeedPatternRepository
from src.domain.entities.patterns import SeedPattern, SeedPatternStatus, BlockFeatures
from src.infrastructure.database.models.seed_pattern_model import SeedPatternModel


class SeedPatternRepositoryImpl(SeedPatternRepository):
    """
    Seed Pattern Repository SQLAlchemy 구현체
    """

    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def save(self, seed_pattern: SeedPattern) -> SeedPattern:
        """Seed pattern 저장 (생성 또는 업데이트) - UPSERT"""
        if seed_pattern.id:
            # ID가 있으면 ID로 업데이트
            model = self.session.query(SeedPatternModel).filter_by(id=seed_pattern.id).first()
            if not model:
                raise ValueError(f"SeedPattern with id {seed_pattern.id} not found")
            self._update_model(model, seed_pattern)
        else:
            # ID가 없으면 pattern_name으로 조회
            existing = self.session.query(SeedPatternModel).filter_by(
                pattern_name=seed_pattern.pattern_name
            ).first()

            if existing:
                # 이미 존재하면 업데이트
                self._update_model(existing, seed_pattern)
                model = existing
            else:
                # 없으면 새로 생성
                model = self._to_model(seed_pattern)
                self.session.add(model)

        self.session.flush()
        return self._to_entity(model)

    def save_all(self, seed_patterns: List[SeedPattern]) -> List[SeedPattern]:
        """여러 seed pattern 일괄 저장"""
        saved = []
        for seed_pattern in seed_patterns:
            saved.append(self.save(seed_pattern))
        return saved

    def find_by_id(self, seed_pattern_id: int) -> Optional[SeedPattern]:
        """ID로 seed pattern 조회"""
        model = self.session.query(SeedPatternModel).filter_by(id=seed_pattern_id).first()
        return self._to_entity(model) if model else None

    def find_by_name(self, pattern_name: str) -> Optional[SeedPattern]:
        """이름으로 seed pattern 조회"""
        model = self.session.query(SeedPatternModel).filter_by(pattern_name=pattern_name).first()
        return self._to_entity(model) if model else None

    def find_by_ticker(
        self,
        ticker: str,
        status: Optional[SeedPatternStatus] = None
    ) -> List[SeedPattern]:
        """종목 코드로 seed pattern 조회"""
        query = self.session.query(SeedPatternModel).filter_by(ticker=ticker)

        if status:
            query = query.filter_by(status=status.value)

        models = query.order_by(SeedPatternModel.detection_date.desc()).all()
        return [self._to_entity(m) for m in models]

    def find_active_patterns(self, ticker: Optional[str] = None) -> List[SeedPattern]:
        """활성화된 seed pattern 조회"""
        query = self.session.query(SeedPatternModel).filter_by(status='active')

        if ticker:
            query = query.filter_by(ticker=ticker)

        models = query.order_by(SeedPatternModel.detection_date.desc()).all()
        return [self._to_entity(m) for m in models]

    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        ticker: Optional[str] = None
    ) -> List[SeedPattern]:
        """날짜 범위로 seed pattern 조회"""
        query = self.session.query(SeedPatternModel).filter(
            and_(
                SeedPatternModel.detection_date >= start_date,
                SeedPatternModel.detection_date <= end_date
            )
        )

        if ticker:
            query = query.filter_by(ticker=ticker)

        models = query.order_by(SeedPatternModel.detection_date.desc()).all()
        return [self._to_entity(m) for m in models]

    def find_all(
        self,
        status: Optional[SeedPatternStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SeedPattern]:
        """모든 seed pattern 조회 (페이지네이션)"""
        query = self.session.query(SeedPatternModel)

        if status:
            query = query.filter_by(status=status.value)

        query = query.order_by(SeedPatternModel.detection_date.desc())

        if limit:
            query = query.limit(limit).offset(offset)

        models = query.all()
        return [self._to_entity(m) for m in models]

    def count(
        self,
        ticker: Optional[str] = None,
        status: Optional[SeedPatternStatus] = None
    ) -> int:
        """Seed pattern 개수 조회"""
        query = self.session.query(SeedPatternModel)

        if ticker:
            query = query.filter_by(ticker=ticker)

        if status:
            query = query.filter_by(status=status.value)

        return query.count()

    def delete_by_id(self, seed_pattern_id: int) -> bool:
        """ID로 seed pattern 삭제"""
        model = self.session.query(SeedPatternModel).filter_by(id=seed_pattern_id).first()
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def delete_by_ticker(self, ticker: str) -> int:
        """종목의 모든 seed pattern 삭제"""
        count = self.session.query(SeedPatternModel).filter_by(ticker=ticker).delete()
        self.session.flush()
        return count

    def update_status(
        self,
        seed_pattern_id: int,
        status: SeedPatternStatus
    ) -> bool:
        """Seed pattern 상태 업데이트"""
        model = self.session.query(SeedPatternModel).filter_by(id=seed_pattern_id).first()
        if not model:
            return False

        model.status = status.value
        self.session.flush()
        return True

    # === Private methods ===

    def _to_model(self, entity: SeedPattern) -> SeedPatternModel:
        """Entity → Model 변환"""
        return SeedPatternModel(
            id=entity.id,
            pattern_name=entity.pattern_name,
            ticker=entity.ticker,
            yaml_config_path=entity.yaml_config_path,
            detection_date=entity.detection_date,
            block_features=[f.to_dict() for f in entity.block_features],
            price_shape=entity.price_shape,
            volume_shape=entity.volume_shape,
            status=entity.status.value,
            description=entity.description,
            custom_metadata=entity.metadata or {}
        )

    def _update_model(self, model: SeedPatternModel, entity: SeedPattern) -> None:
        """Model 업데이트 (기존 모델에 entity 값 반영)"""
        model.pattern_name = entity.pattern_name
        model.ticker = entity.ticker
        model.yaml_config_path = entity.yaml_config_path
        model.detection_date = entity.detection_date
        model.block_features = [f.to_dict() for f in entity.block_features]
        model.price_shape = entity.price_shape
        model.volume_shape = entity.volume_shape
        model.status = entity.status.value
        model.description = entity.description
        model.custom_metadata = entity.metadata or {}

    def _to_entity(self, model: SeedPatternModel) -> SeedPattern:
        """Model → Entity 변환"""
        block_features = [BlockFeatures.from_dict(f) for f in model.block_features]

        return SeedPattern(
            id=model.id,
            pattern_name=model.pattern_name,
            ticker=model.ticker,
            yaml_config_path=model.yaml_config_path,
            detection_date=model.detection_date,
            block_features=block_features,
            price_shape=model.price_shape,
            volume_shape=model.volume_shape,
            status=SeedPatternStatus(model.status),
            description=model.description,
            metadata=model.custom_metadata or {}
        )
