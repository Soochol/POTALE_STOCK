"""
Builtin Functions 단위 테스트
"""
import pytest
from src.domain.entities.conditions.builtin_functions import (
    upside_extension_ratio,
)


class TestUpsideExtensionRatio:
    """upside_extension_ratio 함수 테스트 (3중 조건 검증)"""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조건 만족 케이스 (비율 반환)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_level_up_case_a_all_above(self):
        """케이스 A: 고가/저가 모두 기준가 위 (명확한 레벨업)"""
        # base=10000, high=12000 (+20%), low=11000 (+10%)
        # 조건1: 12000 >= 11000 (10%) ✅
        # 조건2: 11000 >= 9500 (-5%) ✅
        # 조건3: mid=11500 > 10000 ✅
        # ratio = (2000 / 1000) * 100 = 200
        result = upside_extension_ratio(10000, 12000, 11000)
        assert result == 200.0

    def test_level_up_case_b_low_at_boundary(self):
        """케이스 B: 저가가 -5% 경계 (레벨업)"""
        # base=10000, high=12000 (+20%), low=9500 (-5%)
        # 조건1: 12000 >= 11000 ✅
        # 조건2: 9500 >= 9500 ✅ (경계)
        # 조건3: mid=10750 > 10000 ✅
        # ratio = (2000 / 500) * 100 = 400
        result = upside_extension_ratio(10000, 12000, 9500)
        assert result == 400.0

    def test_level_up_case_d_moderate(self):
        """케이스 D: 적당한 레벨업"""
        # base=10000, high=11000 (+10%), low=9500 (-5%)
        # 조건1: 11000 >= 11000 ✅ (경계)
        # 조건2: 9500 >= 9500 ✅ (경계)
        # 조건3: mid=10250 > 10000 ✅
        # ratio = (1000 / 500) * 100 = 200
        result = upside_extension_ratio(10000, 11000, 9500)
        assert result == 200.0

    def test_strong_level_up(self):
        """강한 레벨업 (고가 +20%, 저가 +5%)"""
        # base=15000, high=18000 (+20%), low=15750 (+5%)
        # 조건1: 18000 >= 16500 ✅
        # 조건2: 15750 >= 14250 ✅
        # 조건3: mid=16875 > 15000 ✅
        # ratio = (3000 / 750) * 100 = 400
        result = upside_extension_ratio(15000, 18000, 15750)
        assert result == 400.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조건 불만족 케이스 (0.0 반환)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_failed_case_c_low_too_low(self):
        """케이스 C: 저가가 -10% (조건 2 실패)"""
        # base=10000, high=12000 (+20%), low=9000 (-10%)
        # 조건1: 12000 >= 11000 ✅
        # 조건2: 9000 >= 9500 ❌ (실패!)
        result = upside_extension_ratio(10000, 12000, 9000)
        assert result == 0.0

    def test_failed_case_e_high_too_low(self):
        """케이스 E: 고가가 +5% (조건 1 실패)"""
        # base=10000, high=10500 (+5%), low=10200 (+2%)
        # 조건1: 10500 >= 11000 ❌ (실패!)
        result = upside_extension_ratio(10000, 10500, 10200)
        assert result == 0.0

    def test_failed_high_condition(self):
        """조건 1 실패: 고가가 +10% 미만"""
        # base=10000, high=10900 (+9%), low=10500
        # 조건1: 10900 >= 11000 ❌
        result = upside_extension_ratio(10000, 10900, 10500)
        assert result == 0.0

    def test_failed_low_condition(self):
        """조건 2 실패: 저가가 -5% 초과 하락"""
        # base=10000, high=12000 (+20%), low=9400 (-6%)
        # 조건1: 12000 >= 11000 ✅
        # 조건2: 9400 >= 9500 ❌
        result = upside_extension_ratio(10000, 12000, 9400)
        assert result == 0.0

    def test_failed_mid_price_condition(self):
        """조건 3 실패: 중심가격이 기준가 이하"""
        # base=10000, high=11000 (+10%), low=9000 (-10%)
        # 조건1: 11000 >= 11000 ✅
        # 조건2: 9000 >= 9500 ❌ (이미 여기서 실패)
        # mid=10000 = 10000 (조건3도 실패)
        result = upside_extension_ratio(10000, 11000, 9000)
        assert result == 0.0

    def test_all_below_base(self):
        """고가/저가 모두 기준가 아래 (조건 1 실패)"""
        # base=10000, high=9000, low=8000
        # 조건1: 9000 >= 11000 ❌
        result = upside_extension_ratio(10000, 9000, 8000)
        assert result == 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 엣지 케이스
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_zero_denominator(self):
        """분모가 0인 경우 (저가 = 기준가)"""
        # base=10000, high=12000, low=10000
        # 조건1: 12000 >= 11000 ✅
        # 조건2: 10000 >= 9500 ✅
        # 조건3: mid=11000 > 10000 ✅
        # distance_to_low = 0 → 0.0 반환
        result = upside_extension_ratio(10000, 12000, 10000)
        assert result == 0.0

    def test_high_equals_threshold(self):
        """고가가 정확히 +10% (경계값)"""
        # base=10000, high=11000 (정확히 10%), low=10500
        # 조건1: 11000 >= 11000 ✅ (경계)
        # 조건2: 10500 >= 9500 ✅
        # 조건3: mid=10750 > 10000 ✅
        # ratio = (1000 / 500) * 100 = 200
        result = upside_extension_ratio(10000, 11000, 10500)
        assert result == 200.0

    def test_low_equals_threshold(self):
        """저가가 정확히 -5% (경계값)"""
        # base=10000, high=12000, low=9500 (정확히 -5%)
        # 조건1: 12000 >= 11000 ✅
        # 조건2: 9500 >= 9500 ✅ (경계)
        # 조건3: mid=10750 > 10000 ✅
        result = upside_extension_ratio(10000, 12000, 9500)
        assert result == 400.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 커스텀 파라미터 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_custom_high_threshold_15pct(self):
        """커스텀 고가 임계값 15%"""
        # base=10000, high=11500 (+15%), low=10500
        # min_high_gain_pct=15.0 → threshold=11500
        # 조건1: 11500 >= 11500 ✅
        # 조건2: 10500 >= 9500 ✅
        # 조건3: mid=11000 > 10000 ✅
        # ratio = (1500 / 500) * 100 = 300
        result = upside_extension_ratio(10000, 11500, 10500, min_high_gain_pct=15.0)
        assert result == 300.0

    def test_custom_low_threshold_10pct(self):
        """커스텀 저가 임계값 -10%"""
        # base=10000, high=12000, low=9000 (-10%)
        # max_low_drop_pct=10.0 → threshold=9000
        # 조건1: 12000 >= 11000 ✅
        # 조건2: 9000 >= 9000 ✅ (경계)
        # 조건3: mid=10500 > 10000 ✅
        result = upside_extension_ratio(10000, 12000, 9000, max_low_drop_pct=10.0)
        assert result == 200.0

    def test_custom_both_thresholds(self):
        """커스텀 임계값 조합 (고가 +20%, 저가 -15%)"""
        # base=10000, high=12000 (+20%), low=8500 (-15%)
        # min_high_gain_pct=20.0, max_low_drop_pct=15.0
        # 조건1: 12000 >= 12000 ✅
        # 조건2: 8500 >= 8500 ✅
        # 조건3: mid=10250 > 10000 ✅
        result = upside_extension_ratio(
            10000, 12000, 8500,
            min_high_gain_pct=20.0,
            max_low_drop_pct=15.0
        )
        assert result > 0.0  # 비율 계산됨

    def test_custom_threshold_failure(self):
        """커스텀 임계값으로 조건 불만족"""
        # base=10000, high=11000 (+10%), low=10500
        # min_high_gain_pct=15.0 → threshold=11500
        # 조건1: 11000 >= 11500 ❌
        result = upside_extension_ratio(10000, 11000, 10500, min_high_gain_pct=15.0)
        assert result == 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # YAML 호환성 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def test_yaml_compatible_no_params(self):
        """YAML 호환: 파라미터 생략 (기본값 사용)"""
        # 기본값: min_high_gain_pct=10.0, max_low_drop_pct=5.0
        result = upside_extension_ratio(10000, 12000, 11000)
        assert result == 200.0

    def test_yaml_compatible_with_context(self):
        """YAML 호환: context 딕셔너리 전달"""
        # context는 선택적 파라미터
        result = upside_extension_ratio(10000, 12000, 11000, context={'test': 'value'})
        assert result == 200.0
