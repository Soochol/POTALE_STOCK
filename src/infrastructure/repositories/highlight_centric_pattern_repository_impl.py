"""
Highlight-Centric Pattern Repository Implementation

SQLAlchemy-based implementation of HighlightCentricPatternRepository.
"""

import json
import logging
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.domain.repositories.highlight_centric_pattern_repository import (
    HighlightCentricPatternRepository
)
from src.domain.entities.patterns import (
    HighlightCentricPattern,
    PatternStatus,
    BackwardScanResult
)
from src.domain.entities.detections import DynamicBlockDetection
from src.infrastructure.database.models import HighlightCentricPatternModel
from src.infrastructure.repositories.dynamic_block_repository_impl import (
    DynamicBlockRepositoryImpl
)

logger = logging.getLogger(__name__)


class HighlightCentricPatternRepositoryImpl(HighlightCentricPatternRepository):
    """
    SQLAlchemy-based implementation of HighlightCentricPatternRepository.

    Responsibilities:
    - Persist HighlightCentricPattern entities to database
    - Reconstruct entities from database models
    - Handle forward_blocks relationship
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.block_repo = DynamicBlockRepositoryImpl(session)
        logger.debug("HighlightCentricPatternRepositoryImpl initialized")

    # ============================================================
    # Save Operations
    # ============================================================

    def save(self, pattern: HighlightCentricPattern) -> None:
        """Save or update a pattern."""
        try:
            # Check if pattern already exists
            existing = self.session.query(HighlightCentricPatternModel).filter_by(
                pattern_id=pattern.pattern_id
            ).first()

            if existing:
                # Update existing
                self._update_model_from_entity(existing, pattern)
                logger.debug(f"Updated pattern: {pattern.pattern_id}")
            else:
                # Create new
                model = self._create_model_from_entity(pattern)
                self.session.add(model)
                logger.debug(f"Created pattern: {pattern.pattern_id}")

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save pattern {pattern.pattern_id}: {e}", exc_info=True)
            raise

    def save_all(self, patterns: List[HighlightCentricPattern]) -> None:
        """Save multiple patterns (batch operation)."""
        try:
            for pattern in patterns:
                # Check if exists
                existing = self.session.query(HighlightCentricPatternModel).filter_by(
                    pattern_id=pattern.pattern_id
                ).first()

                if existing:
                    self._update_model_from_entity(existing, pattern)
                else:
                    model = self._create_model_from_entity(pattern)
                    self.session.add(model)

            self.session.commit()
            logger.info(f"Saved {len(patterns)} pattern(s)")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save patterns: {e}", exc_info=True)
            raise

    # ============================================================
    # Query Operations
    # ============================================================

    def find_by_id(self, pattern_id: str) -> Optional[HighlightCentricPattern]:
        """Find pattern by ID."""
        model = self.session.query(HighlightCentricPatternModel).filter_by(
            pattern_id=pattern_id
        ).first()

        if model:
            return self._create_entity_from_model(model)
        return None

    def find_by_ticker(
        self,
        ticker: str,
        status: Optional[PatternStatus] = None
    ) -> List[HighlightCentricPattern]:
        """Find patterns by ticker."""
        query = self.session.query(HighlightCentricPatternModel).filter_by(
            ticker=ticker
        )

        if status:
            query = query.filter_by(status=status.value)

        models = query.order_by(HighlightCentricPatternModel.created_at).all()

        return [self._create_entity_from_model(m) for m in models]

    def find_by_date_range(
        self,
        ticker: str,
        from_date: date,
        to_date: date
    ) -> List[HighlightCentricPattern]:
        """Find patterns within date range."""
        # Convert dates to datetime for comparison
        from_dt = datetime.combine(from_date, datetime.min.time())
        to_dt = datetime.combine(to_date, datetime.max.time())

        models = self.session.query(HighlightCentricPatternModel).filter(
            and_(
                HighlightCentricPatternModel.ticker == ticker,
                HighlightCentricPatternModel.created_at >= from_dt,
                HighlightCentricPatternModel.created_at <= to_dt
            )
        ).order_by(HighlightCentricPatternModel.created_at).all()

        return [self._create_entity_from_model(m) for m in models]

    def find_all(
        self,
        status: Optional[PatternStatus] = None,
        limit: Optional[int] = None
    ) -> List[HighlightCentricPattern]:
        """Find all patterns."""
        query = self.session.query(HighlightCentricPatternModel)

        if status:
            query = query.filter_by(status=status.value)

        query = query.order_by(HighlightCentricPatternModel.created_at)

        if limit:
            query = query.limit(limit)

        models = query.all()

        return [self._create_entity_from_model(m) for m in models]

    def count_by_ticker(
        self,
        ticker: str,
        status: Optional[PatternStatus] = None
    ) -> int:
        """Count patterns by ticker."""
        query = self.session.query(HighlightCentricPatternModel).filter_by(
            ticker=ticker
        )

        if status:
            query = query.filter_by(status=status.value)

        return query.count()

    # ============================================================
    # Delete Operations
    # ============================================================

    def delete(self, pattern_id: str) -> bool:
        """Delete pattern by ID."""
        try:
            model = self.session.query(HighlightCentricPatternModel).filter_by(
                pattern_id=pattern_id
            ).first()

            if model:
                self.session.delete(model)
                self.session.commit()
                logger.info(f"Deleted pattern: {pattern_id}")
                return True

            return False

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete pattern {pattern_id}: {e}", exc_info=True)
            raise

    def exists(self, pattern_id: str) -> bool:
        """Check if pattern exists."""
        count = self.session.query(HighlightCentricPatternModel).filter_by(
            pattern_id=pattern_id
        ).count()

        return count > 0

    # ============================================================
    # Entity ↔ Model Conversion
    # ============================================================

    def _create_model_from_entity(
        self,
        pattern: HighlightCentricPattern
    ) -> HighlightCentricPatternModel:
        """Convert entity to database model."""
        # Extract backward scan data
        found_stronger_root = False
        peak_price_ratio = 100  # Default 1.0 as 100

        if pattern.backward_scan_result:
            found_stronger_root = pattern.backward_scan_result.found_stronger_root
            peak_price_ratio = int(pattern.backward_scan_result.peak_price_ratio * 100)

        # Serialize SR analysis to JSON
        sr_analysis_json = None
        if pattern.sr_analysis:
            sr_analysis_json = json.dumps(pattern.sr_analysis)

        # Create model
        model = HighlightCentricPatternModel(
            pattern_id=pattern.pattern_id,
            ticker=pattern.ticker,
            highlight_block_id=pattern.highlight_block.id,
            root_block_id=pattern.root_block.id,
            found_stronger_root=found_stronger_root,
            backward_lookback_days=pattern.backward_scan_result.lookback_days if pattern.backward_scan_result else 30,
            peak_price_ratio=peak_price_ratio,
            forward_scan_days=1125,  # Default
            forward_block_count=len(pattern.forward_blocks),
            sr_analysis=sr_analysis_json,
            status=pattern.status.value,
            created_at=pattern.created_at,
            completed_at=pattern.completed_at
        )

        return model

    def _update_model_from_entity(
        self,
        model: HighlightCentricPatternModel,
        pattern: HighlightCentricPattern
    ) -> None:
        """Update existing model from entity."""
        # Update fields
        model.ticker = pattern.ticker
        model.highlight_block_id = pattern.highlight_block.id
        model.root_block_id = pattern.root_block.id

        # Update backward scan data
        if pattern.backward_scan_result:
            model.found_stronger_root = pattern.backward_scan_result.found_stronger_root
            model.peak_price_ratio = int(pattern.backward_scan_result.peak_price_ratio * 100)
            model.backward_lookback_days = pattern.backward_scan_result.lookback_days

        # Update forward scan data
        model.forward_block_count = len(pattern.forward_blocks)

        # Update SR analysis
        if pattern.sr_analysis:
            model.sr_analysis = json.dumps(pattern.sr_analysis)

        # Update lifecycle
        model.status = pattern.status.value
        model.completed_at = pattern.completed_at

    def _create_entity_from_model(
        self,
        model: HighlightCentricPatternModel
    ) -> HighlightCentricPattern:
        """Reconstruct entity from database model."""
        # Load blocks
        highlight_block = self.block_repo.find_by_id(model.highlight_block_id)
        root_block = self.block_repo.find_by_id(model.root_block_id)

        if not highlight_block or not root_block:
            raise ValueError(
                f"Failed to load blocks for pattern {model.pattern_id}: "
                f"highlight={model.highlight_block_id}, root={model.root_block_id}"
            )

        # Reconstruct backward scan result
        backward_scan_result = None
        if model.found_stronger_root:
            backward_scan_result = BackwardScanResult.with_stronger_root(
                stronger_block=root_block,
                highlight_peak_price=highlight_block.peak_price,
                lookback_days=model.backward_lookback_days
            )
        else:
            backward_scan_result = BackwardScanResult.no_stronger_root(
                lookback_days=model.backward_lookback_days
            )

        # Deserialize SR analysis
        sr_analysis = None
        if model.sr_analysis:
            sr_analysis = json.loads(model.sr_analysis)

        # Load forward blocks (need to query by pattern relationship)
        # For now, we'll leave forward_blocks empty and load on demand
        # TODO: Implement forward_blocks relationship in database

        # Create entity
        pattern = HighlightCentricPattern(
            pattern_id=model.pattern_id,
            ticker=model.ticker,
            highlight_block=highlight_block,
            root_block=root_block,
            backward_scan_result=backward_scan_result,
            forward_blocks=[],  # TODO: Load from database
            sr_analysis=sr_analysis,
            status=PatternStatus(model.status),
            created_at=model.created_at,
            completed_at=model.completed_at
        )

        return pattern
