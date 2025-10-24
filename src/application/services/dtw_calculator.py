"""
DTW (Dynamic Time Warping) Calculator

시계열 데이터 간 최적 정렬 및 거리 계산
"""
from typing import List, Tuple
import numpy as np


class DTWCalculator:
    """
    Dynamic Time Warping 계산기

    두 시계열 데이터 간의 최적 정렬을 찾고 유사도를 계산합니다.
    """

    @staticmethod
    def calculate_distance(
        sequence1: List[float],
        sequence2: List[float],
        window: int = None
    ) -> float:
        """
        DTW distance 계산

        Args:
            sequence1: 첫 번째 시퀀스
            sequence2: 두 번째 시퀀스
            window: Sakoe-Chiba band width (None이면 제한 없음)

        Returns:
            DTW distance (0에 가까울수록 유사)
        """
        if not sequence1 or not sequence2:
            return float('inf')

        n, m = len(sequence1), len(sequence2)

        # DTW matrix 초기화
        dtw_matrix = np.full((n + 1, m + 1), float('inf'))
        dtw_matrix[0, 0] = 0

        # Window constraint 설정
        if window is None:
            window = max(n, m)

        # DTW 계산
        for i in range(1, n + 1):
            # Sakoe-Chiba band
            start_j = max(1, i - window)
            end_j = min(m, i + window)

            for j in range(start_j, end_j + 1):
                cost = abs(sequence1[i - 1] - sequence2[j - 1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i - 1, j],      # insertion
                    dtw_matrix[i, j - 1],      # deletion
                    dtw_matrix[i - 1, j - 1]   # match
                )

        return dtw_matrix[n, m]

    @staticmethod
    def calculate_similarity(
        sequence1: List[float],
        sequence2: List[float],
        window: int = None,
        normalize: bool = True
    ) -> float:
        """
        DTW 유사도 계산 (0~1 범위)

        Args:
            sequence1: 첫 번째 시퀀스
            sequence2: 두 번째 시퀀스
            window: Sakoe-Chiba band width
            normalize: 길이로 정규화 여부

        Returns:
            유사도 [0~1], 1이 가장 유사
        """
        distance = DTWCalculator.calculate_distance(sequence1, sequence2, window)

        if distance == float('inf'):
            return 0.0

        # 길이로 정규화
        if normalize:
            path_length = len(sequence1) + len(sequence2)
            normalized_distance = distance / path_length if path_length > 0 else distance
        else:
            normalized_distance = distance

        # Distance를 similarity로 변환 (exp decay)
        # distance가 0이면 similarity=1, 멀어질수록 0에 근접
        similarity = np.exp(-normalized_distance)

        return float(similarity)

    @staticmethod
    def get_warping_path(
        sequence1: List[float],
        sequence2: List[float],
        window: int = None
    ) -> List[Tuple[int, int]]:
        """
        DTW warping path 계산

        Args:
            sequence1: 첫 번째 시퀀스
            sequence2: 두 번째 시퀀스
            window: Sakoe-Chiba band width

        Returns:
            Warping path [(i, j), ...]
        """
        if not sequence1 or not sequence2:
            return []

        n, m = len(sequence1), len(sequence2)

        # DTW matrix 계산
        dtw_matrix = np.full((n + 1, m + 1), float('inf'))
        dtw_matrix[0, 0] = 0

        if window is None:
            window = max(n, m)

        for i in range(1, n + 1):
            start_j = max(1, i - window)
            end_j = min(m, i + window)

            for j in range(start_j, end_j + 1):
                cost = abs(sequence1[i - 1] - sequence2[j - 1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i - 1, j],
                    dtw_matrix[i, j - 1],
                    dtw_matrix[i - 1, j - 1]
                )

        # Backtracking
        path = []
        i, j = n, m

        while i > 0 or j > 0:
            path.append((i - 1, j - 1))

            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                # 최소값 방향으로 이동
                candidates = [
                    (dtw_matrix[i - 1, j], (i - 1, j)),      # up
                    (dtw_matrix[i, j - 1], (i, j - 1)),      # left
                    (dtw_matrix[i - 1, j - 1], (i - 1, j - 1))  # diagonal
                ]
                _, (i, j) = min(candidates)

        path.reverse()
        return path

    @staticmethod
    def constrained_dtw(
        sequence1: List[float],
        sequence2: List[float],
        max_length_diff_ratio: float = 0.3
    ) -> float:
        """
        길이 제약이 있는 DTW 유사도 계산

        두 시퀀스의 길이 차이가 너무 크면 0.0 반환

        Args:
            sequence1: 첫 번째 시퀀스
            sequence2: 두 번째 시퀀스
            max_length_diff_ratio: 최대 길이 차이 비율

        Returns:
            유사도 [0~1]
        """
        if not sequence1 or not sequence2:
            return 0.0

        len1, len2 = len(sequence1), len(sequence2)
        max_len = max(len1, len2)
        min_len = min(len1, len2)

        # 길이 차이가 너무 크면 0
        if max_len > 0 and (max_len - min_len) / max_len > max_length_diff_ratio:
            return 0.0

        # DTW similarity 계산
        return DTWCalculator.calculate_similarity(sequence1, sequence2)
