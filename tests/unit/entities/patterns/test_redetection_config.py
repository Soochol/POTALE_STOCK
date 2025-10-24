"""
Unit Tests for RedetectionConfig Entity

재탐지 설정 엔티티 테스트
"""
import pytest

from src.domain.entities.patterns import (
    RedetectionConfig,
    ToleranceConfig,
    MatchingWeights
)


class TestToleranceConfig:
    """ToleranceConfig 테스트"""

    def test_default_values(self):
        """기본값 테스트"""
        tolerance = ToleranceConfig()

        assert tolerance.price_range == 0.05
        assert tolerance.volume_range == 0.30
        assert tolerance.time_range == 10

    def test_custom_values(self):
        """커스텀 값 테스트"""
        tolerance = ToleranceConfig(
            price_range=0.10,
            volume_range=0.40,
            time_range=15
        )

        assert tolerance.price_range == 0.10
        assert tolerance.volume_range == 0.40
        assert tolerance.time_range == 15

    def test_validation_price_range_too_high(self):
        """가격 범위 검증: 1.0 초과"""
        with pytest.raises(ValueError, match="price_range must be between 0 and 1"):
            ToleranceConfig(price_range=1.5)

    def test_validation_price_range_negative(self):
        """가격 범위 검증: 음수"""
        with pytest.raises(ValueError, match="price_range must be between 0 and 1"):
            ToleranceConfig(price_range=-0.1)

    def test_validation_volume_range_too_high(self):
        """거래량 범위 검증: 1.0 초과"""
        with pytest.raises(ValueError, match="volume_range must be between 0 and 1"):
            ToleranceConfig(volume_range=1.2)

    def test_validation_time_range_negative(self):
        """시간 범위 검증: 음수"""
        with pytest.raises(ValueError, match="time_range must be non-negative"):
            ToleranceConfig(time_range=-5)

    def test_edge_values(self):
        """경계값 테스트"""
        # 0과 1은 허용
        tolerance = ToleranceConfig(
            price_range=0.0,
            volume_range=1.0,
            time_range=0
        )
        assert tolerance.price_range == 0.0
        assert tolerance.volume_range == 1.0
        assert tolerance.time_range == 0


class TestMatchingWeights:
    """MatchingWeights 테스트"""

    def test_default_values(self):
        """기본값 테스트"""
        weights = MatchingWeights()

        assert weights.price_shape == 0.4
        assert weights.volume_shape == 0.3
        assert weights.timing == 0.3

        # 합이 1.0
        total = weights.price_shape + weights.volume_shape + weights.timing
        assert abs(total - 1.0) < 1e-6

    def test_custom_values_valid(self):
        """커스텀 값 테스트: 유효한 가중치"""
        weights = MatchingWeights(
            price_shape=0.5,
            volume_shape=0.3,
            timing=0.2
        )

        assert weights.price_shape == 0.5
        assert weights.volume_shape == 0.3
        assert weights.timing == 0.2

    def test_validation_sum_not_one(self):
        """검증: 가중치 합이 1.0이 아님"""
        with pytest.raises(ValueError, match="Matching weights must sum to 1.0"):
            MatchingWeights(
                price_shape=0.5,
                volume_shape=0.3,
                timing=0.3  # 합 = 1.1
            )

    def test_validation_negative_weight(self):
        """검증: 음수 가중치"""
        with pytest.raises(ValueError, match="All weights must be between 0 and 1"):
            MatchingWeights(
                price_shape=-0.1,
                volume_shape=0.6,
                timing=0.5
            )

    def test_validation_weight_over_one(self):
        """검증: 1.0 초과 가중치"""
        with pytest.raises(ValueError, match="All weights must be between 0 and 1"):
            MatchingWeights(
                price_shape=1.2,
                volume_shape=0.0,
                timing=-0.2
            )

    def test_equal_weights(self):
        """동일 가중치 테스트"""
        weights = MatchingWeights(
            price_shape=1.0 / 3,
            volume_shape=1.0 / 3,
            timing=1.0 / 3
        )

        total = weights.price_shape + weights.volume_shape + weights.timing
        assert abs(total - 1.0) < 1e-6


