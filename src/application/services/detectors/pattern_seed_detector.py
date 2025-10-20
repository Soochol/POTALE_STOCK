"""
Pattern Seed Detector Service

Block1/2/3/4 Seed 탐지 서비스
"""
from typing import List, Optional
from datetime import date, timedelta

from src.domain.entities import (
    BaseEntryCondition,
    SeedCondition,
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

    def _create_base_for_block(
        self,
        condition: SeedCondition,
        block_num: int
    ) -> BaseEntryCondition:
        """
        BlockN용 BaseEntryCondition 생성
        BlockN 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback

        Args:
            condition: Seed 조건
            block_num: 블록 번호 (2, 3, 4)

        Returns:
            BaseEntryCondition 객체
        """
        # Block2/3/4 전용 파라미터 속성 이름
        prefix = f"block{block_num}_"

        return BaseEntryCondition(
            block1_entry_surge_rate=getattr(condition, f"{prefix}entry_surge_rate") if getattr(condition, f"{prefix}entry_surge_rate") is not None else condition.base.block1_entry_surge_rate,
            block1_entry_ma_period=getattr(condition, f"{prefix}entry_ma_period") if getattr(condition, f"{prefix}entry_ma_period") is not None else condition.base.block1_entry_ma_period,
            block1_entry_high_above_ma=getattr(condition, f"{prefix}entry_high_above_ma") if getattr(condition, f"{prefix}entry_high_above_ma") is not None else condition.base.block1_entry_high_above_ma,
            block1_entry_max_deviation_ratio=getattr(condition, f"{prefix}entry_max_deviation_ratio") if getattr(condition, f"{prefix}entry_max_deviation_ratio") is not None else condition.base.block1_entry_max_deviation_ratio,
            block1_entry_min_trading_value=getattr(condition, f"{prefix}entry_min_trading_value") if getattr(condition, f"{prefix}entry_min_trading_value") is not None else condition.base.block1_entry_min_trading_value,
            block1_entry_volume_high_months=getattr(condition, f"{prefix}entry_volume_high_months") if getattr(condition, f"{prefix}entry_volume_high_months") is not None else condition.base.block1_entry_volume_high_months,
            block1_entry_volume_spike_ratio=getattr(condition, f"{prefix}entry_volume_spike_ratio") if getattr(condition, f"{prefix}entry_volume_spike_ratio") is not None else condition.base.block1_entry_volume_spike_ratio,
            block1_entry_price_high_months=getattr(condition, f"{prefix}entry_price_high_months") if getattr(condition, f"{prefix}entry_price_high_months") is not None else condition.base.block1_entry_price_high_months,
            block1_exit_condition_type=getattr(condition, f"{prefix}exit_condition_type") if getattr(condition, f"{prefix}exit_condition_type") is not None else condition.base.block1_exit_condition_type,
            block1_exit_ma_period=getattr(condition, f"{prefix}exit_ma_period") if getattr(condition, f"{prefix}exit_ma_period") is not None else condition.base.block1_exit_ma_period,
            block1_cooldown_days=getattr(condition, f"{prefix}cooldown_days") if getattr(condition, f"{prefix}cooldown_days") is not None else condition.base.block1_cooldown_days
        )

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
            base=condition.base  # BaseEntryCondition을 그대로 사용
        )

        # Block1 탐지 (기존 Block1Checker 사용)
        all_block1 = []
        last_seed_date = None

        for i, stock in enumerate(stocks):
            # Cooldown 체크
            if last_seed_date:
                days_diff = (stock.date - last_seed_date).days
                if days_diff < condition.base.block1_cooldown_days:
                    continue

            # Block1 조건 체크
            if self.block1_checker.check_entry(
                condition=block1_condition,
                stock=stock,
                all_stocks=stocks
            ):
                # Block1 Detection 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
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
                    entry_rate=indicators.get('rate'),
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

        # Block1 종료일 이후부터 검색
        # (Block1 종료일이 없으면 시작일 + 1일부터)
        start_search_date = block1.ended_at if block1.ended_at else block1.started_at + timedelta(days=1)

        # Block2Condition 생성 (Block1 조건 + Block2 조건)
        # Block2 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback
        block2_condition = Block2Condition(
            base=self._create_base_for_block(condition, 2),
            # Block2 추가 조건 (3개 필드)
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            block2_min_candles_after_block1=condition.block2_min_candles_after_block1
        )

        # Block1 이후 데이터만 필터링
        stocks_after = [s for s in stocks if s.date >= start_search_date]

        for i, stock in enumerate(stocks_after):
            # Block2 조건 체크
            if self.block2_checker.check_entry(
                condition=block2_condition,
                stock=stock,
                all_stocks=stocks,
                prev_block1=block1
            ):
                # Block2 Detection 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block2 = Block2Detection(
                    block2_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=indicators.get('rate'),
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

        # Block2 종료일 이후부터 검색
        start_search_date = block2.ended_at if block2.ended_at else block2.started_at + timedelta(days=1)

        # Block3Condition 생성 (Block1 + Block2 + Block3 조건)
        # Block3 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback
        block3_condition = Block3Condition(
            base=self._create_base_for_block(condition, 3),
            # Block2 추가 조건 (3개 필드)
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            block2_min_candles_after_block1=condition.block2_min_candles_after_block1,
            # Block3 추가 조건 (3개 필드)
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
                all_stocks=stocks,
                prev_block1=None,
                prev_block2=block2
            ):
                # Block3 Detection 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block3 = Block3Detection(
                    block3_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=indicators.get('rate'),
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

        # Block3 종료일 이후부터 검색
        start_search_date = block3.ended_at if block3.ended_at else block3.started_at + timedelta(days=1)

        # Block4Condition 생성 (Block1 + Block2 + Block3 + Block4 조건)
        # Block4 전용 파라미터가 있으면 사용, 없으면 Block1 값으로 fallback
        block4_condition = Block4Condition(
            base=self._create_base_for_block(condition, 4),
            # Block2 추가 조건 (3개 필드)
            block2_volume_ratio=condition.block2_volume_ratio,
            block2_low_price_margin=condition.block2_low_price_margin,
            block2_min_candles_after_block1=condition.block2_min_candles_after_block1,
            # Block3 추가 조건 (3개 필드)
            block3_volume_ratio=condition.block3_volume_ratio,
            block3_low_price_margin=condition.block3_low_price_margin,
            block3_min_candles_after_block2=condition.block3_min_candles_after_block2,
            # Block4 추가 조건 (3개 필드)
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
                all_stocks=stocks,
                prev_block1=None,  # Block4Checker가 필요로 하지 않음
                prev_block2=None,  # Block4Checker가 필요로 하지 않음
                prev_block3=block3
            ):
                # Block4 Detection 생성
                indicators = stock.indicators if hasattr(stock, 'indicators') else {}
                block4 = Block4Detection(
                    block4_id=None,
                    ticker=stock.ticker,
                    started_at=stock.date,
                    ended_at=None,
                    entry_close=stock.close,
                    entry_rate=indicators.get('rate'),
                    prev_block3_id=block3.block3_id,
                    prev_block3_peak_price=block3.peak_price,
                    peak_price=stock.high,
                    peak_date=stock.date,
                    condition_name="seed"
                )

                return block4  # 첫 번째만!

        return None
