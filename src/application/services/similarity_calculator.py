"""
Similarity Calculator

Seed pattern과 candidate pattern 간의 유사도를 계산
"""
from typing import List, Dict, Any, Literal
from dataclasses import dataclass

from src.domain.entities.patterns import SeedPattern, RedetectionConfig
from src.domain.entities.detections import DynamicBlockDetection
from src.application.services.dtw_calculator import DTWCalculator

SimilarityMethod = Literal["range", "dtw"]


@dataclass
class SimilarityScore:
    """
    유사도 점수

    각 요소별 점수와 최종 weighted score
    """
    price_similarity: float      # 가격 유사도 [0~1]
    volume_similarity: float     # 거래량 유사도 [0~1]
    timing_similarity: float     # 타이밍 유사도 [0~1]
    total_score: float           # 최종 점수 [0~1]

    def __repr__(self) -> str:
        return (
            f"SimilarityScore(price={self.price_similarity:.3f}, "
            f"volume={self.volume_similarity:.3f}, "
            f"timing={self.timing_similarity:.3f}, "
            f"total={self.total_score:.3f})"
        )


class SimilarityCalculator:
    """
    Seed pattern과 candidate pattern 간 유사도 계산

    Version 1: Range-based similarity (간단한 범위 기반)
    Version 2 (Day 4): DTW-based similarity (고급 shape matching)
    """

    def __init__(self, config: RedetectionConfig, method: SimilarityMethod = "range"):
        """
        Args:
            config: Redetection 설정
            method: Similarity 계산 방법 ("range" or "dtw")
        """
        self.config = config
        self.method = method
        self.dtw_calculator = DTWCalculator() if method == "dtw" else None

    def calculate(
        self,
        seed_pattern: SeedPattern,
        candidate_blocks: List[DynamicBlockDetection]
    ) -> SimilarityScore:
        """
        유사도 계산

        Args:
            seed_pattern: Seed pattern
            candidate_blocks: Candidate detections

        Returns:
            SimilarityScore
        """
        # 각 요소별 유사도 계산 (method에 따라 다른 알고리즘)
        if self.method == "dtw":
            price_sim = self._calculate_price_similarity_dtw(seed_pattern, candidate_blocks)
            volume_sim = self._calculate_volume_similarity_dtw(seed_pattern, candidate_blocks)
            timing_sim = self._calculate_timing_similarity(seed_pattern, candidate_blocks)
        else:  # range
            price_sim = self._calculate_price_similarity(seed_pattern, candidate_blocks)
            volume_sim = self._calculate_volume_similarity(seed_pattern, candidate_blocks)
            timing_sim = self._calculate_timing_similarity(seed_pattern, candidate_blocks)

        # Weighted total score
        weights = self.config.matching_weights
        total_score = (
            price_sim * weights.price_shape +
            volume_sim * weights.volume_shape +
            timing_sim * weights.timing
        )

        return SimilarityScore(
            price_similarity=price_sim,
            volume_similarity=volume_sim,
            timing_similarity=timing_sim,
            total_score=total_score
        )

    def _calculate_price_similarity(
        self,
        seed_pattern: SeedPattern,
        candidate_blocks: List[DynamicBlockDetection]
    ) -> float:
        """
        가격 유사도 계산 (Version 1: Range-based)

        Seed pattern의 각 블록 peak_price와 candidate의 peak_price 비교
        Tolerance 범위 내에 있으면 높은 점수

        Returns:
            유사도 [0~1]
        """
        if not candidate_blocks:
            return 0.0

        similarities = []

        for candidate in candidate_blocks:
            # Seed pattern에서 같은 block_id 찾기
            seed_feature = seed_pattern.get_block_feature(candidate.block_id)
            if not seed_feature:
                continue

            # Seed peak price 기준 tolerance 범위
            seed_peak = seed_feature.peak_price
            tolerance = self.config.tolerance.price_range
            min_price, max_price = self.config.get_price_filter_range(seed_peak)

            # Candidate peak이 범위 내에 있는지 확인
            if candidate.peak_price is None:
                continue

            if min_price <= candidate.peak_price <= max_price:
                # 범위 내: 중심에 가까울수록 높은 점수
                center = seed_peak
                distance = abs(candidate.peak_price - center)
                max_distance = seed_peak * tolerance
                similarity = 1.0 - (distance / max_distance if max_distance > 0 else 0)
                similarities.append(max(0.0, similarity))
            else:
                # 범위 밖: 낮은 점수
                similarities.append(0.0)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _calculate_volume_similarity(
        self,
        seed_pattern: SeedPattern,
        candidate_blocks: List[DynamicBlockDetection]
    ) -> float:
        """
        거래량 유사도 계산 (Version 1: Range-based)

        Returns:
            유사도 [0~1]
        """
        if not candidate_blocks:
            return 0.0

        similarities = []

        for candidate in candidate_blocks:
            seed_feature = seed_pattern.get_block_feature(candidate.block_id)
            if not seed_feature:
                continue

            # Seed peak volume 기준 tolerance 범위
            seed_peak_volume = seed_feature.peak_volume
            tolerance = self.config.tolerance.volume_range
            min_volume, max_volume = self.config.get_volume_filter_range(seed_peak_volume)

            if candidate.peak_volume is None:
                continue

            if min_volume <= candidate.peak_volume <= max_volume:
                # 범위 내: 중심에 가까울수록 높은 점수
                center = seed_peak_volume
                distance = abs(candidate.peak_volume - center)
                max_distance = seed_peak_volume * tolerance
                similarity = 1.0 - (distance / max_distance if max_distance > 0 else 0)
                similarities.append(max(0.0, similarity))
            else:
                # 범위 밖: 낮은 점수
                similarities.append(0.0)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _calculate_timing_similarity(
        self,
        seed_pattern: SeedPattern,
        candidate_blocks: List[DynamicBlockDetection]
    ) -> float:
        """
        타이밍 유사도 계산 (Version 1: Duration-based)

        각 블록의 duration이 seed와 유사한지 확인

        Returns:
            유사도 [0~1]
        """
        if not candidate_blocks:
            return 0.0

        similarities = []

        for candidate in candidate_blocks:
            seed_feature = seed_pattern.get_block_feature(candidate.block_id)
            if not seed_feature:
                continue

            # Seed duration 기준 tolerance 범위
            seed_duration = seed_feature.duration_candles
            tolerance = self.config.tolerance.time_range
            min_candles, max_candles = self.config.get_time_filter_range(seed_duration)

            # Candidate duration 계산
            if candidate.started_at and candidate.ended_at:
                # 정확한 계산은 stock data 필요, 여기서는 날짜 차이로 근사
                candidate_duration = (candidate.ended_at - candidate.started_at).days
            elif candidate.started_at:
                # 아직 진행 중이면 최대값으로 가정
                candidate_duration = max_candles
            else:
                continue

            if min_candles <= candidate_duration <= max_candles:
                # 범위 내: 중심에 가까울수록 높은 점수
                center = seed_duration
                distance = abs(candidate_duration - center)
                max_distance = tolerance
                similarity = 1.0 - (distance / max_distance if max_distance > 0 else 0)
                similarities.append(max(0.0, similarity))
            else:
                # 범위 밖: 낮은 점수
                similarities.append(0.0)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def meets_threshold(self, score: SimilarityScore) -> bool:
        """
        유사도 임계값 충족 여부

        Args:
            score: Similarity score

        Returns:
            threshold 이상이면 True
        """
        return score.total_score >= self.config.min_similarity_score

    # ========== DTW-based Similarity (Version 2) ==========

    def _calculate_price_similarity_dtw(
        self,
        seed_pattern: SeedPattern,
        candidate_blocks: List[DynamicBlockDetection]
    ) -> float:
        """
        DTW 기반 가격 유사도 계산

        Seed pattern의 price_shape와 candidate의 price sequence를
        DTW로 비교하여 shape matching 수행

        Returns:
            유사도 [0~1]
        """
        if not candidate_blocks:
            return 0.0

        # Seed pattern의 normalized price shape
        seed_price_shape = seed_pattern.price_shape
        if not seed_price_shape:
            return 0.0

        # Candidate의 price sequence 생성 및 normalize
        candidate_prices = [block.peak_price for block in candidate_blocks if block.peak_price is not None]
        if not candidate_prices:
            return 0.0

        # Normalize candidate prices to [0, 1]
        candidate_price_shape = SeedPattern.normalize_sequence(candidate_prices)

        # DTW similarity 계산
        similarity = self.dtw_calculator.constrained_dtw(
            seed_price_shape,
            candidate_price_shape,
            max_length_diff_ratio=0.5  # 길이 차이 50%까지 허용
        )

        return similarity

    def _calculate_volume_similarity_dtw(
        self,
        seed_pattern: SeedPattern,
        candidate_blocks: List[DynamicBlockDetection]
    ) -> float:
        """
        DTW 기반 거래량 유사도 계산

        Returns:
            유사도 [0~1]
        """
        if not candidate_blocks:
            return 0.0

        # Seed pattern의 normalized volume shape
        seed_volume_shape = seed_pattern.volume_shape
        if not seed_volume_shape:
            return 0.0

        # Candidate의 volume sequence 생성 및 normalize
        candidate_volumes = [block.peak_volume for block in candidate_blocks if block.peak_volume is not None]
        if not candidate_volumes:
            return 0.0

        # Normalize candidate volumes to [0, 1]
        candidate_volume_shape = SeedPattern.normalize_sequence([float(v) for v in candidate_volumes])

        # DTW similarity 계산
        similarity = self.dtw_calculator.constrained_dtw(
            seed_volume_shape,
            candidate_volume_shape,
            max_length_diff_ratio=0.5
        )

        return similarity
