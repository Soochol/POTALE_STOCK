"""
Block1 Condition Preset Repository
블록1 조건 프리셋 저장/조회 Repository
"""
from typing import Optional
from datetime import datetime

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import Block1ConditionPreset
from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from .common import bool_to_int, int_to_bool


class Block1ConditionPresetRepository:
    """Block1 조건 프리셋 Repository"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection

    def save(self, name: str, condition: Block1Condition, description: str = None) -> Block1ConditionPreset:
        """
        Block1Condition을 DB에 저장

        Args:
            name: 조건 프리셋 이름
            condition: Block1Condition 엔티티
            description: 조건 설명

        Returns:
            Block1ConditionPreset: 저장된 프리셋
        """
        with self.db_connection.session_scope() as session:
            # 기존 조건이 있으면 업데이트, 없으면 새로 생성
            preset = session.query(Block1ConditionPreset).filter(
                Block1ConditionPreset.name == name
            ).first()

            if preset:
                # 업데이트
                preset.description = description
                preset.entry_surge_rate = condition.entry_surge_rate
                preset.entry_ma_period = condition.entry_ma_period
                preset.high_above_ma = bool_to_int(condition.high_above_ma)
                preset.max_deviation_ratio = condition.max_deviation_ratio
                preset.min_trading_value = condition.min_trading_value
                preset.volume_high_months = condition.volume_high_months
                preset.volume_spike_ratio = condition.volume_spike_ratio
                preset.price_high_months = condition.price_high_months
                preset.exit_condition_type = condition.exit_condition_type.value
                preset.exit_ma_period = condition.exit_ma_period
                preset.cooldown_days = condition.cooldown_days
                preset.updated_at = datetime.now()
            else:
                # 새로 생성
                preset = Block1ConditionPreset(
                    name=name,
                    description=description,
                    entry_surge_rate=condition.entry_surge_rate,
                    entry_ma_period=condition.entry_ma_period,
                    high_above_ma=bool_to_int(condition.high_above_ma),
                    max_deviation_ratio=condition.max_deviation_ratio,
                    min_trading_value=condition.min_trading_value,
                    volume_high_months=condition.volume_high_months,
                    volume_spike_ratio=condition.volume_spike_ratio,
                    price_high_months=condition.price_high_months,
                    exit_condition_type=condition.exit_condition_type.value,
                    exit_ma_period=condition.exit_ma_period,
                    cooldown_days=condition.cooldown_days,
                    is_active=1
                )
                session.add(preset)

            session.commit()
            session.refresh(preset)
            return preset

    def load(self, name: str) -> Optional[Block1Condition]:
        """
        DB에서 조건 프리셋 로드

        Args:
            name: 조건 프리셋 이름

        Returns:
            Block1Condition 또는 None
        """
        with self.db_connection.session_scope() as session:
            preset = session.query(Block1ConditionPreset).filter(
                Block1ConditionPreset.name == name
            ).first()

            if not preset:
                return None

            return self._to_entity(preset)

    def list_all(self, active_only: bool = True) -> List[Block1ConditionPreset]:
        """
        모든 조건 프리셋 조회

        Args:
            active_only: 활성 조건만 조회 여부

        Returns:
            Block1ConditionPreset 리스트
        """
        with self.db_connection.session_scope() as session:
            query = session.query(Block1ConditionPreset)

            if active_only:
                query = query.filter(Block1ConditionPreset.is_active == 1)

            return query.order_by(Block1ConditionPreset.created_at.desc()).all()

    def delete(self, name: str) -> bool:
        """
        조건 프리셋 삭제 (실제로는 비활성화)

        Args:
            name: 조건 프리셋 이름

        Returns:
            성공 여부
        """
        with self.db_connection.session_scope() as session:
            preset = session.query(Block1ConditionPreset).filter(
                Block1ConditionPreset.name == name
            ).first()

            if not preset:
                return False

            preset.is_active = 0
            preset.updated_at = datetime.now()
            session.commit()
            return True

    def _to_entity(self, preset: Block1ConditionPreset) -> Block1Condition:
        """DB 모델을 Block1Condition 엔티티로 변환"""
        return Block1Condition(
            entry_surge_rate=preset.entry_surge_rate,
            entry_ma_period=preset.entry_ma_period,
            high_above_ma=int_to_bool(preset.high_above_ma) if preset.high_above_ma is not None else None,
            max_deviation_ratio=preset.max_deviation_ratio,
            min_trading_value=preset.min_trading_value,
            volume_high_months=preset.volume_high_months,
            volume_spike_ratio=preset.volume_spike_ratio,
            price_high_months=preset.price_high_months,
            exit_condition_type=Block1ExitConditionType(preset.exit_condition_type),
            exit_ma_period=preset.exit_ma_period,
            cooldown_days=preset.cooldown_days
        )
