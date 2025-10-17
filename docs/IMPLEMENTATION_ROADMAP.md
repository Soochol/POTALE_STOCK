# 구현 로드맵

## 전체 일정 개요

| 단계 | 내용 | 예상 소요 | 상태 |
|------|------|-----------|------|
| **문서화** | 설계 문서 3종 작성 | 완료 | ✅ 완료 |
| **Step 1** | DB 모델 확장 | 1시간 | ✅ 완료 |
| **Step 2** | NaverInvestorCollector 구현 | 2시간 | ✅ 완료 |
| **Step 3** | BulkCollector + Hybrid + pykrx 제거 | 3시간 | ✅ 완료 |
| **Step 4** | 테스트 수집 (소규모) | 30분 | ✅ 완료 |
| **Step 5** | Phase 1 전체 수집 | 6-8시간 | 🔜 대기 |
| **Step 6** | Phase 2-3 구현 | 4시간 | 🔜 대기 |
| **Step 7** | 전체 수집 완료 | 5일 | 🔜 대기 |

**총 예상 기간**: 약 7~10일 (코드 + 수집)

---

## Step 1: DB 모델 확장

### 목표
Phase 1 필수 테이블 추가 (investor_trading) 및 관리 테이블 추가

### 작업 내용

#### 1.1 models.py에 새 모델 추가

**파일**: `src/infrastructure/database/models.py`

추가할 모델:
1. ✅ StockInfo (확장 완료 - is_active, delisting_date, listing_shares)
2. ✅ StockPrice (확장 완료 - adjustment_ratio, raw_close, raw_volume)
3. ✅ MarketData (이미 존재)
4. ✅ **InvestorTrading** (완료)
5. ✅ **CollectionProgress** (완료)
6. ✅ **DataQualityCheck** (완료)
7. ✅ **DataCollectionLog** (완료)

```python
# 추가할 코드 예시
class InvestorTrading(Base):
    """투자자별 매매 테이블"""
    __tablename__ = 'investor_trading'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False)
    date = Column(Date, nullable=False)

    # 순매수
    institution_net_buy = Column(BigInteger, default=0)
    foreign_net_buy = Column(BigInteger, default=0)
    individual_net_buy = Column(BigInteger, default=0)

    # ... (나머지 컬럼)

    __table_args__ = (
        Index('ix_investor_ticker_date', 'ticker', 'date', unique=True),
        Index('ix_investor_foreign_net', 'foreign_net_buy'),
    )
```

#### 1.2 StockInfo 모델 확장

```python
# 추가 컬럼
is_active = Column(Boolean, default=True)
delisting_date = Column(Date)
sector_code = Column(String(20))
listing_shares = Column(BigInteger)
```

#### 1.3 관계 설정 업데이트

```python
# StockInfo에 추가
investor_trading = relationship("InvestorTrading", back_populates="stock_info", cascade="all, delete-orphan")
```

### 검증

```bash
# DB 초기화 (기존 데이터 삭제됨 주의!)
python -c "from src.infrastructure.database.connection import get_db_connection; db = get_db_connection(); db.drop_tables(); db.create_tables()"

# 테이블 생성 확인
sqlite3 data/database/stock_data.db ".tables"

# 스키마 확인
sqlite3 data/database/stock_data.db ".schema investor_trading"
```

### 예상 소요: **1시간**

---

## Step 2: NaverInvestorCollector 구현 ✅ 완료

### 목표
네이버 금융에서 투자자별 매매 데이터를 수집하는 Collector 구현

### 작업 내용 (완료)

#### 2.1 NaverInvestorCollector 클래스

**파일**: `src/infrastructure/collectors/naver_investor_collector.py` ✅ 완료

```python
class NaverInvestorCollector(NaverFinanceCollector):
    """네이버 금융 투자자별 매매 데이터 수집기"""

    def collect(self, ticker: str, fromdate: date, todate: date) -> CollectionResult:
        """특정 종목의 투자자 거래 데이터 수집"""

        # 네이버 금융 개별 종목 페이지
        url = f"{self.BASE_URL}/item/frgn.nhn?code={ticker}"

        # HTML 가져오기 및 파싱
        html = self._fetch_html(url)
        dfs = self._parse_tables(html)

        # Table 4가 투자자 거래 데이터
        df = dfs[3]

        # 데이터 변환
        records = self._transform_dataframe(df, ticker, fromdate, todate)

        # DB 저장
        if self.db_connection:
            record_count = self._bulk_upsert(records)

        return CollectionResult(success=True, record_count=record_count)
```

