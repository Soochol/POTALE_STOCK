# Redetection Automation Scripts

전체 redetection 파이프라인을 자동화하는 스크립트 모음입니다.

## 파이프라인 개요

```
┌─────────────────┐
│ Seed Detection  │  ← Strict conditions로 high-quality 패턴 탐지
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Redetection    │  ← DTW similarity로 유사 패턴 재탐지
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ ML Dataset Gen  │  ← 학습 데이터셋 생성
└─────────────────┘
```

## 스크립트 목록

### 1. `detect_seed_patterns.py`

High-quality seed patterns를 탐지하고 DB에 저장

**사용법:**
```bash
.venv/Scripts/python.exe scripts/redetection/detect_seed_patterns.py \
    --yaml presets/seed_conditions.yaml \
    --ticker 025980 \
    --from-date 2015-01-01 \
    --max-patterns 10
```

**옵션:**
- `--yaml`: Seed detection YAML file (required)
- `--ticker`: Stock ticker (required)
- `--from-date`: Start date (YYYY-MM-DD)
- `--to-date`: End date (YYYY-MM-DD)
- `--max-patterns`: Maximum patterns to save (default: 10)
- `--db`: Database path (default: data/database/stock_data.db)

**출력:**
- Seed patterns saved to `seed_pattern` table

---

### 2. `run_redetection.py`

Seed pattern 기반 유사 패턴 재탐지 (DTW)

**사용법:**
```bash
.venv/Scripts/python.exe scripts/redetection/run_redetection.py \
    --redetection-yaml presets/redetection_conditions.yaml \
    --ticker 025980 \
    --from-date 2015-01-01 \
    --method dtw
```

**옵션:**
- `--redetection-yaml`: Redetection YAML file (required)
- `--ticker`: Stock ticker
- `--seed-pattern`: Specific seed pattern name (optional)
- `--from-date`: Start date for historical data
- `--to-date`: End date
- `--method`: Similarity method (`range` or `dtw`, default: dtw)
- `--no-save`: Dry run without saving to DB
- `--db`: Database path

**출력:**
- Redetections saved to `dynamic_block_detection` table

---

### 3. `generate_ml_dataset.py`

Redetection 결과를 ML training dataset으로 변환

**사용법:**
```bash
.venv/Scripts/python.exe scripts/redetection/generate_ml_dataset.py \
    --output-csv data/ml/block_labels.csv \
    --output-report data/ml/report.txt \
    --min-similarity 0.7
```

**옵션:**
- `--output-csv`: Output CSV file path (default: data/ml/block_labels.csv)
- `--output-report`: Output report file path (default: data/ml/dataset_report.txt)
- `--min-similarity`: Minimum similarity score (default: 0.7)
- `--db`: Database path

**출력:**
- CSV file with block labels
- Text report with statistics

---

### 4. `run_full_pipeline.py` ⭐

**전체 파이프라인 자동 실행 (권장)**

**사용법:**
```bash
.venv/Scripts/python.exe scripts/redetection/run_full_pipeline.py \
    --seed-yaml presets/seed_conditions.yaml \
    --redetection-yaml presets/redetection_conditions.yaml \
    --ticker 025980 \
    --from-date 2015-01-01 \
    --method dtw
```

**옵션:**
- `--seed-yaml`: Seed detection YAML (required)
- `--redetection-yaml`: Redetection YAML (required)
- `--ticker`: Stock ticker (required)
- `--from-date`: Start date (required, YYYY-MM-DD)
- `--to-date`: End date (optional)
- `--max-seed-patterns`: Max seed patterns (default: 10)
- `--method`: Similarity method (`range` or `dtw`, default: dtw)
- `--min-similarity`: Min similarity for ML dataset (default: 0.7)
- `--db`: Database path
- `--quiet`: Suppress output

**출력:**
- Seed patterns in DB
- Redetections in DB
- ML dataset CSV
- Summary report

---

## 사용 예시

### 예시 1: 빠른 시작 (Full Pipeline)

```bash
# 025980 종목에 대해 전체 파이프라인 실행
.venv/Scripts/python.exe scripts/redetection/run_full_pipeline.py \
    --seed-yaml presets/examples/seed_redetection_pair.yaml \
    --redetection-yaml presets/examples/seed_redetection_pair.yaml \
    --ticker 025980 \
    --from-date 2020-01-01 \
    --to-date 2023-12-31
```

### 예시 2: 단계별 실행

```bash
# Step 1: Seed patterns 탐지
.venv/Scripts/python.exe scripts/redetection/detect_seed_patterns.py \
    --yaml presets/seed_conditions.yaml \
    --ticker 025980 \
    --from-date 2020-01-01 \
    --max-patterns 5

# Step 2: Redetection 실행 (DTW)
.venv/Scripts/python.exe scripts/redetection/run_redetection.py \
    --redetection-yaml presets/redetection_conditions.yaml \
    --ticker 025980 \
    --from-date 2015-01-01 \
    --method dtw

# Step 3: ML dataset 생성
.venv/Scripts/python.exe scripts/redetection/generate_ml_dataset.py \
    --output-csv data/ml/labels_025980.csv \
    --min-similarity 0.75
```

### 예시 3: 여러 종목 자동화 (Bash loop)

```bash
# 여러 종목에 대해 반복 실행
for ticker in 025980 005930 035720; do
    echo "Processing $ticker..."
    .venv/Scripts/python.exe scripts/redetection/run_full_pipeline.py \
        --seed-yaml presets/seed_conditions.yaml \
        --redetection-yaml presets/redetection_conditions.yaml \
        --ticker $ticker \
        --from-date 2020-01-01
done
```

