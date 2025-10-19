# 다음 세션 작업: Block1/2/3 통합 탐지 시스템 구현

## 📋 현재까지 완료된 작업 (이번 세션)

### ✅ 1. 파라미터 이름 변경 (완료)
**변경된 파라미터 (7개):**
```
rate_threshold                    → entry_surge_rate
ma_period                         → entry_ma_period
deviation_threshold               → max_deviation_ratio
trading_value_threshold           → min_trading_value
volume_months                     → volume_high_months
prev_day_volume_increase_ratio    → volume_spike_ratio
new_high_months                   → price_high_months
```

**업데이트된 파일:**
- ✅ Domain: `Block1Condition` 엔티티
- ✅ Infrastructure: DB 테이블 스키마, Repository
- ✅ Application: UseCase, Checker, Calculator
- ✅ Scripts: 모든 테스트 스크립트
- ✅ Documentation: `BLOCK_DETECTION.md`

**결과:**
- 총 147개 변경 완료
- DB 테이블 재생성 완료
- 프리셋 재저장 완료
- 탐지 테스트 성공

### ✅ 2. Custom 프리셋 최적화 (완료)
**변경 사항:**
- `volume_high_months`: 3개월 → **12개월**
- `cooldown_days`: **20일**

**탐지 결과:**
- 7건 탐지
- 평균 수익률: +43.89%
- 최고 수익률: +153.20%

**제거된 탐지:**
- 2021-05-26: +23.60% (12개월 신고거래량 조건 불충족)

### ✅ 3. Block1/2/3 Chain 구조 설계 (완료)

**핵심 개념:**
```
Block1 #1 (2018-03-07)
    └─→ Block2 #1 (2018-05-17)  ← Block1 #1에서 파생
         └─→ Block3 #1 (2018-06-20)  ← Block2 #1에서 파생

Block1 #2 (2018-09-21)
    └─→ Block2: 없음 (조건 불충족)

Block1 #3 (2018-12-11)
    └─→ Block2 #2 (2019-01-23)  ← Block1 #3에서 파생
         └─→ Block3: 없음
```

**데이터 관계:**
- Block2 → Block1: `prev_block1_id` 외래키
- Block3 → Block2: `prev_block2_id` 외래키
- 각 Block1은 독립적인 Chain의 시작점

**핵심 로직:**
- Block2 시작 시 → Block1 종료일 자동 조정
- Block3 시작 시 → Block2 종료일 자동 조정
- 중첩 루프로 실시간 통합 탐지

---

## 🚀 다음 세션 작업 내용

### Phase 1: DetectBlocksIntegratedUseCase 구현

**파일:** `src/application/use_cases/detect_blocks_integrated.py`

**구현 내용:**
```python
class DetectBlocksIntegratedUseCase:
    """Block1/2/3 통합 탐지 UseCase (Chain 구조)"""

    def __init__(self,
                 block1_repo,
                 block2_repo,
                 block3_repo,
                 block1_checker,
                 block2_checker,
                 block3_checker):
        self.block1_repo = block1_repo
        self.block2_repo = block2_repo
        self.block3_repo = block3_repo
        self.block1_checker = block1_checker
        self.block2_checker = block2_checker
        self.block3_checker = block3_checker

    def execute(self,
                block1_condition,
                block2_condition,
                block3_condition,
                stocks):
        """
        Block1/2/3 통합 탐지 (Chain 구조)

        Returns:
            (block1_list, block2_list, block3_list)
        """
        return self._detect_all_blocks(...)

    def _detect_all_blocks(self, ...):
        """메인 탐지 로직 - 중첩된 루프"""
        block1_list = []
        block2_list = []
        block3_list = []

        for i, stock in enumerate(stocks):
            # Block1 진입 조건
            if self._check_block1_entry(stock, i, stocks, cond1):

                # Block1 생성
                block1 = self._create_block1(stock, cond1)

                # Block1 기간 동안 Block2 모니터링 (중첩 루프 1)
                for j in range(i+1, len(stocks)):
                    future = stocks[j]

                    # Block2 조건 체크 (우선순위!)
                    if self._check_block2_entry(future, j, stocks, block1, cond2):
                        # Block2 생성
                        block2 = self._create_block2(future, block1, cond2)

                        # ⚠️ Block1 종료일 조정!
                        block1.ended_at = future.date - timedelta(days=1)
                        block1.exit_reason = "block2_started"

                        # Block2 기간 동안 Block3 모니터링 (중첩 루프 2)
                        for k in range(j+1, len(stocks)):
                            future2 = stocks[k]

                            # Block3 조건 체크
                            if self._check_block3_entry(future2, k, stocks, block2, cond3):
                                # Block3 생성
                                block3 = self._create_block3(future2, block2, cond3)

                                # ⚠️ Block2 종료일 조정!
                                block2.ended_at = future2.date - timedelta(days=1)
                                block2.exit_reason = "block3_started"

                                # Block3 종료 조건 모니터링
                                # ... (구현 필요)

                                block3_list.append(block3)
                                break

                            # Block2 종료 조건
                            if self._check_block2_exit(future2, k, stocks, block2, cond2):
                                block2.ended_at = future2.date
                                # ...
                                break

                        block2_list.append(block2)
                        break

                    # Block1 종료 조건
                    if self._check_block1_exit(future, j, stocks, block1, cond1):
                        block1.ended_at = future.date
                        # ...
                        break

                block1_list.append(block1)

        return block1_list, block2_list, block3_list
```

