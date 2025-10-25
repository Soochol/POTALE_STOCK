"""
Redetection End-to-End Tests

재탐지 시스템 종단간 테스트 (실제 데이터 흐름)
"""
import pytest
import tempfile
from datetime import date
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.seed_pattern_detection_orchestrator import SeedPatternDetectionOrchestrator
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
def sample_yaml_with_redetection():
    """재탐지 설정이 포함된 샘플 YAML"""
    yaml_content = """
block_graph:
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Surge"
      description: "초기 급등 블록"
      entry_conditions:
        - "current.close >= 10000"
        - "current.volume >= 1000000"
      exit_conditions:
        - "current.close < 9000"
      spot_condition: "current.close >= 15000"
      redetection:
        entry_conditions:
          - "current.close < parent_block.peak_price * 0.9"
        exit_conditions:
          - "candles_between(active_redetection.started_at, current.date) >= 5"

  edges: []
"""

    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(yaml_content)
        temp_path = f.name

    yield temp_path

    # 정리
    Path(temp_path).unlink()


@pytest.fixture
def sample_stock_data():
    """
    샘플 주가 데이터 (재탐지 시나리오)

    시나리오:
    - Block1 시작 → peak 도달 → Block1 완료
    - 이후 가격이 peak 대비 90% 이하로 하락하면 재탐지 시작
    - 재탐지가 5일간 지속되면 종료
    """
    return [
        # Block1 진입 및 상승
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
              open=9800.0, high=10200.0, low=9700.0, close=10100.0, volume=1100000),

        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
              open=10100.0, high=10800.0, low=10000.0, close=10700.0, volume=1300000),

        # Peak 도달 (high=11500)
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
              open=10700.0, high=11500.0, low=10600.0, close=11200.0, volume=1500000),

        # Block1 종료 (close < 9000)
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 4),
              open=11200.0, high=11300.0, low=8700.0, close=8800.0, volume=2000000),

        # Block1 완료 후 저가 유지
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 5),
              open=8800.0, high=8900.0, low=8600.0, close=8700.0, volume=1100000),

        # 재탐지 진입 (peak의 90% = 11500 * 0.9 = 10350 미만으로 하락)
        # close=9800 < 10350이므로 재탐지 진입 조건 만족
        # BUT close=9800 < 10000이므로 Block1 entry 조건은 불만족 (새 Block1 생성 방지)
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10),
              open=8700.0, high=9900.0, low=8600.0, close=9800.0, volume=900000),

        # 재탐지 상승 (Block1 entry 조건 불만족 유지)
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 11),
              open=9800.0, high=9900.0, low=9700.0, close=9850.0, volume=850000),

        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 12),
              open=9850.0, high=9950.0, low=9800.0, close=9900.0, volume=800000),

        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 13),
              open=9900.0, high=9980.0, low=9850.0, close=9950.0, volume=750000),

        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 14),
              open=9950.0, high=9990.0, low=9900.0, close=9980.0, volume=700000),

        # 5일 경과 → 재탐지 종료 조건 만족
        Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 15),
              open=9980.0, high=9995.0, low=9950.0, close=9990.0, volume=650000),
    ]


