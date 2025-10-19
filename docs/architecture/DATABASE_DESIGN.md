# 데이터베이스 설계서

## 1. 개요

### 1.1 목적
- **2010.01.01부터 현재**까지 한국 주식 시장의 모든 데이터를 체계적으로 저장
- 네이버 금융 웹 스크래핑을 통해 수집 가능한 **전체 데이터** 지원
- 빠른 조회와 분석을 위한 최적화된 스키마

### 1.2 데이터베이스 엔진
- **SQLite 3.x**
- WAL (Write-Ahead Logging) 모드
- 예상 DB 크기: 2010~2025 (15년) 기준 약 **3.5GB ~ 4.5GB**

### 1.3 전체 테이블 구조 요약

| 구분 | 테이블 수 | 설명 |
|------|-----------|------|
| **핵심 (Phase 1)** | 4개 | stock_info, stock_price, market_data, investor_trading |
| **확장 (Phase 2)** | 3개 | short_selling, index_info, index_price |
| **고급 (Phase 3)** | 6개 | margin_trading, foreign_limit, etf_*, sector_* |
| **관리** | 3개 | collection_log, collection_progress, data_quality |
| **총계** | **16개** | - |

---

## 2. 핵심 테이블 (Phase 1 - 필수)

### 2.1 stock_info (종목 정보)

**목적**: 종목 기본 정보 및 메타데이터

```sql
CREATE TABLE stock_info (
    ticker TEXT PRIMARY KEY,               -- 종목코드 (6자리)
    name TEXT NOT NULL,                    -- 종목명
    market TEXT NOT NULL,                  -- 시장구분: KOSPI, KOSDAQ, KONEX
    sector TEXT,                           -- 업종명
    sector_code TEXT,                      -- 업종 코드
    listing_date DATE,                     -- 상장일
    listing_shares BIGINT,                 -- 상장주식수
    is_active BOOLEAN DEFAULT 1,           -- 상장 여부 (1: 활성, 0: 폐지)
    delisting_date DATE,                   -- 상장폐지일
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_info_market ON stock_info(market);
CREATE INDEX idx_stock_info_sector ON stock_info(sector_code);
CREATE INDEX idx_stock_info_active ON stock_info(is_active);
```

**특이사항**:
- `is_active`: 상장폐지 종목 관리
- `listing_shares`: 시가총액 계산에 사용

**예상 레코드 수**: 약 3,000개 (현재 + 폐지)

---

### 2.2 stock_price (주식 가격 - OHLCV)

**목적**: 일별 주식 가격 데이터

```sql
CREATE TABLE stock_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    -- OHLCV
    open REAL NOT NULL,                    -- 시가
    high REAL NOT NULL,                    -- 고가
    low REAL NOT NULL,                     -- 저가
    close REAL NOT NULL,                   -- 종가
    volume BIGINT NOT NULL,                -- 거래량 (주)

    -- 추가 정보
    trading_value BIGINT,                  -- 거래대금 (원)
    change_rate REAL,                      -- 등락률 (%)
    shares_traded BIGINT,                  -- 거래된 주식수

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);

-- 필수 인덱스
CREATE UNIQUE INDEX idx_stock_price_ticker_date ON stock_price(ticker, date);
CREATE INDEX idx_stock_price_date ON stock_price(date);
CREATE INDEX idx_stock_price_ticker ON stock_price(ticker);

-- 분석용 인덱스
CREATE INDEX idx_stock_price_volume ON stock_price(volume DESC);
CREATE INDEX idx_stock_price_change ON stock_price(change_rate DESC);
```

**설계 결정**:
- `volume`: BIGINT (21억 초과 가능)
- `UNIQUE (ticker, date)`: 중복 방지, UPSERT 가능
- `ON DELETE CASCADE`: 폐지 종목 삭제 시 가격 데이터도 삭제

