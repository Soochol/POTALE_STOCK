"""
Unit Tests for SimilarityCalculator Service

Seed pattern과 candidate detection 간 유사도 계산 테스트
"""
import pytest
from datetime import date, timedelta
from typing import List

from src.application.services.similarity_calculator import (
    SimilarityCalculator,
    SimilarityScore
)
from src.domain.entities.patterns import (
    SeedPattern,
    BlockFeatures,
    RedetectionConfig,
    ToleranceConfig,
    MatchingWeights
)
from src.domain.entities.detections import DynamicBlockDetection


class TestSimilarityScore:
    """SimilarityScore 데이터클래스 테스트"""

    def test_creation(self):
        """SimilarityScore 생성 테스트"""
        score = SimilarityScore(
            price_similarity=0.85,
            volume_similarity=0.75,
            timing_similarity=0.90,
            total_score=0.82
        )

        assert score.price_similarity == 0.85
        assert score.volume_similarity == 0.75
        assert score.timing_similarity == 0.90
        assert score.total_score == 0.82

    def test_perfect_match(self):
        """완벽한 매칭 (1.0) 테스트"""
        score = SimilarityScore(
            price_similarity=1.0,
            volume_similarity=1.0,
            timing_similarity=1.0,
            total_score=1.0
        )

        assert score.total_score == 1.0

    def test_no_match(self):
        """매칭 없음 (0.0) 테스트"""
        score = SimilarityScore(
            price_similarity=0.0,
            volume_similarity=0.0,
            timing_similarity=0.0,
            total_score=0.0
        )

        assert score.total_score == 0.0


