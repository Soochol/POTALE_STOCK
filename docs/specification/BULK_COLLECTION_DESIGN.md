# 대량 데이터 수집 시스템 설계서

## 0. 하이브리드 수집 방식 (최신 업데이트)

### 0.1 NaverHybridCollector 개요

**기존 문제점**:
- 네이버 금융 sise_day.nhn: 원본 주가/원본 거래량 제공
- 액면분할/병합 발생 시 주가는 조정되지만 거래량은 조정되지 않음
- 결과: 분할 전후 거래량 비교 불가 (예: 아난티 2018-05-17 분할 시 42배 차이)

**해결책: 하이브리드 수집**

1. **수정주가 수집** (fchart API)
   ```
   URL: https://fchart.stock.naver.com/siseJson.nhn
   Parameter: requestType=1  # 수정주가 요청

   응답 형식:
   [["날짜", "시가", "고가", "저가", "종가", "거래량", "외국인비율"],
    ["20180402", 6960, 7180, 6790, 6810, 136356, 36.21], ...]

   특징:
   - OHLC: 액면분할이 자동 반영된 조정 가격
   - 거래량: 원본 거래량 (조정되지 않음)
   ```

2. **원본 데이터 수집** (sise_day.nhn)
   ```
   URL: https://finance.naver.com/item/sise_day.nhn

   특징:
   - OHLC: 실제 거래된 원본 가격
   - 거래량: 원본 거래량
   ```

3. **수정거래량 자동 계산**
   ```python
   # 조정 비율 계산
   adjustment_ratio = raw_close / adj_close

   # 수정거래량 계산
   if abs(adjustment_ratio - 1.0) > 0.05:
       # 액면분할 전: 거래량 조정 필요
       adjusted_volume = raw_volume × adjustment_ratio
   else:
       # 액면분할 후: 조정 불필요
       adjusted_volume = raw_volume
   ```

4. **검증**
   ```python
   # 거래대금 일치 여부 확인
   trading_value = adjusted_close × adjusted_volume

   # 원본 거래대금과 비교
   raw_trading_value = raw_close × raw_volume

   # 결과: trading_value == raw_trading_value ✅
   ```

### 0.2 저장되는 데이터 필드

```sql
CREATE TABLE stock_price (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,

    -- 수정주가 (fchart API)
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,

    -- 수정거래량 (자동 계산)
    volume INTEGER NOT NULL,

    -- 거래대금 (검증용)
    trading_value INTEGER,

    -- 조정 정보 (참고용)
    adjustment_ratio REAL,
    raw_close REAL,
    raw_volume INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date)
);
```

### 0.3 실제 예시: 아난티 (025980) 액면분할

```
날짜: 2018-05-17
이벤트: 1:4 액면분할 (실제 조정비율 5.0x)

분할 전 (2018-04-02):
  fchart 수정주가:  6,810원
  sise_day 원본주가: 34,050원
  조정비율: 34,050 / 6,810 = 5.0x

  원본 거래량: 136,356주
  수정거래량: 136,356 × 5.0 = 681,780주

  거래대금 검증:
    수정: 6,810 × 681,780 = 4,643,121,800원
    원본: 34,050 × 136,356 = 4,643,121,800원 ✅

분할 후 (2018-05-17):
  fchart 수정주가: 9,400원
  sise_day 원본주가: 9,400원
  조정비율: 9,400 / 9,400 = 1.0x

  원본 거래량: 16,164,141주
  수정거래량: 16,164,141주 (조정 불필요)

  거래대금 검증:
    수정: 9,400 × 16,164,141 = 151,942,925,400원
    원본: 9,400 × 16,164,141 = 151,942,925,400원 ✅
```

### 0.4 하이브리드 수집의 장점

✅ **데이터 일관성**
- 액면분할/병합이 자동으로 반영된 수정주가
- 수정거래량도 자동 계산되어 일관성 유지

✅ **기술적 분석 신뢰성**
- 이동평균, RSI 등 지표 계산 시 왜곡 방지
- 분할 전후 거래량 비교 가능

✅ **거래대금 검증**
- 수정주가 × 수정거래량 = 실제 거래대금
- 데이터 정확성 자동 검증

✅ **자동화**
- 기업 이벤트 DB 불필요
- 가격 비율만으로 자동 조정

---

## 1. 개요

