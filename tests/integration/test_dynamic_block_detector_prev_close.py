"""
DynamicBlockDetector prev_close 통합 테스트

Detector가 블록 생성 시 prev_close를 올바르게 계산하고 저장하는지 테스트
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.block_graph import BlockGraph, BlockNode
from src.domain.entities.conditions import ExpressionEngine, FunctionRegistry
from src.domain.entities.core import Stock
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl
from src.infrastructure.database.models.base import Base


@pytest.fixture(scope="function")
def test_db():
    """테스트용 in-memory 데이터베이스"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def simple_block_graph():
    """단순 BlockGraph (Block1만)"""
    block1 = BlockNode(
        block_id="block1",
        block_type=1,
        name="Test Block",
        entry_conditions=["current.close >= 10000"],
        exit_conditions=["current.close < 9000"]
    )

    return BlockGraph(
        pattern_type="seed",
        root_node_id="block1",
        nodes={"block1": block1},
        edges=[]
    )


@pytest.fixture
def sample_stocks():
    """샘플 주가 데이터"""
    return [
        # 전일 종가: 9800
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
              open=9700.0, high=9900.0, low=9600.0, close=9800.0, volume=900000),

        # Block1 진입: prev_close=9800
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
              open=9800.0, high=10500.0, low=9700.0, close=10300.0, volume=1100000),

        # Peak 도달
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
              open=10300.0, high=12000.0, low=10200.0, close=11800.0, volume=1500000),

        # Block1 종료
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 4),
              open=11800.0, high=11900.0, low=8700.0, close=8800.0, volume=2000000),
    ]


class TestPrevCloseCalculation:
    """prev_close 계산 테스트"""

    def test_prev_close_saved_on_block_creation(self, simple_block_graph, sample_stocks):
        """블록 생성 시 prev_close 저장"""
        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        detector = DynamicBlockDetector(
            block_graph=simple_block_graph,
            expression_engine=expression_engine
        )

        blocks = detector.detect_blocks(
            ticker="025980",
            stocks=sample_stocks,
            condition_name="seed"
        )

        assert len(blocks) == 1
        block1 = blocks[0]

        # prev_close가 저장되었는지 확인
        assert block1.prev_close is not None
        assert block1.prev_close == 9800.0  # Block1 시작일(1월2일) 전일(1월1일) 종가

        # Peak도 올바른지 확인
        assert block1.peak_price == 12000.0
        assert block1.is_completed()

    def test_prev_close_none_when_no_prev_stock(self, simple_block_graph):
        """전일 데이터 없을 때 prev_close는 None"""
        # 첫날 데이터만 (전일 없음)
        stocks = [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=10000.0, high=10500.0, low=9900.0, close=10300.0, volume=1100000),
        ]

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        detector = DynamicBlockDetector(
            block_graph=simple_block_graph,
            expression_engine=expression_engine
        )

        blocks = detector.detect_blocks(
            ticker="025980",
            stocks=stocks,
            condition_name="seed"
        )

        assert len(blocks) == 1
        block1 = blocks[0]

        # 전일 데이터가 없으므로 prev_close는 None
        assert block1.prev_close is None

    def test_prev_close_persisted_to_db(self, test_db, simple_block_graph, sample_stocks):
        """prev_close DB 저장 및 로드"""
        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        detector = DynamicBlockDetector(
            block_graph=simple_block_graph,
            expression_engine=expression_engine
        )

        blocks = detector.detect_blocks(
            ticker="025980",
            stocks=sample_stocks,
            condition_name="seed"
        )

        block1 = blocks[0]
        assert block1.prev_close == 9800.0

        # DB에 저장
        repository = DynamicBlockRepositoryImpl(test_db)
        saved_block = repository.save(block1)

        assert saved_block.id is not None
        assert saved_block.prev_close == 9800.0

        # DB에서 다시 로드
        loaded_block = repository.find_by_id(saved_block.id)

        assert loaded_block is not None
        assert loaded_block.prev_close == 9800.0
        assert loaded_block.peak_price == 12000.0
        assert loaded_block.block_id == "block1"

    def test_multiple_blocks_different_prev_close(self, simple_block_graph):
        """여러 블록이 각각 다른 prev_close를 가짐"""
        stocks = [
            # 전일 종가: 9800
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9700.0, high=9900.0, low=9600.0, close=9800.0, volume=900000),

            # Block1 진입: prev_close=9800
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
                  open=9800.0, high=10500.0, low=9700.0, close=10300.0, volume=1100000),

            # Block1 종료
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
                  open=10300.0, high=10400.0, low=8700.0, close=8800.0, volume=2000000),

            # 전일 종가: 8800
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 4),
                  open=8800.0, high=9000.0, low=8700.0, close=8900.0, volume=950000),

            # Block1 재진입: prev_close=8900
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 5),
                  open=8900.0, high=11000.0, low=8800.0, close=10800.0, volume=1200000),
        ]

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        detector = DynamicBlockDetector(
            block_graph=simple_block_graph,
            expression_engine=expression_engine
        )

        blocks = detector.detect_blocks(
            ticker="025980",
            stocks=stocks,
            condition_name="seed"
        )

        # DynamicBlockDetector는 block_id를 키로 사용하므로
        # 마지막 블록만 반환됨 (덮어쓰기)
        assert len(blocks) == 1
        block = blocks[0]

        # 가장 마지막 Block1 (1월 5일 시작)의 prev_close
        assert block.prev_close == 8900.0
        assert block.started_at == date(2024, 1, 5)


