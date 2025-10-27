"""
SupportResistanceAnalyzer Service Unit Tests

Support/Resistance 분석 서비스 단위 테스트
"""
import pytest
from datetime import date

from src.application.services.support_resistance_analyzer import (
    SupportResistanceAnalyzer,
    SupportResistanceLevel,
    SupportResistanceAnalysis
)
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.domain.entities.core import Stock


class TestSupportResistanceAnalyzer:
    """SupportResistanceAnalyzer 서비스 테스트"""

    @pytest.fixture
    def analyzer(self):
        """SupportResistanceAnalyzer 인스턴스 (tolerance=2%)"""
        return SupportResistanceAnalyzer(tolerance_pct=2.0)

    @pytest.fixture
    def block1(self):
        """Block1 (기준 블록)"""
        return DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,  # reference_high
            peak_volume=1000000
        )

    @pytest.fixture
    def all_stocks_block1_range(self):
        """Block1 기간 내 주가 데이터 (최저가 9000원)"""
        return [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9500, high=9800, low=9400, close=9700, volume=1000000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 2),
                  open=9700, high=10000, low=9600, close=9900, volume=1100000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 3),
                  open=9900, high=10200, low=9000, close=9500, volume=1200000),  # 최저가
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 10),
                  open=9500, high=10000, low=9400, close=9800, volume=1000000),
        ]

    @pytest.fixture
    def block2_strong_support(self):
        """Block2 - Strong support (Block1.high 위)"""
        return DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 15),
            ended_at=date(2024, 1, 20),
            status=BlockStatus.COMPLETED,
            peak_price=12000.0,  # Block1.high(10000) 위
            peak_volume=1500000
        )

    @pytest.fixture
    def block3_weak_support(self):
        """Block3 - Weak support (Block1 range 내)"""
        return DynamicBlockDetection(
            block_id="block3",
            block_type=3,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 2, 1),
            ended_at=date(2024, 2, 10),
            status=BlockStatus.COMPLETED,
            peak_price=9500.0,  # Block1 range(9000~10000) 내
            peak_volume=800000
        )

    @pytest.fixture
    def block4_broken(self):
        """Block4 - Broken support (Block1.low 아래)"""
        return DynamicBlockDetection(
            block_id="block4",
            block_type=4,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 3, 1),
            ended_at=date(2024, 3, 10),
            status=BlockStatus.COMPLETED,
            peak_price=8500.0,  # Block1.low(9000) 아래
            peak_volume=600000
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # analyze() 메서드 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_analyze_strong_support(
        self,
        analyzer,
        block1,
        block2_strong_support,
        all_stocks_block1_range
    ):
        """Strong support 분석"""
        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block2_strong_support],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        assert len(analysis.levels) == 1
        assert analysis.levels[0].is_strong_support()
        assert analysis.levels[0].level_type == "strong_support"
        assert analysis.levels[0].current_price == 12000.0
        assert analysis.levels[0].reference_high == 10000.0

    def test_analyze_weak_support(
        self,
        analyzer,
        block1,
        block3_weak_support,
        all_stocks_block1_range
    ):
        """Weak support 분석"""
        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block3_weak_support],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        assert len(analysis.levels) == 1
        assert analysis.levels[0].is_weak_support()
        assert analysis.levels[0].level_type == "weak_support"
        assert analysis.levels[0].current_price == 9500.0

    def test_analyze_broken_support(
        self,
        analyzer,
        block1,
        block4_broken,
        all_stocks_block1_range
    ):
        """Broken support 분석"""
        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block4_broken],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        assert len(analysis.levels) == 1
        assert analysis.levels[0].is_broken()
        assert analysis.levels[0].level_type == "broken"
        assert analysis.levels[0].current_price == 8500.0

    def test_analyze_multiple_blocks(
        self,
        analyzer,
        block1,
        block2_strong_support,
        block3_weak_support,
        block4_broken,
        all_stocks_block1_range
    ):
        """여러 블록 동시 분석"""
        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block2_strong_support, block3_weak_support, block4_broken],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        assert len(analysis.levels) == 3
        assert analysis.levels[0].is_strong_support()  # block2
        assert analysis.levels[1].is_weak_support()   # block3
        assert analysis.levels[2].is_broken()         # block4

    def test_analyze_summary(
        self,
        analyzer,
        block1,
        block2_strong_support,
        block3_weak_support,
        block4_broken,
        all_stocks_block1_range
    ):
        """분석 요약 정보"""
        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block2_strong_support, block3_weak_support, block4_broken],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        summary = analysis.get_summary()

        assert summary['reference_block_id'] == 'block1'
        assert summary['reference_high'] == 10000.0
        assert summary['num_forward_blocks'] == 3
        assert summary['num_levels_analyzed'] == 3
        assert summary['strong_support_count'] == 1
        assert summary['weak_support_count'] == 1
        assert summary['broken_count'] == 1

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 재시험 이벤트 탐지 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_detect_retest_events(self, analyzer, block1):
        """Block1.high 근처로 복귀한 재시험 이벤트 탐지"""
        # Block2 생성 (Block1.high 위에서 시작)
        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 15),
            ended_at=date(2024, 1, 20),
            peak_price=12000.0
        )

        # Block2 기간 내 주가 데이터 (10100원으로 재시험)
        all_stocks = [
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9500, high=10000, low=9000, close=9700, volume=1000000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 15),
                  open=11000, high=12000, low=10800, close=11500, volume=1500000),
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 17),
                  open=10500, high=10100, low=10000, close=10050, volume=1200000),  # 재시험 (tolerance 2% = 9800~10200)
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 20),
                  open=10100, high=10500, low=10000, close=10300, volume=1300000),
        ]

        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block2],
            all_stocks=all_stocks,
            analysis_period_days=365
        )

        assert len(analysis.retest_events) >= 1
        # 재시험 이벤트 확인
        retest = analysis.retest_events[0]
        assert retest['reference_high'] == 10000.0
        assert 9800 <= retest['price'] <= 10200  # tolerance 2% 범위

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 저항→지지 전환 이벤트 탐지 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_detect_resistance_to_support_flip(self, analyzer, block1):
        """Block1.high 돌파 후 지지로 전환 탐지"""
        # Block2: Block1.high 돌파
        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 15),
            ended_at=date(2024, 1, 20),
            peak_price=12000.0  # Block1.high(10000) 돌파
        )

        # Block3: Block1.high에서 지지받음
        block3 = DynamicBlockDetection(
            block_id="block3",
            block_type=3,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 2, 1),
            ended_at=date(2024, 2, 10),
            peak_price=11000.0
        )

        # 주가 데이터
        all_stocks = [
            # Block1 기간
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 1),
                  open=9500, high=10000, low=9000, close=9700, volume=1000000),
            # Block2 기간 (돌파)
            Stock(ticker="025980", name="강원랜드", date=date(2024, 1, 15),
                  open=10500, high=12000, low=10300, close=11500, volume=1500000),
            # Block3 기간 (지지)
            Stock(ticker="025980", name="강원랜드", date=date(2024, 2, 1),
                  open=10500, high=11000, low=10000, close=10800, volume=1300000),  # 저가가 Block1.high에서 지지
        ]

        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block2, block3],
            all_stocks=all_stocks,
            analysis_period_days=365
        )

        # 저항→지지 전환 이벤트 확인
        assert len(analysis.resistance_to_support_flips) >= 1
        flip = analysis.resistance_to_support_flips[0]
        assert flip['breakout_block_id'] == 'block2'
        assert flip['breakout_price'] == 12000.0
        assert flip['reference_high'] == 10000.0
        assert flip['flip_confirmed'] is True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 편의 메서드 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_is_strong_support_method(self, analyzer):
        """is_strong_support() 편의 메서드"""
        assert analyzer.is_strong_support(current_price=12000, reference_high=10000) is True
        assert analyzer.is_strong_support(current_price=10000, reference_high=10000) is True
        assert analyzer.is_strong_support(current_price=9500, reference_high=10000) is False

    def test_is_weak_support_method(self, analyzer):
        """is_weak_support() 편의 메서드"""
        assert analyzer.is_weak_support(
            current_price=9500,
            reference_high=10000,
            reference_low=9000
        ) is True
        assert analyzer.is_weak_support(
            current_price=12000,
            reference_high=10000,
            reference_low=9000
        ) is False
        assert analyzer.is_weak_support(
            current_price=8500,
            reference_high=10000,
            reference_low=9000
        ) is False

    def test_is_broken_method(self, analyzer):
        """is_broken() 편의 메서드"""
        assert analyzer.is_broken(current_price=8500, reference_low=9000) is True
        assert analyzer.is_broken(current_price=9000, reference_low=9000) is False
        assert analyzer.is_broken(current_price=9500, reference_low=9000) is False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Edge Case 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_analyze_with_no_forward_blocks(self, analyzer, block1, all_stocks_block1_range):
        """Forward blocks가 없을 때"""
        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        assert len(analysis.levels) == 0
        assert len(analysis.retest_events) == 0
        assert len(analysis.resistance_to_support_flips) == 0

    def test_analyze_with_missing_peak_price(self, analyzer, block1, all_stocks_block1_range):
        """peak_price가 없는 블록"""
        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 15),
            peak_price=None  # peak_price 없음
        )

        analysis = analyzer.analyze(
            reference_block=block1,
            forward_blocks=[block2],
            all_stocks=all_stocks_block1_range,
            analysis_period_days=365
        )

        # peak_price가 없으면 레벨 분석 제외
        assert len(analysis.levels) == 0