### 1.1 목적
- **2010.01.01부터 현재**까지 한국 주식 시장의 모든 데이터 일괄 수집
- **NaverHybridCollector**를 통한 수정주가/수정거래량 자동 수집
- 중단 시 재개 가능한 견고한 시스템

### 1.2 수집 범위

| 항목 | 기간 | 종목 수 | 예상 데이터량 |
|------|------|---------|---------------|
| 주식 가격 | 2010.01.01 ~ 현재 | 2,500 | 9M 레코드 |
| 투자자 매매 | 2010.01.01 ~ 현재 | 2,500 | 9M 레코드 (기관/외국인) |
| 공매도 | 2010.01.01 ~ 현재 | 500 | 1.8M 레코드 |
| 지수 | 2010.01.01 ~ 현재 | 40 | 144K 레코드 |
| **합계** | **약 15년** | - | **~20M 레코드** |

### 1.3 예상 소요 시간

```
전제 조건:
- 웹 스크래핑 간격: 0.2초 (네이버 차단 방지)
- 하루 수집 시간: 8시간 (09:00~18:00)
- 네트워크: 안정적
```

| Phase | 내용 | 웹 요청 수 | 소요 시간 | 작업 일수 |
|-------|------|-------------|-----------|-----------|
| 준비 | 종목 정보 수집 | 2,500 | 10분 | 즉시 |
| Phase 1 | 가격 + 투자자 | 3,600일 | 2초/종목 | 30일 |
| Phase 2 | 공매도 + 지수 | 3,600일 | 1초/종목 | 15일 |
| Phase 3 | 신용거래 등 | 3,600일 | 2초/종목 | 30일 |
| **합계** | | | **약 75일** | **(연속 실행 시)** |

**주의**: 네이버 금융은 개별 종목 페이지를 스크래핑해야 하므로 PyKRX보다 느림

---

## 2. 수집 전략

### 2.1 종목별 수집 (네이버 금융의 한계)

**핵심 개념**: 네이버 금융은 **개별 종목 페이지**를 스크래핑해야 함

#### 네이버 금융 vs PyKRX 비교

| 항목 | 네이버 금융 | PyKRX |
|------|------------|-------|
| 수집 방식 | 종목별 페이지 스크래핑 | API (날짜별 일괄) |
| 호출 수 | 2,500종목 × 1회/종목 | 1회 (전체) |
| 효율성 | 낮음 | 매우 높음 |
| 속도 | 느림 (0.2초/종목) | 빠름 (0.1초/전체) |

#### 네이버 금융 수집 방식
   ```python
   # ❌ 날짜별 일괄 수집 불가능
   # 네이버는 개별 종목 페이지만 제공

   # ✅ 종목별로 수집해야 함
   for ticker in all_tickers:
       url = f"https://finance.naver.com/item/frgn.nhn?code={ticker}"
       df = scrape_investor_data(url)
       time.sleep(0.2)  # 차단 방지
   ```

#### 네이버 금융 수집 구조
```python
# 종목 리스트 (2,500개)
all_tickers = get_all_stock_tickers()

for ticker in all_tickers:
    try:
        # 1. 개별 종목 페이지 스크래핑
        url = f"https://finance.naver.com/item/frgn.nhn?code={ticker}"
        html = fetch_html(url)

        # 2. HTML 테이블 파싱
        df = parse_investor_table(html)  # 최근 30일치 데이터

        # 3. DB 저장
        save_investor_data(ticker, df)

        # 4. 진행 상황 업데이트
        update_progress(ticker)

        # 5. 차단 방지 대기
        time.sleep(0.2)  # 네이버는 0.2초 권장

    except Exception as e:
        log_error(ticker, e)
        continue
```

**장점**:
- 네이버 금융은 2010년부터 데이터 제공 (PyKRX보다 오래됨)
- 안정적 (KRX API 차단 없음)

**단점**:
- 느림 (2,500종목 × 0.2초 = 8.3분/회)
- HTML 파싱 필요
- 페이지 구조 변경 시 코드 수정 필요

---

### 2.2 Phase별 수집 전략

#### Phase 1: 핵심 데이터 (필수)

**대상**:
- stock_price (OHLCV)
- market_data (시가총액, PER, PBR)
- investor_trading (투자자별 매매)