class TestRedetectionConfig:
    """RedetectionConfig 테스트"""

    def test_default_values(self):
        """기본값 테스트"""
        config = RedetectionConfig()

        assert config.seed_pattern_reference is None
        assert config.tolerance.price_range == 0.05
        assert config.tolerance.volume_range == 0.30
        assert config.tolerance.time_range == 10
        assert config.matching_weights.price_shape == 0.4
        assert config.matching_weights.volume_shape == 0.3
        assert config.matching_weights.timing == 0.3
        assert config.min_similarity_score == 0.7
        assert config.min_detection_interval_days == 20
        assert config.metadata == {}

    def test_custom_values(self):
        """커스텀 값 테스트"""
        config = RedetectionConfig(
            seed_pattern_reference="my_seed_pattern",
            tolerance=ToleranceConfig(price_range=0.10, volume_range=0.40, time_range=15),
            matching_weights=MatchingWeights(price_shape=0.5, volume_shape=0.3, timing=0.2),
            min_similarity_score=0.75,
            min_detection_interval_days=30,
            metadata={'description': 'test config'}
        )

        assert config.seed_pattern_reference == "my_seed_pattern"
        assert config.tolerance.price_range == 0.10
        assert config.min_similarity_score == 0.75
        assert config.min_detection_interval_days == 30
        assert config.metadata == {'description': 'test config'}

    def test_validation_min_similarity_score_too_high(self):
        """검증: 유사도 임계값 1.0 초과"""
        with pytest.raises(ValueError, match="min_similarity_score must be between 0 and 1"):
            RedetectionConfig(min_similarity_score=1.5)

    def test_validation_min_similarity_score_negative(self):
        """검증: 유사도 임계값 음수"""
        with pytest.raises(ValueError, match="min_similarity_score must be between 0 and 1"):
            RedetectionConfig(min_similarity_score=-0.1)

    def test_validation_min_detection_interval_negative(self):
        """검증: 최소 간격 음수"""
        with pytest.raises(ValueError, match="min_detection_interval_days must be non-negative"):
            RedetectionConfig(min_detection_interval_days=-5)

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        config = RedetectionConfig(
            seed_pattern_reference="seed_v1",
            min_similarity_score=0.80,
            metadata={'key': 'value'}
        )

        data = config.to_dict()

        assert data['seed_pattern_reference'] == "seed_v1"
        assert data['tolerance']['price_range'] == 0.05
        assert data['matching_weights']['price_shape'] == 0.4
        assert data['min_similarity_score'] == 0.80
        assert data['min_detection_interval_days'] == 20
        assert data['metadata'] == {'key': 'value'}

    def test_from_dict(self):
        """딕셔너리에서 생성 테스트"""
        data = {
            'seed_pattern_reference': 'seed_v1',
            'tolerance': {
                'price_range': 0.08,
                'volume_range': 0.35,
                'time_range': 12
            },
            'matching_weights': {
                'price_shape': 0.5,
                'volume_shape': 0.3,
                'timing': 0.2
            },
            'min_similarity_score': 0.75,
            'min_detection_interval_days': 25,
            'metadata': {'test': 'data'}
        }

        config = RedetectionConfig.from_dict(data)

        assert config.seed_pattern_reference == 'seed_v1'
        assert config.tolerance.price_range == 0.08
        assert config.tolerance.volume_range == 0.35
        assert config.tolerance.time_range == 12
        assert config.matching_weights.price_shape == 0.5
        assert config.matching_weights.volume_shape == 0.3
        assert config.matching_weights.timing == 0.2
        assert config.min_similarity_score == 0.75
        assert config.min_detection_interval_days == 25
        assert config.metadata == {'test': 'data'}

    def test_from_dict_partial_data(self):
        """딕셔너리에서 생성 테스트: 일부 데이터만 제공"""
        data = {
            'seed_pattern_reference': 'seed_v1',
            'min_similarity_score': 0.65
        }

        config = RedetectionConfig.from_dict(data)

        # 제공된 값
        assert config.seed_pattern_reference == 'seed_v1'
        assert config.min_similarity_score == 0.65

        # 기본값
        assert config.tolerance.price_range == 0.05
        assert config.matching_weights.price_shape == 0.4
        assert config.min_detection_interval_days == 20

    def test_roundtrip_to_dict_from_dict(self):
        """Roundtrip 테스트: to_dict → from_dict"""
        original = RedetectionConfig(
            seed_pattern_reference="test_seed",
            tolerance=ToleranceConfig(price_range=0.07, volume_range=0.25, time_range=8),
            matching_weights=MatchingWeights(price_shape=0.6, volume_shape=0.2, timing=0.2),
            min_similarity_score=0.82,
            min_detection_interval_days=15,
            metadata={'roundtrip': 'test'}
        )

        # to_dict → from_dict
        data = original.to_dict()
        restored = RedetectionConfig.from_dict(data)

        # 비교
        assert restored.seed_pattern_reference == original.seed_pattern_reference
        assert restored.tolerance.price_range == original.tolerance.price_range
        assert restored.tolerance.volume_range == original.tolerance.volume_range
        assert restored.tolerance.time_range == original.tolerance.time_range
        assert restored.matching_weights.price_shape == original.matching_weights.price_shape
        assert restored.matching_weights.volume_shape == original.matching_weights.volume_shape
        assert restored.matching_weights.timing == original.matching_weights.timing
        assert restored.min_similarity_score == original.min_similarity_score
        assert restored.min_detection_interval_days == original.min_detection_interval_days
        assert restored.metadata == original.metadata

    def test_get_price_filter_range(self):
        """가격 필터 범위 계산 테스트"""
        config = RedetectionConfig(
            tolerance=ToleranceConfig(price_range=0.10)  # ±10%
        )

        seed_price = 10000
        min_price, max_price = config.get_price_filter_range(seed_price)

        assert min_price == 9000  # 10000 - 10%
        assert max_price == 11000  # 10000 + 10%

    def test_get_volume_filter_range(self):
        """거래량 필터 범위 계산 테스트"""
        config = RedetectionConfig(
            tolerance=ToleranceConfig(volume_range=0.20)  # ±20%
        )

        seed_volume = 1000000
        min_volume, max_volume = config.get_volume_filter_range(seed_volume)

        assert min_volume == 800000  # 1000000 - 20%
        assert max_volume == 1200000  # 1000000 + 20%

    def test_get_time_filter_range(self):
        """시간 필터 범위 계산 테스트"""
        config = RedetectionConfig(
            tolerance=ToleranceConfig(time_range=5)  # ±5 candles
        )

        seed_candle_count = 30
        min_candles, max_candles = config.get_time_filter_range(seed_candle_count)

        assert min_candles == 25  # 30 - 5
        assert max_candles == 35  # 30 + 5

    def test_get_time_filter_range_minimum_one(self):
        """시간 필터 범위: 최소값은 1 (음수 불가)"""
        config = RedetectionConfig(
            tolerance=ToleranceConfig(time_range=50)  # ±50 candles
        )

        seed_candle_count = 10
        min_candles, max_candles = config.get_time_filter_range(seed_candle_count)

        assert min_candles == 1  # max(1, 10 - 50) = 1
        assert max_candles == 60  # 10 + 50
