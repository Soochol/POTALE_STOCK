"""
Block1 Condition Preset Repository
블록1 조건 프리셋 저장/조회 Repository
"""
from typing import List, Optional
from datetime import datetime

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import Block1ConditionPreset
from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType


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
        session = self.db_connection.get_session()

        try:
            # 기존 조건이 있으면 업데이트, 없으면 새로 생성
            preset = session.query(Block1ConditionPreset).filter(
                Block1ConditionPreset.name == name
            ).first()

            if preset:
                # 업데이트
                preset.description = description
                preset.entry_surge_rate = condition.entry_surge_rate
                preset.entry_ma_period = condition.entry_ma_period
                preset.high_above_ma = self._bool_to_int(condition.high_above_ma)
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
                    high_above_ma=self._bool_to_int(condition.high_above_ma),
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

        except Exception as e:
            session.rollback()
            raise Exception(f"조건 프리셋 저장 실패: {e}")
        finally:
            session.close()

    def load(self, name: str) -> Optional[Block1Condition]:
        """
        DB에서 조건 프리셋 로드

        Args:
            name: 조건 프리셋 이름

        Returns:
            Block1Condition 또는 None
        """
        session = self.db_connection.get_session()

        try:
            preset = session.query(Block1ConditionPreset).filter(
                Block1ConditionPreset.name == name
            ).first()

            if not preset:
                return None

            return self._to_entity(preset)

        finally:
            session.close()

    def list_all(self, active_only: bool = True) -> List[Block1ConditionPreset]:
        """
        모든 조건 프리셋 조회

        Args:
            active_only: 활성 조건만 조회 여부

        Returns:
            Block1ConditionPreset 리스트
        """
        session = self.db_connection.get_session()

        try:
            query = session.query(Block1ConditionPreset)

            if active_only:
                query = query.filter(Block1ConditionPreset.is_active == 1)

            return query.order_by(Block1ConditionPreset.created_at.desc()).all()

        finally:
            session.close()

    def delete(self, name: str) -> bool:
        """
        조건 프리셋 삭제 (실제로는 비활성화)

        Args:
            name: 조건 프리셋 이름

        Returns:
            성공 여부
        """
        session = self.db_connection.get_session()

        try:
            preset = session.query(Block1ConditionPreset).filter(
                Block1ConditionPreset.name == name
            ).first()

            if not preset:
                return False

            preset.is_active = 0
            preset.updated_at = datetime.now()
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise Exception(f"조건 프리셋 삭제 실패: {e}")
        finally:
            session.close()

    def _to_entity(self, preset: Block1ConditionPreset) -> Block1Condition:
        """DB 모델을 Block1Condition 엔티티로 변환"""
        return Block1Condition(
            entry_surge_rate=preset.entry_surge_rate,
            entry_ma_period=preset.entry_ma_period,
            high_above_ma=self._int_to_bool(preset.high_above_ma),
            max_deviation_ratio=preset.max_deviation_ratio,
            min_trading_value=preset.min_trading_value,
            volume_high_months=preset.volume_high_months,
            volume_spike_ratio=preset.volume_spike_ratio,
            price_high_months=preset.price_high_months,
            exit_condition_type=Block1ExitConditionType(preset.exit_condition_type),
            exit_ma_period=preset.exit_ma_period,
            cooldown_days=preset.cooldown_days
        )

    @staticmethod
    def _bool_to_int(value: Optional[bool]) -> Optional[int]:
        """bool을 int로 변환 (None은 None 유지)"""
        if value is None:
            return None
        return 1 if value else 0

    @staticmethod
    def _int_to_bool(value: Optional[int]) -> Optional[bool]:
        """int를 bool로 변환 (None은 None 유지)"""
        if value is None:
            return None
        return value == 1
