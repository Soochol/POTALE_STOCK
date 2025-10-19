"""
Block2 Condition Preset Repository - Block2 조건 프리셋 저장소
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import update, and_
from sqlalchemy.exc import IntegrityError

from ...domain.entities.block2_condition import Block2Condition
from ...domain.entities.block1_condition import Block1Condition
from ..database.connection import DatabaseConnection
from ..database.models import Block2ConditionPreset
from .block1_condition_preset_repository import Block1ConditionPresetRepository


class Block2ConditionPresetRepository:
    """Block2 조건 프리셋 저장소"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.block1_preset_repo = Block1ConditionPresetRepository(db_connection)

    def save(
        self,
        name: str,
        condition: Block2Condition,
        block1_preset_name: str,
        description: str = None
    ) -> str:
        """
        Block2 조건을 DB에 저장

        Args:
            name: 프리셋 이름
            condition: Block2Condition 엔티티
            block1_preset_name: Block1 프리셋 이름
            description: 설명

        Returns:
            저장된 프리셋 이름
        """
        with self.db.session_scope() as session:
            # 기존 프리셋 확인
            existing = session.query(Block2ConditionPreset).filter_by(name=name).first()

            if existing:
                # 업데이트
                existing.description = description
                existing.block1_preset_name = block1_preset_name
                existing.block_volume_ratio = condition.block_volume_ratio
                existing.low_price_margin = condition.low_price_margin
                existing.cooldown_days = condition.cooldown_days
                existing.min_candles_after_block1 = condition.min_candles_after_block1
                existing.updated_at = datetime.now()
                existing.is_active = 1

                session.commit()
                return name
            else:
                # 새로 생성
                preset = Block2ConditionPreset(
                    name=name,
                    description=description,
                    block1_preset_name=block1_preset_name,
                    block_volume_ratio=condition.block_volume_ratio,
                    low_price_margin=condition.low_price_margin,
                    cooldown_days=condition.cooldown_days,
                    min_candles_after_block1=condition.min_candles_after_block1,
                    is_active=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                session.add(preset)
                session.commit()
                return name

    def load(self, name: str) -> Optional[Block2Condition]:
        """
        DB에서 Block2 조건 로드

        Args:
            name: 프리셋 이름

        Returns:
            Block2Condition 엔티티 또는 None
        """
        with self.db.session_scope() as session:
            preset = session.query(Block2ConditionPreset).filter_by(
                name=name,
                is_active=1
            ).first()

            if not preset:
                return None

            # Block1 조건 로드
            block1_condition = self.block1_preset_repo.load(preset.block1_preset_name)
            if not block1_condition:
                raise ValueError(f"Block1 프리셋 '{preset.block1_preset_name}'을 찾을 수 없습니다.")

            # Block2Condition 엔티티 생성
            return Block2Condition(
                block1_condition=block1_condition,
                block_volume_ratio=preset.block_volume_ratio,
                low_price_margin=preset.low_price_margin,
                cooldown_days=preset.cooldown_days,
                min_candles_after_block1=preset.min_candles_after_block1
            )

    def list_all(self, active_only: bool = True) -> List[dict]:
        """
        모든 Block2 프리셋 조회

        Args:
            active_only: True이면 활성 프리셋만, False면 모두

        Returns:
            프리셋 정보 리스트
        """
        with self.db.session_scope() as session:
            query = session.query(Block2ConditionPreset)

            if active_only:
                query = query.filter_by(is_active=1)

            presets = query.order_by(Block2ConditionPreset.name).all()

            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'block1_preset_name': p.block1_preset_name,
                    'block_volume_ratio': p.block_volume_ratio,
                    'low_price_margin': p.low_price_margin,
                    'cooldown_days': p.cooldown_days,
                    'min_candles_after_block1': p.min_candles_after_block1,
                    'is_active': p.is_active,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at
                }
                for p in presets
            ]

    def delete(self, name: str) -> bool:
        """
        Block2 프리셋 삭제 (Soft Delete)

        Args:
            name: 프리셋 이름

        Returns:
            삭제 성공 여부
        """
        with self.db.session_scope() as session:
            preset = session.query(Block2ConditionPreset).filter_by(name=name).first()

            if not preset:
                return False

            preset.is_active = 0
            preset.updated_at = datetime.now()

            session.commit()
            return True

    def exists(self, name: str) -> bool:
        """
        Block2 프리셋 존재 여부 확인

        Args:
            name: 프리셋 이름

        Returns:
            존재 여부
        """
        with self.db.session_scope() as session:
            count = session.query(Block2ConditionPreset).filter_by(
                name=name,
                is_active=1
            ).count()
            return count > 0