### 예시 4: DTW vs Range 비교

```bash
# DTW method
.venv/Scripts/python.exe scripts/redetection/run_redetection.py \
    --redetection-yaml presets/redetection_conditions.yaml \
    --ticker 025980 \
    --from-date 2020-01-01 \
    --method dtw

# Range method
.venv/Scripts/python.exe scripts/redetection/run_redetection.py \
    --redetection-yaml presets/redetection_conditions.yaml \
    --ticker 025980 \
    --from-date 2020-01-01 \
    --method range
```

---

## 출력 파일 구조

```
data/
├── ml/
│   ├── block_labels_025980_20250101_120000.csv    # ML training labels
│   └── report_025980_20250101_120000.txt           # Summary report
└── database/
    └── stock_data.db                               # Updated with seeds & redetections
```

### CSV Format (block_labels.csv)

```csv
ticker,block_type,sequence,started_at,ended_at,peak_price,peak_volume,duration,similarity_score,source
025980,1,1,2020-01-15,2020-02-10,12500,550000,26,1.0,seed:seed_025980_20250101_001
025980,2,2,2020-02-11,2020-03-05,14200,420000,23,0.95,redetection:pattern_123
```

---

## 워크플로우 가이드

### 1단계: Seed Pattern 생성

1. `presets/seed_conditions.yaml` 파일에 strict conditions 설정
2. `detect_seed_patterns.py` 실행
3. DB에 저장된 seed patterns 확인

```bash
sqlite3 data/database/stock_data.db \
  "SELECT id, pattern_name, ticker, detection_date FROM seed_pattern;"
```

### 2단계: Redetection 실행

1. `presets/redetection_conditions.yaml` 파일에 relaxed conditions + tolerance 설정
2. `run_redetection.py` 실행 (DTW 권장)
3. Redetection 결과 확인

```bash
sqlite3 data/database/stock_data.db \
  "SELECT COUNT(*) FROM dynamic_block_detection WHERE condition_name='redetection';"
```

### 3단계: ML Dataset 생성

1. `generate_ml_dataset.py` 실행
2. CSV 파일 확인
3. ML 학습 파이프라인으로 전달

```bash
# Dataset 확인
head -20 data/ml/block_labels.csv

# Report 확인
cat data/ml/dataset_report.txt
```

---

## 고급 사용법

### Custom YAML 작성

#### Seed YAML Example

```yaml
block_graph:
  pattern_type: seed
  root_node: block1
  nodes:
    block1:
      block_id: block1
      block_type: 1
      entry_conditions:
        - name: surge_detection
          expression: "current.surge_rate > 8.0"
      exit_conditions:
        - name: price_drop
          expression: "current.close < seed.block1.peak_price * 0.9"
```

#### Redetection YAML Example

```yaml
block_graph:
  pattern_type: redetection
  redetection_config:
    seed_pattern_reference: "my_seed_pattern"
    tolerance:
      price_range: 0.10      # ±10%
      volume_range: 0.30     # ±30%
      time_range: 5          # ±5 candles
    matching_weights:
      price_shape: 0.5
      volume_shape: 0.3
      timing: 0.2
    min_similarity_score: 0.70
    min_detection_interval_days: 20
  nodes:
    # ... (relaxed conditions)
```

---

## 트러블슈팅

### 문제 1: "No stock data found"

**원인:** Stock data가 DB에 없음

**해결:**
```bash
.venv/Scripts/python.exe scripts/data_collection/collect_single_ticker.py \
    --ticker 025980 \
    --from-date 2015-01-01
```

### 문제 2: "Seed pattern not found"

**원인:** Seed pattern이 DB에 없음

**해결:** `detect_seed_patterns.py`를 먼저 실행

### 문제 3: Redetection에서 결과가 없음

**원인:**
- Similarity threshold가 너무 높음
- Tolerance가 너무 좁음
- Historical data 부족

**해결:**
- `min_similarity_score`를 낮춤 (0.6~0.7)
- `tolerance.price_range`를 넓힘 (0.15~0.20)
- Date range를 확장

### 문제 4: "price_shape and volume_shape must have same length"

**원인:** Seed pattern의 price_shape와 volume_shape 길이 불일치

**해결:** Block features 수를 확인하고 normalize_sequence 검증

---

## 성능 최적화

### 대량 처리시 권장사항

1. **Batch 처리**: 종목별로 순차 실행
2. **Date range 분할**: 긴 기간은 년도별로 분할
3. **Max patterns 제한**: `--max-seed-patterns 10` 정도로 제한
4. **Database backup**: 실행 전 DB 백업

```bash
# Backup
copy data\database\stock_data.db data\database\stock_data_backup.db

# Run pipeline
.venv/Scripts/python.exe scripts/redetection/run_full_pipeline.py ...
```

---

## 다음 단계

1. **ML 모델 학습**: 생성된 CSV로 BlockClassifier 학습
2. **Visualization**: Redetection 결과 시각화
3. **Backtesting**: 패턴 기반 수익률 분석
4. **Production**: 실시간 패턴 탐지 시스템 구축

---

## 참고 문서

- [Phase 7 Redetection System](../../docs/specification/REDETECTION_SYSTEM.md)
- [DTW Algorithm](../../docs/specification/DTW_SIMILARITY.md)
- [YAML Schema](../../presets/schemas/redetection_schema.yaml)
