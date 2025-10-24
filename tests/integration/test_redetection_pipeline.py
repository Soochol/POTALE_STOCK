"""
Integration Tests for Redetection Pipeline

Seed pattern 생성부터 재탐지까지 E2E 테스트
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.use_cases.dynamic_pattern_redetector import DynamicPatternRedetector
from src.application.services.similarity_calculator import SimilarityCalculator
from src.application.services.block_graph_loader import BlockGraphLoader
from src.domain.entities.patterns import (
    SeedPattern,
    BlockFeatures,
    RedetectionConfig,
    ToleranceConfig,
    MatchingWeights
)
from src.domain.entities.block_graph import BlockGraph
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.core import Stock
from src.domain.entities.conditions import ExpressionEngine
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.seed_pattern_repository_impl import SeedPatternRepositoryImpl


class TestRedetectionPipelineE2E:
    """End-to-End 재탐지 파이프라인 테스트"""

    @pytest.fixture
    def db_session(self):
        """In-memory SQLite database session"""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def seed_pattern_repository(self, db_session):
        """SeedPatternRepository 구현체"""
        return SeedPatternRepositoryImpl(db_session)

    @pytest.fixture
    def redetection_yaml_content(self):
        """Redetection YAML 설정"""
        return {
            'block_graph': {
                'pattern_type': 'redetection',
                'root_node': 'block1',
                'redetection_config': {
                    'seed_pattern_reference': 'test_seed_pattern',
                    'tolerance': {
                        'price_range': 0.10,
                        'volume_range': 0.30,
                        'time_range': 5
                    },
                    'matching_weights': {
                        'price_shape': 0.4,
                        'volume_shape': 0.3,
                        'timing': 0.3
                    },
                    'min_similarity_score': 0.70,
                    'min_detection_interval_days': 20
                },
                'nodes': {
                    'block1': {
                        'block_id': 'block1',
                        'block_type': 1,
                        'name': 'Block1 Redetection',
                        'entry_conditions': [
                            {
                                'name': 'test_condition',
                                'expression': 'current.close > 10000',
                                'description': 'Test condition'
                            }
                        ],
                        'exit_conditions': [
                            {
                                'name': 'test_exit',
                                'expression': 'current.close < 9000',
                                'description': 'Test exit'
                            }
                        ],
                        'parameters': {
                            'min_duration': 1,
                            'max_duration': 100
                        }
                    }
                },
                'edges': []
            }
        }

    @pytest.fixture
    def redetection_graph(self, redetection_yaml_content, tmp_path):
        """Redetection BlockGraph (YAML에서 로드)"""
        # YAML 파일 생성
        yaml_file = tmp_path / "redetection_test.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(redetection_yaml_content, f, allow_unicode=True)

        # BlockGraphLoader로 로드
        loader = BlockGraphLoader()
        graph = loader.load_from_file(str(yaml_file))

        return graph

    @pytest.fixture
    def seed_pattern(self):
        """테스트용 Seed Pattern"""
        return SeedPattern(
            pattern_name="test_seed_pattern",
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
                )
            ],
            price_shape=[0.0, 0.2, 0.5, 0.8, 1.0],
            volume_shape=[0.2, 0.5, 1.0, 0.7, 0.4]
        )

    @pytest.fixture
    def historical_stocks(self):
        """Historical stock 데이터 (재탐지 대상)"""
        stocks = []
        base_date = date(2021, 1, 1)

        # 100일간의 데이터
        for i in range(100):
            close_price = 10000 + i * 50
            stocks.append(
                Stock(
                    ticker="025980",
                    name="테스트종목",
                    date=base_date + timedelta(days=i),
                    open=10000,
                    high=11000,
                    low=9500,
                    close=min(close_price, 10900),  # Ensure close <= high
                    volume=100000 + i * 1000
                )
            )

        return stocks

    def test_save_and_load_seed_pattern(self, seed_pattern_repository, seed_pattern):
        """Seed pattern 저장 및 로드 테스트"""
        # Save
        saved = seed_pattern_repository.save(seed_pattern)
        assert saved.id is not None

        # Load
        loaded = seed_pattern_repository.find_by_id(saved.id)
        assert loaded is not None
        assert loaded.pattern_name == seed_pattern.pattern_name
        assert len(loaded.block_features) == 1
        assert loaded.block_features[0].block_id == "block1"

    def test_load_redetection_graph_from_yaml(self, redetection_graph):
        """YAML에서 redetection graph 로드 테스트"""
        assert redetection_graph.pattern_type == "redetection"
        assert redetection_graph.redetection_config is not None
        assert redetection_graph.redetection_config.seed_pattern_reference == "test_seed_pattern"
        assert redetection_graph.redetection_config.min_similarity_score == 0.70

    def test_initialize_redetector_with_loaded_graph(self, redetection_graph):
        """로드된 graph로 redetector 초기화"""
        engine = ExpressionEngine()
        redetector = DynamicPatternRedetector(redetection_graph, engine)

        assert redetector.redetection_graph == redetection_graph
        assert redetector.redetection_config is not None
        assert redetector.similarity_calculator is not None

    def test_build_seed_context_from_db_pattern(self, seed_pattern_repository, seed_pattern):
        """DB에서 로드한 seed pattern으로 context 구축"""
        # Save to DB
        saved = seed_pattern_repository.save(seed_pattern)

        # Load from DB
        loaded = seed_pattern_repository.find_by_id(saved.id)

        # Build context
        graph = BlockGraph(
            pattern_type="redetection",
            redetection_config=RedetectionConfig()
        )
        engine = ExpressionEngine()
        redetector = DynamicPatternRedetector(graph, engine)

        context = redetector._build_seed_context(loaded)

        assert "block1" in context
        assert context["block1"]["peak_price"] == 12000.0
        assert context["block1"]["peak_volume"] == 500000

    def test_similarity_calculator_with_real_data(self, seed_pattern):
        """실제 데이터로 유사도 계산 테스트"""
        config = RedetectionConfig(
            tolerance=ToleranceConfig(price_range=0.10, volume_range=0.30, time_range=5),
            matching_weights=MatchingWeights(price_shape=0.4, volume_shape=0.3, timing=0.3),
            min_similarity_score=0.70
        )

        calculator = SimilarityCalculator(config)

        # Similar detection
        similar_detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="redetection",
            started_at=date(2021, 1, 1),
            ended_at=date(2021, 1, 10),
            peak_price=11800.0,  # 12000 - 1.67%
            peak_volume=480000,  # 500000 - 4%
            metadata={},
            parent_blocks=[]
        )

        score = calculator.calculate(seed_pattern, [similar_detection])

        assert score.total_score > 0.70  # Should meet threshold
        assert calculator.meets_threshold(score)

    def test_full_redetection_workflow_mock(
        self,
        seed_pattern_repository,
        seed_pattern,
        redetection_graph,
        historical_stocks
    ):
        """전체 재탐지 워크플로우 (mock detector)"""
        # 1. Save seed pattern to DB
        saved_seed = seed_pattern_repository.save(seed_pattern)
        assert saved_seed.id is not None

        # 2. Load seed pattern from DB
        loaded_seed = seed_pattern_repository.find_by_id(saved_seed.id)
        assert loaded_seed is not None

        # 3. Initialize redetector
        engine = ExpressionEngine()
        redetector = DynamicPatternRedetector(redetection_graph, engine)

        # 4. Build seed context
        seed_context = redetector._build_seed_context(loaded_seed)
        assert "block1" in seed_context

        # 5. Apply date filtering
        filtered_stocks = redetector._filter_by_date_range(
            historical_stocks,
            start_date=date(2021, 1, 1),
            end_date=date(2021, 3, 31)
        )
        assert len(filtered_stocks) > 0
        assert len(filtered_stocks) < len(historical_stocks)

        # Note: Full detection requires DynamicBlockDetector integration
        # which is tested separately in detector tests

    def test_cooldown_filter_with_real_detections(self, redetection_graph):
        """실제 detection 데이터로 cooldown 필터 테스트"""
        engine = ExpressionEngine()
        redetector = DynamicPatternRedetector(redetection_graph, engine)

        # Multiple detections with various intervals
        detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 10),  # 9일 간격 (필터됨)
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 2, 1),   # 22일 간격 (통과)
                metadata={}, parent_blocks=[]
            )
        ]

        filtered = redetector._apply_cooldown_filter(detections)

        # min_detection_interval_days=20이므로 2개만 통과
        assert len(filtered) == 2
        assert filtered[0].started_at == date(2021, 1, 1)
        assert filtered[1].started_at == date(2021, 2, 1)

    def test_pattern_grouping_logic(self, redetection_graph):
        """Pattern 그룹화 로직 테스트"""
        engine = ExpressionEngine()
        redetector = DynamicPatternRedetector(redetection_graph, engine)

        # Two separate patterns (60 days apart)
        detections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                metadata={}, parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 3, 15),  # 73일 간격
                metadata={}, parent_blocks=[]
            )
        ]

        groups = redetector._group_by_pattern(detections)

        # 30일 이상 차이나므로 2개 그룹
        assert len(groups) == 2

    def test_redetection_summary_generation(self, redetection_graph):
        """재탐지 요약 생성 테스트"""
        engine = ExpressionEngine()
        redetector = DynamicPatternRedetector(redetection_graph, engine)

        redetections = [
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 1, 1),
                metadata={'similarity_score': 0.85},
                parent_blocks=[]
            ),
            DynamicBlockDetection(
                block_id="block1", block_type=1, ticker="025980",
                condition_name="redetection",
                started_at=date(2021, 6, 1),
                metadata={'similarity_score': 0.78},
                parent_blocks=[]
            )
        ]

        summary = redetector.get_redetection_summary(redetections)

        assert summary['total_count'] == 2
        assert summary['avg_similarity'] == (0.85 + 0.78) / 2
        assert summary['max_similarity'] == 0.85
        assert summary['min_similarity'] == 0.78
        assert summary['date_range'] == (date(2021, 1, 1), date(2021, 6, 1))

    def test_yaml_roundtrip_with_redetection_config(self, redetection_yaml_content, tmp_path):
        """YAML 왕복 변환 테스트 (redetection config 포함)"""
        # Save to YAML
        yaml_file = tmp_path / "roundtrip_test.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(redetection_yaml_content, f, allow_unicode=True)

        # Load from YAML
        loader = BlockGraphLoader()
        loaded_graph = loader.load_from_file(str(yaml_file))

        # Verify redetection config
        assert loaded_graph.pattern_type == "redetection"
        assert loaded_graph.redetection_config is not None
        assert loaded_graph.redetection_config.tolerance.price_range == 0.10
        assert loaded_graph.redetection_config.matching_weights.price_shape == 0.4
        assert loaded_graph.redetection_config.min_similarity_score == 0.70

        # Save back to YAML
        yaml_file_2 = tmp_path / "roundtrip_test_2.yaml"
        loader.save_to_file(loaded_graph, str(yaml_file_2))

        # Load again
        loaded_graph_2 = loader.load_from_file(str(yaml_file_2))

        # Verify consistency
        assert loaded_graph_2.pattern_type == loaded_graph.pattern_type
        assert loaded_graph_2.redetection_config.tolerance.price_range == \
               loaded_graph.redetection_config.tolerance.price_range
