# 프로젝트 구조 상세 설명

## 폴더 구조

```
potale_stock/
├── main.py                          # CLI 진입점
├── requirements.txt                 # 의존성 패키지
├── README.md                        # 프로젝트 설명서
├── STRUCTURE.md                     # 구조 상세 설명 (본 문서)
│
├── config/                          # 설정 파일
│   ├── config.yaml                  # 전역 설정
│   └── conditions.yaml              # 조건 정의
│
├── data/                            # 데이터 저장소
│   ├── database/                    # SQLite 데이터베이스
│   │   └── stock_data.db           # 주식 데이터 DB
│   ├── raw/                         # 원본 데이터 (백업용)
│   │   └── csv/                     # CSV 형식 원본
│   └── cache/                       # 임시 캐시
│
├── models/                          # AI 모델 저장소
│   ├── {ticker}_lstm_model.h5      # 종목별 LSTM 모델
│   └── classification_model.h5      # 분류 모델
│
└── src/                             # 소스 코드
    ├── domain/                      # Domain Layer (Clean Architecture)
    │   ├── entities/                # 비즈니스 엔티티
    │   │   ├── stock.py            # Stock 엔티티
    │   │   ├── condition.py        # Condition, Rule 엔티티
    │   │   └── detection_result.py # DetectionResult 엔티티
    │   │
    │   └── repositories/            # Repository 인터페이스
    │       ├── stock_repository.py
    │       └── condition_repository.py
    │
    ├── application/                 # Application Layer
    │   ├── use_cases/               # Use Cases (비즈니스 로직)
    │   │   ├── collect_stock_data.py
    │   │   ├── detect_condition.py
    │   │   └── manage_condition.py
    │   │
    │   └── services/                # Application Services
    │       ├── indicator_calculator.py  # 기술적 지표 계산
    │       └── condition_checker.py     # 조건 검사
    │
    ├── infrastructure/              # Infrastructure Layer
    │   ├── database/                # 데이터베이스
    │   │   ├── connection.py       # DB 연결 관리
    │   │   └── models.py           # SQLAlchemy 모델
    │   │
    │   ├── repositories/            # Repository 구현체
    │   │   ├── sqlite_stock_repository.py      # SQLite 구현
    │   │   ├── pykrx_stock_repository.py       # pykrx 수집
    │   │   └── yaml_condition_repository.py    # YAML 구현
    │   │
    │   └── collectors/              # 데이터 수집기
    │       ├── base_collector.py
    │       ├── stock_price_collector.py        # 주식 가격 수집
    │       └── market_info_collector.py        # 시장 정보 수집
    │
    ├── learning/                    # AI/ML 모듈
    │   ├── models.py                # AI 모델 정의 (LSTM, 분류)
    │   └── trainer.py               # 학습 관리
    │
    ├── collector/                   # Legacy (호환용)
    └── condition/                   # Legacy (호환용)
```

## 데이터베이스 스키마

### 1. stock_info (종목 정보)
```sql
CREATE TABLE stock_info (
    ticker TEXT PRIMARY KEY,        -- 종목코드
    name TEXT NOT NULL,             -- 종목명
    market TEXT NOT NULL,           -- 시장구분 (KOSPI, KOSDAQ)
    sector TEXT,                    -- 업종
    listing_date DATE,              -- 상장일
    created_at TIMESTAMP,           -- 생성일시
    updated_at TIMESTAMP            -- 수정일시
);
```

### 2. stock_price (주식 가격)
```sql
CREATE TABLE stock_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,           -- 종목코드 (FK)
    date DATE NOT NULL,             -- 날짜
    open REAL NOT NULL,             -- 시가
    high REAL NOT NULL,             -- 고가
    low REAL NOT NULL,              -- 저가
    close REAL NOT NULL,            -- 종가
    volume INTEGER NOT NULL,        -- 거래량
    change_rate REAL,               -- 등락률
    trading_value INTEGER,          -- 거래대금
    created_at TIMESTAMP,           -- 생성일시

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)           -- 복합 유니크 키
);

-- 인덱스
CREATE INDEX ix_stock_price_ticker_date ON stock_price(ticker, date);
CREATE INDEX ix_stock_price_date ON stock_price(date);
```

### 3. market_data (시장 데이터)
```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,           -- 종목코드 (FK)
    date DATE NOT NULL,             -- 날짜
    market_cap INTEGER,             -- 시가총액
    per REAL,                       -- PER (주가수익비율)
    pbr REAL,                       -- PBR (주가순자산비율)
    eps REAL,                       -- EPS (주당순이익)
    bps REAL,                       -- BPS (주당순자산)
    div REAL,                       -- 배당수익률
    dps REAL,                       -- 주당배당금
    created_at TIMESTAMP,           -- 생성일시

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);

-- 인덱스
CREATE INDEX ix_market_data_ticker_date ON market_data(ticker, date);
CREATE INDEX ix_market_data_market_cap ON market_data(market_cap);
```