**예상 레코드 수**:
- 2,500 종목 × 2,400 거래일 = **6,000,000 레코드**
- 예상 크기: 약 500MB

---

### 2.3 market_data (시장 데이터 - 재무지표)

**목적**: 시가총액, 재무 지표

```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    -- 시가총액 관련
    market_cap BIGINT,                     -- 시가총액 (원)
    listed_shares BIGINT,                  -- 상장주식수
    outstanding_shares BIGINT,             -- 유통주식수

    -- 재무 지표 (NULL 허용 - 적자 기업 등)
    per REAL,                              -- PER (주가수익비율)
    pbr REAL,                              -- PBR (주가순자산비율)
    eps REAL,                              -- EPS (주당순이익)
    bps REAL,                              -- BPS (주당순자산)
    div REAL,                              -- DIV (배당수익률, %)
    dps REAL,                              -- DPS (주당배당금, 원)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);

CREATE UNIQUE INDEX idx_market_data_ticker_date ON market_data(ticker, date);
CREATE INDEX idx_market_data_date ON market_data(date);

-- 분석용 인덱스 (시가총액 순위, 밸류에이션 분석)
CREATE INDEX idx_market_data_market_cap ON market_data(market_cap DESC);
CREATE INDEX idx_market_data_per ON market_data(per);
CREATE INDEX idx_market_data_pbr ON market_data(pbr);
```

**설계 결정**:
- 재무지표 NULL 허용: 적자 기업은 PER/EPS가 없음
- `market_cap`: BIGINT (삼성전자 시총 약 500조)

**예상 레코드 수**: 6,000,000 레코드, 약 600MB

---

### 2.4 investor_trading (투자자별 매매) ⭐ 매우 중요!

**목적**: 기관/외국인 매매 데이터 (네이버 금융 제공)

**주의**: 네이버 금융은 개인 매매 데이터를 직접 제공하지 않음

```sql
CREATE TABLE investor_trading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    -- 순매수 (단위: 주) - 가장 중요!
    institution_net_buy BIGINT DEFAULT 0,  -- 기관 순매수
    foreign_net_buy BIGINT DEFAULT 0,      -- 외국인 순매수
    individual_net_buy BIGINT DEFAULT 0,   -- 개인 순매수

    -- 매수 (단위: 주)
    institution_buy BIGINT DEFAULT 0,
    foreign_buy BIGINT DEFAULT 0,
    individual_buy BIGINT DEFAULT 0,

    -- 매도 (단위: 주)
    institution_sell BIGINT DEFAULT 0,
    foreign_sell BIGINT DEFAULT 0,
    individual_sell BIGINT DEFAULT 0,

    -- 거래대금 (단위: 원) - 선택적
    institution_trading_value BIGINT,
    foreign_trading_value BIGINT,
    individual_trading_value BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);

CREATE UNIQUE INDEX idx_investor_ticker_date ON investor_trading(ticker, date);
CREATE INDEX idx_investor_date ON investor_trading(date);

-- 수급 분석용 인덱스 (외국인/기관 매매 추세)
CREATE INDEX idx_investor_foreign_net ON investor_trading(foreign_net_buy DESC);
CREATE INDEX idx_investor_institution_net ON investor_trading(institution_net_buy DESC);
CREATE INDEX idx_investor_individual_net ON investor_trading(individual_net_buy DESC);
```

**설계 결정**:
- `DEFAULT 0`: NULL 대신 0 사용 (계산 편의)
- 순매수 = 매수 - 매도 (네이버 금융에서 직접 제공)
- **개인 데이터**: 네이버는 제공하지 않으므로 `individual_net_buy`는 기본값 0 또는 계산값

**활용도**:
- 🔥 **가장 중요한 테이블!**
- 외국인/기관 매수 종목 찾기
- 수급 패턴 분석
- AI 학습 특성(Feature)

**예상 레코드 수**: 6,000,000 레코드, 약 800MB

---

## 3. 확장 테이블 (Phase 2 - 중요)

