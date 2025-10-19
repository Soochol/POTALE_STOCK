# Naver Hybrid Collector 근본적 해결책

## 문제 분석

### 기존 문제점
1. **페이지 추정 방식의 근본적 한계**
   - 날짜 기반으로 시작 페이지를 추정 (예: 2020년 데이터 → 페이지 191부터 시작)
   - 추정이 틀리면 데이터 누락 또는 "No raw data collected" 에러 발생
   - 종목마다 상장일, 거래량이 달라 일률적인 추정 불가능

2. **날짜 필터링 시점 문제**
   - 페이지별로 즉시 날짜 필터링 적용
   - 필터링 후 빈 결과가 나오면 "데이터가 없다"고 판단
   - 실제로는 데이터가 있지만 날짜 범위 밖이어서 제외된 경우도 있음

3. **불완전한 검증**
   - 수집된 데이터가 요청한 날짜 범위를 완전히 커버하는지 검증 안 함
   - 일부 데이터만 수집되어도 성공으로 처리

## 근본적 해결책

### 1. 항상 페이지 1부터 시작
```python
# 추정하지 않고 무조건 최신 데이터부터 시작
page = 1
```

**이유:**
- 네이버 금융은 최신 데이터가 페이지 1에 있음
- 추정 오류 가능성 제거
- 모든 종목에 일관되게 적용 가능

### 2. 날짜 범위 완전 추적
```python
# 필터링 전에 먼저 전체 날짜 범위 파악
records_unfiltered = self._transform_dataframe(
    dfs[0], ticker,
    date(1900, 1, 1),  # 매우 넓은 범위로 전체 추출
    date(2100, 12, 31)
)

# 페이지별 날짜 범위 추적
page_dates = [r['date'] for r in records_unfiltered]
page_earliest = min(page_dates)
page_latest = max(page_dates)

# 전체 수집 범위 업데이트
if earliest_collected is None or page_earliest < earliest_collected:
    earliest_collected = page_earliest
if latest_collected is None or page_latest > latest_collected:
    latest_collected = page_latest
```

**이유:**
- 페이지별로 어떤 날짜 범위의 데이터가 있는지 정확히 파악
- 필터링 여부와 관계없이 진행 상황 추적 가능

### 3. 연속 빈 페이지 허용
```python
pages_without_data = 0
max_empty_pages = 10

if not records_unfiltered:
    pages_without_data += 1
    if pages_without_data >= max_empty_pages:
        print(f"    [Warning] {max_empty_pages} consecutive empty pages, stopping")
        break
    page += 1
    continue
else:
    pages_without_data = 0  # 리셋
```

**이유:**
- 날짜 범위 밖 페이지를 건너뛰면서도 계속 진행
- 실제로 데이터가 없는 경우에만 종료

### 4. 수집 후 날짜 범위 검증
```python
# 수집된 데이터의 실제 범위 확인
collected_dates = sorted(set(r['date'] for r in all_records))
actual_earliest = min(collected_dates)
actual_latest = max(collected_dates)

# 요청 범위와 비교하여 경고
if actual_earliest > fromdate:
    print(f"    [Warning] Missing data: requested from {fromdate}, but earliest is {actual_earliest}")

if actual_latest < todate and todate <= date.today():
    print(f"    [Warning] Missing data: requested until {todate}, but latest is {actual_latest}")
```

**이유:**
- 누락된 데이터가 있으면 명확히 경고
- 상장 전 날짜 등 정상적인 누락과 비정상적인 누락 구분 가능

### 5. 상세한 수집 통계
```python
trading_days = len(collected_dates)
print(f"    sise_day: {len(df)} records from {page} pages "
      f"({actual_earliest} ~ {actual_latest}, {trading_days} trading days)")
```

**이유:**
- 수집 과정을 투명하게 공개
- 문제 발생 시 디버깅 용이

## 테스트 결과

### 다양한 날짜 범위 테스트
```
[OK] 2024년 데이터: 244건 (10.5초, 44페이지)
[OK] 2020년 데이터: 248건 (31.8초, 143페이지)
[OK] 2015년 데이터: 248건 (59.1초, 265페이지)
[OK] 5년 범위 (2020-2024): 1231건 (31.9초, 143페이지)
```

### 개선 효과
1. **페이지 191 문제 해결**: 2020년 데이터도 페이지 1부터 시작하여 정상 수집 (143페이지에서 완료)
2. **누락 데이터 자동 경고**: 요청 범위와 실제 수집 범위 비교하여 경고 메시지 출력
3. **안정적인 수집**: 모든 테스트 케이스에서 100% 성공

## 성능 특성

### 페이지 수 vs 날짜 범위
- **2024년 (1년)**: 44페이지
- **2020년 (5년 전)**: 143페이지
- **2015년 (10년 전)**: 265페이지

페이지 1부터 시작하므로 오래된 데이터일수록 더 많은 페이지를 확인해야 하지만:
- 날짜 범위 추적으로 불필요한 페이지 건너뛰기 가능
- 연속 10페이지 빈 데이터 시 자동 중단
- 평균 0.2초/페이지로 충분히 빠름

## 향후 개선 가능 사항

### 1. 캐싱 메커니즘
```python
# 수집한 데이터를 캐시에 저장
# 다음 수집 시 캐시된 최신 날짜부터 시작
if cached_latest_date:
    estimated_page = (date.today() - cached_latest_date).days // 10
    page = max(1, estimated_page - 5)
```

### 2. 병렬 수집
```python
# 여러 종목을 동시에 수집
import asyncio
results = await asyncio.gather(
    *[collector.collect_async(ticker, fromdate, todate)
      for ticker in tickers]
)
```

### 3. 재시도 메커니즘
```python
# 네트워크 에러 발생 시 자동 재시도
for attempt in range(max_retries):
    try:
        html = self._fetch_html(url, params)
        break
    except requests.RequestException as e:
        if attempt < max_retries - 1:
            sleep(retry_delay * (attempt + 1))
            continue
        else:
            raise
```

## 결론

기존의 페이지 추정 방식 대신 **항상 페이지 1부터 시작하고 날짜 범위를 완전히 추적하는 방식**으로 변경하여:

1. ✅ 페이지 추정 오류 완전 제거
2. ✅ 누락 데이터 자동 감지 및 경고
3. ✅ 모든 날짜 범위에서 안정적 수집
4. ✅ 투명한 수집 과정 (상세 로그)

이로써 **근본적이고 안정적인 데이터 수집 시스템**을 구축했습니다.
