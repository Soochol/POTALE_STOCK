"""
Detect Patterns Use Case

패턴 재탐지 시스템의 메인 Use Case
3단계 프로세스: Seed 탐지 → Pattern 생성 → 5년 재탐지
"""
from src.domain.entities import BlockPattern, RedetectionCondition, SeedCondition, Stock
from typing import List, Dict
from datetime import timedelta
from src.application.services.detectors.pattern_seed_detector import PatternSeedDetector
from src.application.services.detectors.pattern_redetector import PatternRedetector
from src.application.services.detectors.exit_condition_processor import ExitConditionProcessor
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.application.services.checkers.block1_checker import Block1Checker
from src.application.services.checkers.block2_checker import Block2Checker
from src.application.services.checkers.block3_checker import Block3Checker
from src.application.services.checkers.block4_checker import Block4Checker
from src.domain.entities.conditions.block_conditions import (
    Block1Condition,
    Block2Condition,
    Block3Condition,
    Block4Condition,
)
from src.infrastructure.repositories.pattern.block_pattern_repository import BlockPatternRepository
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block3_repository import Block3Repository
from src.infrastructure.repositories.detection.block4_repository import Block4Repository
from src.infrastructure.database.connection import DatabaseConnection

class DetectPatternsUseCase:
    """
    패턴 탐지 Use Case

    전체 프로세스:
    1. Step 1: 모든 Block1 Seed 찾기 (Cooldown 적용)
    2. Step 2: 각 Block1 Seed마다:
       - Block2/3 Seed 찾기 (첫 번째만)
       - Pattern 생성
       - 5년 재탐지 실행
    3. Step 3: 결과 반환
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.seed_detector = PatternSeedDetector()
        self.redetector = PatternRedetector()
        self.pattern_repo = BlockPatternRepository(db)
        self.block1_repo = Block1Repository(db)
        self.block2_repo = Block2Repository(db)
        self.block3_repo = Block3Repository(db)
        self.block4_repo = Block4Repository(db)

    def execute(
        self,
        ticker: str,
        stocks: List[Stock],
        seed_condition: SeedCondition,
        redetection_condition: RedetectionCondition
    ) -> Dict:
        """
        패턴 탐지 실행

        Args:
            ticker: 종목 코드
            stocks: 주식 데이터 리스트
            seed_condition: Seed 조건 (엄격)
            redetection_condition: 재탐지 조건 (완화 + tolerance)

        Returns:
            결과 딕셔너리
        """
        print("=" * 70)
        print(f"패턴 재탐지 시스템 실행: {ticker}")
        print("=" * 70)

        # ========================================
        # Step 0: Indicator 계산
        # ========================================
        print("\n[Step 0] Indicator 계산 중...")

        # Block1/2/3/4의 모든 entry_ma_period와 exit_ma_period 수집 (중복 제거)
        ma_periods_set = set()
        for attr in ['block1_entry_ma_period', 'block1_exit_ma_period',
                     'block2_entry_ma_period', 'block2_exit_ma_period',
                     'block3_entry_ma_period', 'block3_exit_ma_period',
                     'block4_entry_ma_period', 'block4_exit_ma_period']:
            if attr.startswith('block1_'):
                period = getattr(seed_condition.base, attr, None)
            else:
                period = getattr(seed_condition, attr, None)
            if period is not None:
                ma_periods_set.add(period)
        ma_periods_list = sorted(list(ma_periods_set)) if ma_periods_set else None

        # Block1/2/3/4의 모든 entry_volume_high_days 수집 (중복 제거)
        volume_days_set = set()
        for attr in ['block1_entry_volume_high_days', 'block2_entry_volume_high_days',
                     'block3_entry_volume_high_days', 'block4_entry_volume_high_days']:
            if attr == 'block1_entry_volume_high_days':
                days = seed_condition.base.block1_entry_volume_high_days
            else:
                days = getattr(seed_condition, attr, None)
            if days is not None:
                volume_days_set.add(days)
        volume_days_list = sorted(list(volume_days_set)) if volume_days_set else None

        # Block1/2/3/4의 모든 entry_price_high_days 수집 (중복 제거)
        new_high_days_set = set()
        for attr in ['block1_entry_price_high_days', 'block2_entry_price_high_days',
                     'block3_entry_price_high_days', 'block4_entry_price_high_days']:
            if attr == 'block1_entry_price_high_days':
                days = seed_condition.base.block1_entry_price_high_days
            else:
                days = getattr(seed_condition, attr, None)
            if days is not None:
                new_high_days_set.add(days)
        new_high_days_list = sorted(list(new_high_days_set)) if new_high_days_set else None

        calculator = Block1IndicatorCalculator()
        stocks_with_indicators = calculator.calculate(
            stocks=stocks,
            ma_periods=ma_periods_list,
            volume_days=volume_days_list,
            new_high_days=new_high_days_list
        )
        print(f"  {len(stocks_with_indicators)}건의 데이터에 indicator 추가 완료")
        if ma_periods_list:
            print(f"  MA 계산: {ma_periods_list}일")
        if volume_days_list:
            print(f"  volume_high 계산: {volume_days_list}일 (달력 기준)")
        if new_high_days_list:
            print(f"  new_high 계산: {new_high_days_list}일 (달력 기준)")

        # ========================================
        # Step 1: 모든 Block1 Seed 찾기
        # ========================================
        print("\n[Step 1] Block1 Seed 탐지 중...")
        seed_block1_list = self.seed_detector.find_all_block1_seeds(
            stocks=stocks_with_indicators,
            condition=seed_condition
        )

        print(f"  총 {len(seed_block1_list)}개의 Block1 Seed 발견")

        if not seed_block1_list:
            print("\n[완료] Block1 Seed가 없어 종료합니다.")
            return {"patterns": [], "total_redetections": 0}

        # ========================================
        # Step 2: 각 Block1 Seed마다 Pattern 생성
        # ========================================
        patterns = []
        total_stats = {
            "block1_redetections": 0,
            "block2_redetections": 0,
            "block3_redetections": 0,
            "block4_redetections": 0
        }

        for idx, seed_block1 in enumerate(seed_block1_list, 1):
            print(f"\n{'='*70}")
            print(f"[Pattern #{idx}] 처리 중 (Block1 Seed: {seed_block1.started_at})")
            print(f"{'='*70}")

            # ========================================
            # Step 2-1: Block2 Seed 찾기
            # ========================================
            print(f"  [2-1] Block2 Seed 탐지 중...")
            seed_block2 = self.seed_detector.find_first_block2_after_block1(
                block1=seed_block1,
                stocks=stocks_with_indicators,
                condition=seed_condition
            )

            if not seed_block2:
                print(f"    Block2 Seed 없음 → Pattern #{idx} 종료")
                continue

            print(f"    Block2 Seed 발견: {seed_block2.started_at}")

            # ========================================
            # Step 2-2: Block3 Seed 찾기
            # ========================================
            print(f"  [2-2] Block3 Seed 탐지 중...")
            seed_block3 = self.seed_detector.find_first_block3_after_block2(
                block1=seed_block1,  # Block2 volume_ratio 체크용
                block2=seed_block2,
                stocks=stocks_with_indicators,
                condition=seed_condition
            )

            if not seed_block3:
                print(f"    Block3 Seed 없음 → Pattern #{idx} 종료")
                continue

            print(f"    Block3 Seed 발견: {seed_block3.started_at}")

            # ========================================
            # Step 2-2.5: Block4 Seed 찾기 (선택적)
            # ========================================
            print(f"  [2-2.5] Block4 Seed 탐지 중...")
            seed_block4 = self.seed_detector.find_first_block4_after_block3(
                block1=seed_block1,  # Block2 volume_ratio 체크용
                block2=seed_block2,  # Block3 volume_ratio 체크용
                block3=seed_block3,
                stocks=stocks_with_indicators,
                condition=seed_condition
            )

            if not seed_block4:
                print(f"    Block4 Seed 없음 (계속 진행)")
            else:
                print(f"    Block4 Seed 발견: {seed_block4.started_at}")

            # ========================================
            # Step 2-3: Seed 저장 (pattern_id=None, detection_type="seed")
            # ========================================
            print(f"  [2-3] Seed 저장 중...")

            # Block1 Seed 저장
            seed_block1.condition_name = "seed"
            seed_block1.pattern_id = None  # 나중에 업데이트
            seed_block1.detection_type = "seed"
            saved_block1 = self.block1_repo.save(seed_block1)
            block1_id = saved_block1.block1_id

            # Block2 Seed 저장
            seed_block2.condition_name = "seed"
            seed_block2.pattern_id = None
            seed_block2.detection_type = "seed"
            saved_block2 = self.block2_repo.save(seed_block2)
            block2_id = saved_block2.block2_id

            # Block3 Seed 저장
            seed_block3.condition_name = "seed"
            seed_block3.pattern_id = None
            seed_block3.detection_type = "seed"
            saved_block3 = self.block3_repo.save(seed_block3)
            block3_id = saved_block3.block3_id

            # Block4 Seed 저장 (있는 경우에만)
            block4_id = None
            if seed_block4:
                seed_block4.condition_name = "seed"
                seed_block4.pattern_id = None
                seed_block4.detection_type = "seed"
                saved_block4 = self.block4_repo.save(seed_block4)
                block4_id = saved_block4.block4_id

            print(f"    Seed 저장 완료")

            # ========================================
            # Step 2-4: Pattern 생성 및 저장
            # ========================================
            print(f"  [2-4] Pattern 생성 중...")

            # 재탐지 기간 계산 (각 Block Seed 발생일 기준, 달력상 일수 - 주말/공휴일 포함)
            # NOTE: timedelta(days=N)는 거래일이 아닌 달력상 날짜 차이로 계산됨

            # Block1 재탐지 기간
            block1_redetection_start = seed_block1.started_at + timedelta(
                days=redetection_condition.block1_redetection_min_days_after_seed
            )
            block1_redetection_end = seed_block1.started_at + timedelta(
                days=redetection_condition.block1_redetection_max_days_after_seed
            )

            # Block2 재탐지 기간
            block2_redetection_start = seed_block2.started_at + timedelta(
                days=redetection_condition.block2_redetection_min_days_after_seed
            )
            block2_redetection_end = seed_block2.started_at + timedelta(
                days=redetection_condition.block2_redetection_max_days_after_seed
            )

            # Block3 재탐지 기간
            block3_redetection_start = seed_block3.started_at + timedelta(
                days=redetection_condition.block3_redetection_min_days_after_seed
            )
            block3_redetection_end = seed_block3.started_at + timedelta(
                days=redetection_condition.block3_redetection_max_days_after_seed
            )

            # Block4 재탐지 기간 (Block4 Seed가 있는 경우에만)
            if seed_block4:
                block4_redetection_start = seed_block4.started_at + timedelta(
                    days=redetection_condition.block4_redetection_min_days_after_seed
                )
                block4_redetection_end = seed_block4.started_at + timedelta(
                    days=redetection_condition.block4_redetection_max_days_after_seed
                )

            # Pattern 객체 생성 (전체 재탐지 기간은 Block1 기준 사용)
            pattern = BlockPattern(
                pattern_id=None,
                ticker=ticker,
                seed_block1_id=block1_id,
                seed_block2_id=block2_id,
                seed_block3_id=block3_id,
                seed_block4_id=block4_id,  # Block4 Seed ID (있으면 값, 없으면 None)
                redetection_start=block1_redetection_start,
                redetection_end=block1_redetection_end
            )

            pattern_id = self.pattern_repo.save(pattern)
            pattern.pattern_id = pattern_id

            print(f"    Pattern #{pattern_id} 생성 완료")
            print(f"    Block1 재탐지 기간: {block1_redetection_start} ~ {block1_redetection_end}")
            print(f"    Block2 재탐지 기간: {block2_redetection_start} ~ {block2_redetection_end}")
            print(f"    Block3 재탐지 기간: {block3_redetection_start} ~ {block3_redetection_end}")
            if seed_block4:
                print(f"    Block4 재탐지 기간: {block4_redetection_start} ~ {block4_redetection_end}")

            # Seed들의 pattern_id 업데이트
            seed_block1.pattern_id = pattern_id
            seed_block2.pattern_id = pattern_id
            seed_block3.pattern_id = pattern_id
            self.block1_repo.save(seed_block1)
            self.block2_repo.save(seed_block2)
            self.block3_repo.save(seed_block3)

            if seed_block4:
                seed_block4.pattern_id = pattern_id
                self.block4_repo.save(seed_block4)

            # ========================================
            # Step 2-5: 재탐지 (각 Block Seed 발생일 기준)
            # ========================================
            print(f"  [2-5] 재탐지 실행 중...")

            # Block1 재탐지
            print(f"    Block1 재탐지 중...")
            block1_redetections = self.redetector.redetect_block1(
                stocks=stocks_with_indicators,
                seed_block1=seed_block1,
                condition=redetection_condition,
                pattern_id=pattern_id,
                redetection_start=block1_redetection_start,
                redetection_end=block1_redetection_end
            )

            for block1 in block1_redetections:
                self.block1_repo.save(block1)

            print(f"      Block1 재탐지: {len(block1_redetections)}개")

            # Block2 재탐지
            print(f"    Block2 재탐지 중...")
            block2_redetections = self.redetector.redetect_block2(
                stocks=stocks_with_indicators,
                seed_block1=seed_block1,
                seed_block2=seed_block2,
                condition=redetection_condition,
                pattern_id=pattern_id,
                redetection_start=block2_redetection_start,
                redetection_end=block2_redetection_end
            )

            for block2 in block2_redetections:
                self.block2_repo.save(block2)

            print(f"      Block2 재탐지: {len(block2_redetections)}개")

            # Block3 재탐지
            print(f"    Block3 재탐지 중...")
            block3_redetections = self.redetector.redetect_block3(
                stocks=stocks_with_indicators,
                seed_block1=seed_block1,  # Block2 volume_ratio 체크용
                seed_block2=seed_block2,
                seed_block3=seed_block3,
                condition=redetection_condition,
                pattern_id=pattern_id,
                redetection_start=block3_redetection_start,
                redetection_end=block3_redetection_end
            )

            for block3 in block3_redetections:
                self.block3_repo.save(block3)

            print(f"      Block3 재탐지: {len(block3_redetections)}개")

            # Block4 재탐지 (Block4 Seed가 있는 경우에만)
            block4_redetections = []
            if seed_block4:
                print(f"    Block4 재탐지 중...")
                block4_redetections = self.redetector.redetect_block4(
                    stocks=stocks_with_indicators,
                    seed_block1=seed_block1,  # Block2 volume_ratio 체크용
                    seed_block2=seed_block2,  # Block3 volume_ratio 체크용
                    seed_block3=seed_block3,
                    seed_block4=seed_block4,
                    condition=redetection_condition,
                    pattern_id=pattern_id,
                    redetection_start=block4_redetection_start,
                    redetection_end=block4_redetection_end
                )

                for block4 in block4_redetections:
                    self.block4_repo.save(block4)

                print(f"      Block4 재탐지: {len(block4_redetections)}개")
            else:
                print(f"    Block4 재탐지: 스킵 (Seed 없음)")

            # 통계 업데이트
            total_stats["block1_redetections"] += len(block1_redetections)
            total_stats["block2_redetections"] += len(block2_redetections)
            total_stats["block3_redetections"] += len(block3_redetections)
            total_stats["block4_redetections"] += len(block4_redetections)

            patterns.append({
                "pattern_id": pattern_id,
                "seed_block1": seed_block1,
                "seed_block2": seed_block2,
                "seed_block3": seed_block3,
                "seed_block4": seed_block4,  # None일 수도 있음
                "block1_redetections": block1_redetections,
                "block2_redetections": block2_redetections,
                "block3_redetections": block3_redetections,
                "block4_redetections": block4_redetections,
                "redetection_stats": {
                    "block1": len(block1_redetections),
                    "block2": len(block2_redetections),
                    "block3": len(block3_redetections),
                    "block4": len(block4_redetections)
                }
            })

        # ========================================
        # Step 3: 종료 조건 체크 (후처리)
        # ========================================
        print(f"\n{'='*70}")
        print("[Step 3] 종료 조건 체크 중...")
        print(f"{'='*70}")

        # ExitConditionProcessor 초기화
        exit_processor = ExitConditionProcessor(
            block1_checker=Block1Checker(),
            block2_checker=Block2Checker(),
            block3_checker=Block3Checker(),
            block4_checker=Block4Checker(),
            block1_repo=self.block1_repo,
            block2_repo=self.block2_repo,
            block3_repo=self.block3_repo,
            block4_repo=self.block4_repo
        )

        # Seed 조건을 Block 조건으로 변환
        block1_condition = Block1Condition(base=seed_condition.base)
        block2_condition = Block2Condition(
            base=seed_condition.base,
            block2_volume_ratio=seed_condition.block2_volume_ratio,
            block2_low_price_margin=seed_condition.block2_low_price_margin,
            block2_min_candles_after_block1=seed_condition.block2_min_candles_after_block1,
            block2_max_candles_after_block1=seed_condition.block2_max_candles_after_block1
        )
        block3_condition = Block3Condition(
            base=seed_condition.base,
            block2_volume_ratio=seed_condition.block2_volume_ratio,
            block2_low_price_margin=seed_condition.block2_low_price_margin,
            block2_min_candles_after_block1=seed_condition.block2_min_candles_after_block1,
            block2_max_candles_after_block1=seed_condition.block2_max_candles_after_block1,
            block3_volume_ratio=seed_condition.block3_volume_ratio,
            block3_low_price_margin=seed_condition.block3_low_price_margin,
            block3_min_candles_after_block2=seed_condition.block3_min_candles_after_block2,
            block3_max_candles_after_block2=seed_condition.block3_max_candles_after_block2
        )
        block4_condition = Block4Condition(
            base=seed_condition.base,
            block2_volume_ratio=seed_condition.block2_volume_ratio,
            block2_low_price_margin=seed_condition.block2_low_price_margin,
            block2_min_candles_after_block1=seed_condition.block2_min_candles_after_block1,
            block2_max_candles_after_block1=seed_condition.block2_max_candles_after_block1,
            block3_volume_ratio=seed_condition.block3_volume_ratio,
            block3_low_price_margin=seed_condition.block3_low_price_margin,
            block3_min_candles_after_block2=seed_condition.block3_min_candles_after_block2,
            block3_max_candles_after_block2=seed_condition.block3_max_candles_after_block2,
            block4_volume_ratio=seed_condition.block4_volume_ratio,
            block4_low_price_margin=seed_condition.block4_low_price_margin,
            block4_min_candles_after_block3=seed_condition.block4_min_candles_after_block3,
            block4_max_candles_after_block3=seed_condition.block4_max_candles_after_block3
        )

        # 종료 조건 체크 통계
        exit_stats = {
            "block1_completed": 0,
            "block2_completed": 0,
            "block3_completed": 0,
            "block4_completed": 0
        }

        # 각 패턴의 모든 블록(Seed + 재탐지) 종료 조건 체크
        for idx, pattern in enumerate(patterns, 1):
            print(f"  Pattern #{idx} 종료 조건 체크 중...")

            # Block1 Seed + 재탐지
            block1_list = [pattern["seed_block1"]] + pattern["block1_redetections"]
            count = exit_processor.process_block1_exits(
                detections=block1_list,
                condition=block1_condition,
                all_stocks=stocks_with_indicators
            )
            exit_stats["block1_completed"] += count

            # Block2 Seed + 재탐지
            block2_list = [pattern["seed_block2"]] + pattern["block2_redetections"]
            count = exit_processor.process_block2_exits(
                detections=block2_list,
                condition=block2_condition,
                all_stocks=stocks_with_indicators
            )
            exit_stats["block2_completed"] += count

            # Block3 Seed + 재탐지
            block3_list = [pattern["seed_block3"]] + pattern["block3_redetections"]
            count = exit_processor.process_block3_exits(
                detections=block3_list,
                condition=block3_condition,
                all_stocks=stocks_with_indicators
            )
            exit_stats["block3_completed"] += count

            # Block4 Seed + 재탐지 (Block4 Seed가 있는 경우에만)
            if pattern["seed_block4"]:
                block4_list = [pattern["seed_block4"]] + pattern["block4_redetections"]
                count = exit_processor.process_block4_exits(
                    detections=block4_list,
                    condition=block4_condition,
                    all_stocks=stocks_with_indicators
                )
                exit_stats["block4_completed"] += count

        print(f"\n  종료 처리 완료:")
        print(f"    Block1 종료: {exit_stats['block1_completed']}개")
        print(f"    Block2 종료: {exit_stats['block2_completed']}개")
        print(f"    Block3 종료: {exit_stats['block3_completed']}개")
        print(f"    Block4 종료: {exit_stats['block4_completed']}개")

        # ========================================
        # Step 4: 완료
        # ========================================
        print(f"\n{'='*70}")
        print(f"전체 탐지 완료!")
        print(f"{'='*70}")
        print(f"  총 Pattern: {len(patterns)}개")
        print(f"  총 Block1 재탐지: {total_stats['block1_redetections']}개")
        print(f"  총 Block2 재탐지: {total_stats['block2_redetections']}개")
        print(f"  총 Block3 재탐지: {total_stats['block3_redetections']}개")
        print(f"  총 Block4 재탐지: {total_stats['block4_redetections']}개")
        print(f"{'='*70}\n")

        return {
            "patterns": patterns,
            "total_patterns": len(patterns),
            "total_stats": total_stats,
            "exit_stats": exit_stats
        }
