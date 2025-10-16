# PyKRX 데이터 수집 가이드

## PyKRX로 수집 가능한 모든 데이터 정리

### 1. 주식 시장 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_market_ticker_list()` | 종목 코드 목록 | ticker | stock_info | ⭐⭐⭐ |
| `get_market_ticker_name()` | 종목명 조회 | ticker, name | stock_info | ⭐⭐⭐ |
| `get_market_ohlcv()` | OHLCV 데이터 | 시가/고가/저가/종가/거래량 | stock_price | ⭐⭐⭐ |
| `get_market_price_change()` | 가격 변동 | 시가/고가/저가/종가/등락률 | stock_price | ⭐⭐ |
| `get_market_cap()` | 시가총액 | 시가총액/상장주식수 | market_data | ⭐⭐⭐ |
| `get_market_fundamental()` | 기본적 분석 | BPS/PER/PBR/EPS/DIV/DPS | market_data | ⭐⭐⭐ |
| `get_market_trading_value()` | 거래대금 | 거래대금/거래량 | stock_price | ⭐⭐ |
| `get_market_trading_volume()` | 거래량 | 거래량/거래대금 | stock_price | ⭐⭐ |

### 2. 지수 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_index_ticker_list()` | 지수 코드 목록 | 지수코드 | index_info | ⭐⭐ |
| `get_index_ticker_name()` | 지수명 조회 | 지수코드, 지수명 | index_info | ⭐⭐ |
| `get_index_ohlcv()` | 지수 OHLCV | 시가/고가/저가/종가/거래량 | index_price | ⭐⭐ |
| `get_index_portfolio_deposit_file()` | 지수 구성 종목 | 종목코드, 비중 | index_composition | ⭐ |
| `get_index_price_change()` | 지수 등락률 | 종가/등락률 | index_price | ⭐ |

### 3. ETF/ETN 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_etf_ticker_list()` | ETF 목록 | ETF 코드 | etf_info | ⭐⭐ |
| `get_etf_ohlcv()` | ETF OHLCV | 시가/고가/저가/종가/거래량 | etf_price | ⭐⭐ |
| `get_etf_portfolio_deposit_file()` | ETF 구성 종목 | 종목코드, 비중 | etf_composition | ⭐ |
| `get_etf_trading_volume()` | ETF 거래량 | 거래량/거래대금 | etf_price | ⭐ |

### 4. 투자자별 매매 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_market_net_purchases_of_equities()` | 순매수 현황 | 기관/외국인/개인 순매수 | investor_trading | ⭐⭐⭐ |
| `get_market_trading_value_by_investor()` | 투자자별 거래대금 | 기관/외국인/개인 거래대금 | investor_trading | ⭐⭐ |
| `get_market_trading_volume_by_investor()` | 투자자별 거래량 | 기관/외국인/개인 거래량 | investor_trading | ⭐⭐ |

### 5. 공매도 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_shorting_status_by_date()` | 공매도 현황 | 공매도 잔고/비중 | short_selling | ⭐⭐ |
| `get_shorting_volume_by_ticker()` | 종목별 공매도 | 공매도 거래량/잔고 | short_selling | ⭐⭐ |
| `get_shorting_investor_by_date()` | 투자자별 공매도 | 기관/외국인 공매도 | short_selling | ⭐ |

### 6. 신용/대출 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_market_margin_trading()` | 신용거래 | 신용잔고/융자잔고 | margin_trading | ⭐ |
| `get_exhaustion_rates_of_foreign_investment()` | 외국인 한도소진율 | 한도/잔량/소진율 | foreign_limit | ⭐ |

### 7. 섹터/업종 데이터

| 함수명 | 설명 | 제공 정보 | DB 테이블 | 우선순위 |
|--------|------|-----------|-----------|----------|
| `get_market_ticker_and_name()` | 종목+업종 | 종목코드/종목명/업종 | stock_info | ⭐⭐ |
| `get_market_sector_classifications()` | 업종 분류 | 업종코드/업종명 | sector_info | ⭐ |

---

## 제안하는 데이터베이스 테이블 구조

### 핵심 테이블 (우선순위 ⭐⭐⭐)

#### 1. stock_info (종목 정보)
```sql
CREATE TABLE stock_info (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market TEXT NOT NULL,          -- KOSPI, KOSDAQ, KONEX
    sector TEXT,                   -- 업종
    sector_code TEXT,              -- 업종 코드
    listing_date DATE,             -- 상장일
    listing_shares BIGINT,         -- 상장주식수
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 2. stock_price (주식 가격 - OHLCV)
```sql
CREATE TABLE stock_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume BIGINT NOT NULL,
    trading_value BIGINT,          -- 거래대금
    change_rate REAL,              -- 등락률
    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);

