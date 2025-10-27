"""
HighlightDetector Service Unit Tests

하이라이트 블록 탐지 서비스 단위 테스트
"""
import pytest
from datetime import date
from unittest.mock import Mock

from src.application.services.highlight_detector import HighlightDetector
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.domain.entities.highlights import HighlightCondition
from src.domain.entities.conditions import ExpressionEngine


class TestHighlightDetector:
    """HighlightDetector 서비스 테스트"""

    @pytest.fixture
    def expression_engine(self):
        """Expression engine mock"""
        return Mock(spec=ExpressionEngine)

    @pytest.fixture
    def detector(self, expression_engine):
        """HighlightDetector 인스턴스"""
        return HighlightDetector(expression_engine)

    @pytest.fixture
    def block_with_2_spots(self):
        """spot2가 있는 블록 (하이라이트 후보)"""
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            status=BlockStatus.ACTIVE,
            peak_price=10000.0,
            peak_volume=1000000
        )
        # spot1 추가
        block.add_spot(
            spot_date=date(2024, 1, 2),
            open_price=10500.0,
            close_price=10800.0,
            high_price=11000.0,
            low_price=10400.0,
            volume=1500000
        )
        # spot2 추가
        block.add_spot(
            spot_date=date(2024, 1, 3),
            open_price=11000.0,
            close_price=11200.0,
            high_price=11500.0,
            low_price=10900.0,
            volume=1600000
        )
        return block

    @pytest.fixture
    def block_with_1_spot(self):
        """spot1만 있는 블록 (하이라이트 아님)"""
        block = DynamicBlockDetection(
            block_id="block2",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 2, 1),
            status=BlockStatus.ACTIVE,
            peak_price=9000.0,
            peak_volume=800000
        )
        block.add_spot(
            spot_date=date(2024, 2, 2),
            open_price=9500.0,
            close_price=9700.0,
            high_price=9800.0,
            low_price=9400.0,
            volume=1200000
        )
        return block

    @pytest.fixture
    def block_without_spots(self):
        """spot이 없는 블록"""
        return DynamicBlockDetection(
            block_id="block3",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 3, 1),
            status=BlockStatus.ACTIVE,
            peak_price=8000.0,
            peak_volume=600000
        )

    @pytest.fixture
    def forward_spot_condition(self):
        """forward_spot 하이라이트 조건"""
        return HighlightCondition(
            type="forward_spot",
            enabled=True,
            priority=1,
            parameters={"required_spot_count": 2},
            description="2 consecutive spots at D+1, D+2"
        )

    @pytest.fixture
    def disabled_condition(self):
        """비활성화된 하이라이트 조건"""
        return HighlightCondition(
            type="forward_spot",
            enabled=False,
            parameters={"required_spot_count": 2}
        )

    @pytest.fixture
    def context(self):
        """평가 컨텍스트"""
        return {
            'ticker': '025980',
            'all_stocks': []
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # find_highlights() 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_find_highlights_with_2_spots(
        self,
        detector,
        block_with_2_spots,
        forward_spot_condition,
        context
    ):
        """spot2가 있는 블록을 하이라이트로 식별"""
        blocks = [block_with_2_spots]
        highlights = detector.find_highlights(blocks, forward_spot_condition, context)

        assert len(highlights) == 1
        assert highlights[0].block_id == "block1"
        assert highlights[0].get_spot_count() == 2

    def test_find_highlights_with_1_spot_not_qualified(
        self,
        detector,
        block_with_1_spot,
        forward_spot_condition,
        context
    ):
        """spot1만 있는 블록은 하이라이트 아님"""
        blocks = [block_with_1_spot]
        highlights = detector.find_highlights(blocks, forward_spot_condition, context)

        assert len(highlights) == 0

    def test_find_highlights_multiple_blocks(
        self,
        detector,
        block_with_2_spots,
        block_with_1_spot,
        block_without_spots,
        forward_spot_condition,
        context
    ):
        """여러 블록 중 하이라이트만 선택"""
        blocks = [block_with_2_spots, block_with_1_spot, block_without_spots]
        highlights = detector.find_highlights(blocks, forward_spot_condition, context)

        assert len(highlights) == 1
        assert highlights[0].block_id == "block1"

    def test_find_highlights_with_disabled_condition(
        self,
        detector,
        block_with_2_spots,
        disabled_condition,
        context
    ):
        """비활성화된 조건은 하이라이트를 찾지 않음"""
        blocks = [block_with_2_spots]
        highlights = detector.find_highlights(blocks, disabled_condition, context)

        assert len(highlights) == 0

    def test_find_highlights_empty_blocks(
        self,
        detector,
        forward_spot_condition,
        context
    ):
        """빈 블록 리스트는 빈 결과 반환"""
        highlights = detector.find_highlights([], forward_spot_condition, context)

        assert len(highlights) == 0

    def test_find_highlights_sorted_by_date(
        self,
        detector,
        forward_spot_condition,
        context
    ):
        """하이라이트는 시작일 기준 오름차순 정렬"""
        # 3개의 하이라이트 블록 (시작일이 다름)
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 3, 1),  # 가장 늦음
            status=BlockStatus.ACTIVE
        )
        block1.add_spot(date(2024, 3, 2), 100, 110, 120, 90, 1000)
        block1.add_spot(date(2024, 3, 3), 110, 120, 130, 100, 1100)

        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),  # 가장 이름
            status=BlockStatus.ACTIVE
        )
        block2.add_spot(date(2024, 1, 2), 100, 110, 120, 90, 1000)
        block2.add_spot(date(2024, 1, 3), 110, 120, 130, 100, 1100)

        block3 = DynamicBlockDetection(
            block_id="block3",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 2, 1),  # 중간
            status=BlockStatus.ACTIVE
        )
        block3.add_spot(date(2024, 2, 2), 100, 110, 120, 90, 1000)
        block3.add_spot(date(2024, 2, 3), 110, 120, 130, 100, 1100)

        blocks = [block1, block2, block3]  # 순서 뒤섞임
        highlights = detector.find_highlights(blocks, forward_spot_condition, context)

        assert len(highlights) == 3
        assert highlights[0].block_id == "block2"  # 가장 이른 날짜
        assert highlights[1].block_id == "block3"  # 중간
        assert highlights[2].block_id == "block1"  # 가장 늦은 날짜

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # find_primary() 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_find_primary_with_single_highlight(
        self,
        detector,
        block_with_2_spots
    ):
        """하이라이트가 1개면 그것이 Primary"""
        highlights = [block_with_2_spots]
        primary = detector.find_primary(highlights)

        assert primary is not None
        assert primary.block_id == "block1"

    def test_find_primary_with_multiple_highlights(
        self,
        detector
    ):
        """하이라이트가 여러 개면 첫 번째가 Primary"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1)
        )
        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 2, 1)
        )

        highlights = [block1, block2]  # 이미 정렬된 상태
        primary = detector.find_primary(highlights)

        assert primary is not None
        assert primary.block_id == "block1"

    def test_find_primary_with_empty_list(self, detector):
        """하이라이트가 없으면 None 반환"""
        primary = detector.find_primary([])

        assert primary is None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # classify_highlights() 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_classify_highlights_single(self, detector, block_with_2_spots):
        """하이라이트가 1개면 Primary만"""
        highlights = [block_with_2_spots]
        classified = detector.classify_highlights(highlights)

        assert len(classified['primary']) == 1
        assert classified['primary'][0].block_id == "block1"
        assert len(classified['secondary']) == 0

    def test_classify_highlights_multiple(self, detector):
        """하이라이트가 여러 개면 첫 번째만 Primary"""
        block1 = DynamicBlockDetection(
            block_id="block1", block_type=1, ticker="025980",
            condition_name="seed", started_at=date(2024, 1, 1)
        )
        block2 = DynamicBlockDetection(
            block_id="block2", block_type=1, ticker="025980",
            condition_name="seed", started_at=date(2024, 2, 1)
        )
        block3 = DynamicBlockDetection(
            block_id="block3", block_type=1, ticker="025980",
            condition_name="seed", started_at=date(2024, 3, 1)
        )

        highlights = [block1, block2, block3]
        classified = detector.classify_highlights(highlights)

        assert len(classified['primary']) == 1
        assert classified['primary'][0].block_id == "block1"
        assert len(classified['secondary']) == 2
        assert classified['secondary'][0].block_id == "block2"
        assert classified['secondary'][1].block_id == "block3"

    def test_classify_highlights_empty(self, detector):
        """하이라이트가 없으면 빈 딕셔너리"""
        classified = detector.classify_highlights([])

        assert len(classified['primary']) == 0
        assert len(classified['secondary']) == 0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # count_highlights() 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_count_highlights(
        self,
        detector,
        block_with_2_spots,
        block_with_1_spot,
        forward_spot_condition,
        context
    ):
        """하이라이트 개수 반환"""
        blocks = [block_with_2_spots, block_with_1_spot]
        count = detector.count_highlights(blocks, forward_spot_condition, context)

        assert count == 1

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # has_highlight() 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_has_highlight_true(
        self,
        detector,
        block_with_2_spots,
        forward_spot_condition,
        context
    ):
        """하이라이트가 있으면 True"""
        blocks = [block_with_2_spots]
        assert detector.has_highlight(blocks, forward_spot_condition, context) is True

    def test_has_highlight_false(
        self,
        detector,
        block_with_1_spot,
        forward_spot_condition,
        context
    ):
        """하이라이트가 없으면 False"""
        blocks = [block_with_1_spot]
        assert detector.has_highlight(blocks, forward_spot_condition, context) is False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # backward_spot 타입 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_find_highlights_backward_spot(self, detector, context):
        """backward_spot 타입 하이라이트 탐지"""
        block = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 5)
        )
        # backward_spot 플래그 설정
        block.set_metadata('is_backward_spot', True)

        condition = HighlightCondition(
            type="backward_spot",
            enabled=True,
            parameters={}
        )

        highlights = detector.find_highlights([block], condition, context)

        assert len(highlights) == 1
        assert highlights[0].block_id == "block2"
