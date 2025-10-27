"""
SupportResistanceAnalyzer - Support/Resistance 분석 Application Service

Block1 range를 기준으로 support/resistance 분석을 수행하는 재사용 가능한 서비스.
Sequential 및 Highlight-Centric 시스템 모두에서 사용.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import date

from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.core import Stock
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SupportResistanceLevel:
    """
    Support/Resistance 레벨 Value Object

    Block1 range를 기준으로 현재 가격 위치를 분류.

    Attributes:
        level_type: "strong_support", "weak_support", "broken"
        reference_block: Block1 (기준 블록)
        reference_high: Block1.peak_price (강한 저항/지지)
        reference_low: Block1 최저가 (약한 지지)
        current_price: 현재 가격
        distance_pct: 기준가 대비 거리 (%)
        analysis_date: 분석 날짜
    """
    level_type: str  # "strong_support", "weak_support", "broken"
    reference_block: DynamicBlockDetection
    reference_high: float
    reference_low: float
    current_price: float
    distance_pct: float
    analysis_date: date

    def is_strong_support(self) -> bool:
        """강한 지지 (Block1.high 위)"""
        return self.level_type == "strong_support"

    def is_weak_support(self) -> bool:
        """약한 지지 (Block1 range 내)"""
        return self.level_type == "weak_support"

    def is_broken(self) -> bool:
        """지지 이탈 (Block1.low 아래)"""
        return self.level_type == "broken"


@dataclass
class SupportResistanceAnalysis:
    """
    Complete Support/Resistance 분석 결과

    Attributes:
        reference_block: Block1 (기준 블록)
        forward_blocks: 분석 대상 블록 리스트
        levels: 각 시점별 support/resistance 레벨
        retest_events: 재시험 이벤트 (Block1.high 근처로 복귀)
        resistance_to_support_flips: 저항에서 지지로 전환된 이벤트
        metadata: 추가 메타데이터
    """
    reference_block: DynamicBlockDetection
    forward_blocks: List[DynamicBlockDetection]
    levels: List[SupportResistanceLevel] = field(default_factory=list)
    retest_events: List[Dict[str, Any]] = field(default_factory=list)
    resistance_to_support_flips: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_summary(self) -> Dict[str, Any]:
        """분석 요약 반환"""
        strong_support_count = sum(1 for lvl in self.levels if lvl.is_strong_support())
        weak_support_count = sum(1 for lvl in self.levels if lvl.is_weak_support())
        broken_count = sum(1 for lvl in self.levels if lvl.is_broken())

        return {
            'reference_block_id': self.reference_block.block_id,
            'reference_high': self.reference_block.peak_price,
            'num_forward_blocks': len(self.forward_blocks),
            'num_levels_analyzed': len(self.levels),
            'strong_support_count': strong_support_count,
            'weak_support_count': weak_support_count,
            'broken_count': broken_count,
            'num_retest_events': len(self.retest_events),
            'num_flips': len(self.resistance_to_support_flips),
            'metadata': self.metadata
        }


class SupportResistanceAnalyzer:
    """
    Support/Resistance 분석 Application Service

    Block1 range를 기준으로 이후 가격 움직임을 분석:
    - Strong support: 가격이 Block1.high 위에서 유지
    - Weak support: 가격이 Block1 range 내에서 유지
    - Broken support: 가격이 Block1.low 아래로 하락

    이 서비스는 Application Layer의 재사용 가능한 모듈로,
    여러 Use Case에서 공유됨 (Clean Architecture 원칙 준수).

    Example:
        >>> analyzer = SupportResistanceAnalyzer()
        >>> analysis = analyzer.analyze(
        ...     reference_block=block1,
        ...     forward_blocks=[block2, block3],
        ...     all_stocks=stocks,
        ...     analysis_period_days=1125
        ... )
        >>> summary = analysis.get_summary()
    """

    def __init__(self, tolerance_pct: float = 2.0):
        """
        Args:
            tolerance_pct: 지지/저항 판정 허용 오차 (기본 2%)
                예: Block1.high가 10000원이면 9800~10200원 범위를 "근처"로 인정
        """
        self.tolerance_pct = tolerance_pct
        logger.debug(f"SupportResistanceAnalyzer initialized with tolerance={tolerance_pct}%")

    def analyze(
        self,
        reference_block: DynamicBlockDetection,
        forward_blocks: List[DynamicBlockDetection],
        all_stocks: List[Stock],
        analysis_period_days: int = 1125
    ) -> SupportResistanceAnalysis:
        """
        Complete support/resistance 분석 수행

        Args:
            reference_block: Block1 (기준 블록)
            forward_blocks: 분석 대상 블록 리스트 (Block2, Block3, ...)
            all_stocks: 전체 주가 데이터 (일별)
            analysis_period_days: 분석 기간 (일수, 기본 1125일 = 4.5년)

        Returns:
            SupportResistanceAnalysis 결과

        Example:
            >>> analysis = analyzer.analyze(block1, [block2], stocks, 1125)
            >>> print(analysis.get_summary())
        """
        logger.info(
            f"Starting support/resistance analysis",
            context={
                'reference_block': reference_block.block_id,
                'num_forward_blocks': len(forward_blocks),
                'analysis_period_days': analysis_period_days
            }
        )

        # Block1 range 추출
        reference_high = reference_block.peak_price
        reference_low = self._get_lowest_price(reference_block, all_stocks)

        if reference_high is None or reference_low is None:
            logger.warning("Cannot analyze: reference_high or reference_low is None")
            return SupportResistanceAnalysis(
                reference_block=reference_block,
                forward_blocks=forward_blocks,
                metadata={'error': 'Missing reference prices'}
            )

        logger.debug(
            f"Reference range",
            context={
                'reference_high': reference_high,
                'reference_low': reference_low,
                'range_pct': ((reference_high - reference_low) / reference_low * 100)
            }
        )

        # 각 forward block에 대한 레벨 분석
        levels = []
        for block in forward_blocks:
            if block.peak_price:
                level = self._classify_level(
                    current_price=block.peak_price,
                    reference_high=reference_high,
                    reference_low=reference_low,
                    reference_block=reference_block,
                    analysis_date=block.started_at or date.today()
                )
                levels.append(level)

        # 재시험 이벤트 탐지
        retest_events = self._detect_retest_events(
            forward_blocks=forward_blocks,
            reference_high=reference_high,
            all_stocks=all_stocks
        )

        # 저항→지지 전환 이벤트 탐지
        flips = self._detect_resistance_to_support_flips(
            forward_blocks=forward_blocks,
            reference_high=reference_high,
            all_stocks=all_stocks
        )

        analysis = SupportResistanceAnalysis(
            reference_block=reference_block,
            forward_blocks=forward_blocks,
            levels=levels,
            retest_events=retest_events,
            resistance_to_support_flips=flips,
            metadata={
                'reference_high': reference_high,
                'reference_low': reference_low,
                'tolerance_pct': self.tolerance_pct,
                'analysis_period_days': analysis_period_days
            }
        )

        logger.info(
            f"Analysis complete",
            context=analysis.get_summary()
        )

        return analysis

    def _classify_level(
        self,
        current_price: float,
        reference_high: float,
        reference_low: float,
        reference_block: DynamicBlockDetection,
        analysis_date: date
    ) -> SupportResistanceLevel:
        """
        현재 가격을 support/resistance 레벨로 분류 (내부 메서드)

        Args:
            current_price: 현재 가격
            reference_high: Block1.peak_price
            reference_low: Block1 최저가
            reference_block: Block1
            analysis_date: 분석 날짜

        Returns:
            SupportResistanceLevel
        """
        # Strong support: Block1.high 위
        if current_price >= reference_high:
            level_type = "strong_support"
            distance_pct = (current_price - reference_high) / reference_high * 100

        # Weak support: Block1 range 내
        elif current_price >= reference_low:
            level_type = "weak_support"
            distance_pct = (current_price - reference_low) / reference_low * 100

        # Broken: Block1.low 아래
        else:
            level_type = "broken"
            distance_pct = (current_price - reference_low) / reference_low * 100

        return SupportResistanceLevel(
            level_type=level_type,
            reference_block=reference_block,
            reference_high=reference_high,
            reference_low=reference_low,
            current_price=current_price,
            distance_pct=distance_pct,
            analysis_date=analysis_date
        )

    def _get_lowest_price(
        self,
        block: DynamicBlockDetection,
        all_stocks: List[Stock]
    ) -> Optional[float]:
        """
        블록 기간 내 최저가 조회 (내부 메서드)

        Args:
            block: 블록
            all_stocks: 전체 주가 데이터

        Returns:
            최저가 (없으면 None)
        """
        if not block.started_at or not block.ended_at:
            return None

        # 블록 기간 내 주가 필터링
        period_stocks = [
            stock for stock in all_stocks
            if block.started_at <= stock.date <= block.ended_at
        ]

        if not period_stocks:
            return None

        # 최저가 반환
        lowest = min(period_stocks, key=lambda s: s.low)
        return lowest.low

    def _detect_retest_events(
        self,
        forward_blocks: List[DynamicBlockDetection],
        reference_high: float,
        all_stocks: List[Stock]
    ) -> List[Dict[str, Any]]:
        """
        재시험 이벤트 탐지 (내부 메서드)

        Block1.high 근처로 가격이 복귀한 이벤트 감지.

        Args:
            forward_blocks: Forward blocks
            reference_high: Block1.peak_price
            all_stocks: 전체 주가 데이터

        Returns:
            재시험 이벤트 리스트
        """
        retest_events = []

        for block in forward_blocks:
            if not block.started_at or not block.ended_at:
                continue

            # 블록 기간 내 주가 데이터
            period_stocks = [
                stock for stock in all_stocks
                if block.started_at <= stock.date <= block.ended_at
            ]

            for stock in period_stocks:
                # Block1.high ± tolerance 범위로 복귀한 경우
                tolerance = reference_high * (self.tolerance_pct / 100)
                if abs(stock.high - reference_high) <= tolerance:
                    retest_events.append({
                        'date': stock.date,
                        'price': stock.high,
                        'reference_high': reference_high,
                        'distance_pct': (stock.high - reference_high) / reference_high * 100,
                        'block_id': block.block_id
                    })

        logger.debug(
            f"Detected {len(retest_events)} retest events",
            context={'num_events': len(retest_events)}
        )

        return retest_events

    def _detect_resistance_to_support_flips(
        self,
        forward_blocks: List[DynamicBlockDetection],
        reference_high: float,
        all_stocks: List[Stock]
    ) -> List[Dict[str, Any]]:
        """
        저항→지지 전환 이벤트 탐지 (내부 메서드)

        Block1.high를 돌파 후 지지로 전환된 경우 감지.

        Args:
            forward_blocks: Forward blocks
            reference_high: Block1.peak_price
            all_stocks: 전체 주가 데이터

        Returns:
            전환 이벤트 리스트
        """
        flips = []

        # 각 forward block 검사
        for i, block in enumerate(forward_blocks):
            if not block.peak_price or block.peak_price <= reference_high:
                continue  # Block1.high 돌파하지 못함

            # Block1.high 돌파 후, 이후 블록이 Block1.high 위에서 지지받는지 확인
            if i + 1 < len(forward_blocks):
                next_block = forward_blocks[i + 1]
                if next_block.started_at:
                    # 이후 블록 기간 내 주가 데이터
                    period_stocks = [
                        stock for stock in all_stocks
                        if next_block.started_at <= stock.date <= (next_block.ended_at or date.today())
                    ]

                    # Block1.high 위에서 지지받는지 확인
                    for stock in period_stocks:
                        tolerance = reference_high * (self.tolerance_pct / 100)
                        # 저가가 Block1.high ± tolerance 범위에서 지지
                        if abs(stock.low - reference_high) <= tolerance:
                            flips.append({
                                'breakout_block_id': block.block_id,
                                'breakout_price': block.peak_price,
                                'support_date': stock.date,
                                'support_price': stock.low,
                                'reference_high': reference_high,
                                'flip_confirmed': True
                            })
                            break  # 첫 번째 이벤트만 기록

        logger.debug(
            f"Detected {len(flips)} resistance-to-support flips",
            context={'num_flips': len(flips)}
        )

        return flips

    def is_strong_support(
        self,
        current_price: float,
        reference_high: float
    ) -> bool:
        """
        현재 가격이 강한 지지 영역인지 확인 (편의 메서드)

        Args:
            current_price: 현재 가격
            reference_high: Block1.peak_price

        Returns:
            강한 지지 영역이면 True

        Example:
            >>> analyzer.is_strong_support(12000, 10000)
            True
        """
        return current_price >= reference_high

    def is_weak_support(
        self,
        current_price: float,
        reference_high: float,
        reference_low: float
    ) -> bool:
        """
        현재 가격이 약한 지지 영역인지 확인 (편의 메서드)

        Args:
            current_price: 현재 가격
            reference_high: Block1.peak_price
            reference_low: Block1 최저가

        Returns:
            약한 지지 영역이면 True

        Example:
            >>> analyzer.is_weak_support(9500, 10000, 9000)
            True
        """
        return reference_low <= current_price < reference_high

    def is_broken(
        self,
        current_price: float,
        reference_low: float
    ) -> bool:
        """
        현재 가격이 지지 이탈 상태인지 확인 (편의 메서드)

        Args:
            current_price: 현재 가격
            reference_low: Block1 최저가

        Returns:
            지지 이탈 상태면 True

        Example:
            >>> analyzer.is_broken(8500, 9000)
            True
        """
        return current_price < reference_low
