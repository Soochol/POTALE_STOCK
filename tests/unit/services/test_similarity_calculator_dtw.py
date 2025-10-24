"""
Unit Tests for DTW-based Similarity Calculator

DTW 방식 유사도 계산 테스트
"""
import pytest
from datetime import date

from src.application.services.similarity_calculator import SimilarityCalculator
from src.domain.entities.patterns import (
    SeedPattern,
    BlockFeatures,
    RedetectionConfig,
    ToleranceConfig,
    MatchingWeights
)
from src.domain.entities.detections import DynamicBlockDetection


class TestSimilarityCalculatorDTW:
    """DTW-based SimilarityCalculator 테스트"""

    @pytest.fixture
    def default_config(self):
        """기본 RedetectionConfig"""
        return RedetectionConfig(
            tolerance=ToleranceConfig(
                price_range=0.10,
                volume_range=0.30,
                time_range=5
            ),
            matching_weights=MatchingWeights(
                price_shape=0.5,
                volume_shape=0.3,
                timing=0.2
            ),
            min_similarity_score=0.70
        )

    @pytest.fixture
    def seed_pattern_upward_trend(self):
        """상승 트렌드 Seed Pattern"""
        return SeedPattern(
            pattern_name="upward_trend",
            ticker="025980",
            yaml_config_path="test.yaml",
            detection_date=date(2020, 1, 1),
            block_features=[
                BlockFeatures(
                    block_id="block1", block_type=1,
                    started_at=date(2020, 1, 1), ended_at=date(2020, 1, 10),
                    duration_candles=10,
                    low_price=10000.0, high_price=11000.0,
                    peak_price=11000.0, peak_date=date(2020, 1, 10),
                    min_volume=100000, max_volume=500000,
                    peak_volume=500000, avg_volume=300000
                ),
                BlockFeatures(
                    block_id="block2", block_type=2,
                    started_at=date(2020, 1, 11), ended_at=date(2020, 1, 20),
                    duration_candles=10,
                    low_price=11000.0, high_price=13000.0,
                    peak_price=13000.0, peak_date=date(2020, 1, 20),
                    min_volume=80000, max_volume=400000,
                    peak_volume=400000, avg_volume=250000
                ),
                BlockFeatures(
                    block_id="block3", block_type=3,
                    started_at=date(2020, 1, 21), ended_at=date(2020, 1, 30),
                    duration_candles=10,
                    low_price=13000.0, high_price=15000.0,
                    peak_price=15000.0, peak_date=date(2020, 1, 30),
                    min_volume=60000, max_volume=300000,
                    peak_volume=300000, avg_volume=200000
                )
            ],
            price_shape=[0.0, 0.5, 1.0],  # Upward trend
            volume_shape=[1.0, 0.7, 0.5]  # Downward volume
        )

    @pytest.fixture
    def similar_upward_detections(self):
        """유사한 상승 트렌드 detections"""
        return [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1), ended_at=date(2021, 1, 10),
                peak_price=10900.0, peak_volume=490000,
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2", block_type=2, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 11), ended_at=date(2021, 1, 20),
                peak_price=12800.0, peak_volume=390000,
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block3", block_type=3, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 21), ended_at=date(2021, 1, 30),
                peak_price=14800.0, peak_volume=290000,
                metadata={}, parent_blocks=[]
            )
        ]

    @pytest.fixture
    def downward_trend_detections(self):
        """반대 트렌드 (하락) detections"""
        return [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1), ended_at=date(2021, 1, 10),
                peak_price=15000.0, peak_volume=300000,
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2", block_type=2, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 11), ended_at=date(2021, 1, 20),
                peak_price=13000.0, peak_volume=400000,
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block3", block_type=3, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 21), ended_at=date(2021, 1, 30),
                peak_price=11000.0, peak_volume=500000,
                metadata={}, parent_blocks=[]
            )
        ]

    def test_initialization_dtw(self, default_config):
        """DTW 방식 초기화 테스트"""
        calculator = SimilarityCalculator(default_config, method="dtw")

        assert calculator.method == "dtw"
        assert calculator.dtw_calculator is not None

    def test_initialization_range(self, default_config):
        """Range 방식 초기화 테스트 (기본값)"""
        calculator = SimilarityCalculator(default_config, method="range")

        assert calculator.method == "range"
        assert calculator.dtw_calculator is None

    def test_dtw_similar_upward_trend(self, default_config, seed_pattern_upward_trend, similar_upward_detections):
        """DTW로 유사한 상승 트렌드 인식"""
        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, similar_upward_detections)

        # DTW should recognize similar upward trend
        assert score.price_similarity > 0.7
        assert score.total_score > 0.6

    def test_dtw_opposite_trend(self, default_config, seed_pattern_upward_trend, downward_trend_detections):
        """DTW는 반대 트렌드도 유사하게 인식 (shape만 비교)"""
        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, downward_trend_detections)

        # DTW compares shape only, so opposite trends still have high similarity
        # (same linear shape, just reversed direction)
        assert score.price_similarity > 0.5
        # Total score might be slightly lower due to timing differences
        assert score.total_score > 0.0

    def test_dtw_vs_range_similar_pattern(self, default_config, seed_pattern_upward_trend, similar_upward_detections):
        """DTW와 Range 방식 비교 (유사한 패턴)"""
        calc_dtw = SimilarityCalculator(default_config, method="dtw")
        calc_range = SimilarityCalculator(default_config, method="range")

        score_dtw = calc_dtw.calculate(seed_pattern_upward_trend, similar_upward_detections)
        score_range = calc_range.calculate(seed_pattern_upward_trend, similar_upward_detections)

        # Both should recognize similarity
        assert score_dtw.total_score > 0.6
        assert score_range.total_score > 0.6

    def test_dtw_different_length_sequences(self, default_config, seed_pattern_upward_trend):
        """DTW는 길이가 다른 시퀀스도 처리"""
        # 2개 블록만 있는 candidate (길이 차이)
        short_detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1), ended_at=date(2021, 1, 10),
                peak_price=11000.0, peak_volume=500000,
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2", block_type=2, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 11), ended_at=date(2021, 1, 20),
                peak_price=13000.0, peak_volume=400000,
                metadata={}, parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, short_detections)

        # DTW should handle different lengths
        # Similarity may be lower due to length difference, but should not crash
        assert 0.0 <= score.total_score <= 1.0

    def test_dtw_empty_detections(self, default_config, seed_pattern_upward_trend):
        """빈 detections는 0.0 유사도"""
        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, [])

        assert score.price_similarity == 0.0
        assert score.volume_similarity == 0.0
        assert score.total_score == 0.0

    def test_dtw_threshold_check(self, default_config, seed_pattern_upward_trend, similar_upward_detections):
        """DTW 유사도 threshold 확인"""
        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, similar_upward_detections)

        # min_similarity_score = 0.70
        if score.total_score >= 0.70:
            assert calculator.meets_threshold(score) is True
        else:
            assert calculator.meets_threshold(score) is False

    def test_dtw_shape_matching_robustness(self, default_config):
        """DTW shape matching의 견고성 테스트"""
        # Slightly shifted peak pattern
        seed = SeedPattern(
            pattern_name="peak",
            ticker="025980",
            yaml_config_path="test.yaml",
            detection_date=date(2020, 1, 1),
            block_features=[
                BlockFeatures(
                    block_id="block1", block_type=1,
                    started_at=date(2020, 1, 1), ended_at=date(2020, 1, 10),
                    duration_candles=10,
                    low_price=10000.0, high_price=12000.0,
                    peak_price=12000.0, peak_date=date(2020, 1, 10),
                    min_volume=100000, max_volume=500000,
                    peak_volume=500000, avg_volume=300000
                ),
                BlockFeatures(
                    block_id="block2", block_type=2,
                    started_at=date(2020, 1, 11), ended_at=date(2020, 1, 20),
                    duration_candles=10,
                    low_price=12000.0, high_price=11000.0,
                    peak_price=11000.0, peak_date=date(2020, 1, 20),
                    min_volume=80000, max_volume=400000,
                    peak_volume=400000, avg_volume=250000
                )
            ],
            price_shape=[0.0, 1.0, 0.0],  # Peak pattern
            volume_shape=[1.0, 0.7, 0.5]  # Same length as price_shape
        )

        # Similar peak but with noise
        candidate = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1), ended_at=date(2021, 1, 10),
                peak_price=11900.0, peak_volume=490000,
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2", block_type=2, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 11), ended_at=date(2021, 1, 20),
                peak_price=11100.0, peak_volume=380000,
                metadata={}, parent_blocks=[]
            )
        ]

        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed, candidate)

        # DTW should recognize similar peak shape despite noise
        assert score.price_similarity > 0.5

    def test_dtw_volume_shape_matching(self, default_config, seed_pattern_upward_trend, similar_upward_detections):
        """DTW volume shape matching 테스트"""
        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, similar_upward_detections)

        # Volume shape should also be matched
        assert score.volume_similarity > 0.0
        assert 0.0 <= score.volume_similarity <= 1.0

    def test_dtw_weighted_score(self, default_config, seed_pattern_upward_trend, similar_upward_detections):
        """DTW weighted score 계산 테스트"""
        calculator = SimilarityCalculator(default_config, method="dtw")
        score = calculator.calculate(seed_pattern_upward_trend, similar_upward_detections)

        # Verify weighted calculation
        weights = default_config.matching_weights
        expected_total = (
            score.price_similarity * weights.price_shape +
            score.volume_similarity * weights.volume_shape +
            score.timing_similarity * weights.timing
        )

        assert abs(score.total_score - expected_total) < 1e-6