### 3.1 short_selling (공매도)

```sql
CREATE TABLE short_selling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    short_volume BIGINT,                   -- 공매도 거래량 (주)
    short_value BIGINT,                    -- 공매도 거래대금 (원)
    short_balance BIGINT,                  -- 공매도 잔고 (주)
    balance_ratio REAL,                    -- 잔고 비율 (%, 전체 대비)
    short_ratio REAL,                      -- 공매도 비율 (%, 거래량 대비)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);

CREATE UNIQUE INDEX idx_short_ticker_date ON short_selling(ticker, date);
CREATE INDEX idx_short_balance_ratio ON short_selling(balance_ratio DESC);
CREATE INDEX idx_short_ratio ON short_selling(short_ratio DESC);
```

**활용도**: 공매도 비율 높은 종목 (반등 가능성)

**예상 레코드 수**: 500 종목 × 2,400일 = 1,200,000 레코드

---

### 3.2 index_info (지수 정보)

```sql
CREATE TABLE index_info (
    code TEXT PRIMARY KEY,                 -- 지수 코드 (예: '1001' = KOSPI)
    name TEXT NOT NULL,                    -- 지수명
    market TEXT,                           -- 시장: KOSPI, KOSDAQ
    base_date DATE,                        -- 기준일
    base_value REAL,                       -- 기준값
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**주요 지수**:
- 1001: KOSPI
- 2001: KOSDAQ
- 업종별 지수 약 30개

---

### 3.3 index_price (지수 가격)

```sql
CREATE TABLE index_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    date DATE NOT NULL,

    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume BIGINT,                         -- 거래량
    trading_value BIGINT,                  -- 거래대금
    change_rate REAL,                      -- 등락률

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (code) REFERENCES index_info(code) ON DELETE CASCADE,
    UNIQUE (code, date)
);

CREATE UNIQUE INDEX idx_index_price_code_date ON index_price(code, date);
CREATE INDEX idx_index_price_date ON index_price(date);
```

**활용도**: 시장 추세 분석, 베타 계산

**예상 레코드 수**: 40 지수 × 2,400일 = 96,000 레코드

---

## 4. 고급 테이블 (Phase 3 - 선택)

### 4.1 margin_trading (신용거래)

```sql
CREATE TABLE margin_trading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    credit_balance BIGINT,                 -- 신용잔고
    credit_buy BIGINT,                     -- 신용매수
    credit_repay BIGINT,                   -- 신용상환
    loan_balance BIGINT,                   -- 융자잔고
    loan_new BIGINT,                       -- 융자신규
    loan_repay BIGINT,                     -- 융자상환

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);
```

---

### 4.2 foreign_limit (외국인 한도)

```sql
CREATE TABLE foreign_limit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    limit_shares BIGINT,                   -- 한도 주식수
    holding_shares BIGINT,                 -- 외국인 보유 주식수
    available_shares BIGINT,               -- 매수 가능 주식수
    exhaustion_rate REAL,                  -- 소진율 (%)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);
