"""
Unit Tests for DynamicPatternRedetector Use Case

Seed pattern 기반 유사 패턴 재탐지 테스트
"""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import List

from src.application.use_cases.dynamic_pattern_redetector import DynamicPatternRedetector
from src.application.services.similarity_calculator import SimilarityScore
from src.domain.entities.patterns import (
    SeedPattern,
    BlockFeatures,
    RedetectionConfig,
    ToleranceConfig,
    MatchingWeights
)
from src.domain.entities.block_graph import BlockGraph, BlockNode
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.core import Stock
from src.domain.entities.conditions import ExpressionEngine


class TestDynamicPatternRedetectorInitialization:
    """초기화 및 검증 테스트"""

    @pytest.fixture
    def valid_redetection_graph(self):
        """유효한 redetection BlockGraph"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig()
        )
        return graph

    @pytest.fixture
    def expression_engine(self):
        """Mock ExpressionEngine"""
        return Mock(spec=ExpressionEngine)

    def test_initialization_success(self, valid_redetection_graph, expression_engine):
        """정상 초기화 테스트"""
        redetector = DynamicPatternRedetector(
            valid_redetection_graph,
            expression_engine
        )

        assert redetector.redetection_graph == valid_redetection_graph
        assert redetector.expression_engine == expression_engine
        assert redetector.redetection_config is not None
        assert redetector.similarity_calculator is not None

    def test_initialization_invalid_pattern_type(self, expression_engine):
        """잘못된 pattern_type 검증"""
        invalid_graph = BlockGraph(
            pattern_type="seed"  # Should be "redetection"
        )

        with pytest.raises(ValueError, match="pattern_type='redetection'"):
            DynamicPatternRedetector(invalid_graph, expression_engine)

    def test_initialization_missing_config(self, expression_engine):
        """redetection_config 누락 검증"""
        graph_without_config = BlockGraph(
            pattern_type="redetection",
            redetection_config=None
        )

        with pytest.raises(ValueError, match="redetection_config"):
            DynamicPatternRedetector(graph_without_config, expression_engine)


class TestDateFiltering:
    """날짜 필터링 테스트"""

    @pytest.fixture
    def stocks(self):
        """테스트용 Stock 데이터"""
        return [
            Stock(ticker="025980", name="테스트종목", date=date(2020, 1, i),
                  open=10000, high=11000, low=9500, close=10000, volume=100000)
            for i in range(1, 31)  # 2020-01-01 ~ 2020-01-30
        ]

    @pytest.fixture
    def redetector(self):
        """DynamicPatternRedetector 인스턴스"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig()
        )
        engine = Mock(spec=ExpressionEngine)
        return DynamicPatternRedetector(graph, engine)

    def test_filter_no_dates(self, redetector, stocks):
        """날짜 필터 없음 (전체)"""
        filtered = redetector._filter_by_date_range(stocks, None, None)
        assert len(filtered) == 30

    def test_filter_start_date_only(self, redetector, stocks):
        """시작 날짜만 지정"""
        filtered = redetector._filter_by_date_range(
            stocks,
            start_date=date(2020, 1, 15),
            end_date=None
        )

        assert len(filtered) == 16  # 2020-01-15 ~ 2020-01-30
        assert filtered[0].date == date(2020, 1, 15)
        assert filtered[-1].date == date(2020, 1, 30)

    def test_filter_end_date_only(self, redetector, stocks):
        """종료 날짜만 지정"""
        filtered = redetector._filter_by_date_range(
            stocks,
            start_date=None,
            end_date=date(2020, 1, 15)
        )

        assert len(filtered) == 15  # 2020-01-01 ~ 2020-01-15
        assert filtered[0].date == date(2020, 1, 1)
        assert filtered[-1].date == date(2020, 1, 15)

    def test_filter_both_dates(self, redetector, stocks):
        """시작/종료 날짜 모두 지정"""
        filtered = redetector._filter_by_date_range(
            stocks,
            start_date=date(2020, 1, 10),
            end_date=date(2020, 1, 20)
        )

        assert len(filtered) == 11  # 2020-01-10 ~ 2020-01-20
        assert filtered[0].date == date(2020, 1, 10)
        assert filtered[-1].date == date(2020, 1, 20)

    def test_filter_empty_result(self, redetector, stocks):
        """필터 결과 없음"""
        filtered = redetector._filter_by_date_range(
            stocks,
            start_date=date(2021, 1, 1),  # 범위 밖
            end_date=date(2021, 12, 31)
        )

        assert len(filtered) == 0


