"""
Redetection Condition Preset Repository

재탐지 조건 프리셋 저장/조회
"""
from typing import Optional, List
from src.domain.entities.redetection_condition import RedetectionCondition
from src.domain.entities.base_entry_condition import BaseEntryCondition
from src.domain.entities.block1_condition import Block1ExitConditionType
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import RedetectionConditionPreset


class RedetectionConditionPresetRepository:
    """재탐지 조건 프리셋 Repository"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def save(self, name: str, condition: RedetectionCondition, description: str = None) -> str:
        """
        재탐지 조건 프리셋 저장

        Args:
            name: 프리셋 이름
            condition: RedetectionCondition 엔티티
            description: 설명

        Returns:
            저장된 프리셋 이름
        """
        with self.db.session_scope() as session:
            # 기존 프리셋 확인
            existing = session.query(RedetectionConditionPreset).filter_by(name=name).first()

            if existing:
                # 업데이트
                existing.description = description
                existing.entry_surge_rate = condition.base.block1_entry_surge_rate
                existing.entry_ma_period = condition.base.block1_entry_ma_period
                existing.entry_high_above_ma = 1 if condition.base.block1_entry_high_above_ma else 0
                existing.entry_max_deviation_ratio = condition.base.block1_entry_max_deviation_ratio
                existing.entry_min_trading_value = condition.base.block1_entry_min_trading_value
                existing.entry_volume_high_months = condition.base.block1_entry_volume_high_months
                existing.entry_volume_spike_ratio = condition.base.block1_entry_volume_spike_ratio
                existing.entry_price_high_months = condition.base.block1_entry_price_high_months
                existing.block1_tolerance_pct = condition.block1_tolerance_pct
                existing.block2_tolerance_pct = condition.block2_tolerance_pct
                existing.block3_tolerance_pct = condition.block3_tolerance_pct
                existing.block4_tolerance_pct = condition.block4_tolerance_pct
                existing.exit_condition_type = condition.base.block1_exit_condition_type.value
                existing.exit_ma_period = condition.base.block1_exit_ma_period
                existing.cooldown_days = condition.base.block1_cooldown_days
                existing.block2_volume_ratio = condition.block2_volume_ratio
                existing.block2_low_price_margin = condition.block2_low_price_margin
                existing.block2_min_candles_after_block1 = condition.block2_min_candles_after_block1
                existing.block3_volume_ratio = condition.block3_volume_ratio
                existing.block3_low_price_margin = condition.block3_low_price_margin
                existing.block3_min_candles_after_block2 = condition.block3_min_candles_after_block2
                existing.block4_volume_ratio = condition.block4_volume_ratio
                existing.block4_low_price_margin = condition.block4_low_price_margin
                existing.block4_min_candles_after_block3 = condition.block4_min_candles_after_block3
                # Block2 전용 파라미터
                existing.block2_entry_surge_rate = condition.block2_entry_surge_rate
                existing.block2_entry_ma_period = condition.block2_entry_ma_period
                existing.block2_entry_high_above_ma = 1 if condition.block2_entry_high_above_ma else (0 if condition.block2_entry_high_above_ma is False else None)
                existing.block2_entry_max_deviation_ratio = condition.block2_entry_max_deviation_ratio
                existing.block2_entry_min_trading_value = condition.block2_entry_min_trading_value
                existing.block2_entry_volume_high_months = condition.block2_entry_volume_high_months
                existing.block2_entry_volume_spike_ratio = condition.block2_entry_volume_spike_ratio
                existing.block2_entry_price_high_months = condition.block2_entry_price_high_months
                existing.block2_exit_condition_type = condition.block2_exit_condition_type.value if condition.block2_exit_condition_type else None
                existing.block2_exit_ma_period = condition.block2_exit_ma_period
                existing.block2_cooldown_days = condition.block2_cooldown_days
                # Block3 전용 파라미터
                existing.block3_entry_surge_rate = condition.block3_entry_surge_rate
                existing.block3_entry_ma_period = condition.block3_entry_ma_period
                existing.block3_entry_high_above_ma = 1 if condition.block3_entry_high_above_ma else (0 if condition.block3_entry_high_above_ma is False else None)
                existing.block3_entry_max_deviation_ratio = condition.block3_entry_max_deviation_ratio
                existing.block3_entry_min_trading_value = condition.block3_entry_min_trading_value
                existing.block3_entry_volume_high_months = condition.block3_entry_volume_high_months
                existing.block3_entry_volume_spike_ratio = condition.block3_entry_volume_spike_ratio
                existing.block3_entry_price_high_months = condition.block3_entry_price_high_months
                existing.block3_exit_condition_type = condition.block3_exit_condition_type.value if condition.block3_exit_condition_type else None
                existing.block3_exit_ma_period = condition.block3_exit_ma_period
                existing.block3_cooldown_days = condition.block3_cooldown_days
                # Block4 전용 파라미터
                existing.block4_entry_surge_rate = condition.block4_entry_surge_rate
                existing.block4_entry_ma_period = condition.block4_entry_ma_period
                existing.block4_entry_high_above_ma = 1 if condition.block4_entry_high_above_ma else (0 if condition.block4_entry_high_above_ma is False else None)
                existing.block4_entry_max_deviation_ratio = condition.block4_entry_max_deviation_ratio
                existing.block4_entry_min_trading_value = condition.block4_entry_min_trading_value
                existing.block4_entry_volume_high_months = condition.block4_entry_volume_high_months
                existing.block4_entry_volume_spike_ratio = condition.block4_entry_volume_spike_ratio
                existing.block4_entry_price_high_months = condition.block4_entry_price_high_months
                existing.block4_exit_condition_type = condition.block4_exit_condition_type.value if condition.block4_exit_condition_type else None
                existing.block4_exit_ma_period = condition.block4_exit_ma_period
                existing.block4_cooldown_days = condition.block4_cooldown_days
            else:
                # 신규 생성
                preset = RedetectionConditionPreset(
                    name=name,
                    description=description,
                    block1_entry_surge_rate=condition.base.block1_entry_surge_rate,
                    block1_entry_ma_period=condition.base.block1_entry_ma_period,
                    block1_entry_high_above_ma=1 if condition.base.block1_entry_high_above_ma else 0,
                    block1_entry_max_deviation_ratio=condition.base.block1_entry_max_deviation_ratio,
                    block1_entry_min_trading_value=condition.base.block1_entry_min_trading_value,
                    block1_entry_volume_high_months=condition.base.block1_entry_volume_high_months,
                    block1_entry_volume_spike_ratio=condition.base.block1_entry_volume_spike_ratio,
                    block1_entry_price_high_months=condition.base.block1_entry_price_high_months,
                    block1_tolerance_pct=condition.block1_tolerance_pct,
                    block2_tolerance_pct=condition.block2_tolerance_pct,
                    block3_tolerance_pct=condition.block3_tolerance_pct,
                    block4_tolerance_pct=condition.block4_tolerance_pct,
                    block1_exit_condition_type=condition.base.block1_exit_condition_type.value,
                    block1_exit_ma_period=condition.base.block1_exit_ma_period,
                    block1_cooldown_days=condition.base.block1_cooldown_days,
                    block2_volume_ratio=condition.block2_volume_ratio,
                    block2_low_price_margin=condition.block2_low_price_margin,
                    block2_min_candles_after_block1=condition.block2_min_candles_after_block1,
                    block3_volume_ratio=condition.block3_volume_ratio,
                    block3_low_price_margin=condition.block3_low_price_margin,
                    block3_min_candles_after_block2=condition.block3_min_candles_after_block2,
                    block4_volume_ratio=condition.block4_volume_ratio,
                    block4_low_price_margin=condition.block4_low_price_margin,
                    block4_min_candles_after_block3=condition.block4_min_candles_after_block3,
                    # Block2 전용 파라미터
                    block2_entry_surge_rate=condition.block2_entry_surge_rate,
                    block2_entry_ma_period=condition.block2_entry_ma_period,
                    block2_entry_high_above_ma=1 if condition.block2_entry_high_above_ma else (0 if condition.block2_entry_high_above_ma is False else None),
                    block2_entry_max_deviation_ratio=condition.block2_entry_max_deviation_ratio,
                    block2_entry_min_trading_value=condition.block2_entry_min_trading_value,
                    block2_entry_volume_high_months=condition.block2_entry_volume_high_months,
                    block2_entry_volume_spike_ratio=condition.block2_entry_volume_spike_ratio,
                    block2_entry_price_high_months=condition.block2_entry_price_high_months,
                    block2_exit_condition_type=condition.block2_exit_condition_type.value if condition.block2_exit_condition_type else None,
                    block2_exit_ma_period=condition.block2_exit_ma_period,
                    block2_cooldown_days=condition.block2_cooldown_days,
                    # Block3 전용 파라미터
                    block3_entry_surge_rate=condition.block3_entry_surge_rate,
                    block3_entry_ma_period=condition.block3_entry_ma_period,
                    block3_entry_high_above_ma=1 if condition.block3_entry_high_above_ma else (0 if condition.block3_entry_high_above_ma is False else None),
                    block3_entry_max_deviation_ratio=condition.block3_entry_max_deviation_ratio,
                    block3_entry_min_trading_value=condition.block3_entry_min_trading_value,
                    block3_entry_volume_high_months=condition.block3_entry_volume_high_months,
                    block3_entry_volume_spike_ratio=condition.block3_entry_volume_spike_ratio,
                    block3_entry_price_high_months=condition.block3_entry_price_high_months,
                    block3_exit_condition_type=condition.block3_exit_condition_type.value if condition.block3_exit_condition_type else None,
                    block3_exit_ma_period=condition.block3_exit_ma_period,
                    block3_cooldown_days=condition.block3_cooldown_days,
                    # Block4 전용 파라미터
                    block4_entry_surge_rate=condition.block4_entry_surge_rate,
                    block4_entry_ma_period=condition.block4_entry_ma_period,
                    block4_entry_high_above_ma=1 if condition.block4_entry_high_above_ma else (0 if condition.block4_entry_high_above_ma is False else None),
                    block4_entry_max_deviation_ratio=condition.block4_entry_max_deviation_ratio,
                    block4_entry_min_trading_value=condition.block4_entry_min_trading_value,
                    block4_entry_volume_high_months=condition.block4_entry_volume_high_months,
                    block4_entry_volume_spike_ratio=condition.block4_entry_volume_spike_ratio,
                    block4_entry_price_high_months=condition.block4_entry_price_high_months,
                    block4_exit_condition_type=condition.block4_exit_condition_type.value if condition.block4_exit_condition_type else None,
                    block4_exit_ma_period=condition.block4_exit_ma_period,
                    block4_cooldown_days=condition.block4_cooldown_days
                )
                session.add(preset)

            session.commit()
            return name

    def load(self, name: str) -> Optional[RedetectionCondition]:
        """
        재탐지 조건 프리셋 로드

        Args:
            name: 프리셋 이름

        Returns:
            RedetectionCondition 엔티티 또는 None
        """
        with self.db.session_scope() as session:
            preset = session.query(RedetectionConditionPreset).filter_by(name=name).first()

            if not preset:
                return None

            # BaseEntryCondition 생성
            base = BaseEntryCondition(
                block1_entry_surge_rate=preset.block1_entry_surge_rate,
                block1_entry_ma_period=preset.block1_entry_ma_period,
                block1_entry_high_above_ma=bool(preset.block1_entry_high_above_ma),
                block1_entry_max_deviation_ratio=preset.block1_entry_max_deviation_ratio,
                block1_entry_min_trading_value=preset.block1_entry_min_trading_value,
                block1_entry_volume_high_months=preset.block1_entry_volume_high_months,
                block1_entry_volume_spike_ratio=preset.block1_entry_volume_spike_ratio,
                block1_entry_price_high_months=preset.block1_entry_price_high_months,
                block1_exit_condition_type=Block1ExitConditionType(preset.block1_exit_condition_type),
                block1_exit_ma_period=preset.block1_exit_ma_period,
                block1_cooldown_days=preset.block1_cooldown_days
            )

            return RedetectionCondition(
                base=base,
                block1_tolerance_pct=preset.block1_tolerance_pct,
                block2_tolerance_pct=preset.block2_tolerance_pct,
                block3_tolerance_pct=preset.block3_tolerance_pct,
                block4_tolerance_pct=preset.block4_tolerance_pct,
                block2_volume_ratio=preset.block2_volume_ratio,
                block2_low_price_margin=preset.block2_low_price_margin,
                block2_min_candles_after_block1=preset.block2_min_candles_after_block1,
                block3_volume_ratio=preset.block3_volume_ratio,
                block3_low_price_margin=preset.block3_low_price_margin,
                block3_min_candles_after_block2=preset.block3_min_candles_after_block2,
                block4_volume_ratio=preset.block4_volume_ratio,
                block4_low_price_margin=preset.block4_low_price_margin,
                block4_min_candles_after_block3=preset.block4_min_candles_after_block3,
                # Block2 전용 파라미터
                block2_entry_surge_rate=preset.block2_entry_surge_rate,
                block2_entry_ma_period=preset.block2_entry_ma_period,
                block2_entry_high_above_ma=bool(preset.block2_entry_high_above_ma) if preset.block2_entry_high_above_ma is not None else None,
                block2_entry_max_deviation_ratio=preset.block2_entry_max_deviation_ratio,
                block2_entry_min_trading_value=preset.block2_entry_min_trading_value,
                block2_entry_volume_high_months=preset.block2_entry_volume_high_months,
                block2_entry_volume_spike_ratio=preset.block2_entry_volume_spike_ratio,
                block2_entry_price_high_months=preset.block2_entry_price_high_months,
                block2_exit_condition_type=Block1ExitConditionType(preset.block2_exit_condition_type) if preset.block2_exit_condition_type else None,
                block2_exit_ma_period=preset.block2_exit_ma_period,
                block2_cooldown_days=preset.block2_cooldown_days,
                # Block3 전용 파라미터
                block3_entry_surge_rate=preset.block3_entry_surge_rate,
                block3_entry_ma_period=preset.block3_entry_ma_period,
                block3_entry_high_above_ma=bool(preset.block3_entry_high_above_ma) if preset.block3_entry_high_above_ma is not None else None,
                block3_entry_max_deviation_ratio=preset.block3_entry_max_deviation_ratio,
                block3_entry_min_trading_value=preset.block3_entry_min_trading_value,
                block3_entry_volume_high_months=preset.block3_entry_volume_high_months,
                block3_entry_volume_spike_ratio=preset.block3_entry_volume_spike_ratio,
                block3_entry_price_high_months=preset.block3_entry_price_high_months,
                block3_exit_condition_type=Block1ExitConditionType(preset.block3_exit_condition_type) if preset.block3_exit_condition_type else None,
                block3_exit_ma_period=preset.block3_exit_ma_period,
                block3_cooldown_days=preset.block3_cooldown_days,
                # Block4 전용 파라미터
                block4_entry_surge_rate=preset.block4_entry_surge_rate,
                block4_entry_ma_period=preset.block4_entry_ma_period,
                block4_entry_high_above_ma=bool(preset.block4_entry_high_above_ma) if preset.block4_entry_high_above_ma is not None else None,
                block4_entry_max_deviation_ratio=preset.block4_entry_max_deviation_ratio,
                block4_entry_min_trading_value=preset.block4_entry_min_trading_value,
                block4_entry_volume_high_months=preset.block4_entry_volume_high_months,
                block4_entry_volume_spike_ratio=preset.block4_entry_volume_spike_ratio,
                block4_entry_price_high_months=preset.block4_entry_price_high_months,
                block4_exit_condition_type=Block1ExitConditionType(preset.block4_exit_condition_type) if preset.block4_exit_condition_type else None,
                block4_exit_ma_period=preset.block4_exit_ma_period,
                block4_cooldown_days=preset.block4_cooldown_days
            )

    def list_all(self) -> List[str]:
        """모든 프리셋 이름 조회"""
        with self.db.session_scope() as session:
            presets = session.query(RedetectionConditionPreset).filter_by(is_active=1).all()
            return [p.name for p in presets]

    def delete(self, name: str) -> bool:
        """
        프리셋 삭제 (soft delete)

        Args:
            name: 프리셋 이름

        Returns:
            삭제 성공 여부
        """
        with self.db.session_scope() as session:
            preset = session.query(RedetectionConditionPreset).filter_by(name=name).first()

            if not preset:
                return False

            preset.is_active = 0
            session.commit()
            return True
