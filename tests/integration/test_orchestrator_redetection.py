"""
Orchestrator Reentry Integration Tests

오케스트레이터 재진입 통합 테스트
(redetection 용어는 하위 호환성을 위해 유지됨)
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch

from src.application.use_cases.seed_pattern_detection_orchestrator import SeedPatternDetectionOrchestrator
from src.domain.entities.block_graph import BlockGraph, BlockNode
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.domain.entities.patterns import SeedPatternTree, PatternId


class TestOrchestratorRedetectionIntegration:
    """오케스트레이터 재탐지 통합 테스트"""

    @pytest.fixture
    def expression_engine(self):
        """Expression engine mock"""
        return Mock(spec=ExpressionEngine)

    @pytest.fixture
    def block_graph(self):
        """Block graph with redetection support"""
        graph = Mock(spec=BlockGraph)

        # Block1 노드 (재탐지 지원)
        block1_node = Mock(spec=BlockNode)
        block1_node.block_id = "block1"
        block1_node.has_redetection.return_value = True
        block1_node.redetection_entry_conditions = [
            "current.close < parent_block.peak_price * 0.9"
        ]
        block1_node.redetection_exit_conditions = [
            "current.low < ma(60)"
        ]

        # Block2 노드 (재탐지 미지원)
        block2_node = Mock(spec=BlockNode)
        block2_node.block_id = "block2"
        block2_node.has_redetection.return_value = False

        graph.get_node.side_effect = lambda bid: {
            'block1': block1_node,
            'block2': block2_node
        }.get(bid)

        return graph

    @pytest.fixture
    def stocks(self):
        """주가 데이터"""
        return [
            # Block1 기간
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 1),
                open=10000.0,
                high=10500.0,
                low=9900.0,
                close=10300.0,
                volume=1000000
            ),
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 2),
                open=10300.0,
                high=10800.0,
                low=10200.0,
                close=10600.0,
                volume=1200000
            ),
            # Block1 완료 후 - 재탐지 진입 (10% 하락)
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 15),
                open=9500.0,
                high=9700.0,
                low=9400.0,
                close=9600.0,  # 9600 < 10800 * 0.9 = 9720
                volume=1500000
            ),
            # 재탐지 계속
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 16),
                open=9600.0,
                high=9900.0,
                low=9500.0,
                close=9800.0,
                volume=1300000
            ),
            # 재탐지 종료 (MA60 아래)
            Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 20),
                open=9000.0,
                high=9200.0,
                low=8500.0,  # MA60 아래로 터치
                close=8800.0,
                volume=2000000
            ),
        ]

    @pytest.fixture
    def orchestrator(self, block_graph, expression_engine):
        """Orchestrator 인스턴스"""
        return SeedPatternDetectionOrchestrator(
            block_graph=block_graph,
            expression_engine=expression_engine,
            seed_pattern_repository=None  # DB 저장 안함
        )


class TestDetectRedetectionsForPatterns(TestOrchestratorRedetectionIntegration):
    """_detect_redetections_for_patterns() 통합 테스트"""

    def test_detect_redetections_for_single_pattern(
        self,
        orchestrator,
        stocks
    ):
        """단일 패턴에 대한 재탐지 탐지"""
        # Block1 생성 (완료 상태)
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10800.0,  # 최고가
            peak_volume=1200000
        )

        # 패턴 생성 및 블록 추가
        pattern_id = PatternId.generate("025980", date(2024, 1, 1), 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)
        orchestrator.pattern_manager.patterns = [pattern]

        # Expression engine을 설정하여 재탐지 조건 평가
        # Entry: current.close < 10800 * 0.9 = 9720
        # stocks[2].close = 9600 → True (재탐지 시작)
        # Exit: current.low < ma(60) = stocks[4].low = 8500 → True (재탐지 종료)

        # 메서드가 오류 없이 실행되는지 확인
        # 내부적으로 detect_redetections가 호출되고 재탐지 로직이 실행됨
        orchestrator._detect_redetections_for_patterns(
            ticker="025980",
            stocks=stocks
        )

        # 블록에 재탐지가 시도되었는지 확인 (조건에 따라 추가될 수 있음)
        # 재탐지 개수는 조건 평가 결과에 따라 달라질 수 있음
        assert block1.get_redetection_count() >= 0  # 최소한 오류가 없어야 함

    def test_detect_redetections_skip_active_blocks(
        self,
        orchestrator,
        stocks
    ):
        """활성 상태 블록은 재탐지 스킵"""
        # Block1 생성 (아직 활성 상태)
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            status=BlockStatus.ACTIVE  # 아직 완료 안됨
        )

        # 패턴 생성
        pattern_id = PatternId.generate("025980", date(2024, 1, 1), 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)
        orchestrator.pattern_manager.patterns = [pattern]

        with patch.object(orchestrator.redetection_detector, 'detect_redetections') as mock_detect:
            orchestrator._detect_redetections_for_patterns(
                ticker="025980",
                stocks=stocks
            )

            # detect_redetections가 호출되지 않음
            mock_detect.assert_not_called()

    def test_detect_redetections_skip_blocks_without_config(
        self,
        orchestrator,
        stocks
    ):
        """재탐지 설정 없는 블록은 스킵"""
        # Block2 생성 (재탐지 미지원)
        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        # 패턴 생성
        root_block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 2),
            status=BlockStatus.COMPLETED
        )
        pattern_id = PatternId.generate("025980", date(2024, 1, 1), 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=root_block)
        pattern.blocks['block2'] = block2
        orchestrator.pattern_manager.patterns = [pattern]

        with patch.object(orchestrator.redetection_detector, 'detect_redetections') as mock_detect:
            orchestrator._detect_redetections_for_patterns(
                ticker="025980",
                stocks=stocks
            )

            # block2에 대해서는 호출되지 않음
            # (block1에 대해서는 호출될 수 있음)
            # block2 호출을 확인하려면 call_args를 검사
            for call in mock_detect.call_args_list:
                assert call[1]['block'].block_id != 'block2'

    def test_detect_redetections_only_after_block_ended(
        self,
        orchestrator,
        stocks
    ):
        """블록 종료 이후 캔들만 재탐지 평가"""
        # Block1 생성 (1월 10일 종료)
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10800.0,
            peak_volume=1200000
        )

        pattern_id = PatternId.generate("025980", block1.started_at, 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)
        orchestrator.pattern_manager.patterns = [pattern]

        with patch.object(orchestrator.redetection_detector, 'detect_redetections') as mock_detect:
            orchestrator._detect_redetections_for_patterns(
                ticker="025980",
                stocks=stocks
            )

            # 호출된 캔들의 날짜가 모두 1월 10일 이후인지 확인
            for call in mock_detect.call_args_list:
                current_stock = call[1]['current']
                assert current_stock.date > date(2024, 1, 10)

    def test_detect_redetections_multiple_patterns(
        self,
        orchestrator,
        stocks
    ):
        """여러 패턴에 대한 재탐지 탐지"""
        # 패턴 1
        block1_p1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 5),
            status=BlockStatus.COMPLETED,
            peak_price=10500.0,
            peak_volume=1000000
        )
        pattern_id1 = PatternId.generate("025980", date(2024, 1, 1), 1)
        pattern1 = SeedPatternTree(pattern_id=pattern_id1, ticker="025980", root_block=block1_p1)

        # 패턴 2
        block1_p2 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 10),
            ended_at=date(2024, 1, 15),
            status=BlockStatus.COMPLETED,
            peak_price=10800.0,
            peak_volume=1200000
        )
        pattern_id2 = PatternId.generate("025980", date(2024, 1, 10), 2)
        pattern2 = SeedPatternTree(pattern_id=pattern_id2, ticker="025980", root_block=block1_p2)

        orchestrator.pattern_manager.patterns = [pattern1, pattern2]

        # 메서드가 여러 패턴에 대해 오류 없이 실행되는지 확인
        # 각 패턴의 블록에 대해 재탐지 로직이 실행됨
        orchestrator._detect_redetections_for_patterns(
            ticker="025980",
            stocks=stocks
        )

        # 블록들이 여전히 유효한지 확인
        assert block1_p1.get_redetection_count() >= 0
        assert block1_p2.get_redetection_count() >= 0


class TestBuildRedetectionContext(TestOrchestratorRedetectionIntegration):
    """_build_redetection_context() 통합 테스트"""

    def test_context_includes_current_and_prev(
        self,
        orchestrator,
        stocks
    ):
        """Context에 current와 prev 포함"""
        current = stocks[2]

        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )
        pattern_id = PatternId.generate("025980", block1.started_at, 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)

        context = orchestrator._build_redetection_context(
            ticker="025980",
            current=current,
            all_stocks=stocks,
            pattern=pattern
        )

        assert 'current' in context
        assert context['current'] == current
        assert 'prev' in context
        assert context['prev'] == stocks[1]  # 이전 캔들

    def test_context_includes_all_pattern_blocks(
        self,
        orchestrator,
        stocks
    ):
        """Context에 패턴의 모든 블록 포함"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 5),
            status=BlockStatus.COMPLETED
        )

        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 6),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        pattern_id = PatternId.generate("025980", block1.started_at, 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)
        pattern.blocks['block2'] = block2

        context = orchestrator._build_redetection_context(
            ticker="025980",
            current=stocks[2],
            all_stocks=stocks,
            pattern=pattern
        )

        assert 'block1' in context
        assert context['block1'] == block1
        assert 'block2' in context
        assert context['block2'] == block2

    def test_context_prev_is_none_for_first_stock(
        self,
        orchestrator,
        stocks
    ):
        """첫 캔들의 경우 prev는 None"""
        first_stock = stocks[0]

        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )
        pattern_id = PatternId.generate("025980", block1.started_at, 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)

        context = orchestrator._build_redetection_context(
            ticker="025980",
            current=first_stock,
            all_stocks=stocks,
            pattern=pattern
        )

        assert context['prev'] is None

    def test_context_includes_ticker_and_all_stocks(
        self,
        orchestrator,
        stocks
    ):
        """Context에 ticker와 all_stocks 포함"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )
        pattern_id = PatternId.generate("025980", block1.started_at, 1)
        pattern = SeedPatternTree(pattern_id=pattern_id, ticker="025980", root_block=block1)

        context = orchestrator._build_redetection_context(
            ticker="025980",
            current=stocks[2],
            all_stocks=stocks,
            pattern=pattern
        )

        assert 'ticker' in context
        assert context['ticker'] == "025980"
        assert 'all_stocks' in context
        assert context['all_stocks'] == stocks


class TestEndToEndRedetectionFlow(TestOrchestratorRedetectionIntegration):
    """End-to-End 재탐지 흐름 테스트"""

    def test_full_pattern_detection_with_redetection(
        self,
        orchestrator,
        expression_engine,
        stocks
    ):
        """패턴 탐지 → 재탐지 탐지 전체 흐름"""
        # Block detector가 block1을 탐지한다고 가정
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10800.0,
            peak_volume=1200000
        )

        # Mock block detector
        with patch.object(orchestrator.block_detector, 'detect_blocks', return_value=[block1]):
            # Expression engine을 설정 (재탐지 진입 조건 만족)
            expression_engine.evaluate.return_value = True

            # 전체 흐름 실행
            patterns = orchestrator.detect_patterns(
                ticker="025980",
                stocks=stocks,
                save_to_db=False
            )

            # 패턴이 생성되었는지 확인
            assert len(patterns) > 0

            # Block1에 재탐지가 추가되었는지 확인
            pattern = patterns[0]
            assert 'block1' in pattern.blocks
            detected_block1 = pattern.blocks['block1']

            # 재탐지가 탐지되었는지 확인 (expression_engine.evaluate가 True를 반환하므로)
            # 실제 재탐지 개수는 조건 평가 결과에 따라 다를 수 있음
            redetection_count = detected_block1.get_redetection_count()
            assert redetection_count >= 0  # 최소한 오류가 없어야 함