```

---

### 4.3 etf_info, etf_price (ETF)

```sql
CREATE TABLE etf_info (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    underlying_index TEXT,                 -- 기초지수
    etf_type TEXT,                         -- 유형: 주식형, 채권형
    issuer TEXT,                           -- 운용사
    listing_date DATE,
    expense_ratio REAL,                    -- 총보수 (%)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE etf_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume BIGINT NOT NULL,
    trading_value BIGINT,
    nav REAL,                              -- 순자산가치 (NAV)
    tracking_error REAL,                   -- 추적오차
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES etf_info(ticker) ON DELETE CASCADE,
    UNIQUE (ticker, date)
);
```

---

### 4.4 sector_info (업종 정보)

```sql
CREATE TABLE sector_info (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_code TEXT,                      -- 상위 업종
    level INTEGER,                         -- 1:대분류, 2:중분류, 3:소분류
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_code) REFERENCES sector_info(code)
);
```

---

## 5. 관리 테이블

### 5.1 data_collection_log (수집 로그)

**이미 구현됨**

```sql
CREATE TABLE data_collection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_type TEXT NOT NULL,         -- 'price', 'investor', 'short' 등
    ticker TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT NOT NULL,                  -- 'success', 'failed', 'partial'
    record_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds REAL,

    INDEX idx_collection_log_date(started_at),
    INDEX idx_collection_log_ticker(ticker)
);
```

---

### 5.2 collection_progress (진행 상황 추적)

**신규 - BulkCollector용**

```sql
CREATE TABLE collection_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase INTEGER NOT NULL,                -- 1, 2, 3
    collection_type TEXT NOT NULL,         -- 'daily', 'stock_info', 'index'
    target_date DATE,                      -- 현재 수집 중인 날짜
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- 진행률
    total_items INTEGER DEFAULT 0,         -- 전체 항목 수
    completed_items INTEGER DEFAULT 0,     -- 완료 항목 수
    failed_items INTEGER DEFAULT 0,        -- 실패 항목 수

    -- 상태
    status TEXT NOT NULL,                  -- 'pending', 'running', 'completed', 'paused', 'failed'
    error_message TEXT,

    -- 시간
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_completion TIMESTAMP,        -- 예상 완료 시각
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_progress_phase(phase),
    INDEX idx_progress_status(status)
);
```

**활용도**:
- 수집 중단 시 재개 지점 파악
- 진행률 표시
- 예상 완료 시간 계산

---

### 5.3 data_quality_check (데이터 품질)

**신규 - 검증용**

```sql
CREATE TABLE data_quality_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date DATE NOT NULL,
    table_name TEXT NOT NULL,
    check_type TEXT NOT NULL,              -- 'completeness', 'accuracy', 'consistency'

    -- 완전성 체크
    expected_count INTEGER,
    actual_count INTEGER,
    missing_count INTEGER,
    missing_dates TEXT,                    -- JSON array

    -- 결과
    status TEXT NOT NULL,                  -- 'pass', 'fail', 'warning'
    message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_quality_table(table_name),
    INDEX idx_quality_date(check_date)
);
```

**활용도**:
- 일별 데이터 누락 확인
- 거래일 vs 실제 데이터 확인
- 품질 리포트 생성

---

## 6. 테이블 간 관계도 (ERD)

```
stock_info (1) ─┬─ (N) stock_price
                ├─ (N) market_data
                ├─ (N) investor_trading
                ├─ (N) short_selling
                ├─ (N) margin_trading
                └─ (N) foreign_limit

index_info (1) ──── (N) index_price

etf_info (1) ────── (N) etf_price

sector_info (1) ─┬─ (N) stock_info
                 └─ (N) sector_info (self join)
```

---

## 7. 데이터 크기 추정 (2010~2025, 15년)

| 테이블 | 레코드 수 | 예상 크기 | 비고 |
|--------|-----------|-----------|------|
| stock_info | 3,000 | 1MB | 정적 데이터 |
| stock_price | 9,000,000 | 750MB | 가장 큼 (15년) |
| market_data | 9,000,000 | 900MB | PER, PBR 등 |
| investor_trading | 9,000,000 | 1,200MB | 기관/외국인만 |
| short_selling | 1,800,000 | 200MB | 일부 종목만 |
| index_price | 144,000 | 15MB | 40개 지수 |
| margin_trading | 9,000,000 | 750MB | Phase 3 |
| etf_price | 1,800,000 | 150MB | 500개 ETF |
| **합계** | **~42M** | **~3.9GB** | |

**실제 크기**: 압축 및 인덱스 포함 시 약 **4.5~5GB**

---

## 8. 성능 최적화 전략

### 8.1 인덱스 전략

**필수 인덱스** (모든 일별 데이터 테이블):
```sql
UNIQUE INDEX (ticker, date)  -- 중복 방지, 조회 속도
INDEX (date)                 -- 날짜별 조회
INDEX (ticker)               -- 종목별 조회
```

**분석용 인덱스** (선택):
```sql
INDEX (market_cap DESC)      -- 시총 순위
INDEX (foreign_net_buy DESC) -- 외국인 매수 순위
INDEX (volume DESC)          -- 거래량 순위
```

### 8.2 SQLite 최적화

```sql
-- WAL 모드
PRAGMA journal_mode=WAL;

