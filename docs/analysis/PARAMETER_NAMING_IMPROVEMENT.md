# 파라미터 네이밍 개선 및 JSON 구조 개선

## 📅 작업 일시
2025-10-19

## 🎯 목적
블록별로 동일한 조건 **항목**을 사용하지만 **파라미터 값**은 독립적으로 설정 가능한 구조를 명확히 하기 위한 개선

## ✅ 완료된 작업

### 1. Entity 클래스 문서화 강화

모든 Block2/3/4 Condition 엔티티에 파라미터 독립성 설명 추가:

```python
⭐ 파라미터 독립성 (중요):
- entry_*, exit_*, cooldown_days: BlockN 전용 값 (다른 블록과 다를 수 있음)
- 예: Block1은 entry_surge_rate=8.0%, Block2는 entry_surge_rate=5.0% 사용 가능
- 이는 블록별 최적화를 위한 설계 (2025-10 리팩토링 완료)
```

**수정 파일:**
- [src/domain/entities/block2_condition.py](../src/domain/entities/block2_condition.py#L29-L32)
- [src/domain/entities/block3_condition.py](../src/domain/entities/block3_condition.py#L28-L31)
- [src/domain/entities/block4_condition.py](../src/domain/entities/block4_condition.py#L30-L33)

---

### 2. JSON 구조 개선 (블록별 섹션 분리)

#### Before (Flat 구조):
```json
{
  "aggressive_seed": {
    "entry_surge_rate": 8.0,
    "entry_ma_period": 120,
    "block2_volume_ratio": 80.0,
    "block3_volume_ratio": 20.0
  }
}
```

**문제점:**
- Block1~4가 모두 같은 entry_surge_rate 값을 사용 (8.0%)
- 블록별로 다른 값 설정 불가능
- 어느 블록용 값인지 불명확

#### After (블록별 섹션 구조):
```json
{
  "aggressive_seed": {
    "description": "공격적 Seed 조건 - 엄격한 진입, 블록별 단계적 완화",

    "block1": {
      "entry_surge_rate": 8.0,
      "entry_ma_period": 120,
      "exit_ma_period": 60
    },

    "block2": {
      "entry_surge_rate": 6.0,        // Block1과 다른 값!
      "entry_ma_period": 90,           // Block1과 다른 값!
      "exit_ma_period": 45,
      "volume_ratio": 80.0,
      "low_price_margin": 10.0,
      "min_candles_after_prev": 4
    },

    "block3": {
      "entry_surge_rate": 4.0,        // 더 완화!
      "entry_ma_period": 60,
      "exit_ma_period": 30,
      "volume_ratio": 20.0,
      "low_price_margin": 10.0,
      "min_candles_after_prev": 4
    },

    "block4": {
      "entry_surge_rate": 2.0,        // 가장 완화!
      "entry_ma_period": 30,
      "exit_ma_period": 20,
      "volume_ratio": 20.0,
      "low_price_margin": 10.0,
      "min_candles_after_prev": 4
    }
  }
}
```

**개선점:**
- ✅ 블록별 섹션으로 명확히 구분
- ✅ 블록별 독립적인 값 설정 가능 (8% → 6% → 4% → 2%)
- ✅ 가독성 대폭 향상
- ✅ 블록 특화 파라미터는 간결한 이름 사용 (`volume_ratio` instead of `block2_volume_ratio`)

**수정 파일:**
- [presets/seed_conditions.json](../presets/seed_conditions.json)
- [presets/redetection_conditions.json](../presets/redetection_conditions.json)

---

### 3. Preset 프리셋 전략 다양화

#### aggressive_seed (공격적 - 단계별 완화 전략)
| Block | entry_surge_rate | entry_ma_period | 전략 |
|-------|-----------------|-----------------|------|
| Block1 | 8.0% | 120일 | 엄격한 진입 |
| Block2 | 6.0% | 90일 | 중간 완화 |
| Block3 | 4.0% | 60일 | 추가 완화 |
| Block4 | 2.0% | 30일 | 최대 완화 |

#### standard_seed (표준 - 동일 조건 유지)
| Block | entry_surge_rate | entry_ma_period | 전략 |
|-------|-----------------|-----------------|------|
| Block1~4 | 8.0% | 120일 | 일관된 기준 |

#### conservative_seed (보수적 - 동일 조건 유지)
| Block | entry_surge_rate | entry_ma_period | 전략 |
|-------|-----------------|-----------------|------|
| Block1~4 | 8.0% | 120일 | 일관된 기준 |

---

### 4. 파싱 로직 업데이트

[update_presets_from_json.py](../update_presets_from_json.py) 스크립트 개선:

- 새 블록별 섹션 구조 파싱 지원
- Block1~4 독립적 값 추출
- 구 flat 구조 하위 호환성 유지
- 블록별 파라미터 차이 자동 감지 및 출력

**출력 예시:**
```
[aggressive_seed]
  Block2 조건:
    진입 등락률: 6.0% (Block1과 다름)  ← 자동 감지!
```

---

## 📊 파라미터 네이밍 현황

### 현재 네이밍 규칙 (유지)

| 범주 | 네이밍 패턴 | 예시 | 설명 |
|------|-----------|------|------|
| 공통 조건 | `entry_*`, `exit_*` | `entry_surge_rate`, `exit_ma_period` | 각 블록이 독립적 값 보유 |
| 블록 특화 | `blockN_*` | `block2_volume_ratio`, `block3_low_price_margin` | 해당 블록만 사용 |
| 블록 전환 | `blockN_min_candles_after_blockM` | `block2_min_candles_after_block1` | 이전 블록 대비 최소 캔들 수 |
| 재탐지 전용 | `blockN_tolerance_pct` | `block1_tolerance_pct` | 가격 범위 허용 오차 |

### 파라미터 전체 매핑

| 파라미터 | Block1 | Block2 | Block3 | Block4 | 독립 설정 가능? |
|---------|--------|--------|--------|--------|---------------|
| `entry_surge_rate` | ✅ | ✅ | ✅ | ✅ | ✅ 가능 |
| `entry_ma_period` | ✅ | ✅ | ✅ | ✅ | ✅ 가능 |
| `exit_ma_period` | ✅ | ✅ | ✅ | ✅ | ✅ 가능 |
| `cooldown_days` | ✅ | ✅ | ✅ | ✅ | ✅ 가능 |
| `blockN_volume_ratio` | ❌ | ✅ | ✅ | ✅ | N/A |
| `blockN_low_price_margin` | ❌ | ✅ | ✅ | ✅ | N/A |
| `blockN_min_candles_after_*` | ❌ | ✅ | ✅ | ✅ | N/A |

---

## 🧪 테스트 결과

### 테스트 1: JSON 구조 파싱
```bash
python update_presets_from_json.py --dry-run
```
**결과:** ✅ 성공 - 블록별 섹션 정상 파싱, 파라미터 차이 자동 감지

### 테스트 2: DB 업데이트
```bash
python update_presets_from_json.py
```
**결과:** ✅ 성공 - 6개 preset 모두 정상 저장

### 테스트 3: 패턴 탐지
```bash
python test_ananti_full_detection.py
```
**결과:** ✅ 성공 - 아난티(025980) 5개 Seed 탐지

---

## 💡 핵심 개선 효과

### 1. 명확성 향상
- ✅ JSON에서 블록별 값이 명확히 구분됨
- ✅ 블록 간 파라미터 차이를 한눈에 파악 가능
- ✅ 설정 파일만 봐도 전략 의도 파악 가능

### 2. 유연성 증가
- ✅ 블록별 독립적 최적화 가능
- ✅ 단계별 완화 전략 구현 가능 (8%→6%→4%→2%)
- ✅ 다양한 preset 전략 설계 가능

### 3. 유지보수성 개선
- ✅ 설정 변경 시 블록별 명확한 구분
- ✅ 실수 가능성 감소
- ✅ 코드 변경 없이 JSON만 수정으로 전략 변경

---

## 📝 사용 예시

### 예시 1: 단계별 완화 전략 (aggressive_seed)
```python
# Block1: 엄격한 진입 (8% 이상 급등만 탐지)
Block1Condition(entry_surge_rate=8.0, entry_ma_period=120)

# Block2: 중간 완화 (6% 이상이면 추가 상승 신호로 인정)
Block2Condition(entry_surge_rate=6.0, entry_ma_period=90)

# Block3: 추가 완화 (4% 이상)
Block3Condition(entry_surge_rate=4.0, entry_ma_period=60)

# Block4: 최대 완화 (2% 이상)
Block4Condition(entry_surge_rate=2.0, entry_ma_period=30)
```

**전략 의도:** 초기에는 엄격하게 진입하되, 블록이 진행될수록 조건을 완화하여 지속적인 상승 신호 포착

### 예시 2: 일관된 기준 유지 (standard_seed)
```python
# 모든 블록이 동일한 조건 사용
Block1~4: entry_surge_rate=8.0, entry_ma_period=120
```

**전략 의도:** 모든 단계에서 동일한 엄격한 기준 유지

---

## 🔄 호환성

### 하위 호환성
- ✅ 기존 flat 구조 JSON도 파싱 가능 (경고 메시지 출력)
- ✅ DB 스키마 변경 없음
- ✅ Entity 클래스 구조 변경 없음

### 마이그레이션
- ✅ 기존 시스템은 그대로 동작
- ✅ JSON만 새 구조로 교체하면 즉시 적용
- ✅ 점진적 마이그레이션 가능

---

## 📚 관련 문서

- [BLOCK_DETECTION.md](BLOCK_DETECTION.md) - 블록 탐지 시스템 전체 문서
- [REFACTORING_TODO.md](REFACTORING_TODO.md) - 리팩토링 완료 내역
- [presets/seed_conditions.json](../presets/seed_conditions.json) - Seed 조건 설정
- [presets/redetection_conditions.json](../presets/redetection_conditions.json) - 재탐지 조건 설정

---

## 🚀 다음 단계 (선택사항)

1. **추가 preset 전략 설계**
   - 업종별 최적화 전략
   - 변동성 기반 전략
   - 시가총액 기반 전략

2. **UI/CLI 도구 개발**
   - Preset 비교 도구
   - 시각화 대시보드
   - 설정 검증 도구

3. **백테스팅**
   - 다양한 preset 성능 비교
   - 최적 파라미터 탐색
   - 전략 효과 검증