**구현해야 할 메서드:**
1. `_check_block1_entry()` - Block1 진입 조건 체크
2. `_check_block1_exit()` - Block1 종료 조건 체크
3. `_check_block2_entry()` - Block2 진입 조건 체크 (Block1 조건 + 추가)
4. `_check_block2_exit()` - Block2 종료 조건 체크
5. `_check_block3_entry()` - Block3 진입 조건 체크 (Block2 조건 + 추가)
6. `_check_block3_exit()` - Block3 종료 조건 체크
7. `_create_block1()` - Block1 엔티티 생성
8. `_create_block2()` - Block2 엔티티 생성 (prev_block1_id 설정)
9. `_create_block3()` - Block3 엔티티 생성 (prev_block2_id 설정)

### Phase 2: 실행 스크립트 작성

**파일:** `detect_all_blocks.py`

```python
"""
Block1/2/3 통합 탐지 스크립트
"""
from src.application.use_cases.detect_blocks_integrated import DetectBlocksIntegratedUseCase
from src.infrastructure.repositories.block1_condition_preset_repository import Block1ConditionPresetRepository
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.block2_repository import Block2Repository
from src.infrastructure.repositories.block3_repository import Block3Repository
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.database.connection import DatabaseConnection
from src.domain.entities.block2_condition import Block2Condition
from src.domain.entities.block3_condition import Block3Condition
from datetime import date

def main():
    # 1. DB 연결
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    # 2. Repository 초기화
    preset_repo = Block1ConditionPresetRepository(db_conn)
    stock_repo = SqliteStockRepository(db_path)
    block1_repo = Block1Repository(db_conn)
    block2_repo = Block2Repository(db_conn)
    block3_repo = Block3Repository(db_conn)

    # 3. 조건 로드
    block1_cond = preset_repo.load("custom")

    # Block2 조건 (임시 - 기본값)
    block2_cond = Block2Condition(
        block1_condition=block1_cond,
        block_volume_ratio=15.0,  # 블록1 최고 거래량의 15%
        low_price_margin=10.0,    # 저가 10% 마진
        cooldown_days=20,
        min_candles_after_block1=4
    )

    # Block3 조건 (임시 - 기본값)
    block3_cond = Block3Condition(
        block2_condition=block2_cond,
        # ... (Block3 추가 조건)
    )

    # 4. 주가 데이터 로드
    ticker = "025980"
    start_date = date(2015, 1, 2)
    end_date = date(2025, 10, 17)
    stocks = stock_repo.get_stock_data(ticker, start_date, end_date)

    print(f"주가 데이터: {len(stocks)}건 ({stocks[0].date} ~ {stocks[-1].date})")
    print()

    # 5. 통합 탐지 실행
    use_case = DetectBlocksIntegratedUseCase(
        block1_repo, block2_repo, block3_repo,
        # ... (Checker 인스턴스)
    )

    block1_list, block2_list, block3_list = use_case.execute(
        block1_cond, block2_cond, block3_cond, stocks
    )

    # 6. 결과 출력
    print("="*70)
    print("통합 탐지 결과")
    print("="*70)
    print(f"Block1: {len(block1_list)}건")
    print(f"Block2: {len(block2_list)}건")
    print(f"Block3: {len(block3_list)}건")
    print()

    # Chain 출력
    for block1 in block1_list:
        print(f"Block1 #{block1.id}: {block1.started_at} ~ {block1.ended_at}")
        print(f"  수익률: +{block1.peak_gain_ratio:.2f}%")
        print(f"  종료: {block1.exit_reason}")

        # 연결된 Block2 찾기
        block2 = next((b for b in block2_list if b.prev_block1_id == block1.id), None)
        if block2:
            print(f"  └─ Block2: {block2.started_at} ~ {block2.ended_at}")

            # 연결된 Block3 찾기
            block3 = next((b for b in block3_list if b.prev_block2_id == block2.id), None)
            if block3:
                print(f"     └─ Block3: {block3.started_at} ~ {block3.ended_at}")
        print()

if __name__ == "__main__":
    main()
```

