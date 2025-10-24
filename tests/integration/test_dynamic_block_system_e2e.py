"""
Dynamic Block System End-to-End Integration Test

전체 파이프라인 테스트:
YAML → BlockGraph → Detector → Repository
"""
import pytest
from datetime import date, timedelta
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.conditions import ExpressionEngine, function_registry
from src.infrastructure.database.models.base import Base
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl


# Mock Stock for testing
@dataclass
class MockStock:
    """테스트용 Mock Stock"""
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    indicators: dict = None

    def __post_init__(self):
        if self.indicators is None:
            self.indicators = {}


@pytest.fixture
def yaml_path():
    """YAML 예제 파일 경로"""
    return str(Path(__file__).parent.parent.parent / 'presets' / 'examples' / 'simple_pattern_example.yaml')


@pytest.fixture
def engine():
    """테스트용 인메모리 DB"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """테스트용 세션"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(session):
    """Repository"""
    return DynamicBlockRepositoryImpl(session)


@pytest.fixture
def loader():
    """BlockGraphLoader"""
    return BlockGraphLoader()


@pytest.fixture
def expression_engine():
    """ExpressionEngine"""
    return ExpressionEngine(function_registry)


@pytest.fixture
def sample_stock_data():
    """샘플 주가 데이터 생성"""
    base_date = date(2024, 1, 1)
    stocks = []

    # Day 1-3: Block1 진입 조건 불만족
    for i in range(3):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=9000,
            high=9500,
            low=8500,
            close=9200,
            volume=500000
        ))

    # Day 4: Block1 시작 (close >= 10000, volume >= 1M)
    stocks.append(MockStock(
        ticker='025980',
        date=base_date + timedelta(days=3),
        open=9500,
        high=10500,
        low=9000,
        close=10200,
        volume=1200000
    ))

    # Day 5-6: Block1 진행
    for i in range(4, 6):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=10200,
            high=10800,
            low=10000,
            close=10600,
            volume=1100000
        ))

    # Day 7: Block2 시작 (close >= 11000, volume >= 800k)
    stocks.append(MockStock(
        ticker='025980',
        date=base_date + timedelta(days=6),
        open=10600,
        high=11500,
        low=10500,
        close=11200,
        volume=900000
    ))

    # Day 8-9: Block2 진행
    for i in range(7, 9):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=11200,
            high=11800,
            low=11000,
            close=11600,
            volume=850000
        ))

    # Day 10: Block3 시작 (close >= 12000)
    stocks.append(MockStock(
        ticker='025980',
        date=base_date + timedelta(days=9),
        open=11600,
        high=12500,
        low=11500,
        close=12200,
        volume=1000000
    ))

    # Day 11-12: Block3 진행
    for i in range(10, 12):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=12200,
            high=12800,
            low=12000,
            close=12600,
            volume=950000
        ))

    # Day 13: Block3 종료 (volume < 500k)
    stocks.append(MockStock(
        ticker='025980',
        date=base_date + timedelta(days=12),
        open=12600,
        high=12700,
        low=12400,
        close=12500,
        volume=400000
    ))

    return stocks


