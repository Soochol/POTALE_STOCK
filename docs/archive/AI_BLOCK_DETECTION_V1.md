# AI-Based Block Pattern Detection System

AI/ML 기반 블록 패턴 탐지 시스템 상세 명세서

## 목차

1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [Feature Engineering](#feature-engineering)
4. [모델 아키텍처](#모델-아키텍처)
5. [학습 파이프라인](#학습-파이프라인)
6. [사용 방법](#사용-방법)
7. [확장 및 커스터마이징](#확장-및-커스터마이징)

---

## 개요

### 목적

기존 규칙 기반 블록 탐지 시스템을 보완하여, 머신러닝을 통해 블록1/2/3 패턴을 자동으로 학습하고 탐지하는 시스템입니다.

### 주요 특징

- **확장 가능한 Feature Registry**: Feature 추가/삭제가 YAML 설정으로 가능
- **모델 독립적**: 다양한 모델 아키텍처 실험 가능
- **실험 관리**: 버전 관리 및 재현 가능한 실험
- **프로토타입 지원**: 적은 레이블 데이터로도 시작 가능

---

## 시스템 아키텍처

### 전체 구조

```
데이터 수집 → 레이블링 → Feature 추출 → 모델 학습 → 평가 → 추론
```

### 디렉토리 구조

```
src/learning/
├── feature_engineering/      # Feature 추출
│   ├── registry.py           # Feature Registry 시스템
│   ├── technical_indicators.py # 기술적 지표
│   ├── block_features.py     # 50+ feature 함수
│   └── dataset_builder.py    # 데이터셋 생성
├── models/
│   └── block_classifier.py   # BlockClassifier 모델
├── training/                  # 학습 파이프라인 (TODO)
├── inference/                 # 추론 시스템 (TODO)
└── evaluation/                # 평가 도구 (TODO)

presets/
├── feature_configs/           # Feature 설정
│   └── block_classifier_v1.yaml
├── model_configs/             # 모델 설정 (TODO)
└── training_configs/          # 학습 설정 (TODO)

scripts/
├── generate_synthetic_labels.py   # 가짜 레이블 생성
├── import_block_labels.py         # CSV → DB
├── build_block_dataset.py         # 데이터셋 빌드
├── train_block_classifier.py      # 모델 학습
└── test_full_pipeline.py          # 통합 테스트
```

---

## Feature Engineering

### Feature Registry 시스템

Feature는 decorator 패턴으로 등록됩니다:

```python
from src.learning.feature_engineering.registry import feature_registry

@feature_registry.register(
    'volume_spike_ratio',
    category='volume',
    description='Volume / MA20 ratio'
)
def volume_spike_ratio(df: pd.DataFrame) -> pd.Series:
    ma20 = calculate_moving_average(df['volume'], 20)
    return (df['volume'] / ma20).fillna(1.0)
```

### Feature 카테고리 (v1)

#### 1. 가격 Feature (10개)
- `price_close_normalized`: 정규화된 종가
- `price_change_1d/5d/20d`: 등락률
- `price_high_vs_prev_close`: 고가 vs 전일종가
- `price_high_low_range`: 고저 범위
- `price_new_high_6m/12m/24m`: 신고가 여부

#### 2. 거래량 Feature (12개)
- `volume_normalized`, `volume_log_normalized`: 정규화
- `volume_ma5/20/60_ratio`: MA 대비 비율
- `volume_spike_ratio`, `volume_spike_2x/3x`: 스팟 탐지
- `volume_new_high_6m/12m/24m`: 신고거래량
- `volume_prev_day_ratio`: 전일 대비

#### 3. 거래대금 Feature (5개)
- `trading_value_billion`: 거래대금 (억)
- `trading_value_normalized`: 정규화
- `trading_value_ma20_ratio`: MA 대비
- `trading_value_above_300b/1500b`: 임계값 플래그

#### 4. 이동평균선 Feature (9개)
- `ma5/20/60/120`: 이동평균선
- `ma_deviation_60/120`: 이격도
- `high_above_ma60/120`: 고가 돌파 여부
- `ma_alignment`: 정배열 여부

#### 5. 기술적 지표 (5개)
- `rsi_14`: RSI
- `macd`, `macd_signal`, `macd_histogram`: MACD
- `bollinger_width`: 볼린저 밴드 폭

#### 6. 블록 관계 Feature (4개) - Block2/3 전용
- `block1_price_ratio`: Block1 고가 대비
- `block1_volume_ratio`: Block1 거래량 대비
- `block1_days_since`: Block1 종료 후 경과일
- `block1_support_distance`: Block1 지지선 거리

**총 50개 feature**

### Feature 설정 (YAML)

[presets/feature_configs/block_classifier_v1.yaml](../../presets/feature_configs/block_classifier_v1.yaml):

```yaml
version: v1
description: "Baseline feature set"

features:
  - price_close_normalized
  - price_change_1d
  # ... (50 features)

hyperparameters:
  sequence_length: 60
  rsi_period: 14
  volume_lookback: 20
```

### Feature 추가 방법

1. **Feature 함수 작성** (`src/learning/feature_engineering/block_features.py`):
```python
@feature_registry.register(
    'my_new_feature',
    category='custom',
    description='My custom feature'
)
def my_new_feature(df: pd.DataFrame) -> pd.Series:
    return df['close'] * df['volume']
```

2. **설정 파일에 추가**:
```yaml
# presets/feature_configs/block_classifier_v2.yaml
features:
  - my_new_feature  # 추가!
```

3. **데이터셋 재생성**:
```bash
python scripts/ml_system/build_block_dataset.py \
    --feature-config presets/feature_configs/block_classifier_v2.yaml \
    --output data/ml/dataset_v2.pkl
```

---

## 모델 아키텍처

### BlockClassifier

#### 구조
```
Input (n_features,)
    ↓
Dense(128, ReLU) + Dropout(0.3)
    ↓
Dense(64, ReLU) + Dropout(0.3)
    ↓
Dense(32, ReLU) + Dropout(0.3)
    ↓
Output(4, Softmax) → [None, Block1, Block2, Block3]
```

#### 특징
- Dense layer 기반 (현재는 시계열 없이 feature만 사용)
- Class imbalance 처리: Class weighting
- Early stopping, ReduceLROnPlateau callbacks

---

## 학습 파이프라인

### 전체 워크플로우

#### 1. 레이블 데이터 준비

**CSV 형식**:
```csv
ticker,block_type,sequence,started_at,ended_at,spot_candles,spot_center,support_type,notes
025980,1,1,2020-01-15,2020-02-10,"2020-01-17,2020-01-18",5500,middle,"첫 상승"
025980,2,1,2020-08-01,2020-08-10,"2020-08-05",12000,top,"강한 상승"
```

#### 2. 데이터베이스 임포트

```bash
python scripts/ml_system/import_block_labels.py --csv data/labels/block_labels.csv
```

#### 3. 데이터셋 생성

```bash
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/dataset_v1.pkl
```

#### 4. 모델 학습

```bash
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_v1.h5 \
    --epochs 100 \
    --batch-size 32
```

### Class Weighting

Block3는 희귀하므로 자동으로 높은 가중치 부여:

```python
class_weights = {
    0: 1.0,   # None
    1: 2.0,   # Block1
    2: 3.0,   # Block2
    3: 5.0    # Block3 (희귀)
}
```

---

## 사용 방법

### 가짜 데이터로 테스트

```bash
# 전체 파이프라인 테스트 (quick)
python scripts/ml_system/test_full_pipeline.py --quick-test

# 또는 수동으로:

# 1. 가짜 레이블 생성
python scripts/ml_system/generate_synthetic_labels.py \
    --tickers 025980,005930,035720 \
    --blocks-per-ticker 3 \
    --output data/labels/synthetic_labels.csv

# 2. 데이터셋 빌드
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/synthetic_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/dataset_v1.pkl

# 3. 학습
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_v1.h5 \
    --epochs 50
```

### 실제 데이터로 학습

1. **레이블 파일 작성** (`data/labels/block_labels.csv`):
   - 최소 10종목, 30개 블록 권장
   - CSV 형식 준수

2. **데이터셋 생성 및 학습**:
```bash
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/real_dataset.pkl

python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/real_dataset.pkl \
    --output models/block_classifier_real.h5 \
    --epochs 100
```

---

## 확장 및 커스터마이징

### Feature 실험

```bash
# Feature 목록 확인
python -c "from src.learning.feature_engineering.registry import feature_registry; feature_registry.print_summary()"

# 새 feature set 생성
cp presets/feature_configs/block_classifier_v1.yaml \
   presets/feature_configs/block_classifier_v2.yaml

# v2.yaml 수정 후 재학습
python scripts/ml_system/build_block_dataset.py \
    --feature-config presets/feature_configs/block_classifier_v2.yaml \
    --output data/ml/dataset_v2.pkl
```

### 모델 하이퍼파라미터 튜닝

```bash
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_tuned.h5 \
    --epochs 150 \
    --batch-size 64 \
    --learning-rate 0.0005 \
    --dropout 0.4
```

---

## TODO (향후 구현)

### Phase 2
- [ ] **Preprocessing Config**: 정규화 방법, 윈도우 크기 설정화
- [ ] **Evaluation System**: 상세 평가 지표, Confusion Matrix
- [ ] **Model Registry**: 다양한 모델 아키텍처 (LSTM, Transformer, CNN-LSTM)

### Phase 3
- [ ] **Inference System**: 전체 종목 스캔, 실시간 탐지
- [ ] **Signal Generation**: 매수/매도 신호 생성
- [ ] **Ensemble Models**: 다중 모델 조합
- [ ] **Auto ML**: Hyperparameter 자동 탐색

---

## 참고 자료

- [Block Detection 명세서](BLOCK_DETECTION.md) - 규칙 기반 시스템
- [Feature Engineering Best Practices](../../README.md) - 프로젝트 README
- [CLAUDE.md](../../CLAUDE.md) - 개발자 가이드