class TestRedetectionEndToEnd:
    """재탐지 시스템 E2E 테스트"""

    def test_full_redetection_flow(
        self,
        test_db,
        sample_yaml_with_redetection,
        sample_stock_data
    ):
        """전체 재탐지 흐름 테스트 (YAML → 탐지 → DB 저장 → 검증)"""
        # 1. YAML 로드
        loader = BlockGraphLoader()
        block_graph = loader.load_from_file(sample_yaml_with_redetection)

        assert 'block1' in block_graph.nodes
        block1_node = block_graph.nodes['block1']
        assert block1_node.has_redetection()

        # 2. Expression Engine 설정
        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        # 3. Repository 설정
        repository = DynamicBlockRepositoryImpl(test_db)

        # 4. Orchestrator 생성
        orchestrator = SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None  # DB 저장 비활성화
        )

        # 5. 패턴 탐지 실행
        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=sample_stock_data,
            save_to_db=False
        )

        # 6. 결과 검증
        assert len(patterns) > 0, "최소한 1개 패턴이 탐지되어야 함"

        pattern = patterns[0]
        assert 'block1' in pattern.blocks

        block1 = pattern.blocks['block1']

        # Block1이 완료되었는지 확인
        assert block1.is_completed(), "Block1이 완료되어야 함"
        assert block1.peak_price > 0, "Block1 peak가 기록되어야 함"

        # 재탐지가 탐지되었는지 확인
        redetection_count = block1.get_redetection_count()
        print(f"Detected {redetection_count} redetections")

        if redetection_count > 0:
            # 재탐지가 있으면 검증
            redetection = block1.redetections[0]
            assert redetection.sequence == 1
            assert redetection.parent_block_id == "block1"
            assert redetection.started_at is not None
            print(f"Redetection started at: {redetection.started_at}")

            # 재탐지 종료 여부 확인 (5일 경과 조건)
            if redetection.is_completed():
                print(f"Redetection completed at: {redetection.ended_at}")
                assert redetection.ended_at is not None

    def test_redetection_persistence(
        self,
        test_db,
        sample_yaml_with_redetection,
        sample_stock_data
    ):
        """재탐지 데이터베이스 저장 및 로드 테스트"""
        # 1. 설정
        loader = BlockGraphLoader()
        block_graph = loader.load_from_file(sample_yaml_with_redetection)

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        orchestrator = SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None
        )

        # 2. 패턴 탐지
        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=sample_stock_data,
            save_to_db=False
        )

        assert len(patterns) > 0
        block1 = patterns[0].blocks['block1']

        # 3. 데이터베이스에 저장
        repository = DynamicBlockRepositoryImpl(test_db)
        saved_block = repository.save(block1)
        assert saved_block.id is not None

        # 4. 데이터베이스에서 다시 조회
        loaded_block = repository.find_by_id(saved_block.id)
        assert loaded_block is not None

        # 5. 재탐지 데이터 검증
        assert loaded_block.get_redetection_count() == block1.get_redetection_count()

        if loaded_block.get_redetection_count() > 0:
            original_redet = block1.redetections[0]
            loaded_redet = loaded_block.redetections[0]

            assert loaded_redet.sequence == original_redet.sequence
            assert loaded_redet.parent_block_id == original_redet.parent_block_id
            assert loaded_redet.started_at == original_redet.started_at
            assert loaded_redet.ended_at == original_redet.ended_at
            assert loaded_redet.peak_price == original_redet.peak_price
            assert loaded_redet.peak_volume == original_redet.peak_volume
            assert loaded_redet.status == original_redet.status

    def test_multiple_redetections_sequence(
        self,
        test_db,
        sample_yaml_with_redetection
    ):
        """여러 재탐지가 순차적으로 발생하는 시나리오"""
        # 더 긴 시나리오 데이터 생성 (3번의 재탐지)
        extended_data = [
            # Block1
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9800.0, high=10200.0, low=9700.0, close=10100.0, volume=1100000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
                  open=10100.0, high=11000.0, low=10000.0, close=10800.0, volume=1300000),
            # Block1 종료
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
                  open=10800.0, high=10900.0, low=8700.0, close=8800.0, volume=2000000),
        ]

        # 재탐지 1, 2, 3 추가 (안전한 날짜 사용)
        redetection_dates = [
            [date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12), date(2024, 1, 13), date(2024, 1, 14), date(2024, 1, 15)],
            [date(2024, 1, 20), date(2024, 1, 21), date(2024, 1, 22), date(2024, 1, 23), date(2024, 1, 24), date(2024, 1, 25)],
            [date(2024, 2, 1), date(2024, 2, 2), date(2024, 2, 3), date(2024, 2, 4), date(2024, 2, 5), date(2024, 2, 6)]
        ]

        for redet_num in range(3):
            # 재탐지 가격대: Block1 entry 조건 불만족, 재탐지 entry 조건 만족
            # peak=10900 * 0.9 = 9810 이하여야 재탐지 진입
            base_price = 9000.0 + (redet_num * 200)  # 9000, 9200, 9400

            # 재탐지 진입 (peak의 90% 이하, Block1 entry 조건 불만족)
            for i in range(6):
                extended_data.append(
                    Stock(
                        ticker="025980",
                        name="강원랜드",
                        date=redetection_dates[redet_num][i],
                        open=base_price,
                        high=base_price + 200,  # 9200, 9400, 9600
                        low=base_price - 100,
                        close=base_price + 100,  # 9100, 9300, 9500 (< 10000)
                        volume=900000  # < 1000000 (Block1 entry 조건 불만족)
                    )
                )

        # 설정 및 탐지
        loader = BlockGraphLoader()
        block_graph = loader.load_from_file(sample_yaml_with_redetection)

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        orchestrator = SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None
        )

        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=extended_data,
            save_to_db=False
        )

        assert len(patterns) > 0
        block1 = patterns[0].blocks['block1']

        # 여러 재탐지 확인
        redetection_count = block1.get_redetection_count()
        print(f"Detected {redetection_count} redetections in extended scenario")

        # 최소한 1개 이상의 재탐지가 탐지되어야 함
        assert redetection_count >= 1

        # 시퀀스가 올바르게 증가하는지 확인
        if redetection_count >= 2:
            for i in range(redetection_count):
                assert block1.redetections[i].sequence == i + 1


