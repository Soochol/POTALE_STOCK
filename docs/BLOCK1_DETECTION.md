# 블록1 탐지 시스템

블록1은 특정 기술적 조건을 만족하는 주가 패턴을 자동으로 탐지하는 시스템입니다.

## 📋 목차

1. [개요](#개요)
2. [블록1 조건](#블록1-조건)
3. [아키텍처](#아키텍처)
4. [사용 방법](#사용-방법)
5. [API 레퍼런스](#api-레퍼런스)

---

## 개요

블록1은 다음과 같은 특징을 가진 주가 패턴입니다:

- **진입 조건**: 5가지 기술적 지표 (개별 판단)
- **종료 조건**: 3가지 중 택1 (이평선 이탈, 삼선전환도, 캔들 몸통 중간)
- **중복 방지**: 최초 발생 후 N일간 재탐지 제외 (기본 120일)

### 블록1의 활용

- 급등주 포착
- 이동평균선 돌파 패턴 탐지
- 거래량 급증 종목 발견
- 매매 신호 생성

---

## 블록1 조건

### 🚀 진입 조건 (5가지, 개별 판단)

각 조건은 독립적으로 설정 가능하며, 설정된 조건만 검사합니다.

#### 1. 등락률 조건
- **설명**: 전일종가 대비 당일고가 등락률 N% 이상 (양수만)
- **파라미터**: `rate_threshold` (예: 8.0 = 8%)
- **계산식**: `(고가 - 전일종가) / 전일종가 × 100 >= N`
- **의미**: 당일 고가 기준으로 강한 상승 포착

#### 2. 이평선 조건 A: 고가 위치
- **설명**: 당일 고가가 이동평균선 N 이상
- **파라미터**: `ma_period`, `high_above_ma=True`
- **계산식**: `고가 >= MA_N`

#### 3. 이평선 조건 B: 이격도
- **설명**: 이동평균선을 100으로 봤을 때 종가 비율
- **파라미터**: `ma_period`, `deviation_threshold`
- **계산식**: `(종가 / MA_N) × 100 <= M`
- **예시**:
  - MA120 = 5,000원, 종가 = 6,000원 → 이격도 = 120
  - `deviation_threshold=120` → 이격도 120 이하 (MA의 120% 이하)
- **의미**: 주가가 이평선에서 너무 멀리 떨어지지 않음 (과열 방지)

#### 4. 거래대금 조건
- **설명**: 거래대금 N억 이상
- **파라미터**: `trading_value_threshold` (단위: 억)
- **계산식**: `종가 × 거래량 >= N × 100,000,000`

#### 5. 거래량 조건
- **설명**: N개월 신고거래량 (최근 N개월 중 최대)
- **파라미터**: `volume_months` (예: 3, 6개월)
- **계산식**: `당일거래량 >= max(최근_N개월_거래량)`

---

### 🛑 종료 조건 (3가지 중 택1)

종료 조건은 `exit_condition_type`으로 선택합니다.

#### 1. 이동평균선 이탈 (`MA_BREAK`)
- **설명**: 종가가 이동평균선 아래로 하락
- **조건**: `종가 < MA_N`

#### 2. 삼선전환도 첫 음봉 (`THREE_LINE_REVERSAL`)
- **설명**: 삼선전환도(Three Line Break)에서 처음 음봉 발생
- **알고리즘**: 3선 전환 차트 기법
- **조건**: 양봉 연속 후 첫 음봉 출현

#### 3. 캔들 몸통 중간 가격 이탈 (`BODY_MIDDLE`)
- **설명**: 블록1 발생일 캔들 몸통 중간 가격 이하로 하락
- **조건**: `종가 < (블록1_시가 + 블록1_종가) / 2`

---

### 🔒 중복 방지

- **조건**: 최초 발생일 이후 N일까지 동일 블록1 재탐지 제외
- **파라미터**: `cooldown_days` (기본값: 120일)
- **규칙**:
  - 활성 블록1이 있으면 새 블록1 탐지 불가
  - 종료 후 cooldown 기간 내 재탐지 불가
  - cooldown 기간 경과 후 새 블록1 탐지 가능

---

## 아키텍처

### 계층 구조 (Clean Architecture)

```
┌─────────────────────────────────────┐
│   Use Case Layer                    │
│   - DetectBlock1UseCase             │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│   Service Layer                     │
│   - Block1IndicatorCalculator       │
│   - Block1Checker                   │
│   - ThreeLineBreakCalculator        │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│   Repository Layer                  │
│   - Block1Repository                │
└─────────────┬───────────────────────┘
              │
┌─────────────┴───────────────────────┐
│   Database Layer                    │
│   - Block1Detection Table           │
└─────────────────────────────────────┘
```

### 주요 컴포넌트

#### 1. Domain Layer
- `Block1Condition`: 블록1 조건 엔티티
- `Block1Detection`: 블록1 탐지 결과 엔티티

#### 2. Application Layer
- `DetectBlock1UseCase`: 블록1 탐지 유스케이스
- `Block1IndicatorCalculator`: 지표 계산 서비스
- `Block1Checker`: 진입/종료 조건 검사 서비스
- `ThreeLineBreakCalculator`: 삼선전환도 계산

#### 3. Infrastructure Layer
- `Block1Repository`: 블록1 저장/조회
- `Block1Detection` (Model): DB 테이블

---

## 사용 방법

### 1. 기본 사용 예제

```python
from datetime import date
from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from src.application.use_cases.detect_block1 import DetectBlock1UseCase
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.database.connection import DatabaseConnection

# 1. 블록1 조건 정의
condition = Block1Condition(
    rate_threshold=5.0,            # 등락률 5% 이상
    ma_period=20,                  # 20일 이동평균선
    high_above_ma=True,            # 고가 >= 20일선
    deviation_threshold=10.0,      # 이격도 10% 이하
    trading_value_threshold=100.0, # 거래대금 100억 이상
    volume_months=6,               # 6개월 신고거래량
    exit_condition_type=Block1ExitConditionType.MA_BREAK,
    cooldown_days=120
)

# 2. Use Case 초기화
db = DatabaseConnection("stock_data.db")
repository = Block1Repository(db)
use_case = DetectBlock1UseCase(repository)

# 3. 블록1 탐지 실행
detections = use_case.execute(
    condition=condition,
    condition_name="기본_블록1",
    stocks=stocks  # Stock 객체 리스트
)

# 4. 결과 확인
for detection in detections:
    print(f"{detection.ticker}: {detection.started_at} ~ {detection.ended_at}")
```

### 2. 조건별 예제

#### 급등주 탐지
```python
condition = Block1Condition(
    rate_threshold=10.0,           # 10% 이상 급등
    trading_value_threshold=200.0, # 200억 이상
    volume_months=3,               # 3개월 신고거래량
    cooldown_days=30
)
```

#### 이평선 돌파 탐지
```python
condition = Block1Condition(
    rate_threshold=3.0,
    ma_period=60,                  # 60일선 돌파
    high_above_ma=True,
    deviation_threshold=5.0,
    exit_condition_type=Block1ExitConditionType.MA_BREAK
)
```

#### 거래량 급증 탐지
```python
condition = Block1Condition(
    volume_months=12,              # 12개월 최고거래량
    trading_value_threshold=300.0,
    cooldown_days=180
)
```

### 3. 블록1 조회

```python
# 활성 블록1 조회
active_blocks = use_case.get_active_blocks("005930")

# 특정 기간 블록1 조회
all_blocks = use_case.get_all_blocks(
    ticker="005930",
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31)
)
```

---

## API 레퍼런스

### Block1Condition

블록1 조건 엔티티

**필드:**
- `rate_threshold: Optional[float]` - 등락률 임계값 (%)
- `ma_period: Optional[int]` - 이동평균선 기간
- `high_above_ma: Optional[bool]` - 고가 >= 이평선 검사 여부
- `deviation_threshold: Optional[float]` - 이격도 임계값 (%)
- `trading_value_threshold: Optional[float]` - 거래대금 임계값 (억)
- `volume_months: Optional[int]` - 신고거래량 기간 (개월)
- `exit_condition_type: Block1ExitConditionType` - 종료 조건 타입
- `cooldown_days: int` - 중복 방지 기간 (기본 120일)

**메서드:**
- `validate() -> bool` - 조건 유효성 검사

---

### Block1Detection

블록1 탐지 결과 엔티티

**필드:**
- `ticker: str` - 종목코드
- `block1_id: str` - 고유 ID (UUID)
- `status: str` - 상태 ("active", "completed")
- `started_at: date` - 시작일
- `ended_at: Optional[date]` - 종료일
- `entry_open/high/low/close: float` - 진입 시점 OHLC
- `entry_volume: int` - 진입 시점 거래량
- `entry_trading_value: float` - 진입 시점 거래대금 (억)
- `entry_ma_value: Optional[float]` - 진입 시점 이동평균선
- `entry_rate: Optional[float]` - 진입 시점 등락률
- `entry_deviation: Optional[float]` - 진입 시점 이격도
- `peak_price: Optional[float]` - 블록1 기간 중 최고가 (자동 갱신)
- `peak_date: Optional[date]` - 최고가 달성일
- `exit_reason: Optional[str]` - 종료 사유
- `exit_price: Optional[float]` - 종료 가격

**프로퍼티:**
- `duration_days: Optional[int]` - 블록1 지속 기간 (일)
- `entry_body_middle: float` - 진입 캔들 몸통 중간 가격
- `peak_gain_ratio: Optional[float]` - 진입가 대비 최고가 상승률 (%)

**메서드:**
- `update_peak(current_price, current_date) -> bool` - 최고가 갱신 (갱신 시 True 반환)
- `complete(ended_at, exit_reason, exit_price)` - 블록1 종료 처리

---

### DetectBlock1UseCase

블록1 탐지 유스케이스

**메서드:**
- `execute(condition, condition_name, stocks) -> List[Block1Detection]`
  - 블록1 탐지 실행
  - Args:
    - `condition: Block1Condition` - 블록1 조건
    - `condition_name: str` - 조건 이름
    - `stocks: List[Stock]` - 주식 데이터 리스트
  - Returns: 새로 탐지된 블록1 리스트

- `get_active_blocks(ticker) -> List[Block1Detection]`
  - 활성 블록1 조회

- `get_all_blocks(ticker, from_date, to_date) -> List[Block1Detection]`
  - 모든 블록1 조회

---

## 데이터베이스 스키마

### block1_detection 테이블

```sql
CREATE TABLE block1_detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block1_id VARCHAR(50) UNIQUE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    started_at DATE NOT NULL,
    ended_at DATE,

    entry_open FLOAT NOT NULL,
    entry_high FLOAT NOT NULL,
    entry_low FLOAT NOT NULL,
    entry_close FLOAT NOT NULL,
    entry_volume BIGINT NOT NULL,
    entry_trading_value FLOAT,

    entry_ma_value FLOAT,
    entry_rate FLOAT,
    entry_deviation FLOAT,

    peak_price FLOAT,
    peak_date DATE,

    exit_reason VARCHAR(50),
    exit_price FLOAT,

    condition_name VARCHAR(100),
    created_at DATETIME,
    updated_at DATETIME,

    FOREIGN KEY(ticker) REFERENCES stock_info(ticker)
);

CREATE INDEX ix_block1_ticker_started ON block1_detection(ticker, started_at);
CREATE INDEX ix_block1_status ON block1_detection(status);
CREATE INDEX ix_block1_started ON block1_detection(started_at);
CREATE UNIQUE INDEX ix_block1_id ON block1_detection(block1_id);
```

---

## 예제 실행

```bash
# 예제 파일 실행
python examples/block1_detection_example.py
```

---

## 문의 및 지원

블록1 탐지 시스템에 대한 문의사항이 있으시면 이슈를 등록해주세요.
