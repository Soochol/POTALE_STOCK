"""
Redetection Condition Preset Repository

재탐지 조건 프리셋 저장/조회 (BaseConditionPresetRepository 사용)
"""
from src.domain.entities import BaseEntryCondition, RedetectionCondition, Block1ExitConditionType
from typing import Optional
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import RedetectionConditionPreset
from ..common import BaseConditionPresetRepository, ConditionPresetMapperMixin

class RedetectionConditionPresetRepository(BaseConditionPresetRepository, ConditionPresetMapperMixin):
    """재탐지 조건 프리셋 Repository"""

    def __init__(self, db: DatabaseConnection):
        super().__init__(db, RedetectionConditionPreset)

    def _build_model_fields(self, condition: RedetectionCondition, name: str, description: Optional[str]) -> dict:
        """
        RedetectionCondition 엔티티를 DB 모델 필드 딕셔너리로 변환

        Args:
            condition: RedetectionCondition 엔티티
            name: 프리셋 이름
            description: 프리셋 설명

        Returns:
            dict: 모델 생성에 필요한 필드 딕셔너리
        """
        # 기본 필드
        fields = {
            'name': name,
            'description': description,
        }

        # Block1 Base 조건 매핑
        fields.update(self.map_base_to_model_dict(condition.base, "block1_"))

        # 재탐지 전용: Tolerance 필드
        fields.update({
            'block1_tolerance_pct': condition.block1_tolerance_pct,
            'block2_tolerance_pct': condition.block2_tolerance_pct,
            'block3_tolerance_pct': condition.block3_tolerance_pct,
            'block4_tolerance_pct': condition.block4_tolerance_pct,
        })

        # 재탐지 전용: 기간 범위 필드 (Seed 발생일 기준)
        fields.update({
            'block1_redetection_min_days_after_seed': condition.block1_redetection_min_days_after_seed,
            'block1_redetection_max_days_after_seed': condition.block1_redetection_max_days_after_seed,
            'block2_redetection_min_days_after_seed': condition.block2_redetection_min_days_after_seed,
            'block2_redetection_max_days_after_seed': condition.block2_redetection_max_days_after_seed,
            'block3_redetection_min_days_after_seed': condition.block3_redetection_min_days_after_seed,
            'block3_redetection_max_days_after_seed': condition.block3_redetection_max_days_after_seed,
            'block4_redetection_min_days_after_seed': condition.block4_redetection_min_days_after_seed,
            'block4_redetection_max_days_after_seed': condition.block4_redetection_max_days_after_seed,
        })

        # Block2/3/4 진입 조건 매핑
        fields.update({
            'block2_volume_ratio': condition.block2_volume_ratio,
            'block2_low_price_margin': condition.block2_low_price_margin,
            'block2_min_candles_from_block': condition.block2_min_candles_from_block,
            'block2_max_candles_from_block': condition.block2_max_candles_from_block,
            'block2_lookback_min_candles': condition.block2_lookback_min_candles,
            'block2_lookback_max_candles': condition.block2_lookback_max_candles,
            'block3_volume_ratio': condition.block3_volume_ratio,
            'block3_low_price_margin': condition.block3_low_price_margin,
            'block3_min_candles_from_block': condition.block3_min_candles_from_block,
            'block3_max_candles_from_block': condition.block3_max_candles_from_block,
            'block3_lookback_min_candles': condition.block3_lookback_min_candles,
            'block3_lookback_max_candles': condition.block3_lookback_max_candles,
            'block4_volume_ratio': condition.block4_volume_ratio,
            'block4_low_price_margin': condition.block4_low_price_margin,
            'block4_min_candles_from_block': condition.block4_min_candles_from_block,
            'block4_max_candles_from_block': condition.block4_max_candles_from_block,
            'block4_lookback_min_candles': condition.block4_lookback_min_candles,
            'block4_lookback_max_candles': condition.block4_lookback_max_candles,
        })

        # Block2/3/4 전용 파라미터 (Optional)
        for block_num in [2, 3, 4]:
            fields.update(self.map_optional_block_params(condition, block_num))

        return fields

    def _build_entity_from_preset(self, preset: RedetectionConditionPreset) -> RedetectionCondition:
        """
        DB Preset 모델을 RedetectionCondition 엔티티로 변환

        Args:
            preset: RedetectionConditionPreset 모델

        Returns:
            RedetectionCondition 엔티티
        """
        # BaseEntryCondition 생성
        base = BaseEntryCondition(
            block1_entry_surge_rate=preset.block1_entry_surge_rate,
            block1_entry_ma_period=preset.block1_entry_ma_period,
            block1_entry_max_deviation_ratio=preset.block1_entry_max_deviation_ratio,
            block1_entry_min_trading_value=preset.block1_entry_min_trading_value,
            block1_entry_volume_high_days=preset.block1_entry_volume_high_days,
            block1_entry_volume_spike_ratio=preset.block1_entry_volume_spike_ratio,
            block1_entry_price_high_days=preset.block1_entry_price_high_days,
            block1_exit_condition_type=Block1ExitConditionType(preset.block1_exit_condition_type),
            block1_exit_ma_period=preset.block1_exit_ma_period,
            block1_auto_exit_on_next_block=bool(preset.block1_auto_exit_on_next_block),
            block1_min_start_interval_days=preset.block1_min_start_interval_days,
            block2_auto_exit_on_next_block=bool(preset.block2_auto_exit_on_next_block),
            block3_auto_exit_on_next_block=bool(preset.block3_auto_exit_on_next_block),
            block4_auto_exit_on_next_block=bool(preset.block4_auto_exit_on_next_block)
        )

        # RedetectionCondition 생성
        return RedetectionCondition(
            base=base,
            block1_tolerance_pct=preset.block1_tolerance_pct,
            block2_tolerance_pct=preset.block2_tolerance_pct,
            block3_tolerance_pct=preset.block3_tolerance_pct,
            block4_tolerance_pct=preset.block4_tolerance_pct,
            # 재탐지 전용: 기간 범위 (Seed 발생일 기준)
            block1_redetection_min_days_after_seed=preset.block1_redetection_min_days_after_seed,
            block1_redetection_max_days_after_seed=preset.block1_redetection_max_days_after_seed,
            block2_redetection_min_days_after_seed=preset.block2_redetection_min_days_after_seed,
            block2_redetection_max_days_after_seed=preset.block2_redetection_max_days_after_seed,
            block3_redetection_min_days_after_seed=preset.block3_redetection_min_days_after_seed,
            block3_redetection_max_days_after_seed=preset.block3_redetection_max_days_after_seed,
            block4_redetection_min_days_after_seed=preset.block4_redetection_min_days_after_seed,
            block4_redetection_max_days_after_seed=preset.block4_redetection_max_days_after_seed,
            block2_volume_ratio=preset.block2_volume_ratio,
            block2_low_price_margin=preset.block2_low_price_margin,
            block2_min_candles_from_block=preset.block2_min_candles_from_block,
            block2_max_candles_from_block=preset.block2_max_candles_from_block,
            block2_lookback_min_candles=preset.block2_lookback_min_candles,
            block2_lookback_max_candles=preset.block2_lookback_max_candles,
            block3_volume_ratio=preset.block3_volume_ratio,
            block3_low_price_margin=preset.block3_low_price_margin,
            block3_min_candles_from_block=preset.block3_min_candles_from_block,
            block3_max_candles_from_block=preset.block3_max_candles_from_block,
            block3_lookback_min_candles=preset.block3_lookback_min_candles,
            block3_lookback_max_candles=preset.block3_lookback_max_candles,
            block4_volume_ratio=preset.block4_volume_ratio,
            block4_low_price_margin=preset.block4_low_price_margin,
            block4_min_candles_from_block=preset.block4_min_candles_from_block,
            block4_max_candles_from_block=preset.block4_max_candles_from_block,
            block4_lookback_min_candles=preset.block4_lookback_min_candles,
            block4_lookback_max_candles=preset.block4_lookback_max_candles,
            # Block2 전용 파라미터
            block2_entry_surge_rate=preset.block2_entry_surge_rate,
            block2_entry_ma_period=preset.block2_entry_ma_period,
            block2_entry_max_deviation_ratio=preset.block2_entry_max_deviation_ratio,
            block2_entry_min_trading_value=preset.block2_entry_min_trading_value,
            block2_entry_volume_high_days=preset.block2_entry_volume_high_days,
            block2_entry_volume_spike_ratio=preset.block2_entry_volume_spike_ratio,
            block2_entry_price_high_days=preset.block2_entry_price_high_days,
            block2_exit_condition_type=Block1ExitConditionType(preset.block2_exit_condition_type) if preset.block2_exit_condition_type else None,
            block2_exit_ma_period=preset.block2_exit_ma_period,
            block2_min_start_interval_days=preset.block2_min_start_interval_days,
            # Block3 전용 파라미터
            block3_entry_surge_rate=preset.block3_entry_surge_rate,
            block3_entry_ma_period=preset.block3_entry_ma_period,
            block3_entry_max_deviation_ratio=preset.block3_entry_max_deviation_ratio,
            block3_entry_min_trading_value=preset.block3_entry_min_trading_value,
            block3_entry_volume_high_days=preset.block3_entry_volume_high_days,
            block3_entry_volume_spike_ratio=preset.block3_entry_volume_spike_ratio,
            block3_entry_price_high_days=preset.block3_entry_price_high_days,
            block3_exit_condition_type=Block1ExitConditionType(preset.block3_exit_condition_type) if preset.block3_exit_condition_type else None,
            block3_exit_ma_period=preset.block3_exit_ma_period,
            block3_min_start_interval_days=preset.block3_min_start_interval_days,
            # Block4 전용 파라미터
            block4_entry_surge_rate=preset.block4_entry_surge_rate,
            block4_entry_ma_period=preset.block4_entry_ma_period,
            block4_entry_max_deviation_ratio=preset.block4_entry_max_deviation_ratio,
            block4_entry_min_trading_value=preset.block4_entry_min_trading_value,
            block4_entry_volume_high_days=preset.block4_entry_volume_high_days,
            block4_entry_volume_spike_ratio=preset.block4_entry_volume_spike_ratio,
            block4_entry_price_high_days=preset.block4_entry_price_high_days,
            block4_exit_condition_type=Block1ExitConditionType(preset.block4_exit_condition_type) if preset.block4_exit_condition_type else None,
            block4_exit_ma_period=preset.block4_exit_ma_period,
            block4_min_start_interval_days=preset.block4_min_start_interval_days
        )