class TestSeedContextBuilding:
    """Seed context 구축 테스트"""

    @pytest.fixture
    def redetector(self):
        """DynamicPatternRedetector 인스턴스"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig()
        )
        engine = Mock(spec=ExpressionEngine)
        return DynamicPatternRedetector(graph, engine)

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
            price_shape=[0.0, 0.5, 1.0],
            volume_shape=[0.2, 1.0, 0.5]
        )

    def test_build_seed_context(self, redetector, seed_pattern):
        """Seed context 구축 테스트"""
        context = redetector._build_seed_context(seed_pattern)

        # Block1 context
        assert "block1" in context
        assert context["block1"]["block_type"] == 1
        assert context["block1"]["low"] == 10000.0
        assert context["block1"]["high"] == 12000.0
        assert context["block1"]["peak_price"] == 12000.0
        assert context["block1"]["peak_volume"] == 500000
        assert context["block1"]["duration"] == 10

        # Block2 context
        assert "block2" in context
        assert context["block2"]["block_type"] == 2
        assert context["block2"]["low"] == 12000.0
        assert context["block2"]["peak_price"] == 14000.0

    def test_build_seed_context_dates(self, redetector, seed_pattern):
        """Seed context 날짜 포함 테스트"""
        context = redetector._build_seed_context(seed_pattern)

        assert context["block1"]["started_at"] == date(2020, 1, 1)
        assert context["block1"]["ended_at"] == date(2020, 1, 10)
        assert context["block1"]["peak_date"] == date(2020, 1, 10)


class TestCooldownFilter:
    """Cooldown 필터 테스트"""

    @pytest.fixture
    def redetector_20_days(self):
        """20일 cooldown redetector"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig(
                min_detection_interval_days=20
            )
        )
        engine = Mock(spec=ExpressionEngine)
        return DynamicPatternRedetector(graph, engine)

    @pytest.fixture
    def detections_close_dates(self):
        """가까운 날짜의 detection들"""
        return [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 1),
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 10),  # 9일 차이 (필터됨)
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 2, 1),   # 31일 차이 (통과)
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 2, 10),  # 9일 차이 (필터됨)
                metadata={}, parent_blocks=[]
            )
        ]

    def test_cooldown_filter(self, redetector_20_days, detections_close_dates):
        """Cooldown 필터 적용 테스트"""
        filtered = redetector_20_days._apply_cooldown_filter(detections_close_dates)

        # 첫 번째 (2020-01-01)와 세 번째 (2020-02-01)만 통과
        assert len(filtered) == 2
        assert filtered[0].started_at == date(2020, 1, 1)
        assert filtered[1].started_at == date(2020, 2, 1)

    def test_cooldown_disabled(self):
        """Cooldown 비활성화 (0일)"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig(
                min_detection_interval_days=0  # 비활성화
            )
        )
        engine = Mock(spec=ExpressionEngine)
        redetector = DynamicPatternRedetector(graph, engine)

        detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 1),
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 2),  # 1일 차이도 허용
                metadata={}, parent_blocks=[]
            )
        ]

        filtered = redetector._apply_cooldown_filter(detections)
        assert len(filtered) == 2  # 모두 통과

    def test_cooldown_empty_list(self, redetector_20_days):
        """빈 리스트 cooldown 필터"""
        filtered = redetector_20_days._apply_cooldown_filter([])
        assert len(filtered) == 0

    def test_cooldown_none_dates(self, redetector_20_days):
        """None started_at 처리"""
        detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=None,  # None
                metadata={}, parent_blocks=[]
            )
        ]

        filtered = redetector_20_days._apply_cooldown_filter(detections)
        assert len(filtered) == 0  # None은 제외


class TestPatternGrouping:
    """Pattern 그룹화 테스트"""

    @pytest.fixture
    def redetector(self):
        """DynamicPatternRedetector 인스턴스"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig()
        )
        engine = Mock(spec=ExpressionEngine)
        return DynamicPatternRedetector(graph, engine)

    def test_group_single_pattern(self, redetector):
        """단일 패턴 그룹화"""
        detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 1),
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2", block_type=2, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 15),  # 14일 차이 (같은 그룹)
                metadata={}, parent_blocks=[]
            )
        ]

        groups = redetector._group_by_pattern(detections)

        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_group_multiple_patterns(self, redetector):
        """여러 패턴 그룹화"""
        detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 1),
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 3, 1),  # 60일 차이 (다른 그룹)
                metadata={}, parent_blocks=[]
            )
        ]

        groups = redetector._group_by_pattern(detections)

        assert len(groups) == 2
        assert len(groups[0]) == 1
        assert len(groups[1]) == 1

    def test_group_empty_list(self, redetector):
        """빈 리스트 그룹화"""
        groups = redetector._group_by_pattern([])
        assert len(groups) == 0


