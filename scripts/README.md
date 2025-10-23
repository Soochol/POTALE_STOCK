# Scripts Directory

스크립트는 기능별로 분류되어 있습니다.

## 📂 디렉토리 구조

```
scripts/
├── data_collection/          # 데이터 수집
├── rule_based_detection/     # 규칙 기반 패턴 탐지
├── preset_management/        # 프리셋 관리
└── ml_system/                # AI/ML 시스템
```

---

## 📊 데이터 수집 (data_collection/)

주가 데이터를 네이버 금융에서 수집하는 스크립트들

- **collect_single_ticker.py**: 단일 종목 데이터 수집
- **collect_all_tickers.py**: 전체 종목 데이터 수집 (비동기 병렬)

```bash
# 단일 종목 수집
python scripts/data_collection/collect_single_ticker.py --ticker 025980 --from-date 2015-01-01

# 전체 종목 수집
python scripts/data_collection/collect_all_tickers.py --from-date 2015-01-01
```

---

## 🔍 규칙 기반 패턴 탐지 (rule_based_detection/)

기존 규칙 기반 블록 탐지 시스템 (Seed + Redetection)

- **detect_patterns.py**: 패턴 탐지 메인 스크립트
- **debug_block1_detection.py**: Block1 탐지 디버깅 도구
- **test_seed_detector_2020.py**: Seed 탐지 테스트

```bash
# 패턴 탐지
python scripts/rule_based_detection/detect_patterns.py --ticker 025980 --from-date 2015-01-01

# Block1 디버깅
python scripts/rule_based_detection/debug_block1_detection.py --ticker 025980
```

---

## ⚙️ 프리셋 관리 (preset_management/)

규칙 기반 탐지 조건 프리셋 관리

- **update_presets_from_yaml.py**: YAML 파일 → DB 프리셋 업데이트
- **load_presets.py**: 프리셋 확인 및 검증

```bash
# YAML에서 프리셋 업데이트
python scripts/preset_management/update_presets_from_yaml.py

# 프리셋 확인
python scripts/preset_management/load_presets.py
```

---

## 🤖 AI/ML 시스템 (ml_system/)

머신러닝 기반 블록 패턴 탐지 시스템

### 레이블 관리
- **generate_synthetic_labels.py**: 테스트용 가짜 레이블 생성
- **import_block_labels.py**: CSV 레이블 → DB 임포트

### 학습 파이프라인
- **build_block_dataset.py**: ML 데이터셋 빌드
- **train_block_classifier.py**: 모델 학습

### 테스트
- **test_full_pipeline.py**: 전체 ML 파이프라인 통합 테스트

```bash
# 가짜 레이블 생성
python scripts/ml_system/generate_synthetic_labels.py \
    --tickers 025980,005930 \
    --blocks-per-ticker 3 \
    --output data/labels/synthetic_labels.csv

# 데이터셋 빌드
python scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/dataset_v1.pkl

# 모델 학습
python scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_v1.h5 \
    --epochs 100

# 전체 파이프라인 테스트
python scripts/ml_system/test_full_pipeline.py --quick-test
```

---

## 🚀 빠른 시작

### 1. 데이터 수집
```bash
python scripts/data_collection/collect_single_ticker.py --ticker 025980 --from-date 2015-01-01
```

### 2. 규칙 기반 탐지
```bash
python scripts/rule_based_detection/detect_patterns.py --ticker 025980 --from-date 2015-01-01
```

### 3. AI 학습 (프로토타입)
```bash
python scripts/ml_system/test_full_pipeline.py --quick-test
```

---

## 📖 참고 문서

- **규칙 기반 시스템**: [docs/specification/BLOCK_DETECTION.md](../docs/specification/BLOCK_DETECTION.md)
- **AI/ML 시스템**: [docs/specification/AI_BLOCK_DETECTION.md](../docs/specification/AI_BLOCK_DETECTION.md)
- **개발자 가이드**: [CLAUDE.md](../CLAUDE.md)