-- 캐시 크기 증가
PRAGMA cache_size=10000;

-- 동기화 수준 조정
PRAGMA synchronous=NORMAL;

-- 임시 저장소
PRAGMA temp_store=MEMORY;
```

### 8.3 쿼리 최적화

```sql
-- 나쁜 예
SELECT * FROM stock_price WHERE ticker='005930' AND date BETWEEN '2015-01-01' AND '2024-12-31';

-- 좋은 예 (필요한 컬럼만)
SELECT date, close, volume FROM stock_price
WHERE ticker='005930' AND date BETWEEN '2015-01-01' AND '2024-12-31';

-- 매우 좋은 예 (인덱스 활용)
SELECT date, close, volume FROM stock_price
WHERE ticker='005930' AND date >= '2015-01-01' AND date <= '2024-12-31'
ORDER BY date;
```

---

## 9. 백업 및 유지보수

### 9.1 백업 전략

```bash
# 전체 백업
cp stock_data.db stock_data_backup_$(date +%Y%m%d).db

# 압축 백업
sqlite3 stock_data.db ".backup stock_data_backup.db"
gzip stock_data_backup.db
```

### 9.2 VACUUM

```sql
-- 주기적으로 실행 (용량 최적화)
VACUUM;

-- 자동 VACUUM 설정
PRAGMA auto_vacuum=FULL;
```

### 9.3 데이터 정리

```sql
-- 상장폐지 5년 이상 종목 삭제
DELETE FROM stock_info
WHERE is_active=0
AND delisting_date < date('now', '-5 years');
```

---

## 10. 마이그레이션 고려사항

### 10.1 PostgreSQL로 마이그레이션 시

**장점**:
- 파티셔닝 지원 (연도별 분할)
- 더 나은 동시성
- 고급 인덱스 (BRIN, GiST)

**마이그레이션 시점**:
- DB 크기 > 5GB
- 동시 접속 > 10명
- 복잡한 분석 쿼리 필요 시

### 10.2 스키마 호환성

현재 SQLAlchemy 사용 → PostgreSQL 마이그레이션 용이

---

## 11. 요약 및 권장사항

### 우선순위별 구현 계획

**Phase 1 (필수, 즉시)**:
- ✅ stock_info (이미 구현)
- ✅ stock_price (이미 구현)
- ✅ market_data (이미 구현)
- ❌ investor_trading (구현 필요! 가장 중요)

**Phase 2 (중요, 1주일 내)**:
- ❌ short_selling
- ❌ index_info, index_price

**Phase 3 (선택, 필요시)**:
- ❌ margin_trading, foreign_limit, etf_*, sector_*

**관리 테이블**:
- ✅ data_collection_log (이미 구현)
- ❌ collection_progress (BulkCollector 필요)
- ❌ data_quality_check (검증 필요)

### 다음 단계

1. **models.py 확장**: Phase 1 테이블 추가
2. **Repository 구현**: InvestorTradingRepository
3. **Collector 구현**: InvestorTradingCollector
4. **BulkCollector**: 전체 수집 관리

---

## 부록: SQL DDL 전체

전체 테이블 생성 SQL은 별도 파일 참조:
- `sql/schema_phase1.sql`: Phase 1 테이블
- `sql/schema_phase2.sql`: Phase 2 테이블
- `sql/schema_phase3.sql`: Phase 3 테이블