**수집 방식**:
```python
def collect_phase1_for_ticker(ticker, fromdate, todate):
    """Phase 1: 특정 종목의 투자자 거래 데이터 수집"""

    # 1. 네이버 금융 개별 종목 페이지
    url = f"https://finance.naver.com/item/frgn.nhn?code={ticker}"

    # 2. HTML 가져오기
    headers = {
        'User-Agent': 'Mozilla/5.0 ...',
    }
    response = requests.get(url, headers=headers)

    # 3. 테이블 파싱 (pandas read_html)
    dfs = pd.read_html(StringIO(response.text), encoding='cp949')
    investor_df = dfs[3]  # 4번째 테이블이 투자자 거래 데이터

    # 4. 데이터 정제
    records = []
    for idx, row in investor_df.iterrows():
        date_str = str(row['날짜'])  # '24.09.20' 형식
        if date_str in ['nan', 'NaN']:
            continue

        # 날짜 변환
        parts = date_str.split('.')
        year = 2000 + int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        trade_date = date(year, month, day)

        # 기관/외국인 순매수량
        institution_net = row['기관_순매수량']
        foreign_net = row['외국인_순매수량']

        records.append({
            'ticker': ticker,
            'date': trade_date,
            'institution_net_buy': institution_net,
            'foreign_net_buy': foreign_net,
            'individual_net_buy': 0,  # 네이버는 제공 안함
        })

    # 5. DB 저장
    bulk_upsert(records)

    return len(records)
```

**웹 요청 수**: 종목당 1회
**소요 시간**: 약 0.2초/종목 (2,500종목 = 8.3분)

---

#### Phase 2: 확장 데이터

**대상**:
- short_selling (공매도)
- index_price (지수)

**수집 방식**:
```python
def collect_phase2_daily(target_date):
    """Phase 2: 공매도 + 지수"""

    # 1. 공매도 현황 (거래량이 많은 종목만)
    short_tickers = get_top_volume_tickers(date, top_n=500)
    for ticker in short_tickers:
        short_data = get_shorting_status_by_date(
            fromdate=date,
            todate=date,
            ticker=ticker
        )
        save_short_selling(short_data)

    # 2. 지수 데이터 (KOSPI, KOSDAQ, 업종별)
    index_codes = ['1001', '2001', ...]  # 약 40개
    for code in index_codes:
        index_ohlcv = get_index_ohlcv(date, code)
        save_index_price(index_ohlcv)
```

**API 호출 수**: 날짜당 540회 (500 + 40)
**소요 시간**: 약 1분/일

---

#### Phase 3: 고급 데이터 (선택)

**대상**:
- margin_trading (신용거래)
- foreign_limit (외국인 한도)
- etf_price (ETF)

**수집 방식**: Phase 1과 유사

---

### 2.3 멀티프로세싱 전략 (불가능)

**네이버 금융에서는 멀티프로세싱 권장하지 않음**

**이유**:
1. **IP 차단 위험**: 동시에 여러 요청 시 네이버가 봇으로 인식
2. **속도 제한**: User-Agent 체크 및 Rate Limiting
3. **안정성**: 단일 프로세스로도 충분히 빠름

**권장 방식**:
- **단일 프로세스** + 0.2초 간격
- 종목별 순차 수집
- 실패 시 재시도 로직

```python
# ❌ 멀티프로세싱 (위험)
with Pool(4) as pool:
    pool.map(collect_ticker, tickers)  # IP 차단 가능

# ✅ 단일 프로세스 (안전)
for ticker in tickers:
    collect_ticker(ticker)
    time.sleep(0.2)  # 필수!
```

---

## 3. 데이터 수집 흐름도

### 3.1 전체 흐름

```
[시작]
  ↓
[1. 종목 정보 수집]
  - stock_info 테이블 업데이트
  - 현재 상장 종목 목록 확보
  ↓
[2. 수집 계획 수립]
  - 시작일: 2015-01-01 (또는 마지막 수집일 다음날)
  - 종료일: 오늘
  - Phase 선택: 1, 2, 3
  ↓
[3. 거래일 필터링]
  - KRX 휴장일 제외 (토, 일, 공휴일)
  - 실제 거래일만 수집 (약 245일/년)
  ↓
[4. 날짜별 수집 루프]
  for each 거래일:
    ├─ Phase 1 수집
    ├─ Phase 2 수집 (선택)
    ├─ Phase 3 수집 (선택)
    ├─ 진행 상황 저장
    ├─ 에러 로깅
    └─ sleep(0.1초)
  ↓
[5. 완료]
  - 최종 통계 출력
  - 품질 검증
  - 누락 데이터 리포트
```

---

### 3.2 날짜별 수집 상세 흐름

