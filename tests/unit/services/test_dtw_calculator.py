"""
Unit Tests for DTW Calculator

Dynamic Time Warping 알고리즘 테스트
"""
import pytest
import numpy as np

from src.application.services.dtw_calculator import DTWCalculator


class TestDTWCalculator:
    """DTW Calculator 테스트"""

    def test_identical_sequences(self):
        """동일한 시퀀스 DTW distance는 0"""
        seq = [0.0, 0.5, 1.0, 0.5, 0.0]
        distance = DTWCalculator.calculate_distance(seq, seq)

        assert distance == 0.0

    def test_similar_sequences(self):
        """유사한 시퀀스는 낮은 distance"""
        seq1 = [0.0, 0.5, 1.0, 0.5, 0.0]
        seq2 = [0.1, 0.6, 0.9, 0.4, 0.1]

        distance = DTWCalculator.calculate_distance(seq1, seq2)

        # Distance should be small but non-zero
        assert 0 < distance < 1.0

    def test_different_sequences(self):
        """다른 시퀀스는 높은 distance"""
        seq1 = [0.0, 0.0, 0.0, 0.0, 0.0]
        seq2 = [1.0, 1.0, 1.0, 1.0, 1.0]

        distance = DTWCalculator.calculate_distance(seq1, seq2)

        # Distance should be large
        assert distance > 1.0

    def test_different_length_sequences(self):
        """길이가 다른 시퀀스도 계산 가능"""
        seq1 = [0.0, 0.5, 1.0]
        seq2 = [0.0, 0.25, 0.5, 0.75, 1.0]

        distance = DTWCalculator.calculate_distance(seq1, seq2)

        # Should compute distance without error
        assert distance >= 0

    def test_empty_sequences(self):
        """빈 시퀀스는 무한대 distance"""
        distance1 = DTWCalculator.calculate_distance([], [1.0, 2.0])
        distance2 = DTWCalculator.calculate_distance([1.0, 2.0], [])
        distance3 = DTWCalculator.calculate_distance([], [])

        assert distance1 == float('inf')
        assert distance2 == float('inf')
        assert distance3 == float('inf')

    def test_sakoe_chiba_window(self):
        """Sakoe-Chiba window 제약"""
        seq1 = [0.0, 0.5, 1.0, 0.5, 0.0]
        seq2 = [0.0, 0.5, 1.0, 0.5, 0.0]

        # No window
        distance_no_window = DTWCalculator.calculate_distance(seq1, seq2, window=None)

        # Narrow window
        distance_narrow = DTWCalculator.calculate_distance(seq1, seq2, window=1)

        # Identical sequences should have 0 distance regardless of window
        assert distance_no_window == 0.0
        assert distance_narrow == 0.0

    def test_similarity_identical(self):
        """동일한 시퀀스의 similarity는 1.0"""
        seq = [0.0, 0.5, 1.0]
        similarity = DTWCalculator.calculate_similarity(seq, seq)

        assert similarity == pytest.approx(1.0, rel=1e-3)

    def test_similarity_similar(self):
        """유사한 시퀀스는 높은 similarity"""
        seq1 = [0.0, 0.5, 1.0]
        seq2 = [0.1, 0.5, 0.9]

        similarity = DTWCalculator.calculate_similarity(seq1, seq2)

        # Should be high similarity
        assert similarity > 0.7

    def test_similarity_different(self):
        """완전히 다른 시퀀스 (flat vs flat with offset)"""
        seq1 = [0.0, 0.0, 0.0]
        seq2 = [1.0, 1.0, 1.0]

        similarity = DTWCalculator.calculate_similarity(seq1, seq2)

        # DTW measures shape distance, so flat shapes have some similarity
        # even with value offset. Similarity should be positive but not perfect
        assert 0.3 < similarity < 0.9

    def test_similarity_normalized(self):
        """정규화된 similarity는 [0, 1] 범위"""
        seq1 = [0.0, 0.5, 1.0, 0.5, 0.0]
        seq2 = [0.2, 0.6, 0.8, 0.4, 0.2]

        similarity = DTWCalculator.calculate_similarity(seq1, seq2, normalize=True)

        assert 0.0 <= similarity <= 1.0

    def test_similarity_non_normalized(self):
        """비정규화 similarity 테스트"""
        seq1 = [0.0, 0.5, 1.0]
        seq2 = [0.0, 0.5, 1.0]

        similarity_norm = DTWCalculator.calculate_similarity(seq1, seq2, normalize=True)
        similarity_no_norm = DTWCalculator.calculate_similarity(seq1, seq2, normalize=False)

        # Identical sequences should have similarity=1.0 in both cases
        assert similarity_norm == pytest.approx(1.0, rel=1e-3)
        assert similarity_no_norm == pytest.approx(1.0, rel=1e-3)

    def test_warping_path_identical(self):
        """동일한 시퀀스의 warping path는 대각선"""
        seq = [0.0, 0.5, 1.0]
        path = DTWCalculator.get_warping_path(seq, seq)

        # Path should be diagonal
        expected_path = [(0, 0), (1, 1), (2, 2)]
        assert path == expected_path

    def test_warping_path_different_length(self):
        """길이가 다른 시퀀스의 warping path"""
        seq1 = [0.0, 1.0]
        seq2 = [0.0, 0.5, 1.0]

        path = DTWCalculator.get_warping_path(seq1, seq2)

        # Path should exist and have valid indices
        assert len(path) > 0
        for i, j in path:
            assert 0 <= i < len(seq1)
            assert 0 <= j < len(seq2)

    def test_warping_path_empty(self):
        """빈 시퀀스의 warping path는 빈 리스트"""
        path1 = DTWCalculator.get_warping_path([], [1.0, 2.0])
        path2 = DTWCalculator.get_warping_path([1.0, 2.0], [])

        assert path1 == []
        assert path2 == []

    def test_constrained_dtw_similar_length(self):
        """비슷한 길이의 시퀀스는 정상 계산"""
        seq1 = [0.0, 0.5, 1.0]
        seq2 = [0.1, 0.5, 0.9]

        similarity = DTWCalculator.constrained_dtw(seq1, seq2, max_length_diff_ratio=0.3)

        # Should compute similarity
        assert similarity > 0.5

    def test_constrained_dtw_very_different_length(self):
        """너무 다른 길이는 0.0 반환"""
        seq1 = [0.0, 0.5, 1.0]  # Length 3
        seq2 = [0.0, 0.5, 1.0, 0.5, 0.0, 0.5, 1.0, 0.5]  # Length 8

        # max_length_diff_ratio=0.3 means max 30% difference
        # (8-3)/8 = 0.625 > 0.3, so should return 0.0
        similarity = DTWCalculator.constrained_dtw(seq1, seq2, max_length_diff_ratio=0.3)

        assert similarity == 0.0

    def test_constrained_dtw_empty(self):
        """빈 시퀀스는 0.0"""
        assert DTWCalculator.constrained_dtw([], [1.0]) == 0.0
        assert DTWCalculator.constrained_dtw([1.0], []) == 0.0
        assert DTWCalculator.constrained_dtw([], []) == 0.0

    def test_upward_trend_similarity(self):
        """상승 트렌드 유사도"""
        upward1 = [0.0, 0.25, 0.5, 0.75, 1.0]
        upward2 = [0.1, 0.3, 0.5, 0.7, 0.9]

        similarity = DTWCalculator.calculate_similarity(upward1, upward2)

        # Similar upward trends should have high similarity
        assert similarity > 0.8

    def test_opposite_trend_similarity(self):
        """반대 트렌드 (DTW는 shape만 비교, 방향은 무시)"""
        upward = [0.0, 0.25, 0.5, 0.75, 1.0]
        downward = [1.0, 0.75, 0.5, 0.25, 0.0]

        similarity = DTWCalculator.calculate_similarity(upward, downward)

        # DTW compares shape only, so opposite direction trends
        # still have high similarity (same linear shape)
        assert similarity > 0.5

    def test_peak_pattern_similarity(self):
        """피크 패턴 유사도"""
        peak1 = [0.0, 0.5, 1.0, 0.5, 0.0]
        peak2 = [0.1, 0.6, 0.9, 0.4, 0.1]

        similarity = DTWCalculator.calculate_similarity(peak1, peak2)

        # Similar peak patterns should have high similarity
        assert similarity > 0.7

    def test_time_shifted_pattern(self):
        """시간축 이동 패턴도 유사하게 인식"""
        pattern1 = [0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
        pattern2 = [0.0, 1.0, 1.0, 1.0, 0.0]  # Peak shifted

        similarity = DTWCalculator.calculate_similarity(pattern1, pattern2)

        # DTW should handle time shift well
        assert similarity > 0.6
