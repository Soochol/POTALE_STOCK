"""
Pattern Redetector Service

Block1/2/3 재탐지 서비스
가격 범위 필터 + 완화된 조건 적용
"""
from typing import List, Optional
from datetime import date
from src.domain.entities.stock import Stock
from src.domain.entities.redetection_condition import RedetectionCondition
from src.domain.entities.block1_detection import Block1Detection
from src.domain.entities.block2_detection import Block2Detection
from src.domain.entities.block3_detection import Block3Detection
from src.application.services.block1_checker import Block1Checker
from src.application.services.block2_checker import Block2Checker
from src.application.services.block3_checker import Block3Checker


class PatternRedetector:
    """
    패턴 재탐지 서비스

    5년 재탐지를 위한 완화된 조건 + 가격 범위 필터 적용
    - Block1 재탐지: seed_peak ± tolerance
    - Block2 재탐지: seed_peak ± tolerance + low > block1_seed
    - Block3 재탐지: seed_peak ± tolerance + low > block2_seed
    - Cooldown: 20일
    """

    def __init__(self):
        self.block1_checker = Block1Checker()
        self.block2_checker = Block2Checker()
        self.block3_checker = Block3Checker()

    def redetect_block1(
        self,
        stocks: List[Stock],
        seed_block1: Block1Detection,
        condition: RedetectionCondition,
        redetection_start: date,
        redetection_end: date
    ) -> List[Block1Detection]:
        """
        Block1 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block1: Block1 Seed (기준점)
            condition: 재탐지 조건
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block1 재탐지 리스트
        """
        from src.domain.entities.block1_condition import Block1Condition

        # RedetectionCondition을 Block1Condition으로 변환
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            high_above_ma=condition.high_above_ma,
            max_deviation_ratio=condition.max_deviation_ratio,
            min_trading_value=condition.min_trading_value,
            volume_high_months=condition.volume_high_months,
            volume_spike_ratio=condition.volume_spike_ratio,
            price_high_months=condition.price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
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
                if days_diff < condition.cooldown_days:
                    continue

            # Block1 기본 조건 체크
            if self.block1_checker.check_entry(
                condition=block1_condition,
                stock=stock,
                prev_stock=stocks_in_period[i - 1] if i > 0 else None
            ):
                # Block1 재탐지 생성
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
                    entry_rate=((stock.high - stocks_in_period[i - 1].close) / stocks_in_period[i - 1].close * 100) if i > 0 else 0,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="redetection"
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
        redetection_start: date,
        redetection_end: date
    ) -> List[Block2Detection]:
        """
        Block2 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block1: Block1 Seed (저가 마진 체크용)
            seed_block2: Block2 Seed (가격 범위 기준)
            condition: 재탐지 조건
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block2 재탐지 리스트
        """
        from src.domain.entities.block2_condition import Block2Condition
        from src.domain.entities.block1_condition import Block1Condition

        # Block1Condition 생성
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            high_above_ma=condition.high_above_ma,
            max_deviation_ratio=condition.max_deviation_ratio,
            min_trading_value=condition.min_trading_value,
            volume_high_months=condition.volume_high_months,
            volume_spike_ratio=condition.volume_spike_ratio,
            price_high_months=condition.price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block2Condition 생성
        block2_condition = Block2Condition(
            block1_condition=block1_condition,
            block_volume_ratio=condition.block2_volume_ratio,
            low_price_margin=condition.block2_low_price_margin,
            cooldown_days=condition.cooldown_days
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
                if days_diff < condition.cooldown_days:
                    continue

            # Block2 기본 조건 체크
            if self.block2_checker.check_entry(
                condition=block2_condition,
                stock=stock,
                prev_stock=stocks_in_period[i - 1] if i > 0 else None,
                prev_block1=seed_block1
            ):
                # Block2 재탐지 생성
                block2 = Block2Detection(
                    block2_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=((stock.high - stocks_in_period[i - 1].close) / stocks_in_period[i - 1].close * 100) if i > 0 else 0,
                    prev_block1_id=seed_block1.block1_id,
                    prev_block1_peak_price=seed_block1.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="redetection"
                )

                redetections.append(block2)
                last_redetection_date = stock.date

        return redetections

    def redetect_block3(
        self,
        stocks: List[Stock],
        seed_block2: Block2Detection,
        seed_block3: Block3Detection,
        condition: RedetectionCondition,
        redetection_start: date,
        redetection_end: date
    ) -> List[Block3Detection]:
        """
        Block3 재탐지

        Args:
            stocks: 주식 데이터 리스트
            seed_block2: Block2 Seed (저가 마진 체크용)
            seed_block3: Block3 Seed (가격 범위 기준)
            condition: 재탐지 조건
            redetection_start: 재탐지 시작일
            redetection_end: 재탐지 종료일

        Returns:
            Block3 재탐지 리스트
        """
        from src.domain.entities.block3_condition import Block3Condition
        from src.domain.entities.block2_condition import Block2Condition
        from src.domain.entities.block1_condition import Block1Condition

        # Block1Condition 생성
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            high_above_ma=condition.high_above_ma,
            max_deviation_ratio=condition.max_deviation_ratio,
            min_trading_value=condition.min_trading_value,
            volume_high_months=condition.volume_high_months,
            volume_spike_ratio=condition.volume_spike_ratio,
            price_high_months=condition.price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block2Condition 생성
        block2_condition = Block2Condition(
            block1_condition=block1_condition,
            block_volume_ratio=condition.block2_volume_ratio,
            low_price_margin=condition.block2_low_price_margin,
            cooldown_days=condition.cooldown_days
        )

        # Block3Condition 생성
        block3_condition = Block3Condition(
            block2_condition=block2_condition,
            block_volume_ratio=condition.block3_volume_ratio,
            low_price_margin=condition.block3_low_price_margin
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
                if days_diff < condition.cooldown_days:
                    continue

            # Block3 기본 조건 체크
            if self.block3_checker.check_entry(
                condition=block3_condition,
                stock=stock,
                prev_stock=stocks_in_period[i - 1] if i > 0 else None,
                prev_block2=seed_block2
            ):
                # Block3 재탐지 생성
                block3 = Block3Detection(
                    block3_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=((stock.high - stocks_in_period[i - 1].close) / stocks_in_period[i - 1].close * 100) if i > 0 else 0,
                    prev_block2_id=seed_block2.block2_id,
                    prev_block2_peak_price=seed_block2.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="redetection"
                )

                redetections.append(block3)
                last_redetection_date = stock.date

        return redetections
