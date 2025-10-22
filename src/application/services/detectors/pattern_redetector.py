"""
Pattern Redetector Service

Block1/2/3/4 재탐지 서비스
가격 범위 필터 + 완화된 조건 적용
"""
from typing import List, Optional
from datetime import date

from src.domain.entities import (
    BaseEntryCondition,
    RedetectionCondition,
    Stock,
    Block1Detection,
    Block2Detection,
    Block3Detection,
    Block4Detection,
)
from src.application.services.checkers.block1_checker import Block1Checker
from src.application.services.checkers.block2_checker import Block2Checker
from src.application.services.checkers.block3_checker import Block3Checker
from src.application.services.checkers.block4_checker import Block4Checker

class PatternRedetector:
    """
    패턴 재탐지 서비스

    5년 재탐지를 위한 완화된 조건 + 가격 범위 필터 적용
    - Block1 재탐지: seed_peak ± tolerance
    - Block2 재탐지: seed_peak ± tolerance + low > block1_seed
    - Block3 재탐지: seed_peak ± tolerance + low > block2_seed
    - Block4 재탐지: seed_peak ± tolerance + low > block3_seed
    - Cooldown: 20일
    """

    def __init__(self):
        self.block1_checker = Block1Checker()
        self.block2_checker = Block2Checker()
        self.block3_checker = Block3Checker()
        self.block4_checker = Block4Checker()

    def _create_base_for_block(
        self,
        condition: RedetectionCondition,
        block_num: int
    ) -> BaseEntryCondition:
        """
        BlockN용 BaseEntryCondition 생성

        YAML에서 모든 Block(1/2/3/4)의 모든 필드를 명시적으로 설정하므로
        fallback 로직을 사용하지 않고 BlockN의 값을 그대로 사용합니다.

        예: Block3.entry_volume_high_months = null → None으로 설정 (조건 비활성화)
            이전 로직은 null을 "미설정"으로 간주하여 Block1 값으로 fallback했음 (버그)

        Args:
            condition: 재탐지 조건
            block_num: 블록 번호 (2, 3, 4)

        Returns:
            BaseEntryCondition 객체
        """
        # Block2/3/4 전용 파라미터 속성 이름
        prefix = f"block{block_num}_"

        return BaseEntryCondition(
            block1_entry_surge_rate=getattr(condition, f"{prefix}entry_surge_rate"),
            block1_entry_ma_period=getattr(condition, f"{prefix}entry_ma_period"),
            block1_entry_max_deviation_ratio=getattr(condition, f"{prefix}entry_max_deviation_ratio"),
            block1_entry_min_trading_value=getattr(condition, f"{prefix}entry_min_trading_value"),
            block1_entry_volume_high_days=getattr(condition, f"{prefix}entry_volume_high_days"),
            block1_entry_volume_spike_ratio=getattr(condition, f"{prefix}entry_volume_spike_ratio"),
            block1_entry_price_high_days=getattr(condition, f"{prefix}entry_price_high_days"),
            block1_exit_condition_type=getattr(condition, f"{prefix}exit_condition_type"),
            block1_exit_ma_period=getattr(condition, f"{prefix}exit_ma_period"),
            block1_cooldown_days=getattr(condition, f"{prefix}cooldown_days")
        )

    def redetect_block1(
        self,
        stocks: List[Stock],
        seed_block1: Block1Detection,
        condition: RedetectionCondition,
        pattern_id: int,
        redetection_start: date,
        redetection_end: date
    ) -> List[Block1Detection]:
        """
        Block1 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block1: Block1 Seed (기준점)
            condition: 재탐지 조건
            pattern_id: 패턴 ID
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block1 재탐지 리스트
        """
        from src.domain.entities.conditions.block_conditions import Block1Condition

        # RedetectionCondition을 Block1Condition으로 변환
        block1_condition = Block1Condition(
            base=condition.base  # BaseEntryCondition을 그대로 사용
        )

        # 가격 범위 계산
        tolerance = condition.block1_tolerance_pct / 100.0  # 10% -> 0.1
        price_min = seed_block1.peak_price * (1 - tolerance)
        price_max = seed_block1.peak_price * (1 + tolerance)

        # 재탐지 기간 내 데이터만 필터링
        stocks_in_period = [
            s for s in stocks
            if redetection_start <= s.date <= redetection_end
        ]

        redetections = []
        last_redetection_date = None

        for i, stock in enumerate(stocks_in_period):
            # 가격 범위 체크
            if not (price_min <= stock.high <= price_max):
                continue

            # Cooldown 체크
            if last_redetection_date:
                days_diff = (stock.date - last_redetection_date).days
                if days_diff < condition.base.block1_cooldown_days:
                    continue

            # Block1 기본 조건 체크
            if self.block1_checker.check_entry(
                condition=block1_condition,
                stock=stock,
                all_stocks=stocks
            ):
                # Block1 재탐지 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block1 = Block1Detection(
                    block1_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_open=stock.open,
                    entry_high=stock.high,
                    entry_low=stock.low,
                    entry_close=stock.close,
                    entry_volume=stock.volume,
                    entry_trading_value=stock.close * stock.volume / 100_000_000,
                    entry_rate=indicators.get('rate'),
                    peak_price=stock.high,
                    peak_date=stock.date,
                    peak_volume=stock.volume,  # 진입일 거래량으로 초기화
                    condition_name="redetection",
                    pattern_id=pattern_id
                )

                redetections.append(block1)
                last_redetection_date = stock.date

        return redetections

    def redetect_block2(
        self,
        stocks: List[Stock],
        seed_block1: Block1Detection,
        seed_block2: Block2Detection,
        condition: RedetectionCondition,
        pattern_id: int,
        redetection_start: date,
        redetection_end: date
    ) -> List[Block2Detection]:
        """
        Block2 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block1: Block1 Seed (저가 마진 체크용)
            seed_block2: Block2 Seed (가격 범위 기준)
            pattern_id: 패턴 ID
            condition: 재탐지 조건
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block2 재탐지 리스트
        """
        from src.domain.entities.conditions.block_conditions import Block2Condition

        # Block2Condition 생성 (Block1 조건 + Block2 조건)
        # Block2 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback
        block2_condition = Block2Condition(
            base=self._create_base_for_block(condition, 2),
            # Block2 추가 조건 (2개 필드)
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin
        )

        # 가격 범위 계산 (Block2 Seed 기준)
        tolerance = condition.block2_tolerance_pct / 100.0  # 15% -> 0.15
        price_min = seed_block2.peak_price * (1 - tolerance)
        price_max = seed_block2.peak_price * (1 + tolerance)

        # 재탐지 기간 내 데이터만 필터링
        stocks_in_period = [
            s for s in stocks
            if redetection_start <= s.date <= redetection_end
        ]

        redetections = []
        last_redetection_date = None

        for i, stock in enumerate(stocks_in_period):
            # 가격 범위 체크 (Block2 Seed 기준)
            if not (price_min <= stock.high <= price_max):
                continue

            # 저가 마진 체크 (Block1 Seed 기준)
            low_margin = condition.block2_low_price_margin / 100.0  # 10% -> 0.1
            if stock.low * (1 + low_margin) <= seed_block1.peak_price:
                continue

            # Cooldown 체크
            if last_redetection_date:
                days_diff = (stock.date - last_redetection_date).days
                if days_diff < condition.base.block1_cooldown_days:
                    continue

            # Block2 기본 조건 체크
            if self.block2_checker.check_entry(
                condition=block2_condition,
                stock=stock,
                all_stocks=stocks,
                prev_seed_block1=seed_block1
            ):
                # Block2 재탐지 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block2 = Block2Detection(
                    block2_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=indicators.get('rate'),
                    prev_block_id=seed_block1.block1_id,
                    prev_block_peak_price=seed_block1.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    peak_volume=stock.volume,  # 진입일 거래량으로 초기화
                    condition_name="redetection",
                    pattern_id=pattern_id
                )

                redetections.append(block2)
                last_redetection_date = stock.date

        return redetections

    def redetect_block3(
        self,
        stocks: List[Stock],
        seed_block1: Block1Detection,
        seed_block2: Block2Detection,
        seed_block3: Block3Detection,
        condition: RedetectionCondition,
        pattern_id: int,
        redetection_start: date,
        redetection_end: date
    ) -> List[Block3Detection]:
        """
        Block3 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block1: Block1 Seed (Block2 조건 체크용 - volume_ratio)
            seed_block2: Block2 Seed (저가 마진 체크용)
            seed_block3: Block3 Seed (가격 범위 기준)
            condition: 재탐지 조건
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block3 재탐지 리스트
        """
        from src.domain.entities.conditions.block_conditions import Block3Condition

        # Block3Condition 생성 (Block1 + Block2 + Block3 조건)
        # Block3 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback
        block3_condition = Block3Condition(
            base=self._create_base_for_block(condition, 3),
            # Block2 추가 조건 (2개 필드)
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            # Block3 추가 조건 (2개 필드)
            block3_volume_ratio=condition.block3_volume_ratio,
            block3_low_price_margin=condition.block3_low_price_margin
        )

        # 가격 범위 계산 (Block3 Seed 기준)
        tolerance = condition.block3_tolerance_pct / 100.0  # 20% -> 0.2
        price_min = seed_block3.peak_price * (1 - tolerance)
        price_max = seed_block3.peak_price * (1 + tolerance)

        # 재탐지 기간 내 데이터만 필터링
        stocks_in_period = [
            s for s in stocks
            if redetection_start <= s.date <= redetection_end
        ]

        redetections = []
        last_redetection_date = None

        for i, stock in enumerate(stocks_in_period):
            # 가격 범위 체크 (Block3 Seed 기준)
            if not (price_min <= stock.high <= price_max):
                continue

            # 저가 마진 체크 (Block2 Seed 기준)
            low_margin = condition.block3_low_price_margin / 100.0  # 10% -> 0.1
            if stock.low * (1 + low_margin) <= seed_block2.peak_price:
                continue

            # Cooldown 체크
            if last_redetection_date:
                days_diff = (stock.date - last_redetection_date).days
                if days_diff < condition.base.block1_cooldown_days:
                    continue

            # Block3 기본 조건 체크
            if self.block3_checker.check_entry(
                condition=block3_condition,
                stock=stock,
                all_stocks=stocks,
                prev_seed_block1=seed_block1,  # Block2 조건용 (volume_ratio 체크)
                prev_seed_block2=seed_block2   # Block3 조건용 (저가 마진 체크)
            ):
                # Block3 재탐지 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block3 = Block3Detection(
                    block3_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=indicators.get('rate'),
                    prev_block_id=seed_block2.block2_id,
                    prev_block_peak_price=seed_block2.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    peak_volume=stock.volume,  # 진입일 거래량으로 초기화
                    condition_name="redetection",
                    pattern_id=pattern_id
                )

                redetections.append(block3)
                last_redetection_date = stock.date

        return redetections

    def redetect_block4(
        self,
        stocks: List[Stock],
        seed_block1: Block1Detection,
        seed_block2: Block2Detection,
        seed_block3: Block3Detection,
        seed_block4: Block4Detection,
        condition: RedetectionCondition,
        pattern_id: int,
        redetection_start: date,
        redetection_end: date
    ) -> List[Block4Detection]:
        """
        Block4 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block1: Block1 Seed (Block2 조건 체크용 - volume_ratio)
            seed_block2: Block2 Seed (Block3 조건 체크용 - volume_ratio)
            seed_block3: Block3 Seed (저가 마진 체크용)
            seed_block4: Block4 Seed (가격 범위 기준)
            condition: 재탐지 조건
            pattern_id: 패턴 ID
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block4 재탐지 리스트
        """
        from src.domain.entities.conditions.block_conditions import Block4Condition

        # Block4Condition 생성 (Block1 + Block2 + Block3 + Block4 조건)
        # Block4 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback
        block4_condition = Block4Condition(
            base=self._create_base_for_block(condition, 4),
            # Block2 추가 조건 (2개 필드)
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            # Block3 추가 조건 (2개 필드)
            block3_volume_ratio=condition.block3_volume_ratio,
            block3_low_price_margin=condition.block3_low_price_margin,
            # Block4 추가 조건 (2개 필드)
            block4_volume_ratio=condition.block4_volume_ratio,
            block4_low_price_margin=condition.block4_low_price_margin
        )

        # 가격 범위 계산 (Block4 Seed 기준)
        tolerance = condition.block4_tolerance_pct / 100.0  # 25% -> 0.25
        price_min = seed_block4.peak_price * (1 - tolerance)
        price_max = seed_block4.peak_price * (1 + tolerance)

        # 재탐지 기간 내 데이터만 필터링
        stocks_in_period = [
            s for s in stocks
            if redetection_start <= s.date <= redetection_end
        ]

        redetections = []
        last_redetection_date = None

        for i, stock in enumerate(stocks_in_period):
            # 가격 범위 체크 (Block4 Seed 기준)
            if not (price_min <= stock.high <= price_max):
                continue

            # 저가 마진 체크 (Block3 Seed 기준)
            low_margin = condition.block4_low_price_margin / 100.0  # 10% -> 0.1
            if stock.low * (1 + low_margin) <= seed_block3.peak_price:
                continue

            # Cooldown 체크
            if last_redetection_date:
                days_diff = (stock.date - last_redetection_date).days
                if days_diff < condition.base.block1_cooldown_days:
                    continue

            # Block4 기본 조건 체크
            if self.block4_checker.check_entry(
                condition=block4_condition,
                stock=stock,
                all_stocks=stocks,
                prev_seed_block1=seed_block1,  # Block2 조건용 (volume_ratio 체크)
                prev_seed_block2=seed_block2,  # Block3 조건용 (volume_ratio 체크)
                prev_seed_block3=seed_block3   # Block4 조건용 (저가 마진 체크)
            ):
                # Block4 재탐지 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block4 = Block4Detection(
                    block4_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=indicators.get('rate'),
                    prev_block_id=seed_block3.block3_id,
                    prev_block_peak_price=seed_block3.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    peak_volume=stock.volume,  # 진입일 거래량으로 초기화
                    condition_name="redetection",
                    pattern_id=pattern_id
                )

                redetections.append(block4)
                last_redetection_date = stock.date

        return redetections
