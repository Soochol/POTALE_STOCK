"""
Builtin Functions 단위 테스트
"""
import pytest
from src.domain.entities.conditions.builtin_functions import (
    upside_extension_ratio,
)


class TestUpsideExtensionRatio:
    """upside_extension_ratio 함수 테스트"""

    def test_upside_positive_direction(self):
        """상승 방향 테스트 (+200%)"""
        # base=10000, high=12000, low=11000
        # distance_to_high = |10000 - 12000| = 2000
        # distance_to_low = |10000 - 11000| = 1000
        # ratio = (2000 / 1000) * 100 = 200
        # high_price >= base_price → +200
        result = upside_extension_ratio(10000, 12000, 11000, {})
        assert result == 200.0

    def test_upside_negative_direction(self):
        """하락 방향 테스트 (-50%)"""
        # base=10000, high=9000, low=8000
        # distance_to_high = |10000 - 9000| = 1000
        # distance_to_low = |10000 - 8000| = 2000
        # ratio = (1000 / 2000) * 100 = 50
        # high_price < base_price → -50
        result = upside_extension_ratio(10000, 9000, 8000, {})
        assert result == -50.0

    def test_equal_distances(self):
        """고가/저가 거리가 같은 경우 (100%)"""
        # base=10000, high=11000, low=9000
        # distance_to_high = 1000
        # distance_to_low = 1000
        # ratio = 100
        result = upside_extension_ratio(10000, 11000, 9000, {})
        assert result == 100.0

    def test_zero_denominator(self):
        """분모가 0인 경우 (저가 = 기준가)"""
        # base=10000, high=12000, low=10000
        # distance_to_low = 0 → 0.0 반환
        result = upside_extension_ratio(10000, 12000, 10000, {})
        assert result == 0.0

    def test_high_equals_base(self):
        """고가가 기준가와 같은 경우 (경계값)"""
        # base=10000, high=10000, low=9000
        # distance_to_high = 0
        # distance_to_low = 1000
        # ratio = 0
        # high_price >= base_price → +0
        result = upside_extension_ratio(10000, 10000, 9000, {})
        assert result == 0.0

    def test_realistic_case_strong_upside(self):
        """실전 케이스: 강한 상승 (300%)"""
        # base=15000, high=18000, low=16000
        # distance_to_high = 3000
        # distance_to_low = 1000
        # ratio = 300
        result = upside_extension_ratio(15000, 18000, 16000, {})
        assert result == 300.0

    def test_realistic_case_weak_upside(self):
        """실전 케이스: 약한 상승 (50%)"""
        # base=20000, high=21000, low=18000
        # distance_to_high = 1000
        # distance_to_low = 2000
        # ratio = 50
        result = upside_extension_ratio(20000, 21000, 18000, {})
        assert result == 50.0

    def test_base_between_high_and_low(self):
        """기준가가 고가와 저가 사이에 있는 경우"""
        # base=10000, high=11000, low=9500
        # distance_to_high = 1000
        # distance_to_low = 500
        # ratio = 200
        result = upside_extension_ratio(10000, 11000, 9500, {})
        assert result == 200.0

    def test_all_below_base(self):
        """고가/저가가 모두 기준가 아래인 경우"""
        # base=10000, high=9500, low=9000
        # distance_to_high = 500
        # distance_to_low = 1000
        # ratio = 50
        # high_price < base_price → -50
        result = upside_extension_ratio(10000, 9500, 9000, {})
        assert result == -50.0

    def test_all_above_base(self):
        """고가/저가가 모두 기준가 위인 경우"""
        # base=10000, high=12000, low=11000
        # distance_to_high = 2000
        # distance_to_low = 1000
        # ratio = 200
        # high_price >= base_price → +200
        result = upside_extension_ratio(10000, 12000, 11000, {})
        assert result == 200.0
