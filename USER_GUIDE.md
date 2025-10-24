# POTALE_STOCK 사용 가이드

**처음부터 끝까지 실행하는 방법**

---

## 📋 목차

1. [환경 확인](#1-환경-확인)
2. [데이터 수집](#2-데이터-수집)
3. [조건 설정 (YAML)](#3-조건-설정-yaml)
4. [블록 패턴 탐지](#4-블록-패턴-탐지)
5. [결과 확인](#5-결과-확인)
6. [Redetection 실행 (선택)](#6-redetection-실행-선택)
7. [ML 학습 (선택)](#7-ml-학습-선택)

---

## 1. 환경 확인

### 1-1. Python 가상환경 활성화 확인
```bash
# Windows PowerShell
.venv\Scripts\python.exe --version
```

**예상 출력**:
```
Python 3.10.18
```

### 1-2. 데이터베이스 확인
```bash
sqlite3 data/database/stock_data.db ".tables"
```

**예상 출력**:
```
stock_info       stock_price      collection_progress
block1_detection block2_detection ...
```

---

## 2. 데이터 수집

### 2-1. 단일 종목 수집 (테스트용)

```bash
.venv\Scripts\python.exe scripts\data_collection\collect_single_ticker.py --ticker 005930 --from-date 2020-01-01
```

**파라미터 설명**:
- `--ticker 005930`: 삼성전자 종목코드
- `--from-date 2020-01-01`: 2020년 1월 1일부터 수집
- `--force-full`: (선택) 전체 재수집

**예상 출력**:
```
Starting data collection for 005930...
Collecting price data from 2020-01-01...
Successfully collected 1,234 data points
✓ Collection complete!
```

### 2-2. 수집된 데이터 확인

```bash
sqlite3 data/database/stock_data.db "SELECT ticker, COUNT(*), MIN(date), MAX(date) FROM stock_price WHERE ticker='005930' GROUP BY ticker;"
```

**예상 출력**:
```
005930|1234|2020-01-02|2025-10-24
```

### 2-3. 여러 종목 수집 (실전용)

```bash
# 여러 종목 한번에
.venv\Scripts\python.exe scripts\data_collection\collect_single_ticker.py --ticker 005930,000660,035720 --from-date 2020-01-01

# 또는 전체 종목 (4,189개 - 시간 오래 걸림)
.venv\Scripts\python.exe scripts\data_collection\collect_all_tickers.py --from-date 2020-01-01
```

---

## 3. 조건 설정 (YAML)

### 3-1. 기본 예제 확인

```bash
# 간단한 예제 보기
type presets\examples\simple_pattern_example.yaml
```

### 3-2. 조건 커스터마이징

**예제 복사**:
```bash
copy presets\examples\simple_pattern_example.yaml presets\my_pattern.yaml
```

**파일 편집** (`presets\my_pattern.yaml`):
```yaml
version: "1.0"

block_graph:
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Surge"

      # 진입 조건 (모두 만족해야 함)
      entry_conditions:
        - name: "price_above_10k"
          expression: "current.close >= 10000"
          description: "종가 10,000원 이상"

        - name: "volume_spike"
          expression: "current.volume >= 5000000"
          description: "거래량 500만주 이상"

      # 종료 조건 (하나라도 만족하면 종료)
      exit_conditions:
        - name: "price_drop"
          expression: "current.close < 9000"
          description: "종가 9,000원 미만으로 하락"

      parameters:
        min_duration_candles: 1
        max_duration_candles: 50

  edges: []
```

### 3-3. 사용 가능한 조건 표현식

```yaml
# 가격 조건
"current.close >= 10000"              # 종가 10,000원 이상
"current.high > current.open * 1.05"  # 고가가 시가 대비 5% 이상
"current.close >= ma(all_stocks, 20)" # 종가가 20일 이동평균 이상

# 거래량 조건
"current.volume >= 1000000"                        # 100만주 이상
"current.volume >= avg(all_stocks[-20:], 'volume') * 2"  # 20일 평균 대비 2배

# 복합 조건
"current.close >= 10000 and current.volume >= 1000000"

# Block 간 관계 (Block2 이상에서 사용)
"current.close >= block1.peak_price * 1.05"  # Block1 고점 대비 5% 이상
```

**사용 가능한 함수**:
- `ma(data, period)`: 이동평균
- `avg(data, field)`: 평균
- `max(data, field)`: 최대값
- `min(data, field)`: 최소값
- `in_range(value, min, max)`: 범위 체크

---

## 4. 블록 패턴 탐지 (YAML 기반 Dynamic 시스템)

### 4-1. 기본 탐지 실행

```bash
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py \
    --ticker 025980 \
    --config presets\examples\extended_pattern_example.yaml \
    --from-date 2020-01-01
```

**파라미터**:
- `--ticker 025980`: 대상 종목 **(필수)**
- `--config <YAML 경로>`: YAML 설정 파일 경로 **(필수)**
- `--from-date 2020-01-01`: 시작 날짜 (선택, 기본값: 2015-01-01)
- `--to-date 2025-10-24`: (선택) 종료 날짜
- `--verbose`: (선택) 상세 로그 출력
- `--dry-run`: (선택) 실제 저장 없이 테스트

### 4-2. 사용 가능한 YAML 파일

```bash
# Block1만 (간단한 예제)
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py \
    --ticker 025980 \
    --config presets\examples\simple_pattern_example.yaml

# Block1~6 (확장된 예제)
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py \
    --ticker 025980 \
    --config presets\examples\extended_pattern_example.yaml

# 커스텀 YAML
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py \
    --ticker 025980 \
    --config presets\my_pattern.yaml
```

### 4-3. 여러 종목 동시 탐지

```bash
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py \
    --ticker 005930,000660,035720 \
    --config presets\examples\extended_pattern_example.yaml \
    --from-date 2020-01-01
```

---

## 5. 결과 확인 (dynamic_block_detection 테이블)

### 5-1. 탐지된 블록 개수 확인

```bash
sqlite3 data/database/stock_data.db "SELECT block_type, COUNT(*) as count FROM dynamic_block_detection WHERE ticker='025980' GROUP BY block_type ORDER BY block_type;"
```

**예상 출력**:
```
1|15
2|8
3|5
4|2
```

### 5-2. 최근 탐지 결과 확인

```bash
sqlite3 data/database/stock_data.db "SELECT block_type, block_id, started_at, ended_at, peak_price, status FROM dynamic_block_detection WHERE ticker='025980' ORDER BY started_at DESC LIMIT 5;"
```

**예상 출력**:
```
2|block2|2025-06-24|2025-07-03|16500.0|completed
1|block1|2025-06-13|2025-07-24|15200.0|completed
```

### 5-3. 특정 블록 타입 상세 조회

```bash
# Block1만 조회
sqlite3 data/database/stock_data.db "SELECT block_id, started_at, ended_at, peak_price, peak_volume FROM dynamic_block_detection WHERE ticker='025980' AND block_type=1 ORDER BY started_at DESC;"

# Block2만 조회
sqlite3 data/database/stock_data.db "SELECT block_id, started_at, ended_at, peak_price, peak_volume FROM dynamic_block_detection WHERE ticker='025980' AND block_type=2 ORDER BY started_at DESC;"
```

### 5-4. 전체 통계

```bash
sqlite3 data/database/stock_data.db "SELECT
    COUNT(*) as total_blocks,
    COUNT(DISTINCT block_type) as block_types,
    MIN(started_at) as first_detection,
    MAX(ended_at) as last_ended
FROM dynamic_block_detection
WHERE ticker='025980';"
```

---

## 6. Redetection 실행 (선택)

### 6-1. Seed Pattern 생성

**전제조건**: Block detection이 완료되어 있어야 함

```bash
# Seed 패턴 탐지 (엄격한 조건)
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py --ticker 005930 --from-date 2024-01-01 --config presets\examples\seed_redetection_pair.yaml
```

### 6-2. Redetection 실행

```bash
# Historical data에서 유사 패턴 재탐지
# (자동화 스크립트가 있다면)
.venv\Scripts\python.exe scripts\redetection\run_redetection.py --ticker 005930 --seed-pattern seed_pattern_1 --from-date 2020-01-01
```

### 6-3. 유사도 확인

```bash
sqlite3 data/database/stock_data.db "SELECT pattern_id, similarity_score, started_at FROM block1_detection WHERE condition_name='redetection' AND ticker='005930' ORDER BY similarity_score DESC LIMIT 10;"
```

---

## 7. ML 학습 (선택)

### 7-1. Training Data 생성

```bash
# Redetection 결과를 ML dataset으로 변환
.venv\Scripts\python.exe scripts\redetection\generate_ml_dataset.py --output data/ml/block_labels.csv
```

### 7-2. 모델 학습

**학습 스크립트 작성** (`train_model.py`):
```python
from src.learning.models import ModelRegistry
from src.learning.training import ModelTrainer, TrainingConfig
import numpy as np

# Load your data
X_train = np.load('data/ml/X_train.npy')
y_train = np.load('data/ml/y_train.npy')
X_val = np.load('data/ml/X_val.npy')
y_val = np.load('data/ml/y_val.npy')

# Create config
config = TrainingConfig(
    architecture='dense',
    model_name='block_classifier_v1',
    epochs=50,
    batch_size=32,
    learning_rate=0.001
)

# Train
trainer = ModelTrainer(config)
history = trainer.train(X_train, y_train, X_val, y_val)

# Save
trainer.save_model('models/block_classifier_v1.h5')
```

**실행**:
```bash
.venv\Scripts\python.exe train_model.py
```

### 7-3. 모델 평가

```python
from src.learning.evaluation import EvaluationMetrics
import numpy as np

# Load test data
X_test = np.load('data/ml/X_test.npy')
y_test = np.load('data/ml/y_test.npy')

# Load model
from tensorflow import keras
model = keras.models.load_model('models/block_classifier_v1.h5')

# Predict
y_pred_probs = model.predict(X_test)
y_pred = np.argmax(y_pred_probs, axis=1)

# Evaluate
performance = EvaluationMetrics.evaluate_full(
    y_true=y_test,
    y_pred=y_pred,
    model_name='block_classifier_v1'
)

print(performance.get_summary())
```

---

## 🎯 Quick Start (처음 시작하는 경우)

### Step 1: 데이터 수집
```bash
.venv\Scripts\python.exe scripts\data_collection\collect_single_ticker.py --ticker 005930 --from-date 2020-01-01
```

### Step 2: 데이터 확인
```bash
sqlite3 data/database/stock_data.db "SELECT COUNT(*) FROM stock_price WHERE ticker='005930';"
```

### Step 3: 블록 탐지
```bash
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py --ticker 005930 --from-date 2020-01-01 --verbose
```

### Step 4: 결과 확인
```bash
sqlite3 data/database/stock_data.db "SELECT COUNT(*) FROM block1_detection WHERE ticker='005930';"
```

---

## 🔧 Troubleshooting

### 문제 1: 데이터가 수집되지 않음
```bash
# 네트워크 확인
ping finance.naver.com

# 수집 로그 확인
.venv\Scripts\python.exe scripts\data_collection\collect_single_ticker.py --ticker 005930 --from-date 2024-01-01
```

### 문제 2: 블록이 탐지되지 않음
- YAML 조건이 너무 엄격한지 확인
- 주가 데이터 범위 확인
- `--verbose` 옵션으로 상세 로그 확인

```bash
# 최근 주가 확인
sqlite3 data/database/stock_data.db "SELECT date, close, volume FROM stock_price WHERE ticker='005930' ORDER BY date DESC LIMIT 10;"
```

### 문제 3: YAML 문법 오류
```bash
# YAML 검증
.venv\Scripts\python.exe -c "import yaml; yaml.safe_load(open('presets/my_pattern.yaml'))"
```

---

## 📊 유용한 SQL 쿼리

### 전체 통계
```sql
SELECT
    'Block1' as block_type,
    COUNT(*) as total,
    COUNT(DISTINCT ticker) as tickers,
    MIN(started_at) as earliest,
    MAX(ended_at) as latest
FROM block1_detection
UNION ALL
SELECT 'Block2', COUNT(*), COUNT(DISTINCT ticker), MIN(started_at), MAX(ended_at)
FROM block2_detection;
```

### 종목별 블록 수
```sql
SELECT
    ticker,
    COUNT(CASE WHEN EXISTS(SELECT 1 FROM block1_detection b WHERE b.ticker = stock_info.ticker) THEN 1 END) as block1_count
FROM stock_info
GROUP BY ticker
ORDER BY block1_count DESC
LIMIT 10;
```

### 최고 수익률 블록
```sql
SELECT
    ticker,
    started_at,
    ended_at,
    (peak_price - low_price) / low_price * 100 as profit_pct
FROM block1_detection
ORDER BY profit_pct DESC
LIMIT 10;
```

---

## 📝 다음 단계

1. ✅ 데이터 수집 완료
2. ✅ 블록 탐지 실행
3. 📊 결과 분석 및 조건 튜닝
4. 🔄 Redetection으로 유사 패턴 발견
5. 🤖 ML 모델 학습 및 자동화

---

**문의사항이나 오류가 발생하면 이슈를 남겨주세요!**
