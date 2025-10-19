"""
Block2 Condition Preset Repository - Block2 조건 프리셋 저장소 (완전한 조건 저장)
"""
from typing import List, Optional
from datetime import datetime

from ...domain.entities.block2_condition import Block2Condition
from ...domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from ..database.connection import DatabaseConnection
from ..database.models import Block2ConditionPreset


class Block2ConditionPresetRepository:
    """Block2 조건 프리셋 저장소 (Block1 조건 포함)"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def save(
        self,
        name: str,
        condition: Block2Condition,
        description: str = None
    ) -> str:
        """
        Block2 조건을 DB에 저장 (Block1 조건 포함)

        Args:
            name: 프리셋 이름
            condition: Block2Condition 엔티티
            description: 설명

        Returns:
            저장된 프리셋 이름
        """
        with self.db.session_scope() as session:
            # 기존 프리셋 확인
            existing = session.query(Block2ConditionPreset).filter_by(name=name).first()

            block1_cond = condition.block1_condition

            if existing:
                # 업데이트
                existing.description = description

                # Block1 조건
                existing.entry_surge_rate = block1_cond.entry_surge_rate
                existing.entry_ma_period = block1_cond.entry_ma_period
                existing.high_above_ma = block1_cond.high_above_ma
                existing.max_deviation_ratio = block1_cond.max_deviation_ratio
                existing.min_trading_value = block1_cond.min_trading_value
                existing.volume_high_months = block1_cond.volume_high_months
                existing.volume_spike_ratio = block1_cond.volume_spike_ratio
                existing.price_high_months = block1_cond.price_high_months
                existing.exit_condition_type = block1_cond.exit_condition_type.value
                existing.exit_ma_period = block1_cond.exit_ma_period

                # Block2 추가 조건
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

                    # Block1 조건
                    entry_surge_rate=block1_cond.entry_surge_rate,
                    entry_ma_period=block1_cond.entry_ma_period,
                    high_above_ma=block1_cond.high_above_ma,
                    max_deviation_ratio=block1_cond.max_deviation_ratio,
                    min_trading_value=block1_cond.min_trading_value,
                    volume_high_months=block1_cond.volume_high_months,
                    volume_spike_ratio=block1_cond.volume_spike_ratio,
                    price_high_months=block1_cond.price_high_months,
                    exit_condition_type=block1_cond.exit_condition_type.value,
                    exit_ma_period=block1_cond.exit_ma_period,

                    # Block2 추가 조건
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

            # Block1 조건 재구성
            block1_condition = Block1Condition(
                entry_surge_rate=preset.entry_surge_rate,
                entry_ma_period=preset.entry_ma_period,
                high_above_ma=preset.high_above_ma,
                max_deviation_ratio=preset.max_deviation_ratio,
                min_trading_value=preset.min_trading_value,
                volume_high_months=preset.volume_high_months,
                volume_spike_ratio=preset.volume_spike_ratio,
                price_high_months=preset.price_high_months,
                exit_condition_type=Block1ExitConditionType(preset.exit_condition_type),
                exit_ma_period=preset.exit_ma_period,
                cooldown_days=preset.cooldown_days  # Block2의 cooldown 사용
            )

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
                    'entry_surge_rate': p.entry_surge_rate,
                    'entry_ma_period': p.entry_ma_period,
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