```
[특정 날짜 D 수집]
  ↓
[1. 거래일 확인]
  - 주말/공휴일이면 Skip
  ↓
[2. 이미 수집 완료 확인]
  - collection_progress 테이블 체크
  - 완료되었으면 Skip
  ↓
[3. Phase 1: 핵심 데이터]
  ├─ OHLCV 전체 종목 (1회 API)
  ├─ 시가총액 전체 (1회 API)
  ├─ 재무지표 전체 (1회 API)
  └─ 투자자 매매 전체 (1회 API)
  ↓
[4. 데이터 검증]
  - 종목 수 확인 (2,500개 내외)
  - NULL 체크
  - 이상값 탐지
  ↓
[5. DB 저장]
  - Bulk Upsert (3개 테이블)
  - Transaction 사용
  ↓
[6. Phase 2 & 3 (선택)]
  - 공매도, 지수, 신용거래 등
  ↓
[7. 진행 상황 업데이트]
  - collection_progress 테이블
  - 완료 날짜 기록
  ↓
[8. 로그 저장]
  - data_collection_log
  - 성공/실패 기록
  ↓
[다음 날짜로]
```

---

## 4. 진행 상황 추적

### 4.1 collection_progress 테이블 활용

```sql
-- 진행 상황 저장
INSERT INTO collection_progress (
    phase, collection_type, target_date,
    start_date, end_date,
    total_items, completed_items,
    status, started_at
) VALUES (
    1, 'daily', '2015-01-05',
    '2015-01-01', '2024-12-31',
    2400, 5,  -- 전체 2400일 중 5일 완료
    'running', CURRENT_TIMESTAMP
);

-- 진행률 조회
SELECT
    phase,
    ROUND(completed_items * 100.0 / total_items, 2) as progress_pct,
    completed_items || '/' || total_items as progress,
    target_date as current_date,
    status
FROM collection_progress
WHERE status = 'running';
```

**출력 예시**:
```
Phase 1: 15.5% (372/2400) - Current: 2015-12-31 - Status: running
```

---

### 4.2 실시간 진행률 표시

```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

def bulk_collect_with_progress(start_date, end_date, phases):
    trading_days = get_trading_days(start_date, end_date)
    total_days = len(trading_days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TextColumn("ETA: {task.fields[eta]}"),
        console=console
    ) as progress:

        task = progress.add_task(
            f"[cyan]Phase {phases} 수집 중...",
            total=total_days,
            eta="계산 중..."
        )

        for idx, current_date in enumerate(trading_days):
            # 수집 실행
            collect_daily(current_date, phases)

            # 진행률 업데이트
            eta = calculate_eta(idx, total_days, start_time)
            progress.update(task, advance=1, eta=eta)
```

**출력 예시**:
```
⠋ Phase 1 수집 중... ████████░░░░░░░░░░░░ 40% (960/2400) ETA: 15일 3시간
```

---

## 5. 재개(Resume) 기능

### 5.1 중단 시나리오

수집 중단 가능 상황:
1. 네트워크 오류
2. API 제한 (429 Too Many Requests)
3. 사용자 중단 (Ctrl+C)
4. 시스템 재시작
5. 프로그램 오류

---

### 5.2 재개 메커니즘

```python
def resume_collection():
    """중단된 수집 재개"""

    # 1. 마지막 수집 날짜 조회
    last_progress = db.query(CollectionProgress)\
        .filter(CollectionProgress.status.in_(['running', 'paused']))\
        .order_by(CollectionProgress.target_date.desc())\
        .first()

    if not last_progress:
        print("재개할 수집 작업이 없습니다.")
        return

    # 2. 수집 재개
    resume_date = last_progress.target_date + timedelta(days=1)
    end_date = last_progress.end_date
    phases = last_progress.phase

    print(f"📍 {resume_date}부터 재개합니다...")

    # 3. 상태 업데이트
    last_progress.status = 'running'
    last_progress.updated_at = datetime.now()
    db.commit()

    # 4. 수집 실행
    bulk_collect(resume_date, end_date, phases)
```

**CLI 사용**:
```bash
# 중단된 수집 재개
python main.py collect bulk --resume

# 특정 날짜부터 재개
python main.py collect bulk --start-date 2020-01-01 --resume
```

---

### 5.3 자동 재시도

