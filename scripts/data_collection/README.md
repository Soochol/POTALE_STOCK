# Data Collection Scripts

주가 데이터를 네이버 금융에서 수집하는 스크립트

## 스크립트 목록

### collect_single_ticker.py
**목적**: 단일 종목의 주가 및 투자자 데이터 수집

**특징**:
- AsyncUnifiedCollector 사용 (비동기 고성능)
- 증분 수집 지원 (이미 수집된 데이터 건너뛰기)
- 주가 + 투자자 데이터 동시 수집

**사용법**:
```bash
# 기본 수집
python scripts/data_collection/collect_single_ticker.py --ticker 025980 --from-date 2015-01-01

# 투자자 데이터 제외 (주가만)
python scripts/data_collection/collect_single_ticker.py --ticker 025980 --no-investor

# 전체 재수집 (증분 무시)
python scripts/data_collection/collect_single_ticker.py --ticker 025980 --force-full
```

---

### collect_all_tickers.py
**목적**: 전체 종목(약 4,189개) 데이터 수집

**특징**:
- 비동기 병렬 수집 (4-5배 빠름)
- 동시 수집 종목 수 조절 가능
- 진행 상황 실시간 표시
- 에러 처리 및 재시도

**사용법**:
```bash
# 전체 종목 수집
python scripts/data_collection/collect_all_tickers.py --from-date 2015-01-01

# 동시 수집 종목 수 조정
python scripts/data_collection/collect_all_tickers.py --from-date 2015-01-01 --concurrency 15

# 전체 재수집 강제
python scripts/data_collection/collect_all_tickers.py --from-date 2015-01-01 --force-full
```

**성능**:
- 최초 전체 수집 (4,189개, 5년): 1.5-2시간
- 일일 업데이트 (증분): 10-15분

---

## 데이터 수집 방식

- **소스**: 100% 네이버 금융 (pykrx 불필요)
- **하이브리드 수집**: 수정주가 + 수정거래량 자동 계산
- **증분 수집**: `collection_progress` 테이블로 관리
- **비동기 병렬**: aiohttp 기반

## 참고

- [네이버 금융 데이터 수집 가이드](../../docs/specification/NAVER_FINANCE_GUIDE.md)
- [성능 최적화](../../docs/guides/PERFORMANCE_OPTIMIZATION.md)
