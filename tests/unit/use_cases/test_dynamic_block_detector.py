"""
DynamicBlockDetector 단위 테스트
"""
import pytest
from datetime import date, timedelta
from dataclasses import dataclass

from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.core import Stock
from src.domain.entities.block_graph import BlockGraph, BlockNode, BlockEdge, EdgeType
from src.domain.entities.conditions import ExpressionEngine, function_registry


# Mock Stock class for testing
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


class TestDynamicBlockDetector:
    """DynamicBlockDetector 테스트"""

    def setup_method(self):
        """각 테스트 전에 실행"""
        self.expression_engine = ExpressionEngine(function_registry)

    def test_detect_simple_block(self):
        """단순 블록 감지"""
        # BlockGraph 생성
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=['current.close < 9000']
        )
        graph.add_node(node1)

        # Detector 생성
        detector = DynamicBlockDetector(graph, self.expression_engine)

        # 주가 데이터
        stocks = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),  # 조건 만족
            MockStock('025980', date(2024, 1, 16), 10200, 10800, 10000, 10600, 1200000),  # 진행 중
        ]

        # 감지 실행
        detections = detector.detect_blocks('025980', stocks)

        # 검증
        assert len(detections) == 1
        block1 = detections[0]
        assert block1.block_id == 'block1'
        assert block1.started_at == date(2024, 1, 15)
        assert block1.is_active()
        assert block1.peak_price == 10800  # 두 번째 날의 high

    def test_detect_block_not_triggered_when_condition_not_met(self):
        """조건 불만족 시 블록 감지 안 됨"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000']
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        # 조건 불만족 주가 데이터
        stocks = [
            MockStock('025980', date(2024, 1, 15), 9000, 9500, 8500, 9200, 1000000),  # < 10000
        ]

        detections = detector.detect_blocks('025980', stocks)

        # 감지 안 됨
        assert len(detections) == 0

    def test_detect_block_completes_on_exit_condition(self):
        """종료 조건 만족 시 블록 완료"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=['current.close < 9000']
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        stocks = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),  # 시작
            MockStock('025980', date(2024, 1, 16), 10200, 10800, 10000, 10600, 1200000),  # 진행
            MockStock('025980', date(2024, 1, 17), 9000, 9200, 8500, 8800, 800000),  # 종료 (< 9000)
        ]

        detections = detector.detect_blocks('025980', stocks)

        assert len(detections) == 1
        block1 = detections[0]
        assert block1.started_at == date(2024, 1, 15)
        assert block1.ended_at == date(2024, 1, 17)
        assert block1.is_completed()

    def test_detect_multiple_blocks_sequentially(self):
        """여러 블록 순차 감지"""
        graph = BlockGraph()

        # Block1
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=['current.close < 9000']
        )

        # Block2 (Block1 다음)
        node2 = BlockNode(
            block_id='block2',
            block_type=2,
            name='Block 2',
            entry_conditions=['current.close >= 11000'],  # 단순화된 조건
            exit_conditions=['current.close < 10000']
        )

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(BlockEdge('block1', 'block2'))

        detector = DynamicBlockDetector(graph, self.expression_engine)

        stocks = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),  # Block1 시작
            MockStock('025980', date(2024, 1, 16), 10200, 11200, 10000, 11100, 1200000),  # Block2 시작
        ]

        detections = detector.detect_blocks('025980', stocks)

        # Block1과 Block2 모두 감지
        assert len(detections) == 2

        block_ids = [d.block_id for d in detections]
        assert 'block1' in block_ids
        assert 'block2' in block_ids

    def test_peak_price_and_volume_tracking(self):
        """Peak 가격 및 거래량 추적"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000']
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        stocks = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),  # 시작
            MockStock('025980', date(2024, 1, 16), 10200, 12000, 10000, 11800, 1200000),  # Peak high
            MockStock('025980', date(2024, 1, 17), 11800, 11500, 11000, 11200, 1500000),  # Peak volume
            MockStock('025980', date(2024, 1, 18), 11200, 11400, 10800, 11000, 1100000),  # 진행
        ]

        detections = detector.detect_blocks('025980', stocks)

        block1 = detections[0]
        assert block1.peak_price == 12000  # 1/16의 high
        assert block1.peak_volume == 1500000  # 1/17의 volume
        assert block1.peak_date == date(2024, 1, 16)  # Peak price 날짜

    def test_multiple_entry_conditions_and_logic(self):
        """여러 진입 조건 (AND 로직)"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=[
                'current.close >= 10000',
                'current.volume >= 1000000'
            ]
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        # Case 1: 모든 조건 만족
        stocks1 = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1200000),
        ]
        detections1 = detector.detect_blocks('025980', stocks1)
        assert len(detections1) == 1

        # Case 2: 가격만 만족 (거래량 부족)
        stocks2 = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 500000),  # volume < 1M
        ]
        detections2 = detector.detect_blocks('025980', stocks2)
        assert len(detections2) == 0

    def test_multiple_exit_conditions_or_logic(self):
        """여러 종료 조건 (OR 로직)"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=[
                'current.close < 9000',  # 조건 1: 가격 하락
                'current.volume < 500000'  # 조건 2: 거래량 감소
            ]
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        # Case 1: 거래량 감소로 종료
        stocks1 = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),  # 시작
            MockStock('025980', date(2024, 1, 16), 10200, 10300, 10000, 10100, 400000),  # 종료 (volume < 500k)
        ]
        detections1 = detector.detect_blocks('025980', stocks1)
        assert detections1[0].is_completed()

        # Case 2: 가격 하락으로 종료
        stocks2 = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),  # 시작
            MockStock('025980', date(2024, 1, 16), 9000, 9200, 8500, 8800, 1200000),  # 종료 (close < 9000)
        ]
        detections2 = detector.detect_blocks('025980', stocks2)
        assert detections2[0].is_completed()

    def test_context_building(self):
        """Context 구성 확인"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000']
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        stocks = [
            MockStock('025980', date(2024, 1, 15), 9000, 9500, 8500, 9200, 1000000),
            MockStock('025980', date(2024, 1, 16), 10000, 10500, 9500, 10200, 1200000),
        ]

        # _build_context는 private이지만 테스트를 위해 호출
        context = detector._build_context(
            current=stocks[1],
            prev=stocks[0],
            all_stocks=stocks,
            active_blocks={}
        )

        assert 'current' in context
        assert 'prev' in context
        assert 'all_stocks' in context
        assert context['current'] == stocks[1]
        assert context['prev'] == stocks[0]
        assert len(context['all_stocks']) == 2

    def test_can_transition(self):
        """블록 전이 가능 여부 확인"""
        graph = BlockGraph()

        node1 = BlockNode('block1', 1, 'Block 1', entry_conditions=['true'])
        node2a = BlockNode('block2a', 2, 'Block 2A', entry_conditions=['true'])
        node2b = BlockNode('block2b', 2, 'Block 2B', entry_conditions=['true'])

        graph.add_node(node1)
        graph.add_node(node2a)
        graph.add_node(node2b)

        # Conditional edges
        graph.add_edge(BlockEdge(
            'block1', 'block2a',
            edge_type=EdgeType.CONDITIONAL,
            condition='current.volume >= 1000000',
            priority=1
        ))
        graph.add_edge(BlockEdge(
            'block1', 'block2b',
            edge_type=EdgeType.CONDITIONAL,
            condition='current.volume < 1000000',
            priority=2
        ))

        detector = DynamicBlockDetector(graph, self.expression_engine)

        # Context 구성
        current_stock = MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1200000)
        context = {'current': current_stock}

        # Block1 → Block2A (volume >= 1M)
        assert detector.can_transition('block1', 'block2a', context) is True

        # Block1 → Block2B (volume < 1M) - False
        assert detector.can_transition('block1', 'block2b', context) is False

    def test_error_handling_in_condition_evaluation(self):
        """조건 평가 중 에러 처리"""
        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['invalid_function()']  # 존재하지 않는 함수
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        stocks = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),
        ]

        # 에러 발생하지만 프로그램은 중단되지 않음
        detections = detector.detect_blocks('025980', stocks)

        # 조건 평가 실패 시 감지 안 됨
        assert len(detections) == 0

    def test_active_blocks_passed_to_detector(self):
        """진행 중인 블록을 전달하여 계속 추적"""
        from src.domain.entities.detections import DynamicBlockDetection

        graph = BlockGraph()
        node1 = BlockNode(
            block_id='block1',
            block_type=1,
            name='Block 1',
            entry_conditions=['current.close >= 10000'],
            exit_conditions=['current.close < 9000']
        )
        graph.add_node(node1)

        detector = DynamicBlockDetector(graph, self.expression_engine)

        # 이미 진행 중인 블록 생성
        existing_block = DynamicBlockDetection(
            block_id='block1',
            block_type=1,
            ticker='025980',
            condition_name='seed'
        )
        existing_block.start(date(2024, 1, 14))

        stocks = [
            MockStock('025980', date(2024, 1, 15), 10000, 10500, 9500, 10200, 1000000),
            MockStock('025980', date(2024, 1, 16), 9000, 9200, 8500, 8800, 800000),  # 종료 조건
        ]

        # 진행 중인 블록 전달
        detections = detector.detect_blocks('025980', stocks, active_blocks=[existing_block])

        # 기존 블록이 업데이트되어 완료됨
        assert len(detections) == 1
        assert detections[0].block_id == 'block1'
        assert detections[0].is_completed()
        assert detections[0].ended_at == date(2024, 1, 16)
