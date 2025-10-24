"""
Dynamic Pattern Redetector Use Case

Seed pattern을 기반으로 유사한 historical patterns를 재탐지
"""
from typing import List, Optional, Dict, Any
from datetime import date, timedelta

from src.domain.entities.patterns import SeedPattern
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.block_graph import BlockGraph
from src.domain.entities.conditions import ExpressionEngine
from src.domain.entities.core import Stock
from src.application.services.similarity_calculator import SimilarityCalculator, SimilarityScore


class DynamicPatternRedetector:
    """
    Dynamic Pattern Redetector

    Seed pattern을 기반으로 유사한 패턴을 재탐지하는 use case
    """

    def __init__(
        self,
        redetection_graph: BlockGraph,
        expression_engine: ExpressionEngine
    ):
        """
        Args:
            redetection_graph: Redetection BlockGraph (pattern_type="redetection")
            expression_engine: Expression engine
        """
        if redetection_graph.pattern_type != 'redetection':
            raise ValueError("BlockGraph must have pattern_type='redetection'")

        if not redetection_graph.redetection_config:
            raise ValueError("BlockGraph must have redetection_config")

        self.redetection_graph = redetection_graph
        self.expression_engine = expression_engine
        self.redetection_config = redetection_graph.redetection_config
        self.similarity_calculator = SimilarityCalculator(self.redetection_config)

    def redetect_patterns(
        self,
        seed_pattern: SeedPattern,
        ticker: str,
        stocks: List[Stock],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DynamicBlockDetection]:
        """
        유사 패턴 재탐지

        Args:
            seed_pattern: Seed pattern (참조 패턴)
            ticker: 종목 코드
            stocks: Stock data (historical)
            start_date: 시작 날짜 (None이면 전체)
            end_date: 종료 날짜 (None이면 전체)

        Returns:
            재탐지된 DynamicBlockDetection 리스트 (similarity score 포함)
        """
        # 날짜 필터링
        if start_date or end_date:
            stocks = self._filter_by_date_range(stocks, start_date, end_date)

        if not stocks:
            return []

        # Seed context 구축
        seed_context = self._build_seed_context(seed_pattern)

        # Detection 수행 (DynamicBlockDetector 로직 재사용)
        detections = self._detect_blocks_with_seed_context(
            ticker=ticker,
            stocks=stocks,
            seed_context=seed_context
        )

        # Cooldown 적용
        detections = self._apply_cooldown_filter(detections)

        # Similarity score 계산 및 필터링
        redetections = []
        for detection_group in self._group_by_pattern(detections):
            similarity_score = self.similarity_calculator.calculate(
                seed_pattern,
                detection_group
            )

            # Threshold 체크
            if self.similarity_calculator.meets_threshold(similarity_score):
                # Similarity score를 metadata에 추가
                for detection in detection_group:
                    detection.metadata['similarity_score'] = similarity_score.total_score
                    detection.metadata['price_similarity'] = similarity_score.price_similarity
                    detection.metadata['volume_similarity'] = similarity_score.volume_similarity
                    detection.metadata['timing_similarity'] = similarity_score.timing_similarity
                    detection.metadata['seed_pattern_id'] = seed_pattern.id
                    detection.metadata['seed_pattern_name'] = seed_pattern.pattern_name

                redetections.extend(detection_group)

        return redetections

    def _filter_by_date_range(
        self,
        stocks: List[Stock],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[Stock]:
        """날짜 범위 필터링"""
        filtered = stocks

        if start_date:
            filtered = [s for s in filtered if s.date >= start_date]

        if end_date:
            filtered = [s for s in filtered if s.date <= end_date]

        return filtered

    def _build_seed_context(self, seed_pattern: SeedPattern) -> Dict[str, Any]:
        """
        Seed context 구축

        Expression에서 seed.block1.peak_price 등으로 접근 가능하도록
        seed 변수를 context에 추가

        Returns:
            {'block1': {...}, 'block2': {...}, ...}
        """
        seed_context = {}

        for feature in seed_pattern.block_features:
            # block_id를 키로 사용
            seed_context[feature.block_id] = {
                'block_type': feature.block_type,
                'started_at': feature.started_at,
                'ended_at': feature.ended_at,
                'duration': feature.duration_candles,
                'low': feature.low_price,
                'high': feature.high_price,
                'peak_price': feature.peak_price,
                'peak_date': feature.peak_date,
                'min_volume': feature.min_volume,
                'max_volume': feature.max_volume,
                'peak_volume': feature.peak_volume,
                'avg_volume': feature.avg_volume
            }

        return seed_context

    def _detect_blocks_with_seed_context(
        self,
        ticker: str,
        stocks: List[Stock],
        seed_context: Dict[str, Any]
    ) -> List[DynamicBlockDetection]:
        """
        Seed context와 함께 block detection 수행

        DynamicBlockDetector 로직을 재사용하되,
        context에 seed 정보를 추가
        """
        from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector

        # DynamicBlockDetector 생성
        detector = DynamicBlockDetector(self.redetection_graph, self.expression_engine)

        # Detection 수행
        # TODO: DynamicBlockDetector에 seed_context 전달 기능 추가 필요
        # 현재는 일반 detection 수행
        detections = detector.detect_blocks(
            ticker=ticker,
            stocks=stocks,
            condition_name='redetection'
        )

        # 임시: seed context를 metadata에 저장
        for detection in detections:
            detection.metadata['seed_context'] = seed_context

        return detections

    def _apply_cooldown_filter(
        self,
        detections: List[DynamicBlockDetection]
    ) -> List[DynamicBlockDetection]:
        """
        Cooldown 필터 적용

        연속된 detection 간 최소 간격 유지
        """
        if not detections:
            return []

        min_interval = self.redetection_config.min_detection_interval_days
        if min_interval <= 0:
            return detections

        # 시작 날짜로 정렬
        sorted_detections = sorted(
            detections,
            key=lambda d: d.started_at if d.started_at else date.min
        )

        filtered = []
        last_detection_date = None

        for detection in sorted_detections:
            if not detection.started_at:
                continue

            # 첫 detection 또는 충분한 간격이 있는 경우
            if last_detection_date is None or \
               (detection.started_at - last_detection_date).days >= min_interval:
                filtered.append(detection)
                last_detection_date = detection.started_at

        return filtered

    def _group_by_pattern(
        self,
        detections: List[DynamicBlockDetection]
    ) -> List[List[DynamicBlockDetection]]:
        """
        Detection을 pattern으로 그룹화

        연속된 block들을 하나의 pattern으로 묶음
        (Block1 → Block2 → Block3)

        Returns:
            Detection 그룹 리스트
        """
        if not detections:
            return []

        # 간단한 구현: 시작 날짜가 가까운 것들끼리 그룹화
        # TODO: 더 정교한 그룹화 로직 필요 (parent_blocks 활용)

        # 날짜로 정렬
        sorted_detections = sorted(
            detections,
            key=lambda d: (d.started_at if d.started_at else date.min, d.block_type)
        )

        groups = []
        current_group = []
        last_date = None

        for detection in sorted_detections:
            if not detection.started_at:
                continue

            # 새 그룹 시작 조건: 날짜 차이가 30일 이상
            if last_date and (detection.started_at - last_date).days > 30:
                if current_group:
                    groups.append(current_group)
                current_group = [detection]
            else:
                current_group.append(detection)

            last_date = detection.started_at

        # 마지막 그룹 추가
        if current_group:
            groups.append(current_group)

        return groups

    def get_redetection_summary(self, redetections: List[DynamicBlockDetection]) -> Dict[str, Any]:
        """
        재탐지 결과 요약

        Args:
            redetections: 재탐지 결과 리스트

        Returns:
            요약 정보
        """
        if not redetections:
            return {
                'total_count': 0,
                'avg_similarity': 0.0,
                'date_range': None
            }

        # Similarity scores 추출
        similarity_scores = [
            d.metadata.get('similarity_score', 0.0)
            for d in redetections
            if 'similarity_score' in d.metadata
        ]

        # 날짜 범위
        dates = [d.started_at for d in redetections if d.started_at]
        date_range = (min(dates), max(dates)) if dates else None

        return {
            'total_count': len(redetections),
            'avg_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
            'max_similarity': max(similarity_scores) if similarity_scores else 0.0,
            'min_similarity': min(similarity_scores) if similarity_scores else 0.0,
            'date_range': date_range,
            'block_types': list(set(d.block_type for d in redetections))
        }