class TestSupportResistanceLevel:
    """SupportResistanceLevel Value Object 테스트"""

    @pytest.fixture
    def block1(self):
        """Block1 (기준 블록)"""
        return DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            peak_price=10000.0
        )

    def test_strong_support_level(self, block1):
        """Strong support 레벨"""
        level = SupportResistanceLevel(
            level_type="strong_support",
            reference_block=block1,
            reference_high=10000.0,
            reference_low=9000.0,
            current_price=12000.0,
            distance_pct=20.0,
            analysis_date=date(2024, 1, 15)
        )

        assert level.is_strong_support() is True
        assert level.is_weak_support() is False
        assert level.is_broken() is False

    def test_weak_support_level(self, block1):
        """Weak support 레벨"""
        level = SupportResistanceLevel(
            level_type="weak_support",
            reference_block=block1,
            reference_high=10000.0,
            reference_low=9000.0,
            current_price=9500.0,
            distance_pct=5.56,
            analysis_date=date(2024, 1, 15)
        )

        assert level.is_strong_support() is False
        assert level.is_weak_support() is True
        assert level.is_broken() is False

    def test_broken_level(self, block1):
        """Broken support 레벨"""
        level = SupportResistanceLevel(
            level_type="broken",
            reference_block=block1,
            reference_high=10000.0,
            reference_low=9000.0,
            current_price=8500.0,
            distance_pct=-5.56,
            analysis_date=date(2024, 1, 15)
        )

        assert level.is_strong_support() is False
        assert level.is_weak_support() is False
        assert level.is_broken() is True