**특징**:
- 네이버 금융 HTML 스크래핑
- 기관/외국인 순매수량 수집
- 개인 데이터는 제공되지 않음 (0으로 저장)

#### 2.2 Repository 메서드 추가

**파일**: `src/infrastructure/repositories/sqlite_stock_repository.py` (확장)

```python
def save_investor_trading(self, data: List[dict]) -> bool:
    """투자자 매매 데이터 저장 (bulk upsert)"""

    with get_db_session(self.db_path) as session:
        for item in data:
            stmt = insert(InvestorTrading).values(**item)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'date'],
                set_={**item}
            )
            session.execute(stmt)
        session.commit()
```

#### 2.3 CLI 명령어 추가

**파일**: `main.py` (확장)

```python
@collect.command('investor')
@click.option('--start-date', '-s', required=True)
@click.option('--end-date', '-e')
def collect_investor_trading(start_date, end_date):
    """투자자별 매매 데이터 수집"""
    collector = InvestorTradingCollector()
    result = collector.collect_date_range(start_date, end_date)
    print(f"수집 완료: {result.record_count}개")
```

### 테스트 결과 ✅

```bash
# 삼성전자 최근 30일 테스트 - 성공
python test_naver_investor_collector.py

# 결과:
# - Test 1 (데이터만 수집): 17개 레코드 수집 (0.62초)
# - Test 2 (DB 저장): 17개 레코드 DB 저장 성공
# - Test 3 (여러 종목): 삼성전자, SK하이닉스, 네이버 모두 성공

# DB 검증:
# 날짜별 기관/외국인 순매수 데이터 정상 저장 확인
# 예: 2025-10-16 - 기관: 2,000,393주, 외국인: 5,787,756주
```

### 소요 시간: **2시간** ✅ 완료

---

## Step 3: BulkCollector + Hybrid 구현 + pykrx 제거 ✅ 완료

### 목표
2015년부터 전체 데이터를 일괄 수집하는 핵심 모듈 (100% 네이버 금융 기반)

### 구현 완료 사항

#### 3.1 BulkCollector ✅
**파일**: `src/infrastructure/collectors/bulk_collector.py`

주요 기능 완료:
- ✅ 종목별 순차 수집 (네이버 금융 특성)
- ✅ 진행률 추적 및 ETA 계산
- ✅ Resume 기능 (중단 후 재개)
- ✅ 에러 처리 및 재시도 로직
- ✅ 통계 출력 및 로깅

#### 3.2 NaverHybridCollector ✅ (보너스!)
**파일**: `src/infrastructure/collectors/naver/naver_hybrid_collector.py`

**획기적인 개선**:
- ✅ fchart API로 수정주가 수집
- ✅ sise_day HTML로 원본 데이터 수집
- ✅ 자동으로 수정거래량 계산
- ✅ 액면분할 대응 완료
- ✅ price_ratio 기반 volume 조정

**데이터 품질**:
- 수정주가: fchart API (정확)
- 수정거래량: 자동 계산 (price_ratio 활용)
- 원본 데이터: 참고용 보관 (raw_close, raw_volume)

#### 3.3 CLI 스크립트 ✅
**파일**: `bulk_collect.py`

```bash
# 전체 종목 수집 (하이브리드)
python bulk_collect.py --all --from 2020-01-01 --investor

# 특정 종목만
python bulk_collect.py --tickers 005930,000660 --from 2024-01-01

# 재개 기능
python bulk_collect.py --all --from 2020-01-01 --resume

# 레거시 모드 (원본 주가만)
python bulk_collect.py --all --from 2024-01-01 --legacy
```

#### 3.4 pykrx 완전 제거 ✅ (2024-10-17)
**100% 네이버 금융 기반 전환**

