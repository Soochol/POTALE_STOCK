"""
Seed Condition Preset Repository

Seed 조건 프리셋 저장/조회
"""
from typing import Optional, List
from src.domain.entities.seed_condition import SeedCondition
from src.domain.entities.block1_condition import Block1ExitConditionType
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import SeedConditionPreset


class SeedConditionPresetRepository:
    """Seed 조건 프리셋 Repository"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def save(self, name: str, condition: SeedCondition, description: str = None) -> str:
        """
        Seed 조건 프리셋 저장

        Args:
            name: 프리셋 이름
            condition: SeedCondition 엔티티
            description: 설명

        Returns:
            저장된 프리셋 이름
        """
        with self.db.session_scope() as session:
            # 기존 프리셋 확인
            existing = session.query(SeedConditionPreset).filter_by(name=name).first()

            if existing:
                # 업데이트
                existing.description = description
                existing.entry_surge_rate = condition.entry_surge_rate
                existing.entry_ma_period = condition.entry_ma_period
                existing.high_above_ma = 1 if condition.high_above_ma else 0
                existing.max_deviation_ratio = condition.max_deviation_ratio
                existing.min_trading_value = condition.min_trading_value
                existing.volume_high_months = condition.volume_high_months
                existing.volume_spike_ratio = condition.volume_spike_ratio
                existing.price_high_months = condition.price_high_months
                existing.exit_condition_type = condition.exit_condition_type.value
                existing.exit_ma_period = condition.exit_ma_period
                existing.cooldown_days = condition.cooldown_days
                existing.block2_volume_ratio = condition.block2_volume_ratio
                existing.block2_low_price_margin = condition.block2_low_price_margin
                existing.block2_min_candles_after_block1 = condition.block2_min_candles_after_block1
                existing.block3_volume_ratio = condition.block3_volume_ratio
                existing.block3_low_price_margin = condition.block3_low_price_margin
                existing.block3_min_candles_after_block2 = condition.block3_min_candles_after_block2
            else:
                # 신규 생성
                preset = SeedConditionPreset(
                    name=name,
                    description=description,
                    entry_surge_rate=condition.entry_surge_rate,
                    entry_ma_period=condition.entry_ma_period,
                    high_above_ma=1 if condition.high_above_ma else 0,
                    max_deviation_ratio=condition.max_deviation_ratio,
                    min_trading_value=condition.min_trading_value,
                    volume_high_months=condition.volume_high_months,
                    volume_spike_ratio=condition.volume_spike_ratio,
                    price_high_months=condition.price_high_months,
                    exit_condition_type=condition.exit_condition_type.value,
                    exit_ma_period=condition.exit_ma_period,
                    cooldown_days=condition.cooldown_days,
                    block2_volume_ratio=condition.block2_volume_ratio,
                    block2_low_price_margin=condition.block2_low_price_margin,
                    block2_min_candles_after_block1=condition.block2_min_candles_after_block1,
                    block3_volume_ratio=condition.block3_volume_ratio,
                    block3_low_price_margin=condition.block3_low_price_margin,
                    block3_min_candles_after_block2=condition.block3_min_candles_after_block2
                )
                session.add(preset)

            session.commit()
            return name

    def load(self, name: str) -> Optional[SeedCondition]:
        """
        Seed 조건 프리셋 로드

        Args:
            name: 프리셋 이름

        Returns:
            SeedCondition 엔티티 또는 None
        """
        with self.db.session_scope() as session:
            preset = session.query(SeedConditionPreset).filter_by(name=name).first()

            if not preset:
                return None

            return SeedCondition(
                entry_surge_rate=preset.entry_surge_rate,
                entry_ma_period=preset.entry_ma_period,
                high_above_ma=bool(preset.high_above_ma),
                max_deviation_ratio=preset.max_deviation_ratio,
                min_trading_value=preset.min_trading_value,
                volume_high_months=preset.volume_high_months,
                volume_spike_ratio=preset.volume_spike_ratio,
                price_high_months=preset.price_high_months,
                exit_condition_type=Block1ExitConditionType(preset.exit_condition_type),
                exit_ma_period=preset.exit_ma_period,
                cooldown_days=preset.cooldown_days,
                block2_volume_ratio=preset.block2_volume_ratio,
                block2_low_price_margin=preset.block2_low_price_margin,
                block2_min_candles_after_block1=preset.block2_min_candles_after_block1,
                block3_volume_ratio=preset.block3_volume_ratio,
                block3_low_price_margin=preset.block3_low_price_margin,
                block3_min_candles_after_block2=preset.block3_min_candles_after_block2
            )

    def list_all(self) -> List[str]:
        """모든 프리셋 이름 조회"""
        with self.db.session_scope() as session:
            presets = session.query(SeedConditionPreset).filter_by(is_active=1).all()
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
            preset = session.query(SeedConditionPreset).filter_by(name=name).first()

            if not preset:
                return False

            preset.is_active = 0
            session.commit()
            return True