class TestDynamicBlockSystemE2E:
    """End-to-End 통합 테스트"""

    def test_full_pipeline_yaml_to_detection(
        self,
        yaml_path,
        loader,
        expression_engine,
        sample_stock_data
    ):
        """
        전체 파이프라인 테스트: YAML → BlockGraph → Detection
        """
        # 1. YAML 파일에서 BlockGraph 로드
        block_graph = loader.load_from_file(yaml_path)

        # 검증: 그래프 구조
        assert len(block_graph.nodes) == 3
        assert 'block1' in block_graph.nodes
        assert 'block2' in block_graph.nodes
        assert 'block3' in block_graph.nodes
        assert len(block_graph.edges) == 2

        # 2. Detector 생성 및 블록 감지
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', sample_stock_data, condition_name='seed')

        # 검증: 3개 블록 모두 감지됨
        assert len(detections) == 3

        block_ids = {d.block_id for d in detections}
        assert block_ids == {'block1', 'block2', 'block3'}

        # 검증: Block1
        block1 = next(d for d in detections if d.block_id == 'block1')
        assert block1.block_type == 1
        assert block1.started_at == date(2024, 1, 4)  # Day 4
        assert block1.is_active()  # 종료 조건 미충족

        # 검증: Block2
        block2 = next(d for d in detections if d.block_id == 'block2')
        assert block2.block_type == 2
        assert block2.started_at == date(2024, 1, 7)  # Day 7
        assert block2.is_active()

        # 검증: Block3
        block3 = next(d for d in detections if d.block_id == 'block3')
        assert block3.block_type == 3
        assert block3.started_at == date(2024, 1, 10)  # Day 10
        assert block3.is_completed()  # Day 13에 종료 조건 충족
        assert block3.ended_at == date(2024, 1, 13)

    def test_full_pipeline_with_persistence(
        self,
        yaml_path,
        loader,
        expression_engine,
        repository,
        sample_stock_data
    ):
        """
        전체 파이프라인 + 영속성 테스트: YAML → Detection → Repository
        """
        # 1. BlockGraph 로드
        block_graph = loader.load_from_file(yaml_path)

        # 2. 블록 감지
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', sample_stock_data, condition_name='seed')

        # 3. Repository에 저장
        saved_detections = repository.save_all(detections)

        # 검증: 저장 성공
        assert len(saved_detections) == 3
        assert all(d.id is not None for d in saved_detections)

        # 4. Repository에서 다시 조회
        loaded_detections = repository.find_by_ticker('025980', condition_name='seed')

        # 검증: 조회 성공
        assert len(loaded_detections) == 3

        # 검증: 데이터 일치
        for original, loaded in zip(saved_detections, loaded_detections):
            assert loaded.block_id == original.block_id
            assert loaded.block_type == original.block_type
            assert loaded.started_at == original.started_at
            assert loaded.status == original.status

    def test_incremental_detection_with_active_blocks(
        self,
        yaml_path,
        loader,
        expression_engine,
        repository,
        sample_stock_data
    ):
        """
        점진적 감지 테스트: 진행 중인 블록을 전달하여 계속 추적
        """
        # 1. BlockGraph 로드
        block_graph = loader.load_from_file(yaml_path)
        detector = DynamicBlockDetector(block_graph, expression_engine)

        # 2. 첫 번째 배치 (Day 1-7)
        first_batch = sample_stock_data[:7]
        detections_batch1 = detector.detect_blocks('025980', first_batch, condition_name='seed')

        # 저장
        saved_batch1 = repository.save_all(detections_batch1)

        # 검증: Block1, Block2 감지됨
        assert len(saved_batch1) == 2

        # 3. 두 번째 배치 (Day 8-13) - 진행 중인 블록 전달
        second_batch = sample_stock_data[7:]

        # 진행 중인 블록 조회
        active_blocks = repository.find_active_blocks('025980')

        # 감지 (active_blocks 전달)
        detections_batch2 = detector.detect_blocks(
            '025980',
            second_batch,
            condition_name='seed',
            active_blocks=active_blocks
        )

        # 저장
        saved_batch2 = repository.save_all(detections_batch2)

        # 검증: Block3 추가 감지됨
        all_detections = repository.find_by_ticker('025980')
        assert len(all_detections) == 3

        # Block3 검증
        block3 = next(d for d in all_detections if d.block_id == 'block3')
        assert block3.is_completed()

    def test_block_graph_validation(self, yaml_path, loader):
        """BlockGraph 검증 테스트"""
        block_graph = loader.load_from_file(yaml_path)

        # 그래프 검증
        errors = block_graph.validate()
        assert len(errors) == 0

        # DAG 검증 (위상 정렬 가능)
        sorted_ids = block_graph.topological_sort()
        assert sorted_ids == ['block1', 'block2', 'block3']

    def test_peak_tracking_through_pipeline(
        self,
        yaml_path,
        loader,
        expression_engine,
        sample_stock_data
    ):
        """Peak 추적 테스트"""
        # BlockGraph 로드
        block_graph = loader.load_from_file(yaml_path)

        # 블록 감지
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', sample_stock_data)

        # Block1 peak 검증
        block1 = next(d for d in detections if d.block_id == 'block1')
        # Block1은 종료되지 않아 전체 데이터의 최고가를 추적
        # Day 11-12에 12800이 최고가
        assert block1.peak_price == 12800
        assert block1.is_active()  # 종료 조건 미충족

        # Block2 peak 검증
        block2 = next(d for d in detections if d.block_id == 'block2')
        # Block2도 종료되지 않아 Block2 시작 이후의 최고가 추적
        assert block2.peak_price == 12800
        assert block2.is_active()

        # Block3 peak 검증
        block3 = next(d for d in detections if d.block_id == 'block3')
        # Block3는 완료되었으므로 Block3 기간 동안의 최고가
        assert block3.peak_price == 12800
        assert block3.is_completed()

    def test_condition_evaluation_errors_handled(
        self,
        loader,
        expression_engine,
        sample_stock_data
    ):
        """조건 평가 에러 처리 테스트"""
        # 잘못된 조건이 포함된 그래프 생성
        from src.domain.entities.block_graph import BlockGraph, BlockNode

        graph = BlockGraph()
        node = BlockNode(
            block_id='block1',
            block_type=1,
            name='Test Block',
            entry_conditions=['invalid_function()']  # 존재하지 않는 함수
        )
        graph.add_node(node)

        # Detector 생성
        detector = DynamicBlockDetector(graph, expression_engine)

        # 감지 실행 (에러 발생하지 않아야 함)
        detections = detector.detect_blocks('025980', sample_stock_data)

        # 조건 평가 실패로 감지 안 됨
        assert len(detections) == 0

    def test_yaml_roundtrip(self, yaml_path, loader, tmp_path):
        """YAML 왕복 테스트: load → save → load"""
        # 1. YAML 로드
        original_graph = loader.load_from_file(yaml_path)

        # 2. 새 YAML 파일로 저장
        output_path = tmp_path / 'roundtrip_test.yaml'
        loader.save_to_file(original_graph, str(output_path))

        # 3. 저장된 YAML 파일 다시 로드
        loaded_graph = loader.load_from_file(str(output_path))

        # 4. 비교
        assert len(loaded_graph.nodes) == len(original_graph.nodes)
        assert len(loaded_graph.edges) == len(original_graph.edges)
        assert loaded_graph.root_node_id == original_graph.root_node_id

        # 노드 비교
        for node_id in original_graph.nodes:
            assert node_id in loaded_graph.nodes
            orig_node = original_graph.nodes[node_id]
            loaded_node = loaded_graph.nodes[node_id]
            assert loaded_node.block_type == orig_node.block_type
            assert loaded_node.name == orig_node.name