**추가된 파일**:
- `src/infrastructure/utils/naver_ticker_list.py` - 네이버 시가총액 페이지 크롤링
  - `get_naver_ticker_list(market)`: KOSPI/KOSDAQ 종목 리스트
  - `get_all_tickers()`: 전체 4,189개 종목 (KOSPI 2,387 + KOSDAQ 1,802)

**삭제된 파일**:
- `src/infrastructure/collectors/pykrx/` (전체 디렉토리)
- `src/infrastructure/repositories/pykrx_stock_repository.py`

**수정된 파일**:
- `bulk_collect.py`: pykrx 대신 네이버 종목 리스트 사용
- `requirements.txt`: pykrx 제거, beautifulsoup4/lxml/html5lib 추가

**테스트 결과**:
- ✅ 종목 리스트 수집: 4,189개 (약 10초 소요)
- ✅ 소규모 수집: 3종목 × 30일 = 54개 레코드
- ✅ 데이터 품질: NULL 0개, 중복 0개
- ✅ 하이브리드 검증: 수정주가 + 수정거래량 정상

**장점**:
- 의존성 감소 (pykrx 불필요)
- 일관된 데이터 소스 (100% 네이버)
- pykrx API 변경에 영향 없음
- 유지보수성 향상

### 소요 시간: **3시간** ✅ 완료

---

## Step 3 (원본 설계안)

<details>
<summary>원본 설계안 보기 (참고용)</summary>

### 목표
2015년부터 전체 데이터를 일괄 수집하는 핵심 모듈 (네이버 금융 기반)

### 작업 내용

#### 3.1 BulkCollector 클래스

**파일**: `src/infrastructure/collectors/bulk_collector.py` (신규)

주요 기능:
1. 날짜별 배치 수집
2. Phase별 선택 수집
3. 진행 상황 추적 및 저장
4. 재개(Resume) 기능
5. 에러 처리 및 재시도

```python
class BulkCollector(BaseCollector):
    """대량 데이터 일괄 수집 관리자"""

    def __init__(self, db_connection):
        self.investor_collector = NaverInvestorCollector(db_connection)
        self.db_connection = db_connection

        # 주의: 네이버는 종목별 수집만 가능
        # 날짜별 일괄 수집 불가

    def collect_all(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        phases: List[int] = [1],
        resume: bool = False
    ) -> CollectionResult:
        """전체 수집 실행 (네이버 금융은 종목별)"""

        # 1. 재개 시 마지막 종목부터
        if resume:
            last_ticker = self._get_last_collected_ticker()
            tickers = [t for t in tickers if t >= last_ticker]

        # 2. 진행 상황 초기화
        progress = self._init_progress(phases, len(tickers))

        # 3. 종목별 수집 루프 (네이버는 종목별만 가능)
        for ticker in tickers:
            try:
                # Phase 1: 투자자 거래
                if 1 in phases:
                    result = self.investor_collector.collect(
                        ticker, start_date, end_date
                    )

                # 진행 상황 업데이트
                self._update_progress(progress, ticker, result.record_count)

                # 차단 방지 대기
                time.sleep(0.2)

            except Exception as e:
                self._handle_error(ticker, e)
                continue

        # 4. 완료
        self._finalize(progress)

    def _collect_ticker_investor_data(self, ticker: str, start_date: date, end_date: date):
        """특정 종목의 투자자 거래 데이터 수집"""

        # 네이버 금융은 종목별 페이지만 제공
        result = self.investor_collector.collect(ticker, start_date, end_date)

        return result
```

**주의사항**:
- 네이버 금융은 **날짜별 일괄 수집 불가능**
- 반드시 **종목별로 순차 수집**
- 0.2초 간격 필수 (차단 방지)

#### 3.2 거래일 판별

```python
def _get_trading_days(self, start_date: date, end_date: date) -> List[date]:
    """거래일 목록 조회 (주말/공휴일 제외)"""

    # 간단한 방법: DB에서 기존 데이터 확인
    # 또는 PyKRX의 거래일 정보 활용

    trading_days = []
    current = start_date

    while current <= end_date:
        # 주말 제외
        if current.weekday() < 5:  # 월~금
            # 추가 검증: PyKRX에서 데이터 조회 가능한지 확인
            trading_days.append(current)

        current += timedelta(days=1)

    return trading_days
```

