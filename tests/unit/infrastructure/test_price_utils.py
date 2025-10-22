"""
Tests for price_utils.py
가격 유틸리티 함수 테스트
"""
import pytest
from src.infrastructure.utils.price_utils import round_to_tick_size


class TestRoundToTickSize:
    """round_to_tick_size() 함수 테스트"""

    def test_under_1000_won(self):
        """1,000원 미만: 1원 단위 반올림"""
        assert round_to_tick_size(100.0) == 100
        assert round_to_tick_size(500.5) == 501
        assert round_to_tick_size(999.4) == 999
        assert round_to_tick_size(999.6) == 1000

    def test_1000_to_5000_won(self):
        """1,000원 ~ 5,000원 미만: 5원 단위 반올림"""
        assert round_to_tick_size(1000.0) == 1000
        assert round_to_tick_size(1002.0) == 1000  # 1000~1002 → 1000
        assert round_to_tick_size(1003.0) == 1005  # 1003~1007 → 1005
        assert round_to_tick_size(2347.0) == 2345
        assert round_to_tick_size(2348.0) == 2350
        assert round_to_tick_size(4999.0) == 5000

    def test_5000_to_10000_won(self):
        """5,000원 ~ 10,000원 미만: 10원 단위 반올림"""
        assert round_to_tick_size(5000.0) == 5000
        assert round_to_tick_size(5004.0) == 5000  # 5000~5004 → 5000
        assert round_to_tick_size(5005.0) == 5010  # 5005~5014 → 5010
        assert round_to_tick_size(7339.0) == 7340  # 7339 → 7340 (실제 문제 케이스)
        assert round_to_tick_size(7339.6) == 7340  # 7339.6 → 7340
        assert round_to_tick_size(7340.0) == 7340
        assert round_to_tick_size(9999.0) == 10000

    def test_10000_to_50000_won(self):
        """10,000원 ~ 50,000원 미만: 50원 단위 반올림"""
        assert round_to_tick_size(10000.0) == 10000
        assert round_to_tick_size(10024.0) == 10000  # 10000~10024 → 10000
        assert round_to_tick_size(10025.0) == 10050  # 10025~10074 → 10050
        assert round_to_tick_size(25678.0) == 25650
        assert round_to_tick_size(49999.0) == 50000

    def test_50000_to_100000_won(self):
        """50,000원 ~ 100,000원 미만: 100원 단위 반올림"""
        assert round_to_tick_size(50000.0) == 50000
        assert round_to_tick_size(50049.0) == 50000  # 50000~50049 → 50000
        assert round_to_tick_size(50050.0) == 50100  # 50050~50149 → 50100
        assert round_to_tick_size(52345.0) == 52300
        assert round_to_tick_size(99999.0) == 100000

    def test_100000_to_500000_won(self):
        """100,000원 ~ 500,000원 미만: 500원 단위 반올림"""
        assert round_to_tick_size(100000.0) == 100000
        assert round_to_tick_size(100249.0) == 100000  # 100000~100249 → 100000
        assert round_to_tick_size(100250.0) == 100500  # 100250~100749 → 100500
        assert round_to_tick_size(123456.0) == 123500
        assert round_to_tick_size(499999.0) == 500000

    def test_over_500000_won(self):
        """500,000원 이상: 1,000원 단위 반올림"""
        assert round_to_tick_size(500000.0) == 500000
        assert round_to_tick_size(500499.0) == 500000  # 500000~500499 → 500000
        assert round_to_tick_size(500500.0) == 501000  # 500500~501499 → 501000
        assert round_to_tick_size(1234567.0) == 1235000

    def test_boundary_values(self):
        """경계값 테스트"""
        # 999원 → 1,000원 경계
        assert round_to_tick_size(999.4) == 999  # 1원 단위
        assert round_to_tick_size(999.6) == 1000  # 1원 단위 → 1,000원

        # 4,999원 → 5,000원 경계
        assert round_to_tick_size(4998.0) == 5000  # 5원 단위
        assert round_to_tick_size(4999.0) == 5000  # 5원 단위

        # 9,999원 → 10,000원 경계
        assert round_to_tick_size(9999.0) == 10000  # 10원 단위

        # 49,999원 → 50,000원 경계
        assert round_to_tick_size(49999.0) == 50000  # 50원 단위

        # 99,999원 → 100,000원 경계
        assert round_to_tick_size(99999.0) == 100000  # 100원 단위

        # 499,999원 → 500,000원 경계
        assert round_to_tick_size(499999.0) == 500000  # 500원 단위

    def test_real_problem_case(self):
        """실제 문제 케이스 테스트 (ID 805: 2018-04-10)"""
        # fchart API 응답:
        # open=7250, high=7339.xx, low=6990, close=7340.yy

        # Before: int() 변환
        # high=7339, close=7340 → close > high (검증 실패)

        # After: round_to_tick_size() 적용
        # high=7340, close=7340 → close <= high (검증 성공)

        high = round_to_tick_size(7339.6)  # 실제로는 정확한 값 모름, 추정치
        close = round_to_tick_size(7340.4)

        assert high == 7340
        assert close == 7340
        assert close <= high  # 검증 조건 만족!

    def test_integer_prices(self):
        """정수 가격 입력 (이미 호가 단위인 경우)"""
        assert round_to_tick_size(1000) == 1000
        assert round_to_tick_size(5000) == 5000
        assert round_to_tick_size(7340) == 7340
        assert round_to_tick_size(50000) == 50000

    def test_zero_and_negative(self):
        """0 및 음수 처리"""
        assert round_to_tick_size(0.0) == 0
        # 음수는 주식 가격에서 발생하지 않지만, 혹시 모를 경우 대비
        assert round_to_tick_size(-100.0) == -100
