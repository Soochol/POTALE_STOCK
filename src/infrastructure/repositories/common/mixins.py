"""
Repository Mixins
공통 Repository 로직을 위한 Mixin 클래스들
"""
import uuid
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session


class UUIDMixin:
    """
    UUID 자동 생성 Mixin
    Block2/3/4 Repository에서 사용
    """

    @staticmethod
    def generate_uuid() -> str:
        """
        UUID 생성

        Returns:
            str: 생성된 UUID 문자열

        Example:
            >>> uuid_str = UUIDMixin.generate_uuid()
            >>> print(len(uuid_str))  # 36
        """
        return str(uuid.uuid4())

    def ensure_block_id(self, entity, block_id_attr: str) -> None:
        """
        엔티티에 block_id가 없으면 자동 생성

        Args:
            entity: 엔티티 객체 (Block2/3/4 Detection)
            block_id_attr: block_id 속성 이름 (예: 'block2_id')

        Example:
            >>> self.ensure_block_id(detection, 'block2_id')
        """
        if not hasattr(entity, block_id_attr) or not getattr(entity, block_id_attr):
            setattr(entity, block_id_attr, self.generate_uuid())


class DurationCalculatorMixin:
    """
    Duration Days 계산 Mixin
    Block2/3/4 Repository의 update_status에서 사용
    """

    def calculate_duration_days(
        self,
        session: Session,
        model_class,
        block_id_field,
        block_id: str,
        ended_at: date
    ) -> Optional[int]:
        """
        duration_days 계산 (ended_at - started_at + 1)

        Args:
            session: SQLAlchemy 세션
            model_class: 모델 클래스 (Block2DetectionModel 등)
            block_id_field: block_id 필드 (Block2DetectionModel.block2_id 등)
            block_id: 블록 ID
            ended_at: 종료일

        Returns:
            Optional[int]: 계산된 duration_days, 실패 시 None

        Example:
            >>> duration = self.calculate_duration_days(
            ...     session, Block2DetectionModel,
            ...     Block2DetectionModel.block2_id,
            ...     "abc-123", date(2023, 1, 10)
            ... )
            >>> print(duration)  # 5
        """
        model = session.query(model_class).filter(
            block_id_field == block_id
        ).first()

        if model and model.started_at:
            return (ended_at - model.started_at).days + 1

        return None


class ConditionPresetMapperMixin:
    """
    Condition Preset Entity ↔ Model 매핑 Mixin
    대량의 필드를 자동으로 매핑
    """

    def map_base_to_model_dict(self, base_condition, prefix: str = "block1_") -> dict:
        """
        BaseEntryCondition을 DB 모델 필드 딕셔너리로 변환

        Args:
            base_condition: BaseEntryCondition 엔티티
            prefix: 필드 접두사 (block1_, block2_, block3_, block4_)

        Returns:
            dict: 모델 필드 딕셔너리

        Example:
            >>> fields = self.map_base_to_model_dict(condition.base, "block1_")
            >>> print(fields['block1_entry_surge_rate'])  # 20.0
        """
        return {
            f"{prefix}entry_surge_rate": base_condition.block1_entry_surge_rate,
            f"{prefix}entry_ma_period": base_condition.block1_entry_ma_period,
            f"{prefix}entry_max_deviation_ratio": base_condition.block1_entry_max_deviation_ratio,
            f"{prefix}entry_min_trading_value": base_condition.block1_entry_min_trading_value,
            f"{prefix}entry_volume_high_days": base_condition.block1_entry_volume_high_days,
            f"{prefix}entry_volume_spike_ratio": base_condition.block1_entry_volume_spike_ratio,
            f"{prefix}entry_price_high_days": base_condition.block1_entry_price_high_days,
            f"{prefix}exit_condition_type": base_condition.block1_exit_condition_type.value,
            f"{prefix}exit_ma_period": base_condition.block1_exit_ma_period,
            f"{prefix}min_start_interval_days": base_condition.block1_min_start_interval_days,
        }

    def map_optional_block_params(self, condition, block_num: int) -> dict:
        """
        Block2/3/4 전용 파라미터를 딕셔너리로 변환

        Args:
            condition: Condition 엔티티 (SeedCondition/RedetectionCondition)
            block_num: 블록 번호 (2, 3, 4)

        Returns:
            dict: 모델 필드 딕셔너리
        """
        prefix = f"block{block_num}_"

        # 기본 매핑
        result = {
            f"{prefix}entry_surge_rate": getattr(condition, f"{prefix}entry_surge_rate", None),
            f"{prefix}entry_ma_period": getattr(condition, f"{prefix}entry_ma_period", None),
            f"{prefix}entry_max_deviation_ratio": getattr(condition, f"{prefix}entry_max_deviation_ratio", None),
            f"{prefix}entry_min_trading_value": getattr(condition, f"{prefix}entry_min_trading_value", None),
            f"{prefix}entry_volume_high_days": getattr(condition, f"{prefix}entry_volume_high_days", None),
            f"{prefix}entry_volume_spike_ratio": getattr(condition, f"{prefix}entry_volume_spike_ratio", None),
            f"{prefix}entry_price_high_days": getattr(condition, f"{prefix}entry_price_high_days", None),
            f"{prefix}exit_ma_period": getattr(condition, f"{prefix}exit_ma_period", None),
            f"{prefix}min_start_interval_days": getattr(condition, f"{prefix}min_start_interval_days", None),
        }

        # Enum 필드 처리
        exit_type = getattr(condition, f"{prefix}exit_condition_type", None)
        result[f"{prefix}exit_condition_type"] = exit_type.value if exit_type else None

        return result