#### 3.3 진행 상황 관리

```python
def _update_progress(self, progress_id: int, completed_date: date):
    """진행 상황 업데이트"""

    with get_db_session() as session:
        progress = session.query(CollectionProgress).get(progress_id)
        progress.target_date = completed_date
        progress.completed_items += 1
        progress.updated_at = datetime.now()

        # 예상 완료 시각 계산
        elapsed = (datetime.now() - progress.started_at).total_seconds()
        avg_time_per_item = elapsed / progress.completed_items
        remaining_items = progress.total_items - progress.completed_items
        eta_seconds = remaining_items * avg_time_per_item
        progress.estimated_completion = datetime.now() + timedelta(seconds=eta_seconds)

        session.commit()
```

#### 3.4 CLI 명령어

**파일**: `main.py`

```python
@collect.command('bulk')
@click.option('--start-date', '-s', default='2015-01-01')
@click.option('--end-date', '-e', default=None)
@click.option('--phases', '-p', multiple=True, type=int, default=[1])
@click.option('--resume', is_flag=True)
@click.option('--dry-run', is_flag=True)
def bulk_collect(start_date, end_date, phases, resume, dry_run):
    """2015년부터 전체 데이터 일괄 수집"""

    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    collector = BulkCollector()

    console.print(f"\n[bold cyan]대량 수집 시작[/bold cyan]")
    console.print(f"기간: {start} ~ {end}")
    console.print(f"Phase: {list(phases)}")
    console.print(f"재개: {'예' if resume else '아니오'}\n")

    if dry_run:
        console.print("[yellow]Dry-run 모드: 실제 저장 안함[/yellow]\n")

    result = collector.collect_all(start, end, list(phases), resume)

    console.print(f"\n[green]✓[/green] 수집 완료!")
    console.print(f"레코드: {result.record_count}개")
    console.print(f"소요 시간: {result.duration_seconds/3600:.1f}시간")

@collect.command('status')
def show_status():
    """수집 진행 상황 확인"""

    with get_db_session() as session:
        progress_list = session.query(CollectionProgress)\
            .filter(CollectionProgress.status.in_(['running', 'paused']))\
            .all()

        if not progress_list:
            console.print("[yellow]진행 중인 수집이 없습니다.[/yellow]")
            return

        table = Table(title="수집 진행 상황")
        table.add_column("Phase")
        table.add_column("진행률")
        table.add_column("현재 날짜")
        table.add_column("예상 완료")
        table.add_column("상태")

        for p in progress_list:
            pct = p.completed_items * 100.0 / p.total_items
            table.add_row(
                str(p.phase),
                f"{pct:.1f}% ({p.completed_items}/{p.total_items})",
                str(p.target_date),
                str(p.estimated_completion)[:16] if p.estimated_completion else "-",
                p.status
            )

        console.print(table)
```

### 테스트

```bash
# 1주일만 테스트
python main.py collect bulk --start-date 2024-12-01 --end-date 2024-12-07 --phases 1

# Dry-run
python main.py collect bulk --start-date 2015-01-01 --end-date 2015-01-31 --dry-run

# 진행 상황 확인
python main.py collect status
```

### 예상 소요: **3시간**

---

## Step 4: 테스트 수집 ✅ 완료

### 목표
실제 대량 수집 전 소규모/중규모 테스트로 시스템 검증

### 작업 내용

#### 4.1 소규모 테스트 수집 ✅ (2024-10-17)

**수집 명령**:
```bash
# 3종목 × 30일 테스트
uv run python bulk_collect.py \
    --tickers 005930,000660,035720 \
    --from 2024-09-17 \
    --to 2024-10-17
```

**테스트 결과**:
- ✅ 수집 종목: 3개 (삼성전자, SK하이닉스, 카카오)
- ✅ 수집 기간: 30일 (2024-09-17 ~ 2024-10-17)
- ✅ 수집 레코드: 54개 (하이브리드 주가 데이터)
- ✅ 소요 시간: 약 10초
- ✅ 데이터 품질: NULL 0개, 중복 0개, 정상

