"""
Redetection Configuration Entity

Seed pattern을 기반으로 유사 패턴을 재탐지하기 위한 설정
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ToleranceConfig:
    """
    재탐지 허용 오차 설정

    Seed pattern의 특징값을 기준으로 허용 범위를 정의
    """
    price_range: float = 0.05      # 가격 허용 오차 (±5%)
    volume_range: float = 0.30     # 거래량 허용 오차 (±30%)
    time_range: int = 10           # 시간(캔들) 허용 오차 (±10 candles)

    def __post_init__(self):
        """검증"""
        if not 0 <= self.price_range <= 1:
            raise ValueError(f"price_range must be between 0 and 1, got {self.price_range}")
        if not 0 <= self.volume_range <= 1:
            raise ValueError(f"volume_range must be between 0 and 1, got {self.volume_range}")
        if self.time_range < 0:
            raise ValueError(f"time_range must be non-negative, got {self.time_range}")


@dataclass
class MatchingWeights:
    """
    Pattern matching 시 각 요소의 가중치

    가격 shape, 볼륨 shape, 타이밍의 중요도를 정의
    합이 1.0이어야 함
    """
    price_shape: float = 0.4       # 가격 형태 유사도 가중치
    volume_shape: float = 0.3      # 거래량 형태 유사도 가중치
    timing: float = 0.3            # 타이밍 유사도 가중치

    def __post_init__(self):
        """검증: 가중치 합이 1.0이어야 함"""
        total = self.price_shape + self.volume_shape + self.timing
        if not abs(total - 1.0) < 1e-6:
            raise ValueError(f"Matching weights must sum to 1.0, got {total}")

        if any(w < 0 or w > 1 for w in [self.price_shape, self.volume_shape, self.timing]):
            raise ValueError("All weights must be between 0 and 1")


@dataclass
class RedetectionConfig:
    """
    재탐지 설정

    Seed pattern을 기반으로 유사 패턴을 찾기 위한 전체 설정
    """
    # Seed pattern 참조
    seed_pattern_reference: Optional[str] = None  # Seed pattern 이름/ID

    # 허용 오차
    tolerance: ToleranceConfig = field(default_factory=ToleranceConfig)

    # Pattern matching 가중치
    matching_weights: MatchingWeights = field(default_factory=MatchingWeights)

    # 유사도 임계값
    min_similarity_score: float = 0.7  # 최소 유사도 (0~1)

    # Cooldown period
    min_detection_interval_days: int = 20  # 재탐지 간 최소 간격 (일)

    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """검증"""
        if not 0 <= self.min_similarity_score <= 1:
            raise ValueError(
                f"min_similarity_score must be between 0 and 1, got {self.min_similarity_score}"
            )

        if self.min_detection_interval_days < 0:
            raise ValueError(
                f"min_detection_interval_days must be non-negative, got {self.min_detection_interval_days}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (YAML 저장용)"""
        return {
            'seed_pattern_reference': self.seed_pattern_reference,
            'tolerance': {
                'price_range': self.tolerance.price_range,
                'volume_range': self.tolerance.volume_range,
                'time_range': self.tolerance.time_range,
            },
            'matching_weights': {
                'price_shape': self.matching_weights.price_shape,
                'volume_shape': self.matching_weights.volume_shape,
                'timing': self.matching_weights.timing,
            },
            'min_similarity_score': self.min_similarity_score,
            'min_detection_interval_days': self.min_detection_interval_days,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RedetectionConfig':
        """딕셔너리에서 생성 (YAML 로드용)"""
        tolerance_data = data.get('tolerance', {})
        tolerance = ToleranceConfig(
            price_range=tolerance_data.get('price_range', 0.05),
            volume_range=tolerance_data.get('volume_range', 0.30),
            time_range=tolerance_data.get('time_range', 10),
        )

        weights_data = data.get('matching_weights', {})
        matching_weights = MatchingWeights(
            price_shape=weights_data.get('price_shape', 0.4),
            volume_shape=weights_data.get('volume_shape', 0.3),
            timing=weights_data.get('timing', 0.3),
        )

        return cls(
            seed_pattern_reference=data.get('seed_pattern_reference'),
            tolerance=tolerance,
            matching_weights=matching_weights,
            min_similarity_score=data.get('min_similarity_score', 0.7),
            min_detection_interval_days=data.get('min_detection_interval_days', 20),
            metadata=data.get('metadata', {}),
        )

    def get_price_filter_range(self, seed_price: float) -> tuple[float, float]:
        """
        Seed 가격 기준 필터 범위 계산

        Args:
            seed_price: Seed pattern의 기준 가격

        Returns:
            (min_price, max_price) 튜플
        """
        margin = seed_price * self.tolerance.price_range
        return (seed_price - margin, seed_price + margin)

    def get_volume_filter_range(self, seed_volume: int) -> tuple[int, int]:
        """
        Seed 거래량 기준 필터 범위 계산

        Args:
            seed_volume: Seed pattern의 기준 거래량

        Returns:
            (min_volume, max_volume) 튜플
        """
        margin = int(seed_volume * self.tolerance.volume_range)
        return (seed_volume - margin, seed_volume + margin)

    def get_time_filter_range(self, seed_candle_count: int) -> tuple[int, int]:
        """
        Seed 캔들 개수 기준 필터 범위 계산

        Args:
            seed_candle_count: Seed pattern의 캔들 개수

        Returns:
            (min_candles, max_candles) 튜플
        """
        margin = self.tolerance.time_range
        return (
            max(1, seed_candle_count - margin),
            seed_candle_count + margin
        )