```python
def collect_with_retry(date, phases, max_retries=3):
    """재시도 로직"""

    for attempt in range(max_retries):
        try:
            result = collect_daily(date, phases)
            return result

        except APIRateLimitError:
            # API 제한 - 대기 후 재시도
            wait_time = (2 ** attempt) * 60  # 지수 백오프
            print(f"⏳ API 제한. {wait_time}초 대기...")
            time.sleep(wait_time)

        except NetworkError as e:
            # 네트워크 오류 - 짧게 대기
            print(f"⚠ 네트워크 오류: {e}. 10초 후 재시도...")
            time.sleep(10)

        except Exception as e:
            # 기타 오류 - 로깅 후 Skip
            print(f"❌ {date} 수집 실패: {e}")
            log_error(date, str(e))
            break

    return None
```

---

## 6. API 최적화

### 6.1 API 호출 최소화

**기존 방식 (비효율)**:
```python
# 종목별 루프 (2,500회 API 호출!)
for ticker in tickers:
    ohlcv = get_market_ohlcv(date, date, ticker)  # ❌
```

**개선 방식 (효율적)**:
```python
# 한번에 전체 수집 (1회 API 호출!)
all_ohlcv = get_market_ohlcv(date, market="ALL")  # ✅
```

---

### 6.2 API 호출 간격 조정

```python
# 기본: 0.1초
DEFAULT_DELAY = 0.1

# 동적 조정
if api_error_rate > 0.05:  # 5% 이상 에러
    delay *= 2  # 대기 시간 2배
elif api_error_rate < 0.01:  # 1% 미만 에러
    delay *= 0.8  # 대기 시간 단축
```

---

### 6.3 캐싱 전략

```python
# 거래일 정보 캐싱 (매번 조회 불필요)
@lru_cache(maxsize=10)
def get_trading_days(year, month):
    """특정 월의 거래일 조회 (캐싱)"""
    return pykrx.get_trading_days(year, month)
```

---

## 7. 에러 처리

### 7.1 에러 분류

| 에러 유형 | 처리 방법 | 재시도 |
|-----------|-----------|--------|
| NetworkError | 10초 대기 후 재시도 | 3회 |
| APIRateLimitError | 지수 백오프 | 5회 |
| DataNotFoundError | Skip (휴장일 등) | 없음 |
| ValidationError | 로깅 후 Skip | 없음 |
| DatabaseError | Transaction Rollback | 3회 |

---

### 7.2 에러 로깅

```python
# data_collection_log 테이블에 저장
log_collection_error(
    collection_type='phase1_daily',
    target_date=date,
    error_type='APIRateLimitError',
    error_message='429 Too Many Requests',
    retry_count=3
)
```

---

## 8. 데이터 검증

### 8.1 실시간 검증

수집 즉시 검증:
```python
def validate_daily_data(date, data):
    """일별 데이터 검증"""

    checks = []

    # 1. 종목 수 확인
    expected_count = get_listed_stocks_count(date)
    actual_count = len(data)
    if abs(actual_count - expected_count) > 50:  # 50개 이상 차이
        checks.append(f"종목 수 불일치: {actual_count}/{expected_count}")

    # 2. NULL 체크
    null_counts = data.isnull().sum()
    if null_counts['close'] > 0:
        checks.append(f"종가 NULL: {null_counts['close']}건")

    # 3. 이상값 체크
    if (data['close'] <= 0).any():
        checks.append("종가 0 이하 존재")

    # 4. 거래량 체크
    if (data['volume'] < 0).any():
        checks.append("음수 거래량 존재")

    return checks
```

---

### 8.2 배치 검증

수집 완료 후 전체 검증:
```python
def validate_completeness(start_date, end_date):
    """날짜별 데이터 완전성 검증"""

    trading_days = get_trading_days(start_date, end_date)

    for date in trading_days:
        # DB에 해당 날짜 데이터 존재 여부
        count = db.query(StockPrice)\
            .filter(StockPrice.date == date)\
            .count()

        if count == 0:
            print(f"❌ {date}: 데이터 없음")
        elif count < 2000:
            print(f"⚠ {date}: 데이터 부족 ({count}개)")
        else:
            print(f"✅ {date}: OK ({count}개)")
```

---

## 9. 성능 모니터링

### 9.1 수집 통계