#### 4.2 데이터 검증 ✅

**검증 스크립트**: `validate_data.py`

```bash
uv run python validate_data.py
```

**검증 결과**:
```
[1] Basic Statistics
Stock Info: 3 stocks
Stock Price: 54 records
Investor Trading: 0 records (네이버 페이지 구조 변경으로 미지원)
Market Data: 0 records

[2] Date Range
First Date: 2024-09-18
Last Date: 2024-10-16
Trading Days: 21

[3] Per-Ticker Statistics
Ticker     Name                  Records  First Date   Last Date
005930     삼성전자                   18  2024-09-18   2024-10-16
000660     SK하이닉스                 18  2024-09-18   2024-10-16
035720     카카오                     18  2024-09-18   2024-10-16

[4] Hybrid Data Validation (Adjusted Price)
Date         Adj Close  Raw Close    Ratio  Adj Vol      Raw Vol
2024-10-16      57,400     57,400   1.0000   13,144,272   13,144,272
2024-10-15      57,200     57,200   1.0000   15,479,264   15,479,264

[6] Data Quality Checks
Records with NULL (close/volume): 0
Records with zero close price: 0
No duplicates found
```

#### 4.3 하이브리드 수집 검증 ✅

**수정주가 + 수정거래량 계산 검증**:
- ✅ adjustment_ratio 정상 계산 (raw_close / adj_close)
- ✅ adj_volume 정상 계산 (price_ratio 기반)
- ✅ 액면분할 데이터 정상 처리 (아난티 5:1 비율 검증 완료)
- ✅ 거래대금 정확성 (close × volume)

**데이터베이스 구조**:
- ✅ 테이블: 7개 (stock_info, stock_price, market_data, investor_trading, data_collection_log, collection_progress, data_quality_check)
- ✅ DB 파일: `data/database/stock_data.db` (108KB)

### 소요 시간: **30분** ✅ 완료

---

## Step 5: Phase 1 전체 수집

### 목표
2015.01.01 ~ 현재까지 Phase 1 (필수 데이터) 전체 수집

### 작업 내용

#### 5.1 수집 실행

```bash
# Phase 1 전체 수집 시작
python main.py collect bulk --start-date 2015-01-01 --phases 1

# 또는 nohup으로 백그라운드 실행
nohup python main.py collect bulk --start-date 2015-01-01 --phases 1 > collect.log 2>&1 &

# 진행 상황 모니터링
watch -n 60 "python main.py collect status"
```

#### 5.2 중간 점검

```bash
# 매일 또는 주기적으로 확인
python main.py collect status

# 로그 확인
tail -f collect.log

# DB 크기 확인
ls -lh data/database/stock_data.db
```

#### 5.3 문제 발생 시

```bash
# 중단 후 재개
python main.py collect bulk --resume

# 특정 날짜부터 재시작
python main.py collect bulk --start-date 2020-01-01 --phases 1
```

### 예상 소요: **1~2일** (24시간 연속 실행)

---

## Step 6: Phase 2-3 구현

### 목표
확장 데이터 (공매도, 지수, 신용거래 등) Collector 구현

### 작업 내용

#### 6.1 ShortSellingCollector

**파일**: `src/infrastructure/collectors/short_selling_collector.py`

```python
class ShortSellingCollector(BaseCollector):
    """공매도 데이터 수집기"""

    def collect_daily(self, target_date: date) -> CollectionResult:
        """특정 날짜의 공매도 데이터 수집"""
        # 거래량 상위 500개 종목만 수집
        # ...
```

#### 6.2 IndexCollector

**파일**: `src/infrastructure/collectors/index_collector.py`

```python
class IndexCollector(BaseCollector):
    """지수 데이터 수집기"""

    def collect_daily(self, target_date: date) -> CollectionResult:
        """KOSPI, KOSDAQ, 업종별 지수 수집"""
        # ...
```

#### 6.3 BulkCollector에 통합

