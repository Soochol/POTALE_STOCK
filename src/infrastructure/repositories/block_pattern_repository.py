"""
Block Pattern Repository

블록 패턴 저장/조회
"""
from typing import Optional, List
from datetime import date, timedelta
from src.domain.entities.block_pattern import BlockPattern
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import BlockPattern as BlockPatternModel


class BlockPatternRepository:
    """블록 패턴 Repository"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def save(self, pattern: BlockPattern) -> int:
        """
        패턴 저장

        Args:
            pattern: BlockPattern 엔티티

        Returns:
            pattern_id (DB에서 할당된 ID)
        """
        with self.db.session_scope() as session:
            if pattern.pattern_id:
                # 업데이트
                existing = session.query(BlockPatternModel).filter_by(
                    pattern_id=pattern.pattern_id
                ).first()

                if existing:
                    existing.ticker = pattern.ticker
                    existing.seed_block1_id = pattern.seed_block1_id
                    existing.seed_block2_id = pattern.seed_block2_id
                    existing.seed_block3_id = pattern.seed_block3_id
                    existing.redetection_start = pattern.redetection_start
                    existing.redetection_end = pattern.redetection_end
                    session.commit()
                    return existing.pattern_id

            # 신규 생성
            pattern_model = BlockPatternModel(
                ticker=pattern.ticker,
                seed_block1_id=pattern.seed_block1_id,
                seed_block2_id=pattern.seed_block2_id,
                seed_block3_id=pattern.seed_block3_id,
                redetection_start=pattern.redetection_start,
                redetection_end=pattern.redetection_end
            )
            session.add(pattern_model)
            session.commit()

            # ID 반환
            return pattern_model.pattern_id

    def find_by_id(self, pattern_id: int) -> Optional[BlockPattern]:
        """
        패턴 ID로 조회

        Args:
            pattern_id: 패턴 ID

        Returns:
            BlockPattern 엔티티 또는 None
        """
        with self.db.session_scope() as session:
            pattern_model = session.query(BlockPatternModel).filter_by(
                pattern_id=pattern_id
            ).first()

            if not pattern_model:
                return None

            return BlockPattern(
                pattern_id=pattern_model.pattern_id,
                ticker=pattern_model.ticker,
                seed_block1_id=pattern_model.seed_block1_id,
                seed_block2_id=pattern_model.seed_block2_id,
                seed_block3_id=pattern_model.seed_block3_id,
                redetection_start=pattern_model.redetection_start,
                redetection_end=pattern_model.redetection_end
            )

    def find_by_ticker(self, ticker: str) -> List[BlockPattern]:
        """
        종목별 모든 패턴 조회

        Args:
            ticker: 종목 코드

        Returns:
            BlockPattern 리스트
        """
        with self.db.session_scope() as session:
            pattern_models = session.query(BlockPatternModel).filter_by(
                ticker=ticker
            ).order_by(BlockPatternModel.redetection_start).all()

            return [
                BlockPattern(
                    pattern_id=p.pattern_id,
                    ticker=p.ticker,
                    seed_block1_id=p.seed_block1_id,
                    seed_block2_id=p.seed_block2_id,
                    seed_block3_id=p.seed_block3_id,
                    redetection_start=p.redetection_start,
                    redetection_end=p.redetection_end
                )
                for p in pattern_models
            ]

    def find_by_seed_block1_id(self, seed_block1_id: str) -> Optional[BlockPattern]:
        """
        Block1 Seed ID로 패턴 조회

        Args:
            seed_block1_id: Block1 Seed ID

        Returns:
            BlockPattern 엔티티 또는 None
        """
        with self.db.session_scope() as session:
            pattern_model = session.query(BlockPatternModel).filter_by(
                seed_block1_id=seed_block1_id
            ).first()

            if not pattern_model:
                return None

            return BlockPattern(
                pattern_id=pattern_model.pattern_id,
                ticker=pattern_model.ticker,
                seed_block1_id=pattern_model.seed_block1_id,
                seed_block2_id=pattern_model.seed_block2_id,
                seed_block3_id=pattern_model.seed_block3_id,
                redetection_start=pattern_model.redetection_start,
                redetection_end=pattern_model.redetection_end
            )

    def delete(self, pattern_id: int) -> bool:
        """
        패턴 삭제

        Args:
            pattern_id: 패턴 ID

        Returns:
            삭제 성공 여부
        """
        with self.db.session_scope() as session:
            pattern = session.query(BlockPatternModel).filter_by(
                pattern_id=pattern_id
            ).first()

            if not pattern:
                return False

            session.delete(pattern)
            session.commit()
            return True