class TestRedetectionSummary:
    """재탐지 결과 요약 테스트"""

    @pytest.fixture
    def redetector(self):
        """DynamicPatternRedetector 인스턴스"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig()
        )
        engine = Mock(spec=ExpressionEngine)
        return DynamicPatternRedetector(graph, engine)

    @pytest.fixture
    def redetections_with_scores(self):
        """유사도 점수가 포함된 redetection 결과"""
        return [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 1),
                metadata={'similarity_score': 0.85},
                parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block2", block_type=2, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 15),
                metadata={'similarity_score': 0.90},
                parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 6, 1),
                metadata={'similarity_score': 0.75},
                parent_blocks=[]
            )
        ]

    def test_summary_basic_stats(self, redetector, redetections_with_scores):
        """기본 통계 요약"""
        summary = redetector.get_redetection_summary(redetections_with_scores)

        assert summary['total_count'] == 3
        assert summary['avg_similarity'] == (0.85 + 0.90 + 0.75) / 3
        assert summary['max_similarity'] == 0.90
        assert summary['min_similarity'] == 0.75

    def test_summary_date_range(self, redetector, redetections_with_scores):
        """날짜 범위 요약"""
        summary = redetector.get_redetection_summary(redetections_with_scores)

        assert summary['date_range'] == (date(2020, 1, 1), date(2020, 6, 1))

    def test_summary_block_types(self, redetector, redetections_with_scores):
        """Block 타입 요약"""
        summary = redetector.get_redetection_summary(redetections_with_scores)

        assert set(summary['block_types']) == {1, 2}

    def test_summary_empty_list(self, redetector):
        """빈 리스트 요약"""
        summary = redetector.get_redetection_summary([])

        assert summary['total_count'] == 0
        assert summary['avg_similarity'] == 0.0
        assert summary['date_range'] is None

    def test_summary_no_scores(self, redetector):
        """유사도 점수 없는 경우"""
        detections_no_scores = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2020, 1, 1),
                metadata={},  # No similarity_score
                parent_blocks=[]
            )
        ]

        summary = redetector.get_redetection_summary(detections_no_scores)

        assert summary['total_count'] == 1
        assert summary['avg_similarity'] == 0.0


class TestRedetectPatternsIntegration:
    """redetect_patterns() 통합 테스트 (mock 사용)"""

    @pytest.fixture
    def redetector(self):
        """DynamicPatternRedetector 인스턴스"""
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig(
                min_similarity_score=0.70
            )
        )
        engine = Mock(spec=ExpressionEngine)
        return DynamicPatternRedetector(graph, engine)

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
                    block_id="block1", block_type=1,
                    started_at=date(2020, 1, 1), ended_at=date(2020, 1, 10),
                    duration_candles=10,
                    low_price=10000.0, high_price=12000.0,
                    peak_price=12000.0, peak_date=date(2020, 1, 10),
                    min_volume=100000, max_volume=500000,
                    peak_volume=500000, avg_volume=300000
                )
            ],
            price_shape=[0.0, 0.5, 1.0],
            volume_shape=[0.2, 1.0, 0.5]
        )

    @pytest.fixture
    def stocks(self):
        """테스트용 Stock 데이터"""
        return [
            Stock(ticker="025980", name="테스트종목", date=date(2021, 1, i),
                  open=10000, high=11000, low=9500, close=10000, volume=100000)
            for i in range(1, 31)
        ]

    @patch('src.application.use_cases.dynamic_block_detector.DynamicBlockDetector')
    def test_redetect_patterns_full_flow(self, mock_detector_class, redetector, seed_pattern, stocks):
        """전체 재탐지 플로우 테스트 (mock)"""
        # Mock DynamicBlockDetector
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        # Mock detections (high similarity)
        mock_detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                ended_at=date(2021, 1, 10),
                peak_price=11900.0,
                peak_volume=490000,
                metadata={}, parent_blocks=[]
            )
        ]
        mock_detector.detect_blocks.return_value = mock_detections

        # Execute
        redetections = redetector.redetect_patterns(
            seed_pattern=seed_pattern,
            ticker="025980",
            stocks=stocks
        )

        # Verify DynamicBlockDetector was called
        mock_detector.detect_blocks.assert_called_once()

        # Verify results
        assert isinstance(redetections, list)
        # Results may be filtered by similarity threshold

    def test_redetect_patterns_empty_stocks(self, redetector, seed_pattern):
        """빈 stock 데이터"""
        redetections = redetector.redetect_patterns(
            seed_pattern=seed_pattern,
            ticker="025980",
            stocks=[]
        )

        assert redetections == []
