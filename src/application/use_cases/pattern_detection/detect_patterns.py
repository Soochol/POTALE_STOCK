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
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.infrastructure.repositories.pattern.block_pattern_repository import BlockPatternRepository
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block3_repository import Block3Repository
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
        calculator = Block1IndicatorCalculator()
        stocks_with_indicators = calculator.calculate(
            stocks=stocks,
            ma_period=seed_condition.base.block1_entry_ma_period,
            exit_ma_period=seed_condition.base.block1_exit_ma_period,
            volume_months=seed_condition.base.block1_entry_volume_high_months,
            new_high_months=seed_condition.base.block1_entry_price_high_months
        )
        print(f"  {len(stocks_with_indicators)}건의 데이터에 indicator 추가 완료")

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
            "block3_redetections": 0
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
                block2=seed_block2,
                stocks=stocks_with_indicators,
                condition=seed_condition
            )

            if not seed_block3:
                print(f"    Block3 Seed 없음 → Pattern #{idx} 종료")
                continue

            print(f"    Block3 Seed 발견: {seed_block3.started_at}")

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

            print(f"    Seed 저장 완료")

            # ========================================
            # Step 2-4: Pattern 생성 및 저장
            # ========================================
            print(f"  [2-4] Pattern 생성 중...")

            redetection_start = seed_block1.started_at
            redetection_end = redetection_start + timedelta(days=5 * 365)

            pattern = BlockPattern(
                pattern_id=None,
                ticker=ticker,
                seed_block1_id=block1_id,
                seed_block2_id=block2_id,
                seed_block3_id=block3_id,
                redetection_start=redetection_start,
                redetection_end=redetection_end
            )

            pattern_id = self.pattern_repo.save(pattern)
            pattern.pattern_id = pattern_id

            print(f"    Pattern #{pattern_id} 생성 완료")
            print(f"    재탐지 기간: {redetection_start} ~ {redetection_end}")

            # Seed들의 pattern_id 업데이트
            seed_block1.pattern_id = pattern_id
            seed_block2.pattern_id = pattern_id
            seed_block3.pattern_id = pattern_id
            self.block1_repo.save(seed_block1)
            self.block2_repo.save(seed_block2)
            self.block3_repo.save(seed_block3)

            # ========================================
            # Step 2-5: 5년 재탐지
            # ========================================
            print(f"  [2-5] 5년 재탐지 실행 중...")

            # Block1 재탐지
            print(f"    Block1 재탐지 중...")
            block1_redetections = self.redetector.redetect_block1(
                stocks=stocks_with_indicators,
                seed_block1=seed_block1,
                condition=redetection_condition,
                pattern_id=pattern_id,
                redetection_start=redetection_start,
                redetection_end=redetection_end
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
                redetection_start=redetection_start,
                redetection_end=redetection_end
            )

            for block2 in block2_redetections:
                self.block2_repo.save(block2)

            print(f"      Block2 재탐지: {len(block2_redetections)}개")

            # Block3 재탐지
            print(f"    Block3 재탐지 중...")
            block3_redetections = self.redetector.redetect_block3(
                stocks=stocks_with_indicators,
                seed_block2=seed_block2,
                seed_block3=seed_block3,
                condition=redetection_condition,
                pattern_id=pattern_id,
                redetection_start=redetection_start,
                redetection_end=redetection_end
            )

            for block3 in block3_redetections:
                self.block3_repo.save(block3)

            print(f"      Block3 재탐지: {len(block3_redetections)}개")

            # 통계 업데이트
            total_stats["block1_redetections"] += len(block1_redetections)
            total_stats["block2_redetections"] += len(block2_redetections)
            total_stats["block3_redetections"] += len(block3_redetections)

            patterns.append({
                "pattern_id": pattern_id,
                "seed_block1": seed_block1,
                "seed_block2": seed_block2,
                "seed_block3": seed_block3,
                "redetection_stats": {
                    "block1": len(block1_redetections),
                    "block2": len(block2_redetections),
                    "block3": len(block3_redetections)
                }
            })

        # ========================================
        # Step 3: 완료
        # ========================================
        print(f"\n{'='*70}")
        print(f"전체 탐지 완료!")
        print(f"{'='*70}")
        print(f"  총 Pattern: {len(patterns)}개")
        print(f"  총 Block1 재탐지: {total_stats['block1_redetections']}개")
        print(f"  총 Block2 재탐지: {total_stats['block2_redetections']}개")
        print(f"  총 Block3 재탐지: {total_stats['block3_redetections']}개")
        print(f"{'='*70}\n")

        return {
            "patterns": patterns,
            "total_patterns": len(patterns),
            "total_stats": total_stats
        }