### Phase 3: 테스트 및 검증

**1. 데이터 초기화:**
```python
# 기존 탐지 데이터 모두 삭제
DELETE FROM block1_detection WHERE ticker = '025980';
DELETE FROM block2_detection WHERE ticker = '025980';
DELETE FROM block3_detection WHERE ticker = '025980';
```

**2. 통합 탐지 실행:**
```bash
python detect_all_blocks.py
```

**3. 검증 사항:**
- [ ] Block1 종료일이 Block2 시작으로 조정되었는지
- [ ] Block2의 `prev_block1_id`가 올바르게 설정되었는지
- [ ] Block3의 `prev_block2_id`가 올바르게 설정되었는지
- [ ] Chain 관계가 정확한지
- [ ] 종료 사유가 올바른지

### Phase 4: 결과 분석

**예상 결과:**
```
Before (Block1만):
- Block1: 7건
- Block2: 0건
- Block3: 0건

After (통합 탐지):
- Block1: 7건 (일부 종료일 조정됨)
- Block2: 2~4건 예상
- Block3: 0~2건 예상

Chain 예시:
Block1 #1: 2018-03-07 ~ 2018-05-16 (block2_started)
  └─ Block2 #1: 2018-05-17 ~ 2018-06-19
       └─ Block3 #1: 2018-06-20 ~ 2018-06-28
```

---

## 📚 참고 파일

**기존 UseCase:**
- `src/application/use_cases/detect_block1.py` - 로직 참조
- `src/application/use_cases/detect_block2.py` - 로직 참조
- `src/application/use_cases/detect_block3.py` - 로직 참조

**조건 엔티티:**
- `src/domain/entities/block1_condition.py`
- `src/domain/entities/block2_condition.py`
- `src/domain/entities/block3_condition.py`

**Checker 서비스:**
- `src/application/services/block1_checker.py`
- `src/application/services/block2_checker.py`
- `src/application/services/block3_checker.py`

**Repository:**
- `src/infrastructure/repositories/block1_repository.py`
- `src/infrastructure/repositories/block2_repository.py`
- `src/infrastructure/repositories/block3_repository.py`

---

## ⚠️ 주의사항

1. **Block2/3 조건 엔티티 확인**
   - `Block2Condition`, `Block3Condition` 완성 여부
   - 추가 조건 파라미터 확인

2. **성능 고려**
   - 중첩 루프 = O(n²) 또는 O(n³)
   - 10년 데이터(2,637건)는 괜찮음
   - 전체 종목 탐지 시 최적화 필요

3. **DB 외래키 제약**
   - `block2_detection.prev_block1_id` FOREIGN KEY
   - `block3_detection.prev_block2_id` FOREIGN KEY
   - CASCADE 설정 확인

4. **Cooldown 처리**
   - Block1 Cooldown은 기존 로직 유지
   - Block2/3 Cooldown 별도 처리 필요 여부 검토

---

## 💡 구현 팁

### 1. 단계적 구현
```
Step 1: Block1 → Block2 통합 탐지만 먼저 구현
Step 2: 테스트 및 검증
Step 3: Block3 추가
Step 4: 전체 테스트
```

### 2. 디버깅
```python
# 로깅 추가
print(f"[DEBUG] Block1 진입: {stock.date}")
print(f"[DEBUG] Block2 조건 체크: {future.date}")
print(f"[DEBUG] Block1 종료일 조정: {block1.ended_at}")
```

### 3. 기존 코드 재사용
- `detect_block1.py`의 조건 체크 로직 복사
- `block1_checker.py`의 메서드 활용
- 종료 조건 판단 로직 재사용

---

## 🎯 최종 목표

**아난티 Block 탐지 결과:**
```
Block1 #1 (2018-03-07) +103.85%
  └─ Block2 #1 (2018-05-17) +50%
       └─ Block3 #1 (2018-06-20) +20%

Block1 #2 (2018-09-21) +8.14%
  └─ Block2: 없음

Block1 #3 (2018-12-11) +153.20%
  └─ Block2 #2 (2019-01-23) +30%
       └─ Block3: 없음
```

**각 Block1마다 Chain이 연결되어 전체 캠페인을 추적할 수 있어야 함!**

---

다음 세션에서 계속 진행하세요! 🚀
