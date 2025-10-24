"""
Extended Block Validation Tests (Block5, Block6, ..., BlockN)

Phase 6: Block Count Validation
- Verify unlimited blocks work without code changes
- Only YAML configuration needed to add new block types
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
    """Extended pattern YAML 파일 경로"""
    return str(Path(__file__).parent.parent.parent / 'presets' / 'examples' / 'extended_pattern_example.yaml')


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
def extended_stock_data():
    """6개 블록을 모두 트리거하는 주가 데이터 생성"""
    base_date = date(2024, 1, 1)
    stocks = []

    # Day 1-2: 진입 전
    for i in range(2):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=9000,
            high=9500,
            low=8500,
            close=9200,
            volume=500000
        ))

    # Day 3-4: Block1 시작 (close >= 10000, volume >= 1M)
    for i in range(2, 4):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=9500,
            high=10500,
            low=9000,
            close=10200,
            volume=1200000
        ))

    # Day 5-6: Block2 시작 (close >= 11000, volume >= 800k)
    for i in range(4, 6):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=10200,
            high=11500,
            low=10000,
            close=11200,
            volume=900000
        ))

    # Day 7-8: Block3 시작 (close >= 12000)
    for i in range(6, 8):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=11200,
            high=12500,
            low=11000,
            close=12200,
            volume=800000
        ))

    # Day 9-10: Block4 시작 (close >= 13000, volume >= 600k)
    for i in range(8, 10):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=12200,
            high=13500,
            low=12000,
            close=13200,
            volume=700000
        ))

    # Day 11-12: Block5 시작 (close >= 14000, volume >= 700k)
    for i in range(10, 12):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=13200,
            high=14500,
            low=13000,
            close=14200,
            volume=750000
        ))

    # Day 13-14: Block6 시작 (close >= 15000, volume >= 800k)
    for i in range(12, 14):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=14200,
            high=15500,
            low=14000,
            close=15200,
            volume=850000
        ))

    # Day 15-16: Block6 진행
    for i in range(14, 16):
        stocks.append(MockStock(
            ticker='025980',
            date=base_date + timedelta(days=i),
            open=15200,
            high=15800,
            low=15000,
            close=15600,
            volume=820000
        ))

    # Day 17: Block6 종료 (volume < 300k)
    stocks.append(MockStock(
        ticker='025980',
        date=base_date + timedelta(days=16),
        open=15600,
        high=15700,
        low=15400,
        close=15500,
        volume=250000
    ))

    return stocks


class TestExtendedBlocks:
    """Block5, Block6 확장 블록 검증"""

    def test_yaml_loads_6_blocks(self, yaml_path, loader):
        """
        YAML에서 6개 블록 로드 확인
        """
        block_graph = loader.load_from_file(yaml_path)

        # 6개 노드 확인
        assert len(block_graph.nodes) == 6
        assert 'block1' in block_graph.nodes
        assert 'block2' in block_graph.nodes
        assert 'block3' in block_graph.nodes
        assert 'block4' in block_graph.nodes
        assert 'block5' in block_graph.nodes
        assert 'block6' in block_graph.nodes

        # 5개 엣지 확인 (Block1→2→3→4→5→6)
        assert len(block_graph.edges) == 5

        # Root 노드 확인
        assert block_graph.root_node_id == 'block1'

    def test_yaml_validation_passes(self, yaml_path, loader):
        """
        그래프 검증 통과 확인
        """
        block_graph = loader.load_from_file(yaml_path)

        errors = block_graph.validate()
        assert len(errors) == 0

    def test_topological_sort_6_blocks(self, yaml_path, loader):
        """
        위상 정렬로 Block1→Block2→...→Block6 순서 확인
        """
        block_graph = loader.load_from_file(yaml_path)

        sorted_ids = block_graph.topological_sort()
        assert sorted_ids == ['block1', 'block2', 'block3', 'block4', 'block5', 'block6']

    def test_detect_all_6_blocks(
        self,
        yaml_path,
        loader,
        expression_engine,
        extended_stock_data
    ):
        """
        6개 블록 모두 감지됨 확인
        """
        # BlockGraph 로드
        block_graph = loader.load_from_file(yaml_path)

        # Detector 생성
        detector = DynamicBlockDetector(block_graph, expression_engine)

        # 블록 감지
        detections = detector.detect_blocks('025980', extended_stock_data, condition_name='seed')

        # 6개 블록 모두 감지됨
        assert len(detections) == 6

        block_ids = {d.block_id for d in detections}
        assert block_ids == {'block1', 'block2', 'block3', 'block4', 'block5', 'block6'}

    def test_block5_detection(
        self,
        yaml_path,
        loader,
        expression_engine,
        extended_stock_data
    ):
        """
        Block5 감지 확인 (코드 변경 없이 YAML만으로 동작)
        """
        block_graph = loader.load_from_file(yaml_path)
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', extended_stock_data)

        # Block5 조회
        block5 = next((d for d in detections if d.block_id == 'block5'), None)
        assert block5 is not None

        # Block5 검증
        assert block5.block_type == 5
        assert block5.started_at == date(2024, 1, 11)  # Day 11
        assert block5.ticker == '025980'
        # Block5는 Day 17에 volume < 400k로 종료됨
        assert block5.is_completed()
        assert block5.ended_at == date(2024, 1, 17)

    def test_block6_detection(
        self,
        yaml_path,
        loader,
        expression_engine,
        extended_stock_data
    ):
        """
        Block6 감지 확인 (코드 변경 없이 YAML만으로 동작)
        """
        block_graph = loader.load_from_file(yaml_path)
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', extended_stock_data)

        # Block6 조회
        block6 = next((d for d in detections if d.block_id == 'block6'), None)
        assert block6 is not None

        # Block6 검증
        assert block6.block_type == 6
        assert block6.started_at == date(2024, 1, 13)  # Day 13
        assert block6.is_completed()  # Day 17에 종료
        assert block6.ended_at == date(2024, 1, 17)

    def test_block_chain_integrity(
        self,
        yaml_path,
        loader,
        expression_engine,
        extended_stock_data
    ):
        """
        블록 체인 무결성 확인 (Block1→Block2→...→Block6)
        """
        block_graph = loader.load_from_file(yaml_path)
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', extended_stock_data)

        # Block ID로 정렬
        detections_sorted = sorted(detections, key=lambda d: d.block_type)

        # 시작 날짜 순서 확인
        for i in range(len(detections_sorted) - 1):
            current_block = detections_sorted[i]
            next_block = detections_sorted[i + 1]

            # 다음 블록은 현재 블록 이후에 시작
            assert next_block.started_at >= current_block.started_at

    def test_peak_tracking_block5_block6(
        self,
        yaml_path,
        loader,
        expression_engine,
        extended_stock_data
    ):
        """
        Block5, Block6의 Peak 추적 확인
        """
        block_graph = loader.load_from_file(yaml_path)
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', extended_stock_data)

        # Block5 peak 검증
        block5 = next(d for d in detections if d.block_id == 'block5')
        # Block5는 Day 17에 종료되었으므로 Block5 기간(Day 11-17) 동안의 최고가
        # Day 15-16에 15800이 최고가
        assert block5.peak_price == 15800
        assert block5.is_completed()

        # Block6 peak 검증
        block6 = next(d for d in detections if d.block_id == 'block6')
        # Block6도 Day 17에 완료되었으므로 Block6 기간 동안의 최고가
        assert block6.peak_price == 15800
        assert block6.is_completed()

    def test_persistence_6_blocks(
        self,
        yaml_path,
        loader,
        expression_engine,
        repository,
        extended_stock_data
    ):
        """
        6개 블록 영속성 확인 (Repository에 저장/조회)
        """
        # BlockGraph 로드
        block_graph = loader.load_from_file(yaml_path)

        # 블록 감지
        detector = DynamicBlockDetector(block_graph, expression_engine)
        detections = detector.detect_blocks('025980', extended_stock_data, condition_name='seed')

        # Repository에 저장
        saved_detections = repository.save_all(detections)

        # 저장 성공
        assert len(saved_detections) == 6
        assert all(d.id is not None for d in saved_detections)

        # Repository에서 다시 조회
        loaded_detections = repository.find_by_ticker('025980', condition_name='seed')

        # 조회 성공
        assert len(loaded_detections) == 6

        # Block5, Block6 확인
        loaded_block5 = next(d for d in loaded_detections if d.block_id == 'block5')
        loaded_block6 = next(d for d in loaded_detections if d.block_id == 'block6')

        assert loaded_block5.block_type == 5
        assert loaded_block6.block_type == 6

    def test_no_code_changes_needed(self, yaml_path, loader):
        """
        코드 변경 없이 YAML만으로 Block5, Block6 정의 확인

        이 테스트는 conceptual validation:
        - DynamicBlockDetector는 block_type을 하드코딩하지 않음
        - BlockGraph는 노드 개수 제한이 없음
        - ExpressionEngine은 조건 개수 제한이 없음
        """
        block_graph = loader.load_from_file(yaml_path)

        # Block5 노드 확인
        block5_node = block_graph.get_node('block5')
        assert block5_node is not None
        assert block5_node.block_type == 5
        assert block5_node.name == "Fourth Continuation"
        assert len(block5_node.entry_conditions) == 2
        assert len(block5_node.exit_conditions) == 2

        # Block6 노드 확인
        block6_node = block_graph.get_node('block6')
        assert block6_node is not None
        assert block6_node.block_type == 6
        assert block6_node.name == "Final Peak"
        assert len(block6_node.entry_conditions) == 2
        assert len(block6_node.exit_conditions) == 2

        # 엣지 확인 (Block5→Block6)
        edges_from_block5 = block_graph.get_edges_from('block5')
        assert len(edges_from_block5) == 1
        assert edges_from_block5[0].to_block_id == 'block6'