```python
class CollectionStatistics:
    """수집 통계 추적"""

    def __init__(self):
        self.start_time = time.time()
        self.total_days = 0
        self.completed_days = 0
        self.failed_days = 0
        self.total_records = 0
        self.api_calls = 0
        self.errors = []

    def print_summary(self):
        elapsed = time.time() - self.start_time

        print(f"""
        ╔════════════════════════════════════════╗
        ║      수집 완료 통계                    ║
        ╠════════════════════════════════════════╣
        ║ 전체 일수:     {self.total_days:>10}일 ║
        ║ 완료 일수:     {self.completed_days:>10}일 ║
        ║ 실패 일수:     {self.failed_days:>10}일 ║
        ║ 수집 레코드:   {self.total_records:>10}개 ║
        ║ API 호출:      {self.api_calls:>10}회 ║
        ║ 소요 시간:     {elapsed/3600:>10.1f}시간 ║
        ║ 평균 속도:     {self.total_records/elapsed:>10.0f}개/초 ║
        ╚════════════════════════════════════════╝
        """)
```

---

## 10. CLI 명령어 설계

### 10.1 전체 수집

```bash
# Phase 1만 수집
python main.py collect bulk --start-date 2015-01-01 --phases 1

# Phase 1+2 수집
python main.py collect bulk --start-date 2015-01-01 --phases 1 2

# 전체 Phase 수집
python main.py collect bulk --start-date 2015-01-01 --phases 1 2 3

# 종료일 지정
python main.py collect bulk --start-date 2015-01-01 --end-date 2020-12-31

# 특정 시장만
python main.py collect bulk --market KOSPI --start-date 2015-01-01
```

---

### 10.2 재개 및 상태 확인

```bash
# 중단된 수집 재개
python main.py collect bulk --resume

# 진행 상황 확인
python main.py collect status

# 상세 로그 확인
python main.py collect logs --date 2015-01-05

# 누락 데이터 확인
python main.py collect validate --start-date 2015-01-01
```

---

### 10.3 테스트 수집

```bash
# 1주일만 테스트
python main.py collect bulk --start-date 2024-12-01 --end-date 2024-12-07

# Dry-run (실제 저장 안함)
python main.py collect bulk --start-date 2015-01-01 --dry-run
```

---

## 11. 예상 타임라인

### 11.1 Phase 1 (필수)

```
기간: 2015-01-01 ~ 2024-12-31 (약 2,450 거래일)

일별 소요 시간:
- API 호출: 4회 × 0.1초 = 0.4초
- 데이터 처리: 약 10초
- DB 저장: 약 5초
- 총: 약 15초/일

전체 소요 시간:
- 2,450일 × 15초 = 36,750초 = 약 10시간

실제 소요 (에러, 재시도 고려):
- 약 15~20시간 (1~2일)
```

---

### 11.2 Phase 2 (확장)

```
공매도 + 지수:
- 500 종목 × 0.1초 = 50초/일
- 40 지수 × 0.1초 = 4초/일
- 총: 약 54초/일

전체: 2,450일 × 54초 = 약 37시간 (2일)
```

---

### 11.3 Phase 3 (선택)

```
신용거래 + 외국인한도 + ETF:
- 유사 Phase 1
- 약 15~20시간 (1~2일)
```

---

### 11.4 전체 예상

**순차 실행 시**:
- Phase 1: 1~2일
- Phase 2: 2일
- Phase 3: 1~2일
- **합계: 약 4~6일** (24시간 연속 실행 시)

**실제 (하루 8시간 실행)**:
- **약 15~20일**

---

## 12. 체크리스트

### 수집 시작 전

- [ ] DB 백업 완료
- [ ] 충분한 디스크 공간 (최소 5GB)
- [ ] 안정적인 네트워크 연결
- [ ] PyKRX 설치 및 테스트
- [ ] 날짜 범위 확인 (2015-01-01 ~ 현재)
- [ ] Phase 선택 (1, 2, 3)

### 수집 중

- [ ] 진행 상황 주기적 확인
- [ ] 에러 로그 모니터링
- [ ] API 호출 속도 조정
- [ ] DB 크기 확인

### 수집 완료 후

- [ ] 데이터 완전성 검증
- [ ] 날짜별 누락 확인
- [ ] 통계 리포트 생성
- [ ] DB 백업
- [ ] VACUUM 실행 (공간 최적화)

---

## 13. 다음 단계

1. **BulkCollector 클래스 구현**
2. **CLI 명령어 추가**
3. **Phase 1 테스트 수집** (1주일치)
4. **검증 후 전체 수집 실행**
5. **Phase 2, 3 순차 진행**

---

## 부록: 예제 코드

전체 BulkCollector 구현 예제는 다음 문서 참조:
- `IMPLEMENTATION_ROADMAP.md`