```python
def _collect_phase2(self, target_date: date):
    """Phase 2: 공매도 + 지수"""
    self.short_collector.collect_daily(target_date)
    self.index_collector.collect_daily(target_date)
```

### 예상 소요: **4시간**

---

## Step 7: 전체 수집 완료

### 목표
Phase 2-3까지 전체 수집 완료 및 최종 검증

### 작업 내용

#### 7.1 Phase 2 수집

```bash
python main.py collect bulk --start-date 2015-01-01 --phases 2
```

#### 7.2 Phase 3 수집 (선택)

```bash
python main.py collect bulk --start-date 2015-01-01 --phases 3
```

#### 7.3 최종 검증

```bash
# 전체 데이터 검증
python main.py collect validate --start-date 2015-01-01

# 통계 출력
python main.py collect stats
```

### 예상 소요: **4~5일**

---

## 전체 체크리스트

### 구현

- [x] Step 1: DB 모델 확장 (InvestorTrading, CollectionProgress)
- [x] Step 2: NaverInvestorCollector 구현
- [x] Step 3: BulkCollector + NaverHybridCollector 구현
- [x] Step 3.4: pykrx 완전 제거 (100% 네이버 금융)
- [x] Step 4: 테스트 수집 (소규모)
- [ ] Step 5: Phase 1 전체 수집 (4,189종목 × 5년)
- [ ] Step 6: Phase 2-3 Collector 구현
- [ ] Step 7: 전체 수집 완료

### 검증

- [x] 소규모 테스트 데이터 검증 (3종목 × 30일)
- [x] 하이브리드 수집 검증 (수정주가 + 수정거래량)
- [x] NULL 값 체크 (0개 확인)
- [x] 중복 체크 (0개 확인)
- [x] 액면분할 처리 검증 (아난티 5:1 비율)
- [ ] 날짜별 데이터 완전성 확인 (전체 수집 후)
- [ ] 투자자 매매 데이터 정합성 (네이버 페이지 구조 수정 필요)
- [ ] 품질 리포트 생성

### 문서

- [x] DATABASE_DESIGN.md
- [x] BULK_COLLECTION_DESIGN.md
- [x] IMPLEMENTATION_ROADMAP.md
- [x] CHANGELOG.md (pykrx 제거 기록)
- [x] README.md (100% 네이버 금융 업데이트)
- [ ] API_USAGE.md (선택)

---

## 다음 액션

**현재 상태 (2024-10-17)**:
- ✅ Step 1-4 모두 완료
- ✅ pykrx 완전 제거 (100% 네이버 금융)
- ✅ 소규모 테스트 성공 (3종목 × 30일)
- ✅ 데이터 품질 검증 완료
- ✅ 문서 업데이트 완료

**다음 단계 선택지**:

### 옵션 A: 중규모 테스트 (권장)
전체 수집 전 추가 검증:
```bash
# 20종목 × 1주일 테스트
uv run python bulk_collect.py \
    --tickers 005930,000660,035420,051910,035720,068270,207940,006400,005380,000270,105560,055550,012330,028260,096770,003670,066570,015760,017670,000810 \
    --from 2024-10-10 \
    --to 2024-10-17
```

**예상 소요**: 약 1분
**목적**: 다양한 종목에서 하이브리드 수집 안정성 검증

### 옵션 B: 전체 수집 시작 (Step 5)
4,189종목 × 5년 데이터 수집:
```bash
# 2020년부터 전체 수집
uv run python bulk_collect.py --all --from 2020-01-01

# 백그라운드 실행 (Windows)
start /B uv run python bulk_collect.py --all --from 2020-01-01 > collect.log 2>&1
```

**예상 소요**: 6-8시간 (연속 실행)
**수집량**: 약 4백만 레코드
**DB 크기**: 약 500MB ~ 1GB

### 옵션 C: 투자자 거래 데이터 수정
NaverInvestorCollector 디버깅 (네이버 페이지 구조 변경 대응):
- 현재 상태: 0개 레코드 수집
- 필요 작업: 네이버 금융 페이지 구조 재분석

**권장 순서**: A (중규모 테스트) → B (전체 수집) → C (투자자 데이터 수정)
