"""
RedetectionDetector Service Unit Tests

재진입 탐지 서비스 단위 테스트
(redetection 용어는 하위 호환성을 위해 유지됨)
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock

from src.application.services.redetection_detector import RedetectionDetector
from src.domain.entities.block_graph import BlockNode
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock
from src.domain.entities.detections import DynamicBlockDetection, RedetectionEvent, BlockStatus


class TestRedetectionDetector:
    """RedetectionDetector 서비스 테스트"""

    @pytest.fixture
    def expression_engine(self):
        """Expression engine mock"""
        return Mock(spec=ExpressionEngine)

    @pytest.fixture
    def detector(self, expression_engine):
        """RedetectionDetector 인스턴스"""
        return RedetectionDetector(expression_engine)

    @pytest.fixture
    def completed_block(self):
        """완료된 Seed Block"""
        return DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

    @pytest.fixture
    def active_block(self):
        """아직 활성 중인 Block (재탐지 불가)"""
        return DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            status=BlockStatus.ACTIVE  # 아직 완료 안됨
        )

    @pytest.fixture
    def block_node_with_redetection(self):
        """재탐지 설정이 있는 BlockNode"""
        node = Mock(spec=BlockNode)
        node.has_redetection.return_value = True
        node.redetection_entry_conditions = [
            "current.close < parent_block.peak_price * 0.9",  # 10% 하락
            "current.volume >= volume_ma(20) * 2.0"  # 거래량 조건
        ]
        node.redetection_exit_conditions = [
            "current.low < ma(60)"  # MA60 아래로 터치
        ]
        return node

    @pytest.fixture
    def block_node_without_redetection(self):
        """재탐지 설정이 없는 BlockNode"""
        node = Mock(spec=BlockNode)
        node.has_redetection.return_value = False
        return node

    @pytest.fixture
    def current_stock(self):
        """현재 주가 데이터"""
        return Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 20),
            open=9500.0,
            high=9800.0,
            low=9400.0,
            close=9700.0,
            volume=1500000
        )

    @pytest.fixture
    def context(self):
        """평가 컨텍스트"""
        return {
            'current': Stock(
                ticker="025980",
                name="강원랜드",
                date=date(2024, 1, 20),
                open=9500.0,
                high=9800.0,
                low=9400.0,
                close=9700.0,
                volume=1500000
            ),
            'all_stocks': []
        }


class TestDetectRedetections(TestRedetectionDetector):
    """detect_redetections() 메서드 테스트"""

    def test_no_redetection_config(
        self,
        detector,
        completed_block,
        block_node_without_redetection,
        current_stock,
        context
    ):
        """재탐지 설정 없으면 None 반환"""
        result = detector.detect_redetections(
            block=completed_block,
            block_node=block_node_without_redetection,
            current=current_stock,
            context=context
        )

        assert result is None
        block_node_without_redetection.has_redetection.assert_called_once()

    def test_start_new_redetection(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """새 재탐지 시작"""
        # Entry 조건 만족하도록 설정
        expression_engine.evaluate.return_value = True

        result = detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        # 새 재탐지가 생성됨
        assert result is not None
        assert result.sequence == 1
        assert result.parent_block_id == "block1"
        assert result.started_at == current_stock.date
        assert result.is_active()
        assert result.peak_price == current_stock.high
        assert result.peak_volume == current_stock.volume

        # Block에 추가됨
        assert completed_block.get_redetection_count() == 1

    def test_start_redetection_block_not_completed(
        self,
        detector,
        active_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """Block이 아직 완료 안되면 재탐지 시작 불가"""
        result = detector.detect_redetections(
            block=active_block,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        assert result is None
        assert active_block.get_redetection_count() == 0

    def test_start_redetection_entry_conditions_not_met(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """Entry 조건 불만족 시 재탐지 시작 안됨"""
        # Entry 조건 불만족
        expression_engine.evaluate.return_value = False

        result = detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        assert result is None
        assert completed_block.get_redetection_count() == 0

    def test_update_active_redetection_peak(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """Active 재탐지의 peak 업데이트"""
        # 먼저 재탐지 시작
        expression_engine.evaluate.return_value = True
        first_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 15),
            open=9000.0,
            high=9200.0,
            low=8900.0,
            close=9100.0,
            volume=1200000
        )
        detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=first_stock,
            context=context
        )

        # Exit 조건은 불만족으로 설정
        expression_engine.evaluate.return_value = False

        # 더 높은 가격/거래량으로 업데이트
        higher_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 16),
            open=9500.0,
            high=9800.0,  # 더 높음
            low=9400.0,
            close=9700.0,
            volume=1600000  # 더 많음
        )

        result = detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=higher_stock,
            context=context
        )

        # Peak가 업데이트됨
        assert result.peak_price == 9800.0
        assert result.peak_volume == 1600000
        assert result.is_active()

    def test_complete_active_redetection(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """Active 재탐지 종료"""
        # 먼저 재탐지 시작
        expression_engine.evaluate.return_value = True
        first_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 15),
            open=9000.0,
            high=9200.0,
            low=8900.0,
            close=9100.0,
            volume=1200000
        )
        detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=first_stock,
            context=context
        )

        # Exit 조건 만족으로 설정
        expression_engine.evaluate.return_value = True

        # 종료 조건 만족하는 주가
        exit_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 20),
            open=9000.0,
            high=9100.0,
            low=8500.0,  # MA60 아래로 터치
            close=8800.0,
            volume=2000000
        )

        result = detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=exit_stock,
            context=context
        )

        # 재탐지가 완료됨
        assert result.is_completed()
        assert result.ended_at == exit_stock.date

    def test_start_second_redetection_after_first_completed(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        context
    ):
        """첫 재탐지 완료 후 두 번째 재탐지 시작"""
        # 첫 번째 재탐지 시작
        expression_engine.evaluate.return_value = True
        first_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 15),
            open=9000.0,
            high=9200.0,
            low=8900.0,
            close=9100.0,
            volume=1200000
        )
        detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=first_stock,
            context=context
        )

        # 첫 번째 재탐지 종료
        expression_engine.evaluate.return_value = True
        exit_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 20),
            open=9000.0,
            high=9100.0,
            low=8500.0,
            close=8800.0,
            volume=2000000
        )
        detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=exit_stock,
            context=context
        )

        # 두 번째 재탐지 시작
        expression_engine.evaluate.return_value = True
        second_stock = Stock(
            ticker="025980",
            name="강원랜드",
            date=date(2024, 1, 25),
            open=9000.0,
            high=9200.0,
            low=8900.0,
            close=9100.0,
            volume=1300000
        )
        result = detector.detect_redetections(
            block=completed_block,
            block_node=block_node_with_redetection,
            current=second_stock,
            context=context
        )

        # 두 번째 재탐지가 생성됨
        assert result is not None
        assert result.sequence == 2
        assert result.is_active()
        assert completed_block.get_redetection_count() == 2


class TestEvaluateEntryConditions(TestRedetectionDetector):
    """_evaluate_entry_conditions() 메서드 테스트"""

    def test_entry_conditions_all_satisfied(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """모든 entry 조건 만족"""
        expression_engine.evaluate.return_value = True

        result = detector._evaluate_entry_conditions(
            block_node=block_node_with_redetection,
            parent_block=completed_block,
            current=current_stock,
            context=context
        )

        assert result is True
        # 모든 조건을 평가했는지 확인
        assert expression_engine.evaluate.call_count == len(
            block_node_with_redetection.redetection_entry_conditions
        )

    def test_entry_conditions_first_fails(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """첫 번째 조건 실패 시 즉시 False"""
        expression_engine.evaluate.return_value = False

        result = detector._evaluate_entry_conditions(
            block_node=block_node_with_redetection,
            parent_block=completed_block,
            current=current_stock,
            context=context
        )

        assert result is False
        # 첫 조건만 평가하고 멈춤
        assert expression_engine.evaluate.call_count == 1

    def test_entry_conditions_evaluation_error(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """조건 평가 중 오류 발생 시 False"""
        expression_engine.evaluate.side_effect = ValueError("Invalid expression")

        result = detector._evaluate_entry_conditions(
            block_node=block_node_with_redetection,
            parent_block=completed_block,
            current=current_stock,
            context=context
        )

        assert result is False

    def test_entry_conditions_no_conditions(
        self,
        detector,
        expression_engine,
        completed_block,
        current_stock,
        context
    ):
        """Entry 조건이 없으면 False"""
        node = Mock(spec=BlockNode)
        node.redetection_entry_conditions = []  # 빈 리스트

        result = detector._evaluate_entry_conditions(
            block_node=node,
            parent_block=completed_block,
            current=current_stock,
            context=context
        )

        assert result is False

    def test_entry_conditions_context_includes_parent_block(
        self,
        detector,
        expression_engine,
        completed_block,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """Context에 parent_block이 포함되는지 확인"""
        expression_engine.evaluate.return_value = True

        detector._evaluate_entry_conditions(
            block_node=block_node_with_redetection,
            parent_block=completed_block,
            current=current_stock,
            context=context
        )

        # evaluate 호출 시 전달된 context 확인
        call_args = expression_engine.evaluate.call_args[0]
        eval_context = call_args[1]

        assert 'parent_block' in eval_context
        assert eval_context['parent_block'] == completed_block
        assert 'block1' in eval_context  # block_id로도 접근 가능
        assert eval_context['block1'] == completed_block


class TestCheckExitConditions(TestRedetectionDetector):
    """_check_exit_conditions() 메서드 테스트"""

    def test_exit_condition_met(
        self,
        detector,
        expression_engine,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """종료 조건 만족 시 재탐지 완료"""
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9200.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )

        expression_engine.evaluate.return_value = True

        detector._check_exit_conditions(
            redetection=redetection,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        # 재탐지가 완료됨
        assert redetection.is_completed()
        assert redetection.ended_at == current_stock.date

    def test_exit_condition_not_met(
        self,
        detector,
        expression_engine,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """종료 조건 불만족 시 재탐지 계속 활성"""
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9200.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )

        expression_engine.evaluate.return_value = False

        detector._check_exit_conditions(
            redetection=redetection,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        # 재탐지가 여전히 활성 상태
        assert redetection.is_active()
        assert redetection.ended_at is None

    def test_exit_condition_or_logic(
        self,
        detector,
        expression_engine,
        current_stock,
        context
    ):
        """OR 로직 - 하나만 만족해도 종료"""
        node = Mock(spec=BlockNode)
        node.redetection_exit_conditions = [
            "current.low < ma(60)",  # False
            "current.close < parent_block.peak_price * 0.8",  # True → 종료!
            "current.volume < volume_ma(20) * 0.5"  # 평가 안됨
        ]

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9200.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )

        # 첫 번째 False, 두 번째 True
        expression_engine.evaluate.side_effect = [False, True]

        detector._check_exit_conditions(
            redetection=redetection,
            block_node=node,
            current=current_stock,
            context=context
        )

        # 두 번째 조건에서 종료됨
        assert redetection.is_completed()
        assert expression_engine.evaluate.call_count == 2  # 세 번째는 평가 안됨

    def test_exit_condition_no_conditions(
        self,
        detector,
        expression_engine,
        current_stock,
        context
    ):
        """종료 조건 없으면 아무것도 안함"""
        node = Mock(spec=BlockNode)
        node.redetection_exit_conditions = []

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9200.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )

        detector._check_exit_conditions(
            redetection=redetection,
            block_node=node,
            current=current_stock,
            context=context
        )

        # 여전히 활성
        assert redetection.is_active()
        assert expression_engine.evaluate.call_count == 0

    def test_exit_condition_evaluation_error(
        self,
        detector,
        expression_engine,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """평가 오류 발생 시 재탐지 계속 활성"""
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9200.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )

        expression_engine.evaluate.side_effect = ValueError("Invalid expression")

        detector._check_exit_conditions(
            redetection=redetection,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        # 오류 발생해도 활성 유지 (안전한 선택)
        assert redetection.is_active()

    def test_exit_condition_context_includes_active_redetection(
        self,
        detector,
        expression_engine,
        block_node_with_redetection,
        current_stock,
        context
    ):
        """Context에 active_redetection이 포함되는지 확인"""
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9200.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )

        expression_engine.evaluate.return_value = False

        detector._check_exit_conditions(
            redetection=redetection,
            block_node=block_node_with_redetection,
            current=current_stock,
            context=context
        )

        # evaluate 호출 시 전달된 context 확인
        call_args = expression_engine.evaluate.call_args[0]
        eval_context = call_args[1]

        assert 'active_redetection' in eval_context
        assert eval_context['active_redetection'] == redetection
