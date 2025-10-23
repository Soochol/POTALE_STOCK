# ML System Scripts

AI/머신러닝 기반 블록 패턴 탐지 시스템

## 📋 스크립트 목록

### 레이블 관리

#### generate_synthetic_labels.py
**목적**: 테스트용 가짜 레이블 생성

**특징**:
- 거래량 급증 지점 기반 랜덤 레이블 생성
- 파이프라인 테스트용
- 실제 레이블 준비 전 시스템 검증

**사용법**:
```bash
# 특정 종목으로 생성
python scripts/ml_system/generate_synthetic_labels.py \
    --tickers 025980,005930,035720 \
    --blocks-per-ticker 3 \
    --output data/labels/synthetic_labels.csv

# 자동으로 데이터 많은 종목 선택
python scripts/ml_system/generate_synthetic_labels.py \
    --auto-select \
    --blocks-per-ticker 5 \
    --output data/labels/synthetic_labels.csv
```

---

#### import_block_labels.py
**목적**: CSV 레이블 파일을 데이터베이스로 임포트

**특징**:
- CSV → `block_label` 테이블
- 중복 체크 및 스킵
- JSON 변환 (spot_volume_candles)

**CSV 형식**:
```csv
ticker,block_type,sequence,started_at,ended_at,spot_candles,spot_center,support_type,notes
025980,1,1,2020-01-15,2020-02-10,"2020-01-17,2020-01-18",5500,middle,"첫 상승"
025980,2,1,2020-08-01,2020-08-10,"2020-08-05",12000,top,"강한 상승"
```

**사용법**:
```bash
python scripts/ml_system/import_block_labels.py --csv data/labels/block_labels.csv
```

---

### 학습 파이프라인

#### build_block_dataset.py
**목적**: 레이블 데이터로부터 ML 학습 데이터셋 생성

**특징**:
- Feature Registry 기반 feature 추출
- YAML 설정으로 feature 선택
- Pickle 형식으로 저장

**사용법**:
```bash
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/dataset_v1.pkl
```

**Feature Config 변경**:
```bash
# 다른 feature set으로 데이터셋 생성
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v2.yaml \
    --output data/ml/dataset_v2.pkl
```

---

#### train_block_classifier.py
**목적**: BlockClassifier 모델 학습

**특징**:
- Class weighting (불균형 처리)
- Early stopping, ReduceLROnPlateau
- Train/Val/Test 분할
- 평가 지표 출력

**사용법**:
```bash
# 기본 학습
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_v1.h5 \
    --epochs 100

# Hyperparameter 조정
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_tuned.h5 \
    --epochs 150 \
    --batch-size 64 \
    --learning-rate 0.0005 \
    --dropout 0.4
```

---

### 테스트

#### test_full_pipeline.py
**목적**: 전체 ML 파이프라인 통합 테스트

**특징**:
- 레이블 생성 → 데이터셋 빌드 → 학습 자동화
- Quick test 모드 (10 epochs)
- 파이프라인 검증용

**사용법**:
```bash
# 빠른 테스트 (10 epochs)
python scripts/ml_system/test_full_pipeline.py --quick-test

# 특정 종목으로 테스트
python scripts/ml_system/test_full_pipeline.py \
    --quick-test \
    --tickers 025980,005930,035720

# 기존 레이블 사용 (생성 스킵)
python scripts/ml_system/test_full_pipeline.py \
    --quick-test \
    --skip-generation
```

---

## 🚀 전체 워크플로우

### 1. 프로토타입 테스트 (가짜 데이터)
```bash
# 한 번에 전체 파이프라인 테스트
python scripts/ml_system/test_full_pipeline.py --quick-test
```

### 2. 실제 레이블 데이터로 학습

#### Step 1: 레이블 준비
`data/labels/block_labels.csv` 작성 (최소 10종목, 30개 블록)

#### Step 2: DB 임포트
```bash
python scripts/ml_system/import_block_labels.py --csv data/labels/block_labels.csv
```

#### Step 3: 데이터셋 빌드
```bash
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/real_dataset.pkl
```

#### Step 4: 모델 학습
```bash
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/real_dataset.pkl \
    --output models/block_classifier_real.h5 \
    --epochs 100
```

---

## 🎯 Feature 실험

### Feature 목록 확인
```bash
python -c "from src.learning.feature_engineering.registry import feature_registry; feature_registry.print_summary()"
```

### 새 Feature Set 만들기
```bash
# 1. Feature config 복사
cp presets/feature_configs/block_classifier_v1.yaml \
   presets/feature_configs/block_classifier_v2.yaml

# 2. v2.yaml 수정 (feature 추가/삭제)

# 3. 새 데이터셋 빌드
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v2.yaml \
    --output data/ml/dataset_v2.pkl

# 4. 학습
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v2.pkl \
    --output models/block_classifier_v2.h5 \
    --epochs 100
```

---

## 📊 ML 시스템 구조

### Feature Categories (v1 - 50 features)
- **Price** (10): 정규화, 등락률, 신고가
- **Volume** (12): 정규화, MA 대비, 스팟 탐지, 신고거래량
- **Trading Value** (5): 거래대금, 임계값 플래그
- **Moving Averages** (9): MA5/20/60/120, 이격도, 정배열
- **Technical** (5): RSI, MACD, 볼린저밴드
- **Block Relations** (4): Block1 비율, 지지선 거리

### Model Architecture
- **Input**: Feature vector (50 features)
- **Hidden**: Dense(128) → Dense(64) → Dense(32)
- **Output**: Softmax(4) - [None, Block1, Block2, Block3]
- **Dropout**: 0.3
- **Loss**: Categorical Cross-Entropy
- **Class Weighting**: Auto-calculated for imbalance

---

## 📖 참고 문서

- [AI 블록 탐지 시스템 상세 명세](../../docs/specification/AI_BLOCK_DETECTION.md)
- [Feature Engineering](../../src/learning/feature_engineering/)
- [개발자 가이드](../../CLAUDE.md)