CREATE INDEX ix_stock_price_ticker_date ON stock_price(ticker, date);
CREATE INDEX ix_stock_price_date ON stock_price(date);
CREATE INDEX ix_stock_price_volume ON stock_price(volume);
```

#### 3. market_data (시장 데이터 - 시가총액/재무지표)
```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    market_cap BIGINT,             -- 시가총액
    listed_shares BIGINT,          -- 상장주식수
    per REAL,                      -- PER (주가수익비율)
    pbr REAL,                      -- PBR (주가순자산비율)
    eps REAL,                      -- EPS (주당순이익)
    bps REAL,                      -- BPS (주당순자산)
    div REAL,                      -- DIV (배당수익률)
    dps REAL,                      -- DPS (주당배당금)
    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);

CREATE INDEX ix_market_data_ticker_date ON market_data(ticker, date);
CREATE INDEX ix_market_data_market_cap ON market_data(market_cap);
CREATE INDEX ix_market_data_per ON market_data(per);
```

#### 4. investor_trading (투자자별 매매 데이터)
```sql
CREATE TABLE investor_trading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    -- 순매수 (단위: 주)
    institution_net_buy BIGINT,     -- 기관 순매수
    foreign_net_buy BIGINT,         -- 외국인 순매수
    individual_net_buy BIGINT,      -- 개인 순매수

    -- 매수 (단위: 주)
    institution_buy BIGINT,         -- 기관 매수
    foreign_buy BIGINT,             -- 외국인 매수
    individual_buy BIGINT,          -- 개인 매수

    -- 매도 (단위: 주)
    institution_sell BIGINT,        -- 기관 매도
    foreign_sell BIGINT,            -- 외국인 매도
    individual_sell BIGINT,         -- 개인 매도

    -- 거래대금 (단위: 원)
    institution_trading_value BIGINT,
    foreign_trading_value BIGINT,
    individual_trading_value BIGINT,

    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);

CREATE INDEX ix_investor_ticker_date ON investor_trading(ticker, date);
CREATE INDEX ix_investor_foreign_net ON investor_trading(foreign_net_buy);
```

### 확장 테이블 (우선순위 ⭐⭐)

#### 5. short_selling (공매도 데이터)
```sql
CREATE TABLE short_selling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    short_volume BIGINT,            -- 공매도 거래량
    short_value BIGINT,             -- 공매도 거래대금
    short_balance BIGINT,           -- 공매도 잔고
    balance_ratio REAL,             -- 잔고 비율 (%)
    short_ratio REAL,               -- 공매도 비율 (%)

    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);