class TestSimilarityCalculator:
    """SimilarityCalculator 테스트"""

    @pytest.fixture
    def default_config(self):
        """기본 RedetectionConfig"""
        return RedetectionConfig(
            tolerance=ToleranceConfig(
                price_range=0.10,    # ±10%
                volume_range=0.30,   # ±30%
                time_range=5         # ±5 candles
            ),
            matching_weights=MatchingWeights(
                price_shape=0.4,
                volume_shape=0.3,
                timing=0.3
            ),
            min_similarity_score=0.70
        )

    @pytest.fixture
    def seed_pattern(self):
        """테스트용 Seed Pattern"""
        return SeedPattern(
            pattern_name="test_seed",
            ticker="025980",
            yaml_config_path="presets/test_seed.yaml",
            detection_date=date(2020, 1, 1),
            block_features=[
                BlockFeatures(
                    block_id="block1",
                    block_type=1,
                    started_at=date(2020, 1, 1),
                    ended_at=date(2020, 1, 10),
                    duration_candles=10,
                    low_price=10000.0,
                    high_price=12000.0,
                    peak_price=12000.0,
                    peak_date=date(2020, 1, 10),
                    min_volume=100000,
                    max_volume=500000,
                    peak_volume=500000,
                    avg_volume=300000
                ),
                BlockFeatures(
                    block_id="block2",
                    block_type=2,
                    started_at=date(2020, 1, 11),
                    ended_at=date(2020, 1, 20),
                    duration_candles=10,
                    low_price=12000.0,
                    high_price=14000.0,
                    peak_price=14000.0,
                    peak_date=date(2020, 1, 20),
                    min_volume=80000,
                    max_volume=400000,
                    peak_volume=400000,
                    avg_volume=250000
                )
            ],
            price_shape=[0.0, 0.2, 0.5, 0.8, 1.0],
            volume_shape=[0.2, 0.5, 1.0, 0.7, 0.4]
        )

    @pytest.fixture
    def similar_detections(self):
        """유사한 candidate detections (높은 유사도)"""
        return [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 11),
                peak_price=11800.0,      # 12000 ±10% 이내
                peak_volume=480000,      # 500000 ±30% 이내
                metadata={},
                parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2",
                block_type=2,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 12),
                ended_at=date(2021, 1, 21),
                peak_price=13800.0,      # 14000 ±10% 이내
                peak_volume=390000,      # 400000 ±30% 이내
                metadata={},
                parent_blocks=[]
            )
        ]

    @pytest.fixture
    def dissimilar_detections(self):
        """유사하지 않은 candidate detections (낮은 유사도)"""
        return [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 11),
                peak_price=20000.0,      # 12000에서 너무 멀음
                peak_volume=1000000,     # 500000에서 너무 멀음
                metadata={},
                parent_blocks=[]
            )
        ]

    def test_initialization(self, default_config):
        """SimilarityCalculator 초기화 테스트"""
        calculator = SimilarityCalculator(default_config)

        assert calculator.config == default_config
        assert calculator.config.tolerance.price_range == 0.10
        assert calculator.config.matching_weights.price_shape == 0.4

    def test_calculate_similar_pattern(self, default_config, seed_pattern, similar_detections):
        """유사한 패턴 계산 테스트 (높은 유사도)"""
        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, similar_detections)

        # 유사도가 높아야 함
        assert score.price_similarity > 0.80
        assert score.volume_similarity > 0.80
        assert score.timing_similarity > 0.80
        assert score.total_score > 0.80

        # Total score는 가중 평균
        expected_total = (
            score.price_similarity * 0.4 +
            score.volume_similarity * 0.3 +
            score.timing_similarity * 0.3
        )
        assert abs(score.total_score - expected_total) < 1e-6

    def test_calculate_dissimilar_pattern(self, default_config, seed_pattern, dissimilar_detections):
        """유사하지 않은 패턴 계산 테스트 (낮은 유사도)"""
        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, dissimilar_detections)

        # 유사도가 낮아야 함
        assert score.price_similarity < 0.50
        assert score.volume_similarity < 0.50
        assert score.total_score < 0.50

    def test_meets_threshold_pass(self, default_config, seed_pattern, similar_detections):
        """임계값 충족 테스트 (통과)"""
        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, similar_detections)

        # min_similarity_score = 0.70
        assert calculator.meets_threshold(score) is True

    def test_meets_threshold_fail(self, default_config, seed_pattern, dissimilar_detections):
        """임계값 충족 테스트 (실패)"""
        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, dissimilar_detections)

        # min_similarity_score = 0.70
        assert calculator.meets_threshold(score) is False

    def test_empty_candidate_list(self, default_config, seed_pattern):
        """빈 candidate 리스트 테스트"""
        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, [])

        # 빈 리스트는 0.0 유사도
        assert score.price_similarity == 0.0
        assert score.volume_similarity == 0.0
        assert score.timing_similarity == 0.0
        assert score.total_score == 0.0

    def test_single_block_match(self, default_config, seed_pattern):
        """단일 블록 매칭 테스트"""
        # Block1만 있는 candidate
        candidate = [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 11),
                peak_price=11900.0,
                peak_volume=490000,
                metadata={},
                parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, candidate)

        # Block1만 비교 (Block2는 매칭 없음)
        # 유사도는 중간 정도
        assert 0.0 < score.total_score < 1.0

    def test_perfect_match(self, default_config, seed_pattern):
        """완벽한 매칭 테스트 (동일한 값)"""
        # Seed와 동일한 값의 candidate
        perfect_match = [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 10),
                peak_price=12000.0,      # 정확히 동일
                peak_volume=500000,      # 정확히 동일
                metadata={},
                parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2",
                block_type=2,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 11),
                ended_at=date(2021, 1, 20),
                peak_price=14000.0,      # 정확히 동일
                peak_volume=400000,      # 정확히 동일
                metadata={},
                parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, perfect_match)

        # 완벽한 매칭 (price/volume은 1.0, timing은 약간 낮을 수 있음)
        assert score.price_similarity > 0.95
        assert score.volume_similarity > 0.95
        # Total score는 timing 영향으로 약간 낮을 수 있음 (0.94 정도)
        assert score.total_score > 0.90

    def test_boundary_tolerance(self, default_config, seed_pattern):
        """허용 오차 경계 테스트"""
        # Price: 12000 ± 10% = [10800, 13200]
        # Volume: 500000 ± 30% = [350000, 650000]

        # 경계 근처 값 (10900, 360000) - 경계에서 약간 안쪽
        near_boundary_candidate = [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 10),
                peak_price=10900.0,      # 10800보다 안쪽
                peak_volume=360000,      # 350000보다 안쪽
                metadata={},
                parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, near_boundary_candidate)

        # 경계 근처는 낮지만 0보다 큰 유사도
        assert score.price_similarity > 0.0
        assert score.volume_similarity > 0.0
        assert score.total_score > 0.0

    def test_outside_tolerance(self, default_config, seed_pattern):
        """허용 오차 밖 테스트"""
        # Price: 12000 ± 10% = [10800, 13200]
        # 13300은 범위 밖

        out_of_range = [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 10),
                peak_price=13300.0,      # 범위 밖
                peak_volume=500000,
                metadata={},
                parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config)
        score = calculator.calculate(seed_pattern, out_of_range)

        # 범위 밖이므로 price_similarity 낮음
        assert score.price_similarity < 0.5

    def test_custom_weights(self, seed_pattern, similar_detections):
        """커스텀 가중치 테스트"""
        # Price에 높은 가중치
        price_heavy_config = RedetectionConfig(
            matching_weights=MatchingWeights(
                price_shape=0.8,
                volume_shape=0.1,
                timing=0.1
            )
        )

        calculator = SimilarityCalculator(price_heavy_config)
        score = calculator.calculate(seed_pattern, similar_detections)

        # Total score는 가중 평균
        expected_total = (
            score.price_similarity * 0.8 +
            score.volume_similarity * 0.1 +
            score.timing_similarity * 0.1
        )
        assert abs(score.total_score - expected_total) < 1e-6

    def test_timing_similarity(self, default_config, seed_pattern):
        """타이밍 유사도 테스트"""
        # 동일한 duration (10 candles)
        same_duration = [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 10),  # 10일 (동일)
                peak_price=11000.0,
                peak_volume=450000,
                metadata={},
                parent_blocks=[]
            )
        ]

        # 다른 duration (20 candles)
        different_duration = [
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 20),  # 20일 (다름)
                peak_price=11000.0,
                peak_volume=450000,
                metadata={},
                parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config)

        score_same = calculator.calculate(seed_pattern, same_duration)
        score_diff = calculator.calculate(seed_pattern, different_duration)

        # 동일 duration이 더 높은 timing_similarity
        assert score_same.timing_similarity > score_diff.timing_similarity
