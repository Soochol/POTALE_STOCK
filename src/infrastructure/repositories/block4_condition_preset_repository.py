"""
Block4 Condition Preset Repository - Block4 조건 프리셋 저장소 (완전한 조건 저장)
"""
from typing import List, Optional
from datetime import datetime

from ...domain.entities.block4_condition import Block4Condition
from ...domain.entities.block3_condition import Block3Condition
from ...domain.entities.block2_condition import Block2Condition
from ...domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from ..database.connection import DatabaseConnection
from ..database.models import Block4ConditionPreset


class Block4ConditionPresetRepository:
    """Block4 조건 프리셋 저장소 (Block1 + Block2 + Block3 조건 포함)"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def save(
        self,
        name: str,
        condition: Block4Condition,
        description: str = None
    ) -> str:
        """
        Block4 조건을 DB에 저장 (Block1 + Block2 + Block3 조건 포함)

        Args:
            name: 프리셋 이름
            condition: Block4Condition 엔티티
            description: 설명

        Returns:
            저장된 프리셋 이름
        """
        with self.db.session_scope() as session:
            # 기존 프리셋 확인
            existing = session.query(Block4ConditionPreset).filter_by(name=name).first()

            block1_cond = condition.block3_condition.block2_condition.block1_condition
            block2_cond = condition.block3_condition.block2_condition
            block3_cond = condition.block3_condition

            if existing:
                # 업데이트
                existing.description = description

                # Block1 조건
                existing.entry_surge_rate = block1_cond.entry_surge_rate
                existing.entry_ma_period = block1_cond.entry_ma_period
                existing.entry_high_above_ma = block1_cond.entry_high_above_ma
                existing.entry_max_deviation_ratio = block1_cond.entry_max_deviation_ratio
                existing.entry_min_trading_value = block1_cond.entry_min_trading_value
                existing.entry_volume_high_months = block1_cond.entry_volume_high_months
                existing.entry_volume_spike_ratio = block1_cond.entry_volume_spike_ratio
                existing.entry_price_high_months = block1_cond.entry_price_high_months
                existing.exit_condition_type = block1_cond.exit_condition_type.value
                existing.exit_ma_period = block1_cond.exit_ma_period

                # Block2 추가 조건
                existing.block2_volume_ratio = block2_cond.block2_volume_ratio
                existing.block2_low_price_margin = block2_cond.block2_low_price_margin
                existing.block2_min_candles_after_block1 = block2_cond.block2_min_candles_after_block1

                # Block3 추가 조건
                existing.block3_volume_ratio = block3_cond.block3_volume_ratio
                existing.block3_low_price_margin = block3_cond.block3_low_price_margin
                existing.block3_min_candles_after_block2 = block3_cond.block3_min_candles_after_block2

                # Block4 추가 조건
                existing.block4_volume_ratio = condition.block4_volume_ratio
                existing.block4_low_price_margin = condition.block4_low_price_margin
                existing.block4_min_candles_after_block3 = condition.block4_min_candles_after_block3
                existing.cooldown_days = block2_cond.cooldown_days

                existing.updated_at = datetime.now()
                existing.is_active = 1

                session.commit()
                return name
            else:
                # 새로 생성
                preset = Block4ConditionPreset(
                    name=name,
                    description=description,

                    # Block1 조건
                    entry_surge_rate=block1_cond.entry_surge_rate,
                    entry_ma_period=block1_cond.entry_ma_period,
                    entry_high_above_ma=block1_cond.entry_high_above_ma,
                    entry_max_deviation_ratio=block1_cond.entry_max_deviation_ratio,
                    entry_min_trading_value=block1_cond.entry_min_trading_value,
                    entry_volume_high_months=block1_cond.entry_volume_high_months,
                    entry_volume_spike_ratio=block1_cond.entry_volume_spike_ratio,
                    entry_price_high_months=block1_cond.entry_price_high_months,
                    exit_condition_type=block1_cond.exit_condition_type.value,
                    exit_ma_period=block1_cond.exit_ma_period,

                    # Block2 추가 조건
                    block2_volume_ratio=block2_cond.block2_volume_ratio,
                    block2_low_price_margin=block2_cond.block2_low_price_margin,
                    block2_min_candles_after_block1=block2_cond.block2_min_candles_after_block1,

                    # Block3 추가 조건
                    block3_volume_ratio=block3_cond.block3_volume_ratio,
                    block3_low_price_margin=block3_cond.block3_low_price_margin,
                    block3_min_candles_after_block2=block3_cond.block3_min_candles_after_block2,

                    # Block4 추가 조건
                    block4_volume_ratio=condition.block4_volume_ratio,
                    block4_low_price_margin=condition.block4_low_price_margin,
                    block4_min_candles_after_block3=condition.block4_min_candles_after_block3,
                    cooldown_days=block2_cond.cooldown_days,

                    is_active=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                session.add(preset)
                session.commit()
                return name

    def load(self, name: str) -> Optional[Block4Condition]:
        """
        DB에서 Block4 조건 로드

        Args:
            name: 프리셋 이름

        Returns:
            Block4Condition 엔티티 또는 None
        """
        with self.db.session_scope() as session:
            preset = session.query(Block4ConditionPreset).filter_by(
                name=name,
                is_active=1
            ).first()

            if not preset:
                return None

            # Block1 조건 재구성
            block1_condition = Block1Condition(
                entry_surge_rate=preset.entry_surge_rate,
                entry_ma_period=preset.entry_ma_period,
                entry_high_above_ma=preset.entry_high_above_ma,
                entry_max_deviation_ratio=preset.entry_max_deviation_ratio,
                entry_min_trading_value=preset.entry_min_trading_value,
                entry_volume_high_months=preset.entry_volume_high_months,
                entry_volume_spike_ratio=preset.entry_volume_spike_ratio,
                entry_price_high_months=preset.entry_price_high_months,
                exit_condition_type=Block1ExitConditionType(preset.exit_condition_type),
                exit_ma_period=preset.exit_ma_period,
                cooldown_days=preset.cooldown_days
            )

            # Block2 조건 재구성
            block2_condition = Block2Condition(
                block1_condition=block1_condition,
                block2_volume_ratio=preset.block2_volume_ratio,
                block2_low_price_margin=preset.block2_low_price_margin,
                cooldown_days=preset.cooldown_days,
                block2_min_candles_after_block1=preset.block2_min_candles_after_block1
            )

            # Block3 조건 재구성
            block3_condition = Block3Condition(
                block2_condition=block2_condition,
                block3_volume_ratio=preset.block3_volume_ratio,
                block3_low_price_margin=preset.block3_low_price_margin,
                block3_min_candles_after_block2=preset.block3_min_candles_after_block2
            )

            # Block4Condition 엔티티 생성
            return Block4Condition(
                block3_condition=block3_condition,
                block4_volume_ratio=preset.block4_volume_ratio,
                block4_low_price_margin=preset.block4_low_price_margin,
                block4_min_candles_after_block3=preset.block4_min_candles_after_block3
            )

    def list_all(self, active_only: bool = True) -> List[dict]:
        """
        모든 Block4 프리셋 조회

        Args:
            active_only: True이면 활성 프리셋만, False면 모두

        Returns:
            프리셋 정보 리스트
        """
        with self.db.session_scope() as session:
            query = session.query(Block4ConditionPreset)

            if active_only:
                query = query.filter_by(is_active=1)

            presets = query.order_by(Block4ConditionPreset.name).all()

            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'entry_surge_rate': p.entry_surge_rate,
                    'entry_ma_period': p.entry_ma_period,
                    'block2_volume_ratio': p.block2_volume_ratio,
                    'block2_low_price_margin': p.block2_low_price_margin,
                    'block2_min_candles_after_block1': p.block2_min_candles_after_block1,
                    'block3_volume_ratio': p.block3_volume_ratio,
                    'block3_low_price_margin': p.block3_low_price_margin,
                    'block3_min_candles_after_block2': p.block3_min_candles_after_block2,
                    'block4_volume_ratio': p.block4_volume_ratio,
                    'block4_low_price_margin': p.block4_low_price_margin,
                    'block4_min_candles_after_block3': p.block4_min_candles_after_block3,
                    'cooldown_days': p.cooldown_days,
                    'is_active': p.is_active,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at
                }
                for p in presets
            ]

    def delete(self, name: str) -> bool:
        """
        Block4 프리셋 삭제 (Soft Delete)

        Args:
            name: 프리셋 이름

        Returns:
            삭제 성공 여부
        """
        with self.db.session_scope() as session:
            preset = session.query(Block4ConditionPreset).filter_by(name=name).first()

            if not preset:
                return False

            preset.is_active = 0
            preset.updated_at = datetime.now()

            session.commit()
            return True

    def exists(self, name: str) -> bool:
        """
        Block4 프리셋 존재 여부 확인

        Args:
            name: 프리셋 이름

        Returns:
            존재 여부
        """
        with self.db.session_scope() as session:
            count = session.query(Block4ConditionPreset).filter_by(
                name=name,
                is_active=1
            ).count()
            return count > 0
