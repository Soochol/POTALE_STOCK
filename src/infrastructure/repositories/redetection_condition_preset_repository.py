"""
Redetection Condition Preset Repository

재탐지 조건 프리셋 저장/조회
"""
from typing import Optional, List
from src.domain.entities.redetection_condition import RedetectionCondition
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
                existing.entry_surge_rate = condition.entry_surge_rate
                existing.entry_ma_period = condition.entry_ma_period
                existing.entry_high_above_ma = 1 if condition.entry_high_above_ma else 0
                existing.entry_max_deviation_ratio = condition.entry_max_deviation_ratio
                existing.entry_min_trading_value = condition.entry_min_trading_value
                existing.entry_volume_high_months = condition.entry_volume_high_months
                existing.entry_volume_spike_ratio = condition.entry_volume_spike_ratio
                existing.entry_price_high_months = condition.entry_price_high_months
                existing.block1_tolerance_pct = condition.block1_tolerance_pct
                existing.block2_tolerance_pct = condition.block2_tolerance_pct
                existing.block3_tolerance_pct = condition.block3_tolerance_pct
                existing.block4_tolerance_pct = condition.block4_tolerance_pct
                existing.exit_condition_type = condition.exit_condition_type.value
                existing.exit_ma_period = condition.exit_ma_period
                existing.cooldown_days = condition.cooldown_days
                existing.block2_volume_ratio = condition.block2_volume_ratio
                existing.block2_low_price_margin = condition.block2_low_price_margin
                existing.block2_min_candles_after_block1 = condition.block2_min_candles_after_block1
                existing.block3_volume_ratio = condition.block3_volume_ratio
                existing.block3_low_price_margin = condition.block3_low_price_margin
                existing.block3_min_candles_after_block2 = condition.block3_min_candles_after_block2
                existing.block4_volume_ratio = condition.block4_volume_ratio
                existing.block4_low_price_margin = condition.block4_low_price_margin
                existing.block4_min_candles_after_block3 = condition.block4_min_candles_after_block3
            else:
                # 신규 생성
                preset = RedetectionConditionPreset(
                    name=name,
                    description=description,
                    entry_surge_rate=condition.entry_surge_rate,
                    entry_ma_period=condition.entry_ma_period,
                    entry_high_above_ma=1 if condition.entry_high_above_ma else 0,
                    entry_max_deviation_ratio=condition.entry_max_deviation_ratio,
                    entry_min_trading_value=condition.entry_min_trading_value,
                    entry_volume_high_months=condition.entry_volume_high_months,
                    entry_volume_spike_ratio=condition.entry_volume_spike_ratio,
                    entry_price_high_months=condition.entry_price_high_months,
                    block1_tolerance_pct=condition.block1_tolerance_pct,
                    block2_tolerance_pct=condition.block2_tolerance_pct,
                    block3_tolerance_pct=condition.block3_tolerance_pct,
                    block4_tolerance_pct=condition.block4_tolerance_pct,
                    exit_condition_type=condition.exit_condition_type.value,
                    exit_ma_period=condition.exit_ma_period,
                    cooldown_days=condition.cooldown_days,
                    block2_volume_ratio=condition.block2_volume_ratio,
                    block2_low_price_margin=condition.block2_low_price_margin,
                    block2_min_candles_after_block1=condition.block2_min_candles_after_block1,
                    block3_volume_ratio=condition.block3_volume_ratio,
                    block3_low_price_margin=condition.block3_low_price_margin,
                    block3_min_candles_after_block2=condition.block3_min_candles_after_block2,
                    block4_volume_ratio=condition.block4_volume_ratio,
                    block4_low_price_margin=condition.block4_low_price_margin,
                    block4_min_candles_after_block3=condition.block4_min_candles_after_block3
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

            return RedetectionCondition(
                entry_surge_rate=preset.entry_surge_rate,
                entry_ma_period=preset.entry_ma_period,
                entry_high_above_ma=bool(preset.entry_high_above_ma),
                entry_max_deviation_ratio=preset.entry_max_deviation_ratio,
                entry_min_trading_value=preset.entry_min_trading_value,
                entry_volume_high_months=preset.entry_volume_high_months,
                entry_volume_spike_ratio=preset.entry_volume_spike_ratio,
                entry_price_high_months=preset.entry_price_high_months,
                block1_tolerance_pct=preset.block1_tolerance_pct,
                block2_tolerance_pct=preset.block2_tolerance_pct,
                block3_tolerance_pct=preset.block3_tolerance_pct,
                block4_tolerance_pct=preset.block4_tolerance_pct,
                exit_condition_type=Block1ExitConditionType(preset.exit_condition_type),
                exit_ma_period=preset.exit_ma_period,
                cooldown_days=preset.cooldown_days,
                block2_volume_ratio=preset.block2_volume_ratio,
                block2_low_price_margin=preset.block2_low_price_margin,
                block2_min_candles_after_block1=preset.block2_min_candles_after_block1,
                block3_volume_ratio=preset.block3_volume_ratio,
                block3_low_price_margin=preset.block3_low_price_margin,
                block3_min_candles_after_block2=preset.block3_min_candles_after_block2,
                block4_volume_ratio=preset.block4_volume_ratio,
                block4_low_price_margin=preset.block4_low_price_margin,
                block4_min_candles_after_block3=preset.block4_min_candles_after_block3
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