### 4. data_collection_log (수집 로그)
```sql
CREATE TABLE data_collection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_type TEXT NOT NULL,  -- 수집 타입
    ticker TEXT,                    -- 종목코드
    start_date DATE,                -- 수집 시작일
    end_date DATE,                  -- 수집 종료일
    status TEXT NOT NULL,           -- 상태 (success, failed, partial)
    record_count INTEGER,           -- 수집된 레코드 수
    error_message TEXT,             -- 에러 메시지
    started_at TIMESTAMP NOT NULL,  -- 수집 시작 시각
    completed_at TIMESTAMP,         -- 수집 완료 시각
    duration_seconds REAL           -- 소요 시간(초)
);
```

## 데이터 수집 워크플로우

### 1. 초기 설정
```bash
# 1. 종목 정보 수집 (최초 1회)
python main.py collect info --market ALL --include-market-cap

# 2. 주식 가격 데이터 수집
python main.py collect stocks --market KOSPI --top-n 100 -s 2023-01-01
```

### 2. 일상 업데이트
```bash
# 최근 7일 데이터 업데이트
python main.py collect update --days 7

# 특정 종목 업데이트
python main.py collect stocks -t 005930 -t 000660 -s 2024-01-01
```

### 3. 데이터 흐름
```
pykrx API
    ↓
StockPriceCollector / MarketInfoCollector
    ↓
SqliteStockRepository
    ↓
SQLite Database (stock_data.db)
    ↓
Use Cases (조건 탐지, AI 학습 등)
```

## Clean Architecture 레이어별 책임

### 1. Domain Layer (내부 원)
- **목적**: 비즈니스 로직과 규칙
- **의존성**: 없음 (순수한 비즈니스 로직)
- **주요 구성**:
  - Entities: Stock, Condition, Rule, DetectionResult
  - Repository Interfaces: IStockRepository, IConditionRepository

### 2. Application Layer
- **목적**: Use Cases 실행, 비즈니스 흐름 관리
- **의존성**: Domain Layer에만 의존
- **주요 구성**:
  - Use Cases: CollectStockDataUseCase, DetectConditionUseCase
  - Services: IndicatorCalculator, ConditionChecker

### 3. Infrastructure Layer (외부 원)
- **목적**: 외부 시스템과의 통합
- **의존성**: Domain, Application Layer 의존
- **주요 구성**:
  - Database: SQLAlchemy 모델, 연결 관리
  - Repositories: SQLite, YAML 구현체
  - Collectors: pykrx API 연동

### 4. Presentation Layer
- **목적**: 사용자 인터페이스 (CLI)
- **의존성**: 모든 레이어 접근 가능
- **주요 구성**:
  - main.py: Click CLI 커맨드

## 확장 가능성

### 1. 새로운 데이터 소스 추가
```python
# 예: Alpha Vantage API
class AlphaVantageStockRepository(IStockRepository):
    def get_stock_data(self, ticker, start_date, end_date):
        # Alpha Vantage API 호출
        pass
```

### 2. 새로운 조건 타입 추가
```python
# domain/entities/condition.py
class RuleType(Enum):
    CROSS_OVER = "cross_over"
    INDICATOR_THRESHOLD = "indicator_threshold"
    VOLUME_INCREASE = "volume_increase"
    PRICE_CHANGE = "price_change"
    PATTERN_MATCH = "pattern_match"  # 새로운 타입
```

### 3. 새로운 저장소 추가
```python
# infrastructure/repositories/postgresql_stock_repository.py
class PostgresqlStockRepository(IStockRepository):
    # PostgreSQL 구현
    pass
```

## 주요 설정 파일

### config/config.yaml
```yaml
database:
  path: "data/database/stock_data.db"

collector:
  default_start_date: "2023-01-01"
  delay: 0.1  # API 호출 간 대기 시간

learning:
  models_dir: "models/"
  sequence_length: 60
  epochs: 50
```

### config/conditions.yaml
```yaml
conditions:
  - name: "골든크로스"
    description: "5일선이 20일선 상향 돌파"
    rules:
      - type: "cross_over"
        indicator1: "MA_5"
        indicator2: "MA_20"
```

## 성능 최적화

### 1. 데이터베이스
- WAL 모드 활성화 (Write-Ahead Logging)
- 적절한 인덱스 설정
- 배치 insert 사용 (upsert)

### 2. 데이터 수집
- API 호출 간 delay 설정 (기본 0.1초)
- 병렬 처리 가능한 구조
- 진행률 표시 (rich Progress)

### 3. AI 학습
- 데이터 캐싱
- GPU 활용 (TensorFlow)
- Early stopping 콜백