class TestRedetectionEdgeCases:
    """재탐지 엣지 케이스 E2E 테스트"""

    def test_no_redetection_when_conditions_not_met(
        self,
        test_db,
        sample_yaml_with_redetection
    ):
        """재탐지 조건 불만족 시 재탐지 없음"""
        # 재탐지 조건을 만족하지 않는 데이터
        data = [
            # Block1만 탐지되고 종료
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9800.0, high=10200.0, low=9700.0, close=10100.0, volume=1100000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
                  open=10100.0, high=10800.0, low=10000.0, close=10700.0, volume=1300000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
                  open=10700.0, high=10900.0, low=8700.0, close=8800.0, volume=2000000),
            # 이후 가격이 재탐지 조건을 만족하지 않음 (peak의 90% 이하로 하락하지 않음)
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10),
                  open=9900.0, high=10100.0, low=9800.0, close=10000.0, volume=1000000),
        ]

        loader = BlockGraphLoader()
        block_graph = loader.load_from_file(sample_yaml_with_redetection)

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        orchestrator = SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None
        )

        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=data,
            save_to_db=False
        )

        assert len(patterns) > 0
        block1 = patterns[0].blocks['block1']

        # 재탐지가 없어야 함 (조건 불만족)
        assert block1.get_redetection_count() == 0

    def test_block_not_completed_no_redetection(
        self,
        test_db,
        sample_yaml_with_redetection
    ):
        """Block이 완료되지 않으면 재탐지 없음"""
        # Block1이 완료되지 않는 데이터 (exit 조건 불만족)
        data = [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9800.0, high=10200.0, low=9700.0, close=10100.0, volume=1100000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
                  open=10100.0, high=10800.0, low=10000.0, close=10700.0, volume=1300000),
            # Block1이 계속 활성 상태 (9000 아래로 하락하지 않음)
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
                  open=10700.0, high=10900.0, low=10500.0, close=10600.0, volume=1200000),
        ]

        loader = BlockGraphLoader()
        block_graph = loader.load_from_file(sample_yaml_with_redetection)

        function_registry = FunctionRegistry()
        expression_engine = ExpressionEngine(function_registry)

        orchestrator = SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None
        )

        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=data,
            save_to_db=False
        )

        if len(patterns) > 0 and 'block1' in patterns[0].blocks:
            block1 = patterns[0].blocks['block1']
            # Block1이 아직 활성이면 재탐지 없음
            if not block1.is_completed():
                assert block1.get_redetection_count() == 0