CREATE INDEX ix_short_ticker_date ON short_selling(ticker, date);
CREATE INDEX ix_short_balance_ratio ON short_selling(balance_ratio);
```

#### 6. index_info (지수 정보)
```sql
CREATE TABLE index_info (
    code TEXT PRIMARY KEY,          -- 지수 코드 (예: 1001)
    name TEXT NOT NULL,             -- 지수명 (예: KOSPI)
    market TEXT,                    -- 시장 구분
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 7. index_price (지수 가격)
```sql
CREATE TABLE index_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,             -- 지수 코드
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume BIGINT,
    trading_value BIGINT,
    change_rate REAL,
    created_at TIMESTAMP,

    FOREIGN KEY (code) REFERENCES index_info(code),
    UNIQUE (code, date)
);

CREATE INDEX ix_index_price_code_date ON index_price(code, date);
```

### 선택 테이블 (우선순위 ⭐)

#### 8. margin_trading (신용거래)
```sql
CREATE TABLE margin_trading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    credit_balance BIGINT,          -- 신용잔고
    credit_buy BIGINT,              -- 신용매수
    credit_repay BIGINT,            -- 신용상환
    loan_balance BIGINT,            -- 융자잔고
    loan_new BIGINT,                -- 융자신규
    loan_repay BIGINT,              -- 융자상환

    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);
```

#### 9. foreign_limit (외국인 한도)
```sql
CREATE TABLE foreign_limit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    limit_shares BIGINT,            -- 한도 주식수
    holding_shares BIGINT,          -- 보유 주식수
    available_shares BIGINT,        -- 매수 가능 주식수
    exhaustion_rate REAL,           -- 소진율 (%)

    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (ticker, date)
);
```

#### 10. etf_info (ETF 정보)
```sql
CREATE TABLE etf_info (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    underlying_index TEXT,          -- 기초지수
    etf_type TEXT,                  -- ETF 유형
    listing_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 11. etf_price (ETF 가격)
```sql
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
    nav REAL,                       -- 순자산가치
    tracking_error REAL,            -- 추적 오차
    created_at TIMESTAMP,

    FOREIGN KEY (ticker) REFERENCES etf_info(ticker),
    UNIQUE (ticker, date)
);
```

#### 12. index_composition (지수 구성 종목)
```sql
CREATE TABLE index_composition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code TEXT NOT NULL,       -- 지수 코드
    ticker TEXT NOT NULL,           -- 종목 코드
    date DATE NOT NULL,             -- 기준일
    weight REAL,                    -- 비중 (%)
    shares BIGINT,                  -- 주식수
    created_at TIMESTAMP,

    FOREIGN KEY (index_code) REFERENCES index_info(code),
    FOREIGN KEY (ticker) REFERENCES stock_info(ticker),
    UNIQUE (index_code, ticker, date)
);
```

#### 13. sector_info (업종 정보)
```sql
CREATE TABLE sector_info (
    code TEXT PRIMARY KEY,          -- 업종 코드
    name TEXT NOT NULL,             -- 업종명
    parent_code TEXT,               -- 상위 업종 코드
    level INTEGER,                  -- 레벨 (1:대분류, 2:중분류, 3:소분류)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 단계별 데이터 수집 계획

### Phase 1: 필수 데이터 (즉시 구현)
1. ✅ stock_info - 종목 기본 정보
2. ✅ stock_price - OHLCV 데이터
3. ✅ market_data - 시가총액, 재무지표

### Phase 2: 핵심 분석 데이터 (우선 구현)
4. investor_trading - 투자자별 매매
5. short_selling - 공매도 데이터

### Phase 3: 지수 및 ETF (선택 구현)
6. index_info, index_price - 지수 데이터
7. etf_info, etf_price - ETF 데이터

### Phase 4: 고급 데이터 (필요시 구현)
8. margin_trading - 신용거래
9. foreign_limit - 외국인 한도
10. index_composition - 지수 구성
11. sector_info - 업종 분류

---

## PyKRX API 사용 예시

### 1. 종목 정보 수집
```python
from pykrx import stock

# 종목 리스트
tickers = stock.get_market_ticker_list("20240101", market="KOSPI")

# 종목명
name = stock.get_market_ticker_name("005930")  # 삼성전자
```

### 2. OHLCV 데이터
```python
# 특정 종목 OHLCV
df = stock.get_market_ohlcv("20240101", "20241231", "005930")
```

### 3. 시가총액 및 재무지표
```python
# 시가총액
cap = stock.get_market_cap("20240101", market="KOSPI")

# 기본적 분석
fundamental = stock.get_market_fundamental("20240101", market="KOSPI")
```

### 4. 투자자별 매매
```python
# 순매수 현황
net = stock.get_market_net_purchases_of_equities("20240101", "20241231", "005930")

# 거래대금
trading = stock.get_market_trading_value_by_investor("20240101", "20241231", "005930")
```

### 5. 공매도
```python
# 공매도 현황
short = stock.get_shorting_status_by_date("20240101", "20241231", "005930")
```

---

## 데이터 수집 우선순위 및 활용도

### ⭐⭐⭐ 최고 우선순위 (필수)
- **stock_price**: 가격 분석, 차트 패턴, 기술적 지표
- **market_data**: 밸류에이션 분석, 펀더멘털 분석
- **investor_trading**: 수급 분석, 기관/외국인 매매 추세

### ⭐⭐ 높은 우선순위 (권장)
- **short_selling**: 공매도 분석, 반대 지표
- **index_price**: 시장 추세 분석, 베타 계산

### ⭐ 보통 우선순위 (선택)
- **margin_trading**: 신용 거래 분석
- **etf_data**: ETF 투자 전략
- **sector_info**: 업종 분석

---

## 데이터 크기 추정

| 테이블 | 종목 수 | 일 데이터 | 1년 데이터 | 3년 데이터 |
|--------|---------|-----------|-----------|-----------|
| stock_price | 2,500 | 2,500 | ~625K | ~1.9M |
| market_data | 2,500 | 2,500 | ~625K | ~1.9M |
| investor_trading | 2,500 | 2,500 | ~625K | ~1.9M |
| short_selling | 100 (일부) | 100 | ~25K | ~75K |

**예상 DB 크기**: 3년치 데이터 약 **500MB ~ 1GB**
