"""
Highlight Detection Integration Tests

하이라이트 탐지 통합 테스트 - SeedPatternDetectionOrchestrator + HighlightDetector
"""
import pytest
from datetime import date, timedelta

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.seed_pattern_detection_orchestrator import SeedPatternDetectionOrchestrator
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock


class TestHighlightDetectionIntegration:
    """하이라이트 탐지 통합 테스트"""

    @pytest.fixture
    def block_graph(self):
        """테스트용 간단한 BlockGraph (highlight_condition 포함)"""
        import tempfile
        import os

        # 간단한 테스트용 YAML 생성
        yaml_content = """
version: "1.0"

block_graph:
  pattern_type: "seed"
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Block1"

      entry_conditions:
        - expression: "current.volume >= 100_000_000"  # 1억 이상

      exit_conditions:
        - expression: "current.volume < 50_000_000"  # 5천만 미만으로 감소 시 종료

      # Forward spot condition
      forward_spot_condition: "is_forward_spot('block1', 1, 2)"

      spot_entry_conditions:
        - expression: "current.volume >= prev.volume * 1.3"  # 전일 대비 130% 이상

      # Highlight condition (2 consecutive spots)
      highlight_condition:
        type: "forward_spot"
        enabled: true
        priority: 1
        parameters:
          required_spot_count: 2
        description: "Primary highlight: 2 consecutive spots"

    block2:
      block_id: "block2"
      block_type: 2
      name: "Block2"

      entry_conditions:
        - expression: "current.volume >= 50_000_000"

      exit_conditions:
        - expression: "current.volume < 30_000_000"

  edges:
    - from_block: "block1"
      to_block: "block2"
      edge_type: "sequential"
"""

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        # YAML 로드
        loader = BlockGraphLoader()
        graph = loader.load_from_file(temp_path)

        # 임시 파일 삭제
        os.remove(temp_path)

        return graph

    @pytest.fixture
    def expression_engine(self):
        """Expression engine"""
        return ExpressionEngine()

    @pytest.fixture
    def orchestrator(self, block_graph, expression_engine):
        """Orchestrator 인스턴스"""
        return SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None  # DB 저장 안함
        )

    @pytest.fixture
    def mock_stocks_with_highlight(self):
        """
        하이라이트가 발생하는 mock 데이터

        패턴:
        - D일: Block1 시작 (고점 10000, 거래량 2억)
        - D+1일: spot1 (고점 12000, 거래량 3억 - 150% 초과)
        - D+2일: spot2 (고점 13000, 거래량 3.5억 - 150% 초과)
        → 2개 연속 spot 발생 → 하이라이트!
        """
        base_date = date(2024, 1, 1)
        stocks = []

        # D-10 ~ D-1: 정상 거래 (하이라이트 아님)
        for i in range(-10, 0):
            d = base_date + timedelta(days=i)
            stocks.append(Stock(
                ticker="025980",
                name="강원랜드",
                date=d,
                open=8000,
                high=8500,
                low=7900,
                close=8200,
                volume=100_000_000  # 1억 (정상 거래량)
            ))

        # D일: Block1 시작
        stocks.append(Stock(
            ticker="025980",
            name="강원랜드",
            date=base_date,
            open=9000,
            high=10000,
            low=8900,
            close=9800,
            volume=200_000_000,  # 2억
            trading_value=1_960_000_000_000  # 1.96조 (1조 이상)
        ))

        # D+1일: spot1 (거래량 급증)
        stocks.append(Stock(
            ticker="025980",
            name="강원랜드",
            date=base_date + timedelta(days=1),
            open=10000,
            high=12000,
            low=9900,
            close=11500,
            volume=300_000_000,  # 3억 (전일 대비 150%)
            trading_value=3_450_000_000_000  # 3.45조
        ))

        # D+2일: spot2 (거래량 유지)
        stocks.append(Stock(
            ticker="025980",
            name="강원랜드",
            date=base_date + timedelta(days=2),
            open=11500,
            high=13000,
            low=11400,
            close=12800,
            volume=350_000_000,  # 3.5억 (전일 대비 유지)
            trading_value=4_480_000_000_000  # 4.48조
        ))

        # D+3 ~ D+10: 안정화
        for i in range(3, 11):
            d = base_date + timedelta(days=i)
            stocks.append(Stock(
                ticker="025980",
                name="강원랜드",
                date=d,
                open=12500,
                high=13000,
                low=12400,
                close=12700,
                volume=150_000_000  # 1.5억
            ))

        return stocks

    @pytest.fixture
    def mock_stocks_without_highlight(self):
        """
        하이라이트가 발생하지 않는 mock 데이터

        패턴:
        - D일: Block1 시작 (고점 10000, 거래량 2억)
        - D+1일: spot1만 발생 (거래량 3억)
        - D+2일: 거래량 감소 (spot2 안됨)
        → 1개 spot만 → 하이라이트 아님
        """
        base_date = date(2024, 1, 1)
        stocks = []

        # D-10 ~ D-1: 정상 거래
        for i in range(-10, 0):
            d = base_date + timedelta(days=i)
            stocks.append(Stock(
                ticker="025980",
                name="강원랜드",
                date=d,
                open=8000,
                high=8500,
                low=7900,
                close=8200,
                volume=100_000_000
            ))

        # D일: Block1 시작
        stocks.append(Stock(
            ticker="025980",
            name="강원랜드",
            date=base_date,
            open=9000,
            high=10000,
            low=8900,
            close=9800,
            volume=200_000_000,
            trading_value=1_960_000_000_000
        ))

        # D+1일: spot1만 발생
        stocks.append(Stock(
            ticker="025980",
            name="강원랜드",
            date=base_date + timedelta(days=1),
            open=10000,
            high=12000,
            low=9900,
            close=11500,
            volume=300_000_000,
            trading_value=3_450_000_000_000
        ))

        # D+2일: 거래량 감소 (spot2 안됨)
        stocks.append(Stock(
            ticker="025980",
            name="강원랜드",
            date=base_date + timedelta(days=2),
            open=11500,
            high=12500,
            low=11400,
            close=12300,
            volume=150_000_000,  # 1.5억 (전일 대비 감소 - spot 아님)
            trading_value=1_845_000_000_000
        ))

        return stocks

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Integration Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_highlight_detection_with_2_spots(
        self,
        orchestrator,
        mock_stocks_with_highlight
    ):
        """2개 spot 발생 시 하이라이트 탐지"""
        # 패턴 탐지 (DB 저장 안함)
        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=mock_stocks_with_highlight,
            save_to_db=False
        )

        # 패턴이 생성되었는지 확인
        assert len(patterns) >= 1, "At least one pattern should be detected"

        # 첫 번째 패턴 확인
        pattern = patterns[0]

        # 하이라이트가 탐지되었는지 확인
        assert pattern.has_highlight() is True, "Pattern should have highlight"
        assert pattern.primary_highlight_block_id is not None, "Primary highlight should be set"

        # 하이라이트 블록이 block1인지 확인
        assert pattern.primary_highlight_block_id == "block1", "Highlight should be on block1"

        # 하이라이트 메타데이터 확인
        assert 'highlight_type' in pattern.highlight_metadata
        assert pattern.highlight_metadata['highlight_type'] == 'forward_spot'
        assert pattern.highlight_metadata['spot_count'] == 2

        # Primary highlight 블록 조회
        highlight_block = pattern.get_primary_highlight()
        assert highlight_block is not None
        assert highlight_block.block_id == "block1"
        assert highlight_block.get_spot_count() == 2

    def test_no_highlight_with_1_spot(
        self,
        orchestrator,
        mock_stocks_without_highlight
    ):
        """1개 spot만 발생 시 하이라이트 없음"""
        # 패턴 탐지
        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=mock_stocks_without_highlight,
            save_to_db=False
        )

        # 패턴 생성 확인
        assert len(patterns) >= 1

        # 첫 번째 패턴 확인
        pattern = patterns[0]

        # 하이라이트가 없어야 함
        assert pattern.has_highlight() is False, "Pattern should NOT have highlight"
        assert pattern.primary_highlight_block_id is None, "Primary highlight should be None"

        # block1의 spot 개수 확인 (1개만)
        block1 = pattern.get_block('block1')
        assert block1 is not None
        assert block1.get_spot_count() == 1, "Block1 should have only 1 spot"

    def test_highlight_detector_service_is_used(
        self,
        orchestrator
    ):
        """Orchestrator가 HighlightDetector 서비스를 사용하는지 확인"""
        # HighlightDetector가 초기화되었는지 확인
        assert hasattr(orchestrator, 'highlight_detector')
        assert orchestrator.highlight_detector is not None

        # SupportResistanceAnalyzer도 초기화되었는지 확인
        assert hasattr(orchestrator, 'support_resistance_analyzer')
        assert orchestrator.support_resistance_analyzer is not None

    def test_block_graph_has_highlight_condition(
        self,
        block_graph
    ):
        """test1_alt.yaml의 Block1이 highlight_condition을 가지고 있는지 확인"""
        # Block1 노드 조회
        block1_node = block_graph.get_node('block1')
        assert block1_node is not None

        # highlight_condition 확인
        assert block1_node.highlight_condition is not None
        assert block1_node.highlight_condition.type == "forward_spot"
        assert block1_node.highlight_condition.is_enabled() is True
        assert block1_node.highlight_condition.priority == 1
        assert block1_node.highlight_condition.get_parameter("required_spot_count") == 2

    def test_pattern_summary_includes_highlight_info(
        self,
        orchestrator,
        mock_stocks_with_highlight
    ):
        """패턴 속성에 하이라이트 정보가 포함되는지 확인"""
        # 패턴 탐지
        patterns = orchestrator.detect_patterns(
            ticker="025980",
            stocks=mock_stocks_with_highlight,
            save_to_db=False
        )

        # 첫 번째 패턴 확인
        pattern = patterns[0]

        # 하이라이트 정보 확인 (속성 직접 접근)
        assert pattern.has_highlight() is True
        assert pattern.primary_highlight_block_id == 'block1'
        assert pattern.highlight_detected is True
        assert 'spot_count' in pattern.highlight_metadata
        assert pattern.highlight_metadata['spot_count'] == 2
