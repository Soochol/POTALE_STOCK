# Block Condition Refactoring - Remaining Tasks

## 완료된 작업 ✅

### Phase 1: Entity Refactoring (Commit: 5a03c8d)
- ✅ Block2Condition: block1_condition 필드 제거, Block1의 모든 필드를 독립적으로 추가
- ✅ Block3Condition: block2_condition 필드 제거, Block1+Block2의 모든 필드를 독립적으로 추가
- ✅ Block4Condition: block3_condition 필드 제거, Block1+Block2+Block3의 모든 필드를 독립적으로 추가
- ✅ 각 엔티티의 validate() 및 __repr__() 메서드 업데이트

### Phase 2: Checker Refactoring (Commit: 6b9d0d5)
- ✅ Block2Checker.check_entry(): Block1 조건 검사 로직 인라인화
- ✅ Block2Checker.check_exit(): Block1Condition 임시 생성 방식으로 변경
- ✅ Block3Checker.check_entry(): Block1+Block2 조건 검사 로직 인라인화
- ✅ Block3Checker.check_exit(): Block1Condition 임시 생성 방식으로 변경
- ✅ Block4Checker.check_entry(): Block1+Block2+Block3 조건 검사 로직 인라인화
- ✅ Block4Checker.check_exit(): Block1Condition 임시 생성 방식으로 변경

## 남은 작업 ⏳

### Phase 3: PatternSeedDetector Refactoring
**파일:** `src/application/services/pattern_seed_detector.py`

#### 수정 필요 위치:

**1. find_first_block2_after_block1() - 라인 ~150**
```python
# 현재 (잘못됨):
block2_condition = Block2Condition(
    block1_condition=block1_condition,  # ❌ 더 이상 존재하지 않음
    block2_volume_ratio=condition.block2_volume_ratio,
    ...
)

# 수정해야 함:
block2_condition = Block2Condition(
    # Block1 기본 조건
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
    cooldown_days=condition.cooldown_days,
    # Block2 추가 조건
    block2_volume_ratio=condition.block2_volume_ratio,
    block2_low_price_margin=condition.block2_low_price_margin,
    block2_min_candles_after_block1=condition.block2_min_candles_after_block1
)
```

**2. find_first_block3_after_block2() - 라인 ~230**
```python
# Block2Condition 생성 부분 (위와 동일)
# Block3Condition 생성 부분도 유사하게 수정 필요
block3_condition = Block3Condition(
    # Block1 기본 조건 (11개 필드)
    entry_surge_rate=condition.entry_surge_rate,
    ...
    # Block2 추가 조건 (3개 필드)
    block2_volume_ratio=condition.block2_volume_ratio,
    ...
    # Block3 추가 조건 (3개 필드)
    block3_volume_ratio=condition.block3_volume_ratio,
    ...
)
```

**3. find_first_block4_after_block3() - 라인 ~315**
```python
# Block2/3/4Condition 생성 부분 모두 수정 필요
# Block4Condition은 총 11 + 3 + 3 + 3 = 20개 필드 필요
```

### Phase 4: PatternRedetector Refactoring
**파일:** `src/application/services/pattern_redetector.py`

#### 수정 필요 위치:

**1. redetect_block2() - 라인 ~170**
- Block2Condition 생성 부분 (PatternSeedDetector와 동일한 패턴)

**2. redetect_block3() - 라인 ~280**
- Block2Condition 생성 부분
- Block3Condition 생성 부분

**3. redetect_block4() - 라인 ~400**
- Block2Condition 생성 부분
- Block3Condition 생성 부분
- Block4Condition 생성 부분

## 작업 예상 시간
- PatternSeedDetector: 30-40분 (3개 메서드, 각 메서드당 2-3개 BlockNCondition 생성)
- PatternRedetector: 30-40분 (3개 메서드, 각 메서드당 2-4개 BlockNCondition 생성)
- **총 예상: 1-1.5시간**

## 리팩토링의 의미

### Before (문제점):
```python
# Block1의 조건 값이 Block2/3/4에 강제로 상속됨
Block1: entry_surge_rate=8%, exit_ma_period=60
Block2: entry_surge_rate=8%, exit_ma_period=60  # ❌ Block1과 동일하게 강제됨
Block3: entry_surge_rate=8%, exit_ma_period=60  # ❌ Block1과 동일하게 강제됨
Block4: entry_surge_rate=8%, exit_ma_period=60  # ❌ Block1과 동일하게 강제됨
```

### After (해결):
```python
# 각 블록이 독립적인 조건 값을 가질 수 있음
Block1: entry_surge_rate=8%, exit_ma_period=60
Block2: entry_surge_rate=5%, exit_ma_period=20  # ✅ 다른 값 사용 가능!
Block3: entry_surge_rate=3%, exit_ma_period=10  # ✅ 다른 값 사용 가능!
Block4: entry_surge_rate=2%, exit_ma_period=5   # ✅ 다른 값 사용 가능!
```

## 테스트 계획
리팩토링 완료 후:
1. 기존 테스트 스크립트 실행하여 동작 확인
2. 블록별 다른 조건값을 가진 새 프리셋 생성하여 테스트
3. Seed/Redetection 전체 플로우 테스트

## 참고 커밋
- `5a03c8d`: Block2/3/4Condition 엔티티 리팩토링
- `6b9d0d5`: Block2/3/4Checker 리팩토링
- 다음 세션: PatternSeedDetector 및 PatternRedetector 리팩토링 완료