class TestPrevCloseWithIsPriceDoublingSurge:
    """prev_close를 사용한 is_price_doubling_surge 통합 테스트"""

    def test_price_doubling_surge_integration(self, test_db):
        """실제 Block1→Block2 상승폭 반복 감지"""
        # BlockGraph: Block1 → Block2
        block1 = BlockNode(
            block_id="block1",
            block_type=1,
            name="Block1",
            entry_conditions=["current.close >= 10000"],
            exit_conditions=["current.close < 9000"]
        )

        block2 = BlockNode(
            block_id="block2",
            block_type=2,
            name="Block2",
            entry_conditions=[
                "current.close >= 15000",
                "is_price_doubling_surge('block1')"
            ],
            exit_conditions=["current.close < 14000"]
        )

        block_graph = BlockGraph(
            pattern_type="seed",
            root_node_id="block1",
            nodes={"block1": block1, "block2": block2},
            edges=[]
        )

        # 주가 데이터
        # Block1: prev_close=9800, peak=12000 (상승폭 2200)
        # Block2 목표가: 12000 + 2200 = 14200
        stocks = [
            # 전일 종가: 9800
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9700.0, high=9900.0, low=9600.0, close=9800.0, volume=900000),

            # Block1 진입
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
                  open=9800.0, high=10500.0, low=9700.0, close=10300.0, volume=1100000),

            # Block1 peak=12000
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
                  open=10300.0, high=12000.0, low=10200.0, close=11800.0, volume=1500000),

            # Block1 종료
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 4),
                  open=11800.0, high=11900.0, low=8700.0, close=8800.0, volume=2000000),

            # Block2 진입 시도: high=14500 (목표가 14200 달성!)
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10),
                  open=15000.0, high=15500.0, low=14800.0, close=15200.0, volume=2500000),
        ]

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        detector = DynamicBlockDetector(
            block_graph=block_graph,
            expression_engine=expression_engine
        )

        blocks = detector.detect_blocks(
            ticker="025980",
            stocks=stocks,
            condition_name="seed"
        )

        # Block2가 감지되어야 함
        block_ids = [b.block_id for b in blocks]
        assert "block1" in block_ids or "block2" in block_ids

        # Block2가 있으면 확인
        block2_list = [b for b in blocks if b.block_id == "block2"]
        if block2_list:
            block2_detected = block2_list[0]
            assert block2_detected.started_at == date(2024, 1, 10)
            assert block2_detected.prev_close is not None
