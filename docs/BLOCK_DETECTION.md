# 블록 탐지 시스템 (Block1, Block2, Block3)

블록 탐지 시스템은 특정 기술적 조건을 만족하는 주가 패턴을 자동으로 탐지하는 시스템입니다.

블록1 → 블록2 → 블록3로 연속되는 패턴을 탐지하며, 각 블록은 독립적으로도 탐지 가능합니다.

## 📋 목차

1. [개요](#개요)
2. [블록 간 관계](#블록-간-관계)
3. [블록1 조건](#블록1-조건)
4. [블록2 조건](#블록2-조건)
5. [블록3 조건](#블록3-조건)
6. [패턴 재탐지 시스템](#패턴-재탐지-시스템)
7. [아키텍처](#아키텍처)
8. [사용 방법](#사용-방법)
9. [API 레퍼런스](#api-레퍼런스)

---

## 개요

### 블록 시스템이란?

- **블록1**: 초기 상승 모멘텀 포착
- **블록2**: 블록1 이후 추가 상승 신호
- **블록3**: 블록2 이후 최종 상승 신호

각 블록은:
- **독립적 탐지 가능**: 블록1 없이도 블록2/3 탐지 가능
- **연속적 관계**: 블록2 시작 시 블록1은 전날 종료, 블록3 시작 시 블록2는 전날 종료
- **누적 조건**: 블록2는 블록1 조건 + 추가 조건, 블록3은 블록2 조건 + 추가 조건

### 활용 사례

- 급등주 포착 및 추세 지속성 판단
- 이동평균선 돌파 후 추가 상승 확인
- 거래량 급증 패턴의 연속성 분석
- 단계별 매매 신호 생성

---

## 블록 간 관계

### 🔗 블록 전환 메커니즘

```
블록1 진행 중
    ↓
블록2 진입 조건 만족
    ↓
블록1 종료 (블록2 시작 전날)
    ↓
블록2 시작
    ↓
블록3 진입 조건 만족
    ↓
블록2 종료 (블록3 시작 전날)
    ↓
블록3 시작
    ↓
종료 조건 만족
    ↓
블록3 종료
```

### 📊 독립 탐지 vs 연속 탐지

**독립 탐지 (블록1/2/3 각각 별도로 시작 가능):**
```
날짜: 2024-01-10
조건: 블록2 조건 만족
결과: 블록2 시작 (블록1 없어도 OK)
추가 조건: 직전 블록1 찾아서 최고 거래량/가격 기준 적용
          직전 블록1 없으면 해당 조건 무시
```

**연속 탐지 (블록1 → 블록2 → 블록3):**
```
날짜: 2024-01-10, 블록1 진행 중
날짜: 2024-01-15, 블록2 진입 조건 만족
결과:
  - 블록1.ended_at = 2024-01-14 (블록2 시작 전날)
  - 블록2.started_at = 2024-01-15
  - 블록2의 "직전 블록1" = 방금 종료된 블록1
```

---

## 블록1 조건

### 🚀 진입 조건

블록1은 다음 조건들을 **모두(AND)** 만족해야 시작됩니다.

#### 1. 등락률 조건
- **설명**: 전일종가 대비 당일고가 등락률 N% 이상
- **파라미터**: `entry_surge_rate`
- **계산식**: `(고가 - 전일종가) / 전일종가 × 100 >= N`
- **예시**: `entry_surge_rate=8.0` → 고가 기준 8% 이상 상승
- **의미**: 당일 고가 기준으로 강한 상승 포착

#### 2. 이평선 조건 A: 고가 위치 (필수)
- **설명**: 당일 고가가 이동평균선 N 이상
- **파라미터**: `entry_ma_period`, `high_above_ma=True`
- **계산식**: `고가 >= MA_N`
- **예시**: `entry_ma_period=120, high_above_ma=True` → 고가가 MA120 이상
- **의미**: 장기 추세선 돌파 확인

#### 3. 이평선 조건 B: 이격도 (필수)
- **설명**: 이동평균선을 100으로 봤을 때 종가 비율
- **파라미터**: `entry_ma_period`, `max_deviation_ratio`
- **계산식**: `(종가 / MA_N) × 100 <= M`
- **예시**:
  - MA120 = 5,000원, 종가 = 6,000원 → 이격도 = 120
  - `max_deviation_ratio=120` → 이격도 120 이하 (MA의 120% 이하)
- **의미**: 과열 방지 (MA에서 너무 멀리 떨어지지 않음)

#### 4. 거래대금 조건
- **설명**: 거래대금 N억 이상
- **파라미터**: `min_trading_value` (단위: 억)
- **계산식**: `종가 × 거래량 >= N × 100,000,000`
- **예시**: `min_trading_value=300.0` → 300억 이상
- **의미**: 대형 자금 유입 확인

#### 5. 거래량 조건
- **설명**: N개월 신고거래량 (최근 N개월 중 최대)
- **파라미터**: `volume_high_months`
- **계산식**: `당일거래량 >= max(최근_N개월_거래량)`
- **예시**: `volume_high_months=24` → 최근 24개월(2년) 최고 거래량
- **의미**: 장기 거래량 돌파 확인

#### 6. 전날 거래량 조건
- **설명**: 전일 거래량 대비 N% 수준
- **파라미터**: `volume_spike_ratio` (단위: %)
- **계산식**: `당일_거래량 >= 전날_거래량 × (N/100)`
- **예시**:
  - `volume_spike_ratio=400` → 전날 대비 400% (4배)
  - `volume_spike_ratio=300` → 전날 대비 300% (3배)
  - `volume_spike_ratio=200` → 전날 대비 200% (2배)
- **의미**: 단기 거래량 급증 포착
- **권장값**: `400` (400%, 4배)

#### 7. 신고가 조건

- **설명**: 당일 고가가 N개월 신고가인지 확인
- **파라미터**: `price_high_months` (단위: 개월)
- **계산식**: `당일_고가 >= max(과거_N개월_고가)`
- **예시**:
  - `price_high_months=2` → 2개월(60일) 신고가
  - `price_high_months=6` → 6개월(180일) 신고가
  - `price_high_months=12` → 12개월(365일) 신고가
- **의미**: 중장기 가격 돌파 확인
- **기본값**: `2` (2개월 신고가, 필수)
- **계산 기준**: 정확한 달력 기준 (N개월 = N × 30일)
- **과거 데이터**: 과거 N개월 기간의 모든 고가 중 최댓값과 비교

---

### 🛑 종료 조건

블록1은 다음 조건 중 **택1**로 종료됩니다.

#### 1. 이동평균선 이탈 (`MA_BREAK`)
- **설명**: 종가가 종료용 이동평균선 아래로 하락
- **조건**: `종가 < exit_ma_period (예: MA60)`
- **의미**: 중기 추세 이탈

#### 2. 삼선전환도 첫 음봉 (`THREE_LINE_REVERSAL`)
- **설명**: 삼선전환도(Three Line Break)에서 처음 음봉 발생
- **알고리즘**: 3선 전환 차트 기법
- **조건**: 양봉 연속 후 첫 음봉 출현
- **의미**: 추세 반전 신호

#### 3. 캔들 몸통 중간 가격 이탈 (`BODY_MIDDLE`)
- **설명**: 블록1 발생일 캔들 몸통 중간 가격 이하로 하락
- **조건**: `종가 < (블록1_시가 + 블록1_종가) / 2`
- **의미**: 진입일 가격 지지 상실

#### 4. 블록2 시작 조건 만족 (자동)
- **설명**: 블록2 진입 조건이 만족되면 블록1은 자동 종료
- **조건**: 블록2 시작일 전날로 `ended_at` 설정
- **의미**: 다음 단계로 전환

---

### 🔒 중복 방지

- **파라미터**: `cooldown_days` (기본값: 120일)
- **규칙**:
  - 블록1 시작일 기준 120일 동안 새 블록1 탐지 불가
  - cooldown 기간 경과 후 새 블록1 탐지 가능

---

## 블록2 조건

블록2는 블록1보다 **더 강한 상승 신호**를 포착합니다.

### 🚀 진입 조건

블록2는 **블록1의 모든 조건 + 추가 조건**을 만족해야 시작됩니다.

#### 기본 조건 (블록1과 동일)
1. 등락률 조건
2. 이평선 조건 A: 고가 위치 (필수)
3. 이평선 조건 B: 이격도 (필수)
4. 거래대금 조건
5. 거래량 조건
6. 전날 거래량 조건

#### 블록2 추가 조건

##### 7. 직전 블록1 최고 거래량 조건
- **설명**: 직전 블록1 기간 중 최고 거래량 대비 N%
- **파라미터**: `block_volume_ratio` (단위: %)
- **계산식**: `당일_거래량 >= 블록1_최고_거래량 × (N/100)`
- **예시**:
  - 블록1 최고 거래량 = 200만주
  - `block_volume_ratio=15` → 당일 거래량 >= 30만주 (15%)
  - `block_volume_ratio=20` → 당일 거래량 >= 40만주 (20%)
- **의미**: 블록1 대비 상당한 거래량 유지
- **기본값**: `15` (15%)
- **직전 블록1 찾기**: 당일 기준 가장 최근에 종료된 블록1
- **블록1 없으면**: 이 조건 무시

##### 8. 직전 블록1 최고가 조건
- **설명**: 직전 블록1 최고가 대비 저가 수준 확인
- **파라미터**: `low_price_margin` (단위: %)
- **계산식**: `당일_저가 × (1 + N/100) > 블록1_peak_price`
- **예시**:
  - 블록1 최고가 = 10,000원
  - `low_price_margin=10` (10%)
  - 당일 저가 = 9,100원
  - 계산: 9,100 × 1.1 = 10,010원 > 10,000원 → **만족** ✅
- **역계산**: 최고가 대비 약 9% 하락까지 허용 (1/1.1 ≈ 0.909)
- **의미**: 최고가에서 일정 수준 이상 하락 시 블록 전환
- **기본값**: `10` (10%)
- **블록1 없으면**: 이 조건 무시

##### 9. 블록1 시작 후 최소 캔들 수 조건

- **설명**: 블록1 시작일부터 현재일까지의 캔들 수 확인
- **파라미터**: `min_candles_after_block1` (단위: 캔들 수)
- **계산식**: `블록1_시작일부터_현재일까지_캔들_수 > min_candles_after_block1`
- **예시**:
  - 블록1 시작일: 2024-01-01 (1번째 캔들)
  - `min_candles_after_block1=4`
  - 2024-01-02 (2번째 캔들), 2024-01-03 (3번째 캔들), 2024-01-04 (4번째 캔들)
  - 2024-01-05 (5번째 캔들) ← **여기서부터 블록2 탐지 가능** ✅
- **의미**: 블록1에서 블록2로 전환되기 위한 최소 대기 기간
- **기본값**: `4` (5번째 캔들부터 가능)
- **캔들 수 계산**: 실제 거래일 기준 (주말/공휴일 제외)
- **블록1 없으면**: 이 조건 무시

---

### 🛑 종료 조건

블록2는 **블록1과 동일한 종료 조건** + 블록3 전환:

1. MA_BREAK / THREE_LINE_REVERSAL / BODY_MIDDLE 중 택1
2. **블록3 시작 조건 만족 시** → 블록3 시작 전날로 종료

---

### 🚫 중복 방지

블록2도 블록1과 동일한 중복 방지 기간이 적용됩니다:

- **파라미터**: `cooldown_days` (기본값: 120일)
- **규칙 1**: 활성 블록2가 있으면 신규 탐지 불가
- **규칙 2**: 블록2 시작일 이후 N일까지 신규 탐지 불가 (종료 여부 무관)

**예시**:

- 2024-01-01 블록2 시작
- cooldown_days=120
- 2024-01-15 블록2 종료
- → 2024-04-30까지 신규 블록2 탐지 불가
- → 2024-05-01부터 신규 블록2 탐지 가능

---

## 블록3 조건

블록3은 블록2보다 **더 강한 상승 신호**를 포착합니다 (최종 단계).

### 🚀 진입 조건

블록3은 **블록2의 모든 조건 + 추가 조건**을 만족해야 시작됩니다.

#### 기본 조건 (블록2와 동일)
1~6: 블록1/2와 동일

#### 블록3 추가 조건

##### 7. 직전 블록2 최고 거래량 조건
- **설명**: 직전 블록2 기간 중 최고 거래량 대비 N%
- **파라미터**: `block_volume_ratio` (단위: %)
- **계산식**: `당일_거래량 >= 블록2_최고_거래량 × (N/100)`
- **기본값**: `15` (15%)
- **직전 블록2 찾기**: 당일 기준 가장 최근에 종료된 블록2
- **블록2 없으면**: 이 조건 무시

##### 8. 직전 블록2 최고가 조건
- **설명**: 직전 블록2 최고가 대비 저가 수준 확인
- **파라미터**: `low_price_margin` (단위: %)
- **계산식**: `당일_저가 × (1 + N/100) > 블록2_peak_price`
- **기본값**: `10` (10%)
- **블록2 없으면**: 이 조건 무시

##### 9. 블록2 시작 후 최소 캔들 수 조건

- **설명**: 블록2 시작일부터 현재일까지의 캔들 수 확인
- **파라미터**: `min_candles_after_block2` (단위: 캔들 수)
- **계산식**: `블록2_시작일부터_현재일까지_캔들_수 > min_candles_after_block2`
- **예시**:
  - 블록2 시작일: 2024-02-01 (1번째 캔들)
  - `min_candles_after_block2=4`
  - 2024-02-02 (2번째 캔들), 2024-02-03 (3번째 캔들), 2024-02-04 (4번째 캔들)
  - 2024-02-05 (5번째 캔들) ← **여기서부터 블록3 탐지 가능** ✅
- **의미**: 블록2에서 블록3으로 전환되기 위한 최소 대기 기간
- **기본값**: `4` (5번째 캔들부터 가능)
- **캔들 수 계산**: 실제 거래일 기준 (주말/공휴일 제외)
- **블록2 없으면**: 이 조건 무시

---

### 🛑 종료 조건

블록3은 **블록2와 동일한 종료 조건**:

1. MA_BREAK / THREE_LINE_REVERSAL / BODY_MIDDLE 중 택1
2. (블록4 없음)

---

## 패턴 재탐지 시스템

### 📌 개요

패턴 재탐지 시스템은 **Seed 탐지 → 5년 재탐지**의 2단계 프로세스로 유사한 패턴을 반복적으로 찾아냅니다.

**핵심 개념:**
- **Seed (시드)**: 엄격한 조건으로 찾은 최초 패턴 (Block1 #1 → Block2 #1 → Block3 #1)
- **Re-detection (재탐지)**: Seed를 기준으로 5년간 유사 패턴 탐지 (완화된 조건 + 가격 범위 필터)
- **Pattern (패턴)**: 각 Block1 Seed를 기준으로 한 독립적인 탐지 단위

---

### 🔄 3단계 프로세스

#### Step 1: 모든 Block1 Seed 탐지

전체 데이터 범위에서 Block1 조건을 만족하는 모든 Seed를 찾습니다.

```python
# 조건
- Block1 기본 조건 (엄격한 Seed 조건)
- Cooldown: 20일 (이전 Seed와 최소 20일 간격)
- 이전 Block1 진행 중이어도 탐지 가능 (겹침 허용)

# 결과 예시
Block1 #1: 2018-03-07, 고점 12,700원
Block1 #2: 2018-09-21, 고점 11,000원  (6개월 후)
Block1 #3: 2019-05-10, 고점 13,500원  (8개월 후)
```

---

#### Step 2: 각 Block1 Seed마다 Pattern 생성

각 Block1 Seed를 기준으로 **독립적인 Pattern**을 생성합니다.

##### 2-1. Block2 Seed 탐지
```python
# Block1 종료일 이후부터 검색
# Block2 조건 만족하는 첫 번째 → Block2 Seed

Pattern #1:
  Block1 #1: 2018-03-07 ~ 2018-06-14
  Block2 #1: 2018-06-15 발견 (첫 번째만!)
```

##### 2-2. Block3 Seed 탐지
```python
# Block2 종료일 이후부터 검색
# Block3 조건 만족하는 첫 번째 → Block3 Seed

Pattern #1:
  Block1 #1: 2018-03-07, 고점 12,700원
  Block2 #1: 2018-06-15, 고점 15,200원
  Block3 #1: 2018-09-20, 고점 18,500원
```

##### 2-3. Seed 완성 → DB 저장
```python
# BlockPattern 테이블에 저장
BlockPattern(
    pattern_id=1,
    ticker="025980",
    seed_block1_id="uuid-123",
    seed_block2_id="uuid-456",
    seed_block3_id="uuid-789",
    redetection_start=date(2018, 3, 7),
    redetection_end=date(2023, 3, 7)
)

# 각 Seed를 detection_type="seed"로 저장
Block1Detection(pattern_id=1, detection_type="seed", ...)
Block2Detection(pattern_id=1, detection_type="seed", ...)
Block3Detection(pattern_id=1, detection_type="seed", ...)
```

##### 2-4. 5년 재탐지
```python
# 재탐지 기간: Block1 Seed 시작일 ~ +5년
# 2018-03-07 ~ 2023-03-07

매일 스캔하여:
  - Block1 재탐지 (Block1 #1 기준 ±10%)
  - Block2 재탐지 (Block2 #1 기준 ±15%)
  - Block3 재탐지 (Block3 #1 기준 ±20%)

각 재탐지마다 Cooldown 20일 적용
```

---

#### Step 3: 다음 Block1 Seed로 반복

Block1 #2, #3... 각각에 대해 **Step 2를 완전히 반복**합니다.

```python
Pattern #2 (Block1 #2 기준):
  Block1 #2: 2018-09-21, 고점 11,000원
  Block2 #2: 2019-01-15, 고점 13,000원
  Block3 #2: 2019-04-10, 고점 16,800원
  재탐지 기간: 2018-09-21 ~ 2023-09-21

Pattern #3 (Block1 #3 기준):
  Block1 #3: 2019-05-10, 고점 13,500원
  Block2 #3: 2019-08-25, 고점 16,200원
  Block3 #3: 찾지 못함 → Pattern #3 종료
```

---

### 🎯 재탐지 조건 상세

재탐지는 **Seed 조건 + 가격 범위 필터**를 사용합니다.

#### Block1 재탐지

```python
조건 = (
    # 가격 범위: Seed Block1 기준 ±10%
    seed_block1.peak_price × 0.9 <= 당일_고점 <= seed_block1.peak_price × 1.1

    AND

    # Block1 기본 조건 (완화된 재탐지 조건)
    entry_surge_rate >= 5%  # Seed: 8% → 재탐지: 5%
    volume_high_months >= 6  # Seed: 12개월 → 재탐지: 6개월
    ...

    AND

    # Cooldown: 이전 재탐지와 20일 이상 차이
    days_since_last_redetection >= 20
)

예시 - Pattern #1의 Block1 재탐지:
  Seed Block1 #1 고점: 12,700원
  재탐지 가격 범위: 11,430원 ~ 13,970원 (±10%)

  2019-05-10: 고점 12,500원 → ✅ 조건 만족 → Block1 재탐지 #1
  2019-05-15: 고점 12,800원 → ❌ Cooldown (5일 < 20일)
  2019-06-05: 고점 13,200원 → ✅ 조건 만족 → Block1 재탐지 #2
```

---

#### Block2 재탐지

```python
조건 = (
    # 가격 범위: Seed Block2 기준 ±15%
    seed_block2.peak_price × 0.85 <= 당일_고점 <= seed_block2.peak_price × 1.15

    AND

    # 저가 마진: Seed Block1 초과 (Pattern의 Block1 Seed 참조!)
    당일_저점 × 1.1 > seed_block1.peak_price

    AND

    # Block2 기본 조건 (완화된 재탐지 조건)
    entry_surge_rate >= 5%
    volume_high_months >= 6
    ...

    AND

    # Cooldown: 20일
    days_since_last_redetection >= 20
)

예시 - Pattern #1의 Block2 재탐지:
  Seed Block1 #1 고점: 12,700원
  Seed Block2 #1 고점: 15,200원
  재탐지 가격 범위: 12,920원 ~ 17,480원 (±15%)

  2020-03-15:
    - 고점 15,500원 → ✅ 가격 범위 OK
    - 저점 13,200원 → 13,200 × 1.1 = 14,520 > 12,700 ✅
    - 기본 조건 만족 ✅
    → Block2 재탐지 #1
```

---

#### Block3 재탐지

```python
조건 = (
    # 가격 범위: Seed Block3 기준 ±20%
    seed_block3.peak_price × 0.8 <= 당일_고점 <= seed_block3.peak_price × 1.2

    AND

    # 저가 마진: Seed Block2 초과 (Pattern의 Block2 Seed 참조!)
    당일_저점 × 1.1 > seed_block2.peak_price

    AND

    # Block3 기본 조건 (완화된 재탐지 조건)
    entry_surge_rate >= 3%
    volume_high_months >= 3
    ...

    AND

    # Cooldown: 20일
    days_since_last_redetection >= 20
)

예시 - Pattern #1의 Block3 재탐지:
  Seed Block2 #1 고점: 15,200원
  Seed Block3 #1 고점: 18,500원
  재탐지 가격 범위: 14,800원 ~ 22,200원 (±20%)

  2021-08-20:
    - 고점 19,200원 → ✅ 가격 범위 OK
    - 저점 16,800원 → 16,800 × 1.1 = 18,480 > 15,200 ✅
    - 기본 조건 만족 ✅
    → Block3 재탐지 #1
```

---

### 🗄️ 데이터베이스 구조

#### BlockPattern 테이블 (신규)

```sql
CREATE TABLE block_pattern (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR(10) NOT NULL,

    -- Seed 참조
    seed_block1_id VARCHAR(50) NOT NULL,
    seed_block2_id VARCHAR(50) NOT NULL,
    seed_block3_id VARCHAR(50) NOT NULL,

    -- 재탐지 기간
    redetection_start DATE NOT NULL,
    redetection_end DATE NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(seed_block1_id) REFERENCES block1_detection(block1_id),
    FOREIGN KEY(seed_block2_id) REFERENCES block2_detection(block2_id),
    FOREIGN KEY(seed_block3_id) REFERENCES block3_detection(block3_id)
);
```

#### Block Detection 테이블 업데이트

기존 `block1_detection`, `block2_detection`, `block3_detection` 테이블에 컬럼 추가:

```sql
ALTER TABLE block1_detection ADD COLUMN pattern_id INTEGER;
ALTER TABLE block1_detection ADD COLUMN detection_type VARCHAR(20);  -- "seed" or "redetection"

ALTER TABLE block2_detection ADD COLUMN pattern_id INTEGER;
ALTER TABLE block2_detection ADD COLUMN detection_type VARCHAR(20);

ALTER TABLE block3_detection ADD COLUMN pattern_id INTEGER;
ALTER TABLE block3_detection ADD COLUMN detection_type VARCHAR(20);
```

#### 저장 예시

```python
# Pattern #1
BlockPattern(
    pattern_id=1,
    ticker="025980",
    seed_block1_id="uuid-block1-1",
    seed_block2_id="uuid-block2-1",
    seed_block3_id="uuid-block3-1",
    redetection_start=date(2018, 3, 7),
    redetection_end=date(2023, 3, 7)
)

# Seed
Block1Detection(
    block1_id="uuid-block1-1",
    pattern_id=1,
    detection_type="seed",
    started_at=date(2018, 3, 7),
    peak_price=12700
)

# 재탐지
Block1Detection(
    block1_id="uuid-redetect-1-1",
    pattern_id=1,
    detection_type="redetection",
    started_at=date(2019, 5, 10),
    peak_price=12500
)

Block1Detection(
    block1_id="uuid-redetect-1-2",
    pattern_id=1,
    detection_type="redetection",
    started_at=date(2019, 6, 5),
    peak_price=13200
)

# Pattern #2 (독립적)
Block1Detection(
    block1_id="uuid-block1-2",
    pattern_id=2,  # 다른 Pattern!
    detection_type="seed",
    started_at=date(2018, 9, 21),
    peak_price=11000
)
```

---

### 📊 조건 프리셋 시스템

재탐지 시스템은 **2가지 조건 세트**를 사용합니다.

#### SeedConditionPreset (엄격)

최초 패턴 발견을 위한 엄격한 조건

```sql
CREATE TABLE seed_condition_preset (
    name VARCHAR(50) PRIMARY KEY,
    description TEXT,

    -- Block1 조건
    entry_surge_rate FLOAT NOT NULL,         -- 8%
    entry_ma_period INTEGER NOT NULL,        -- 120
    volume_high_months INTEGER NOT NULL,     -- 12
    exit_condition_type VARCHAR(50),
    exit_ma_period INTEGER,
    cooldown_days INTEGER DEFAULT 20,
    ...
);
```

```python
# 예시
SeedConditionPreset(
    name="aggressive_seed",
    description="공격적 Seed 탐지",
    entry_surge_rate=8.0,      # 8% 이상
    volume_high_months=12,     # 12개월 최고
    cooldown_days=20
)
```

#### RedetectionConditionPreset (완화)

유사 패턴 재탐지를 위한 완화된 조건 + 가격 범위

```sql
CREATE TABLE redetection_condition_preset (
    name VARCHAR(50) PRIMARY KEY,
    description TEXT,

    -- Block1 조건 (완화)
    entry_surge_rate FLOAT NOT NULL,         -- 5%
    entry_ma_period INTEGER NOT NULL,        -- 120
    volume_high_months INTEGER NOT NULL,     -- 6

    -- 가격 범위 Tolerance
    block1_tolerance_pct FLOAT NOT NULL,   -- 10% (±10%)
    block2_tolerance_pct FLOAT NOT NULL,   -- 15% (±15%)
    block3_tolerance_pct FLOAT NOT NULL,   -- 20% (±20%)

    cooldown_days INTEGER DEFAULT 20,
    ...
);
```

```python
# 예시
RedetectionConditionPreset(
    name="aggressive_redetect",
    description="공격적 재탐지",
    entry_surge_rate=5.0,           # 5% 이상 (완화!)
    volume_high_months=6,           # 6개월 최고 (완화!)
    block1_tolerance_pct=10.0,      # ±10%
    block2_tolerance_pct=15.0,      # ±15%
    block3_tolerance_pct=20.0,      # ±20%
    cooldown_days=20
)
```

---

### 🔍 Pattern 독립성

각 Pattern은 **완전히 독립적**입니다.

#### 시간 겹침 허용

```
Timeline: 2018 -------------------- 2023 ----- 2024

Pattern #1:
├─ Seed: 2018-03-07
└─ 재탐지: 2018-03-07 ~ 2023-03-07
            ├─ 2019-05-10: Block1 재탐지
            ├─ 2020-03-15: Block2 재탐지
            └─ 2021-08-20: Block3 재탐지

Pattern #2:
├─ Seed: 2018-09-21
└─ 재탐지: 2018-09-21 ~ 2023-09-21  ← Pattern #1과 겹침!
            ├─ 2020-01-10: Block1 재탐지
            ├─ 2020-06-20: Block2 재탐지  ← 같은 날에 Pattern #1도 탐지 가능
            └─ 2022-02-15: Block3 재탐지
```

#### 중복 탐지 허용

```python
# 2020-06-20에 두 Pattern 모두에서 탐지 가능
Block2Detection(
    pattern_id=1,
    detection_type="redetection",
    started_at=date(2020, 6, 20),
    peak_price=15500
)

Block2Detection(
    pattern_id=2,
    detection_type="redetection",
    started_at=date(2020, 6, 20),
    peak_price=13200
)

# 같은 날짜지만:
# - Pattern #1은 Block2 #1 (15,200원 ±15%) 기준으로 탐지
# - Pattern #2는 Block2 #2 (13,000원 ±15%) 기준으로 탐지
# → 서로 다른 가격 범위로 독립적 탐지
```

---

### ❓ FAQ

#### Q1. Pattern 독립성
**Q**: Pattern #1과 Pattern #2의 재탐지 기간이 겹쳐도 되나요?

**A**: 네, 완전히 허용됩니다. 각 Pattern은 독립적이며 같은 날짜가 여러 Pattern에서 동시에 탐지될 수 있습니다.

---

#### Q2. Block1 Seed 탐지 방식
**Q**: Block1 #2, #3은 어떻게 찾나요?

**A**: Cooldown 20일만 적용합니다. 이전 Block1이 진행 중이어도 20일만 지나면 새 Seed 탐지 가능합니다.

```python
2018-03-07: Block1 #1 시작
2018-03-27: Cooldown 미달 (20일 미만) → 스킵
2018-04-05: Cooldown 통과 (29일) → Block1 #2 탐지 가능
```

---

#### Q3. 재탐지 참조 대상
**Q**: 재탐지 시 어느 Seed를 참조하나요?

**A**: 항상 **해당 Pattern의 Seed만** 참조합니다.

```python
# Pattern #2의 Block2 재탐지
조건 = (
    # 가격 범위: Pattern #2의 Block2 #2 기준
    13,000 × 0.85 <= 당일_고점 <= 13,000 × 1.15

    AND

    # 저가 마진: Pattern #2의 Block1 #2 기준
    당일_저점 × 1.1 > 11,000
)

# Pattern #1의 Seed (12,700원, 15,200원)는 절대 참조하지 않음!
```

---

#### Q4. Cooldown 적용
**Q**: 재탐지에도 Cooldown을 적용하나요?

**A**: 네, 20일 Cooldown이 적용됩니다.

```python
2019-05-10: Block1 재탐지 #1 ✅
2019-05-14: 조건 만족하지만 스킵 ❌ (4일 < 20일)
2019-05-30: Block1 재탐지 #2 ✅ (20일 경과)
```

---

#### Q5. 가격 Tolerance
**Q**: Block1/2/3의 가격 범위가 다른가요?

**A**: 네, Block이 높아질수록 더 넓은 범위를 허용합니다.

- Block1: ±10%
- Block2: ±15%
- Block3: ±20%

---

#### Q6. 저가 마진 계산
**Q**: 저가 마진은 무엇을 참조하나요?

**A**: 상위 레벨 Seed를 참조합니다.

- Block2 재탐지 → Block1 seed 참조
- Block3 재탐지 → Block2 seed 참조

```python
# Pattern #1
seed_block1.peak_price = 12,700원
seed_block2.peak_price = 15,200원

# Block2 재탐지
당일_저점 × 1.1 > 12,700  # Block1 seed

# Block3 재탐지
당일_저점 × 1.1 > 15,200  # Block2 seed
```

---

### 📈 실행 순서 요약

```python
def detect_all_patterns(ticker, start_date, end_date, seed_cond, redetect_cond):
    """패턴 탐지 전체 프로세스"""

    # Step 1: 모든 Block1 Seed 찾기
    seed_block1_list = find_all_block1_seeds(
        stocks,
        seed_cond,
        cooldown_days=20
    )

    # Step 2: 각 Block1 Seed마다 Pattern 생성
    for seed_block1 in seed_block1_list:

        # 2-1. Block2 Seed (첫 번째만)
        seed_block2 = find_first_block2_after(seed_block1, seed_cond)
        if not seed_block2:
            continue

        # 2-2. Block3 Seed (첫 번째만)
        seed_block3 = find_first_block3_after(seed_block2, seed_cond)
        if not seed_block3:
            continue

        # 2-3. Pattern 생성 및 Seed 저장
        pattern = create_pattern(seed_block1, seed_block2, seed_block3)
        save_pattern(pattern)

        # 2-4. 5년 재탐지
        redetection_period = (
            seed_block1.started_at,
            seed_block1.started_at + timedelta(days=5*365)
        )

        redetect_blocks(
            pattern=pattern,
            seeds=(seed_block1, seed_block2, seed_block3),
            period=redetection_period,
            condition=redetect_cond,
            cooldown_days=20
        )

    return patterns
```

---

### 📚 재탐지 파라미터 레퍼런스

#### Table 1: RedetectionConditionPreset 파라미터

재탐지 조건 프리셋에 사용되는 모든 파라미터입니다.

| 파라미터명 | 타입 | 기본값 | 설명 | 예시 값 |
|-----------|------|--------|------|---------|
| **기본 식별** | | | | |
| `name` | `VARCHAR(50)` | (필수) | 프리셋 이름 (PK) | `"aggressive_redetect"` |
| `description` | `TEXT` | `NULL` | 프리셋 설명 | `"공격적 재탐지 전략"` |
| | | | | |
| **진입 조건 (완화)** | | | | |
| `entry_surge_rate` | `FLOAT` | `5.0` | 전일 대비 고가 등락률 (%) | `5.0` = 5% 이상 |
| `entry_ma_period` | `INTEGER` | `120` | 진입 이동평균선 기간 (일) | `120` = MA120 |
| `high_above_ma` | `BOOLEAN` | `TRUE` | 고가 >= MA 검사 | `TRUE` |
| `max_deviation_ratio` | `FLOAT` | `120.0` | MA 이격도 상한 | `120.0` = MA의 120% 이하 |
| `min_trading_value` | `FLOAT` | `300.0` | 최소 거래대금 (억원) | `300.0` = 300억 이상 |
| `volume_high_months` | `INTEGER` | `6` | 신고거래량 기간 (개월) | `6` = 6개월 최고 |
| `volume_spike_ratio` | `FLOAT` | `300.0` | 전일 대비 거래량 비율 (%) | `300.0` = 3배 |
| `price_high_months` | `INTEGER` | `1` | 신고가 기간 (개월) | `1` = 1개월 신고가 |
| | | | | |
| **재탐지 전용: 가격 범위** | | | | |
| `block1_tolerance_pct` | `FLOAT` | `10.0` | Block1 재탐지 가격 범위 (%) | `10.0` = ±10% |
| `block2_tolerance_pct` | `FLOAT` | `15.0` | Block2 재탐지 가격 범위 (%) | `15.0` = ±15% |
| `block3_tolerance_pct` | `FLOAT` | `20.0` | Block3 재탐지 가격 범위 (%) | `20.0` = ±20% |
| | | | | |
| **종료 조건** | | | | |
| `exit_condition_type` | `VARCHAR(50)` | `"ma_break"` | 종료 조건 타입 | `"ma_break"`, `"three_line_reversal"`, `"body_middle"` |
| `exit_ma_period` | `INTEGER` | `60` | 종료 이동평균선 기간 (일) | `60` = MA60 이탈 시 종료 |
| | | | | |
| **시스템** | | | | |
| `cooldown_days` | `INTEGER` | `20` | 재탐지 간 최소 간격 (일) | `20` = 20일 이상 |
| `created_at` | `DATETIME` | `CURRENT_TIMESTAMP` | 생성 일시 | 자동 설정 |

**비교: Seed vs Redetection 조건**

| 조건 | Seed (엄격) | Redetection (완화) | 차이 |
|------|-------------|-------------------|------|
| `entry_surge_rate` | `8.0%` | `5.0%` | -3% (완화) |
| `volume_high_months` | `12개월` | `6개월` | -50% (완화) |
| `volume_spike_ratio` | `400%` | `300%` | -100% (완화) |
| `price_high_months` | `2개월` | `1개월` | -50% (완화) |
| **가격 범위 필터** | ❌ 없음 | ✅ 있음 | 재탐지 전용 |

---

#### Table 2: BlockPattern 파라미터

패턴 관리 테이블의 파라미터입니다.

| 파라미터명 | 타입 | 제약조건 | 설명 | 예시 |
|-----------|------|----------|------|------|
| **식별** | | | | |
| `pattern_id` | `INTEGER` | `PRIMARY KEY` | 패턴 고유 ID (자동 증가) | `1`, `2`, `3` |
| `ticker` | `VARCHAR(10)` | `NOT NULL` | 종목 코드 | `"025980"` |
| | | | | |
| **Seed 참조** | | | | |
| `seed_block1_id` | `VARCHAR(50)` | `FK`, `NOT NULL` | Block1 Seed의 block1_id | `"uuid-block1-1"` |
| `seed_block2_id` | `VARCHAR(50)` | `FK`, `NOT NULL` | Block2 Seed의 block2_id | `"uuid-block2-1"` |
| `seed_block3_id` | `VARCHAR(50)` | `FK`, `NOT NULL` | Block3 Seed의 block3_id | `"uuid-block3-1"` |
| | | | | |
| **재탐지 기간** | | | | |
| `redetection_start` | `DATE` | `NOT NULL` | 재탐지 시작일 (= Seed Block1 시작일) | `2018-03-07` |
| `redetection_end` | `DATE` | `NOT NULL` | 재탐지 종료일 (= 시작일 + 5년) | `2023-03-07` |
| | | | | |
| **메타데이터** | | | | |
| `created_at` | `DATETIME` | `DEFAULT NOW()` | 패턴 생성 일시 | `2025-10-19 10:30:00` |

**관계:**
- 1 BlockPattern : N Block1Detection (재탐지)
- 1 BlockPattern : N Block2Detection (재탐지)
- 1 BlockPattern : N Block3Detection (재탐지)

---

#### Table 3: Detection Type 값

`detection_type` 필드에 사용되는 값입니다.

| 값 | 의미 | 사용 시점 | 특징 |
|---|------|-----------|------|
| `"seed"` | Seed 탐지 | 최초 패턴 발견 | • 엄격한 조건 사용<br>• 각 Pattern당 Block1/2/3 각 1개씩<br>• 재탐지 기준점 역할 |
| `"redetection"` | 재탐지 | 5년 재탐지 기간 중 | • 완화된 조건 + 가격 범위 필터<br>• 각 Pattern당 여러 개 가능<br>• Cooldown 20일 적용 |

**조회 예시:**
```sql
-- Pattern #1의 모든 Block1 (Seed + 재탐지)
SELECT * FROM block1_detection WHERE pattern_id = 1;

-- Pattern #1의 Seed만
SELECT * FROM block1_detection WHERE pattern_id = 1 AND detection_type = 'seed';

-- Pattern #1의 재탐지만
SELECT * FROM block1_detection WHERE pattern_id = 1 AND detection_type = 'redetection';
```

---

#### Table 4: Naming Convention 가이드

파라미터 명명 규칙입니다.

| Suffix/Prefix | 의미 | 타입 | 예시 |
|---------------|------|------|------|
| **Suffix** | | | |
| `_pct` | 퍼센트 (%) | `FLOAT` | `block1_tolerance_pct = 10.0` (±10%) |
| `_ratio` | 비율 (배수) | `FLOAT` | `volume_spike_ratio = 400.0` (4배) |
| `_days` | 일수 | `INTEGER` | `cooldown_days = 20` (20일) |
| `_months` | 개월 수 | `INTEGER` | `volume_high_months = 6` (6개월) |
| `_period` | 기간 (일) | `INTEGER` | `entry_ma_period = 120` (120일) |
| `_at` | 시점 (날짜/시간) | `DATE`/`DATETIME` | `started_at`, `created_at` |
| `_date` | 날짜 | `DATE` | `redetection_start` |
| `_id` | 식별자 | `VARCHAR`/`INTEGER` | `pattern_id`, `block1_id` |
| `_type` | 타입/종류 | `VARCHAR` | `detection_type`, `exit_condition_type` |
| | | | |
| **Prefix** | | | |
| `block1_` | Block1 전용 | - | `block1_tolerance_pct` |
| `block2_` | Block2 전용 | - | `block2_tolerance_pct` |
| `block3_` | Block3 전용 | - | `block3_tolerance_pct` |
| `seed_` | Seed 참조 | - | `seed_block1_id` |
| `entry_` | 진입 조건 | - | `entry_surge_rate`, `entry_ma_period` |
| `exit_` | 종료 조건 | - | `exit_condition_type`, `exit_ma_period` |
| `redetection_` | 재탐지 관련 | - | `redetection_start`, `redetection_end` |
| `min_` | 최소값 | - | `min_trading_value` |
| `max_` | 최대값 | - | `max_deviation_ratio` |

**일관성 규칙:**
- Block별 구분: `block1_`, `block2_`, `block3_` prefix 사용
- 퍼센트 값: `_pct` suffix (tolerance, rate 등)
- 비율/배수: `_ratio` suffix
- 기간: `_days`, `_months`, `_period` suffix로 단위 명시
- 시점: `_at`, `_date` suffix
- 식별자: `_id` suffix

---

#### Table 5: 가격 Tolerance 상세 설명

재탐지 시 사용되는 가격 범위 필터입니다.

| 파라미터 | Block | 기본값 | 범위 | 계산식 | 예시 |
|---------|-------|--------|------|--------|------|
| `block1_tolerance_pct` | Block1 | `10.0%` | ±10% | `seed_peak × (1 ± 0.10)` | Seed: 12,000원<br>→ 범위: 10,800 ~ 13,200원 |
| `block2_tolerance_pct` | Block2 | `15.0%` | ±15% | `seed_peak × (1 ± 0.15)` | Seed: 15,000원<br>→ 범위: 12,750 ~ 17,250원 |
| `block3_tolerance_pct` | Block3 | `20.0%` | ±20% | `seed_peak × (1 ± 0.20)` | Seed: 18,000원<br>→ 범위: 14,400 ~ 21,600원 |

**사용 예시:**
```python
# Pattern #1의 Block1 재탐지 조건
seed_block1_peak = 12700  # Seed Block1 고점

# Tolerance 10%
tolerance = 10.0 / 100  # 0.1
price_min = seed_block1_peak * (1 - tolerance)  # 11,430원
price_max = seed_block1_peak * (1 + tolerance)  # 13,970원

# 재탐지 조건
if price_min <= current_high <= price_max:
    # Block1 재탐지 조건 만족
    pass
```

**왜 Block별로 다른가?**
- Block1: 기본 패턴 → 좁은 범위 (±10%)
- Block2: 중간 단계 → 중간 범위 (±15%)
- Block3: 최종 단계 → 넓은 범위 (±20%)

Block이 높아질수록 변동성이 커지므로 더 넓은 범위를 허용합니다.

---

## 파라미터 기본값 요약

| 파라미터 | 블록1 | 블록2 | 블록3 | 설명 |
|---------|------|------|------|------|
| `entry_surge_rate` | 8.0 | 8.0 | 8.0 | 등락률 8% |
| `entry_ma_period` | 120 | 120 | 120 | 진입 MA120 |
| `exit_ma_period` | 60 | 60 | 60 | 종료 MA60 |
| `max_deviation_ratio` | 120 | 120 | 120 | 이격도 120 |
| `min_trading_value` | 300 | 300 | 300 | 거래대금 300억 |
| `volume_high_months` | 24 | 24 | 24 | 24개월 신고거래량 |
| `volume_spike_ratio` | 400 | 400 | 400 | 전날 대비 400% (4배, 필수) |
| `price_high_months` | 2 | 2 | 2 | 2개월 신고가 (필수) |
| `block_volume_ratio` | - | 15 | 15 | 이전 블록 최고의 15% |
| `low_price_margin` | - | 10 | 10 | 저가 마진 10% |
| `cooldown_days` | 120 | 120 | - | 쿨다운 120일 |
| `min_candles_after_block1` | - | 4 | - | 블록1 시작 후 최소 4캔들 (5번째부터 블록2) |
| `min_candles_after_block2` | - | - | 4 | 블록2 시작 후 최소 4캔들 (5번째부터 블록3) |

---

## 아키텍처

### 계층 구조 (Clean Architecture)

```
┌─────────────────────────────────────┐
│   Use Case Layer                    │
│   - DetectBlock1UseCase             │
│   - DetectBlock2UseCase             │
│   - DetectBlock3UseCase             │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│   Service Layer                     │
│   - Block1/2/3IndicatorCalculator   │
│   - Block1/2/3Checker               │
│   - ThreeLineBreakCalculator        │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│   Repository Layer                  │
│   - Block1/2/3Repository            │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│   Database Layer                    │
│   - Block1/2/3Detection Tables      │
└─────────────────────────────────────┘
```

---

## 사용 방법

### 1. 블록1 탐지 예제

```python
from datetime import date
from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from src.application.use_cases.detect_block1 import DetectBlock1UseCase
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.database.connection import DatabaseConnection

# 블록1 조건
condition = Block1Condition(
    entry_surge_rate=8.0,
    entry_ma_period=120,
    high_above_ma=True,
    max_deviation_ratio=120.0,
    min_trading_value=300.0,
    volume_high_months=24,
    volume_spike_ratio=3.0,  # 전날 대비 300% 증가 (선택)
    exit_condition_type=Block1ExitConditionType.MA_BREAK,
    exit_entry_ma_period=60,
    cooldown_days=120
)

# 탐지 실행
db = DatabaseConnection("stock_data.db")
repository = Block1Repository(db)
use_case = DetectBlock1UseCase(repository)

detections = use_case.execute(
    condition=condition,
    condition_name="강력한_블록1",
    stocks=stocks
)
```

### 2. 블록2 탐지 예제

```python
from src.domain.entities.block2_condition import Block2Condition
from src.application.use_cases.detect_block2 import DetectBlock2UseCase
from src.infrastructure.repositories.block2_repository import Block2Repository

# 블록2 조건 (블록1 조건 + 추가 조건)
condition = Block2Condition(
    # 기본 조건 (블록1과 동일)
    entry_surge_rate=8.0,
    entry_ma_period=120,
    high_above_ma=True,
    max_deviation_ratio=120.0,
    min_trading_value=300.0,
    volume_high_months=24,
    volume_spike_ratio=3.0,

    # 블록2 추가 조건
    block_volume_ratio=0.15,  # 블록1 최고 거래량의 15%
    low_price_margin=0.1,     # 10% 마진

    # 종료 조건
    exit_condition_type=Block1ExitConditionType.MA_BREAK,
    exit_entry_ma_period=60,
    cooldown_days=120
)

# 탐지 실행
repository = Block2Repository(db)
use_case = DetectBlock2UseCase(repository)

detections = use_case.execute(
    condition=condition,
    condition_name="강력한_블록2",
    stocks=stocks
)
```

### 3. 전체 블록 통합 탐지

```python
# 블록1, 블록2, 블록3을 순차적으로 탐지
block1_detections = detect_block1_use_case.execute(...)
block2_detections = detect_block2_use_case.execute(...)
block3_detections = detect_block3_use_case.execute(...)

# 결과 출력
print(f"블록1: {len(block1_detections)}개")
print(f"블록2: {len(block2_detections)}개")
print(f"블록3: {len(block3_detections)}개")
```

---

## API 레퍼런스

### Block1Condition

**새로 추가된 필드:**
- `prev_day_volume_increase_ratio: Optional[float]` - 전날 거래량 대비 증가율
  - `None`: 조건 무시 (기본값)
  - `3.0`: 전날 대비 300% 증가 필요 (4배)

### Block2Condition

**Block1Condition 상속 + 추가 필드:**
- `block_volume_ratio: float = 0.15` - 직전 블록1 최고 거래량 비율
- `low_price_margin: float = 0.1` - 저가 마진 (10%)

### Block3Condition

**Block2Condition 상속 + 동일 필드**

---

## 데이터베이스 스키마

### block2_detection 테이블

```sql
CREATE TABLE block2_detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block2_id VARCHAR(50) UNIQUE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- 블록1 참조 (옵션)
    block1_id VARCHAR(50),

    started_at DATE NOT NULL,
    ended_at DATE,

    -- ... (블록1과 동일한 필드들)

    FOREIGN KEY(block1_id) REFERENCES block1_detection(block1_id)
);
```

### block3_detection 테이블

```sql
CREATE TABLE block3_detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block3_id VARCHAR(50) UNIQUE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- 블록2 참조 (옵션)
    block2_id VARCHAR(50),

    started_at DATE NOT NULL,
    ended_at DATE,

    -- ... (블록1/2와 동일한 필드들)

    FOREIGN KEY(block2_id) REFERENCES block2_detection(block2_id)
);
```

---

## 예제 실행

```bash
# 블록1 탐지
python examples/block1_detection_example.py

# 블록2 탐지
python examples/block2_detection_example.py

# 블록3 탐지
python examples/block3_detection_example.py

# 통합 탐지
python collect_and_detect_ananti.py
```

---

## 문의 및 지원

블록 탐지 시스템에 대한 문의사항이 있으시면 이슈를 등록해주세요.
