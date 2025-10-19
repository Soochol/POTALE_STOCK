"""
Pattern Seed Detector Service

Block1/2/3/4 Seed 탐지 서비스
"""
from typing import List, Optional
from datetime import date, timedelta
from src.domain.entities.stock import Stock
from src.domain.entities.seed_condition import SeedCondition
from src.domain.entities.block1_detection import Block1Detection
from src.domain.entities.block2_detection import Block2Detection
from src.domain.entities.block3_detection import Block3Detection
from src.domain.entities.block4_detection import Block4Detection
from src.application.services.block1_checker import Block1Checker
from src.application.services.block2_checker import Block2Checker
from src.application.services.block3_checker import Block3Checker
from src.application.services.block4_checker import Block4Checker


class PatternSeedDetector:
    """
    패턴 Seed 탐지 서비스

    Seed 탐지를 위한 엄격한 조건 적용
    - Block1 Seed: Cooldown 20일 적용
    - Block2 Seed: Block1 이후 첫 번째만
    - Block3 Seed: Block2 이후 첫 번째만
    - Block4 Seed: Block3 이후 첫 번째만
    """

    def __init__(self):
        self.block1_checker = Block1Checker()
        self.block2_checker = Block2Checker()
        self.block3_checker = Block3Checker()
        self.block4_checker = Block4Checker()

    def find_all_block1_seeds(
        self,
        stocks: List[Stock],
        condition: SeedCondition
    ) -> List[Block1Detection]:
        """
        모든 Block1 Seed 찾기

        Args:
            stocks: 주식 데이터 리스트
            condition: Seed 조건

        Returns:
            Block1 Seed 리스트
        """
        from src.domain.entities.block1_condition import Block1Condition

        # SeedCondition을 Block1Condition으로 변환
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            entry_high_above_ma=condition.entry_high_above_ma,
            entry_max_deviation_ratio=condition.entry_max_deviation_ratio,
            entry_min_trading_value=condition.entry_min_trading_value,
            entry_volume_high_months=condition.entry_volume_high_months,
            entry_volume_spike_ratio=condition.entry_volume_spike_ratio,
            entry_price_high_months=condition.entry_price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block1 탐지 (기존 Block1Checker 사용)
        all_block1 = []
        last_seed_date = None

        for i, stock in enumerate(stocks):
            # Cooldown 체크
            if last_seed_date:
                days_diff = (stock.date - last_seed_date).days
                if days_diff < condition.cooldown_days:
                    continue

            # Block1 조건 체크
            if self.block1_checker.check_entry(
                condition=block1_condition,
                stock=stock,
                prev_stock=stocks[i - 1] if i > 0 else None
            ):
                # Block1 Detection 생성
                block1 = Block1Detection(
                    block1_id=None,  # Repository에서 할당
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_open=stock.open,
                    entry_high=stock.high,
                    entry_low=stock.low,
                    entry_close=stock.close,
                    entry_volume=stock.volume,
                    entry_trading_value=stock.close * stock.volume / 100_000_000,
                    entry_rate=((stock.high - stocks[i - 1].close) / stocks[i - 1].close * 100) if i > 0 else 0,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    peak_volume=stock.volume,  # 진입일 거래량으로 초기화
                    condition_name="seed"
                )

                all_block1.append(block1)
                last_seed_date = stock.date

        return all_block1

    def find_first_block2_after_block1(
        self,
        block1: Block1Detection,
        stocks: List[Stock],
        condition: SeedCondition
    ) -> Optional[Block2Detection]:
        """
        Block1 이후 첫 번째 Block2 Seed 찾기

        Args:
            block1: Block1 Seed
            stocks: 주식 데이터 리스트
            condition: Seed 조건

        Returns:
            Block2 Seed 또는 None
        """
        from src.domain.entities.block2_condition import Block2Condition
        from src.domain.entities.block1_condition import Block1Condition

        # Block1 종료일 이후부터 검색
        # (Block1 종료일이 없으면 시작일 + 1일부터)
        start_search_date = block1.ended_at if block1.ended_at else block1.started_at + timedelta(days=1)

        # Block1Condition 생성
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            entry_high_above_ma=condition.entry_high_above_ma,
            entry_max_deviation_ratio=condition.entry_max_deviation_ratio,
            entry_min_trading_value=condition.entry_min_trading_value,
            entry_volume_high_months=condition.entry_volume_high_months,
            entry_volume_spike_ratio=condition.entry_volume_spike_ratio,
            entry_price_high_months=condition.entry_price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block2Condition 생성
        block2_condition = Block2Condition(
            block1_condition=block1_condition,
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            cooldown_days=condition.cooldown_days,
            block2_min_candles_after_block1=condition.block2_min_candles_after_block1
        )

        # Block1 이후 데이터만 필터링
        stocks_after = [s for s in stocks if s.date >= start_search_date]

        for i, stock in enumerate(stocks_after):
            # Block2 조건 체크
            if self.block2_checker.check_entry(
                condition=block2_condition,
                stock=stock,
                prev_stock=stocks_after[i - 1] if i > 0 else None,
                prev_block1=block1
            ):
                # Block2 Detection 생성
                block2 = Block2Detection(
                    block2_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=((stock.high - stocks_after[i - 1].close) / stocks_after[i - 1].close * 100) if i > 0 else 0,
                    prev_block1_id=block1.block1_id,
                    prev_block1_peak_price=block1.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="seed"
                )

                return block2  # 첫 번째만!

        return None

    def find_first_block3_after_block2(
        self,
        block2: Block2Detection,
        stocks: List[Stock],
        condition: SeedCondition
    ) -> Optional[Block3Detection]:
        """
        Block2 이후 첫 번째 Block3 Seed 찾기

        Args:
            block2: Block2 Seed
            stocks: 주식 데이터 리스트
            condition: Seed 조건

        Returns:
            Block3 Seed 또는 None
        """
        from src.domain.entities.block3_condition import Block3Condition
        from src.domain.entities.block2_condition import Block2Condition
        from src.domain.entities.block1_condition import Block1Condition

        # Block2 종료일 이후부터 검색
        start_search_date = block2.ended_at if block2.ended_at else block2.started_at + timedelta(days=1)

        # Block1Condition 생성
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            entry_high_above_ma=condition.entry_high_above_ma,
            entry_max_deviation_ratio=condition.entry_max_deviation_ratio,
            entry_min_trading_value=condition.entry_min_trading_value,
            entry_volume_high_months=condition.entry_volume_high_months,
            entry_volume_spike_ratio=condition.entry_volume_spike_ratio,
            entry_price_high_months=condition.entry_price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block2Condition 생성
        block2_condition = Block2Condition(
            block1_condition=block1_condition,
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            cooldown_days=condition.cooldown_days,
            block2_min_candles_after_block1=condition.block2_min_candles_after_block1
        )

        # Block3Condition 생성
        block3_condition = Block3Condition(
            block2_condition=block2_condition,
            block3_volume_ratio=condition.block3_volume_ratio,
            block3_low_price_margin=condition.block3_low_price_margin,
            block3_min_candles_after_block2=condition.block3_min_candles_after_block2
        )

        # Block2 이후 데이터만 필터링
        stocks_after = [s for s in stocks if s.date >= start_search_date]

        for i, stock in enumerate(stocks_after):
            # Block3 조건 체크
            if self.block3_checker.check_entry(
                condition=block3_condition,
                stock=stock,
                prev_stock=stocks_after[i - 1] if i > 0 else None,
                prev_block2=block2
            ):
                # Block3 Detection 생성
                block3 = Block3Detection(
                    block3_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=((stock.high - stocks_after[i - 1].close) / stocks_after[i - 1].close * 100) if i > 0 else 0,
                    prev_block2_id=block2.block2_id,
                    prev_block2_peak_price=block2.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="seed"
                )

                return block3  # 첫 번째만!

        return None

    def find_first_block4_after_block3(
        self,
        block3: Block3Detection,
        stocks: List[Stock],
        condition: SeedCondition
    ) -> Optional[Block4Detection]:
        """
        Block3 이후 첫 번째 Block4 Seed 찾기

        Args:
            block3: Block3 Seed
            stocks: 주식 데이터 리스트
            condition: Seed 조건

        Returns:
            Block4 Seed 또는 None
        """
        from src.domain.entities.block4_condition import Block4Condition
        from src.domain.entities.block3_condition import Block3Condition
        from src.domain.entities.block2_condition import Block2Condition
        from src.domain.entities.block1_condition import Block1Condition

        # Block3 종료일 이후부터 검색
        start_search_date = block3.ended_at if block3.ended_at else block3.started_at + timedelta(days=1)

        # Block1Condition 생성
        block1_condition = Block1Condition(
            entry_surge_rate=condition.entry_surge_rate,
            entry_ma_period=condition.entry_ma_period,
            entry_high_above_ma=condition.entry_high_above_ma,
            entry_max_deviation_ratio=condition.entry_max_deviation_ratio,
            entry_min_trading_value=condition.entry_min_trading_value,
            entry_volume_high_months=condition.entry_volume_high_months,
            entry_volume_spike_ratio=condition.entry_volume_spike_ratio,
            entry_price_high_months=condition.entry_price_high_months,
            exit_condition_type=condition.exit_condition_type,
            exit_ma_period=condition.exit_ma_period,
            cooldown_days=condition.cooldown_days
        )

        # Block2Condition 생성
        block2_condition = Block2Condition(
            block1_condition=block1_condition,
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            cooldown_days=condition.cooldown_days,
            block2_min_candles_after_block1=condition.block2_min_candles_after_block1
        )

        # Block3Condition 생성
        block3_condition = Block3Condition(
            block2_condition=block2_condition,
            block3_volume_ratio=condition.block3_volume_ratio,
            block3_low_price_margin=condition.block3_low_price_margin,
            block3_min_candles_after_block2=condition.block3_min_candles_after_block2
        )

        # Block4Condition 생성
        block4_condition = Block4Condition(
            block3_condition=block3_condition,
            block4_volume_ratio=condition.block4_volume_ratio,
            block4_low_price_margin=condition.block4_low_price_margin,
            block4_min_candles_after_block3=condition.block4_min_candles_after_block3
        )

        # Block3 이후 데이터만 필터링
        stocks_after = [s for s in stocks if s.date >= start_search_date]

        for i, stock in enumerate(stocks_after):
            # Block4 조건 체크
            if self.block4_checker.check_entry(
                condition=block4_condition,
                stock=stock,
                prev_stock=stocks_after[i - 1] if i > 0 else None,
                prev_block1=None,  # Block4Checker가 필요로 하지 않음
                prev_block2=None,  # Block4Checker가 필요로 하지 않음
                prev_block3=block3
            ):
                # Block4 Detection 생성
                block4 = Block4Detection(
                    block4_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=((stock.high - stocks_after[i - 1].close) / stocks_after[i - 1].close * 100) if i > 0 else 0,
                    prev_block3_id=block3.block3_id,
                    prev_block3_peak_price=block3.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="seed"
                )

                return block4  # 첫 번째만!

        return None
