# Changelog

## [2024-10-17] pykrx 완전 제거 - 100% 네이버 금융 기반 전환

### 🎯 주요 변경사항

**pykrx 의존성 완전 제거**하고 모든 데이터 수집을 **100% 네이버 금융 기반**으로 전환했습니다.

### ✅ 추가된 기능

#### 1. 네이버 종목 리스트 수집 시스템
- **파일**: `src/infrastructure/utils/naver_ticker_list.py`
- **기능**: 네이버 금융 시가총액 페이지에서 전체 종목 코드 크롤링
- **수집 종목 수**:
  - KOSPI: 2,387개
  - KOSDAQ: 1,802개
  - 총: 4,189개
- **소요 시간**: 약 10초

```python
from src.infrastructure.utils import get_all_tickers

# 전체 종목 리스트 가져오기
tickers = get_all_tickers()  # 4,189개 종목
```

### 🗑️ 제거된 기능

#### 1. pykrx 관련 코드 전체 삭제
- ❌ `src/infrastructure/collectors/pykrx/` (전체 디렉토리)
  - `stock_price_collector.py`
  - `market_info_collector.py`
  - `investor_trading_collector.py`
- ❌ `src/infrastructure/repositories/pykrx_stock_repository.py`
- ❌ `requirements.txt`에서 pykrx>=1.0.40 제거

#### 2. main.py CLI 비활성화 (Deprecated)
- ⚠️ `main.py` - pykrx 기반 collector에 의존하는 레거시 CLI
  - `collect` 명령어: DEPRECATED → `bulk_collect.py` 사용 권장
  - `detect` 명령어: DEPRECATED → 데이터 수집 후 SQLite에서 읽어야 함
  - `train` 명령어: DEPRECATED → 데이터 수집 후 SQLite에서 읽어야 함
  - `condition` 명령어: 정상 작동 (조건 관리 기능)

### 🔧 수정된 기능

#### 1. bulk_collect.py
**변경 전**:
```python
from pykrx import stock
kospi_tickers = stock.get_market_ticker_list(...)
```

**변경 후**:
```python
from src.infrastructure.utils import get_all_tickers
tickers = get_all_tickers()  # 네이버 금융에서 수집
```

#### 2. requirements.txt
**추가된 패키지**:
```
beautifulsoup4>=4.12.0
lxml>=4.9.0
html5lib>=1.1
```

### 📊 테스트 결과

| 테스트 항목 | 결과 | 비고 |
|------------|------|------|
| 종목 리스트 수집 | ✅ 성공 | 4,189개 종목 |
| 단일 종목 데이터 수집 | ✅ 성공 | 005930 (삼성전자) 10개 레코드 |
| 하이브리드 수집 | ✅ 정상 | 수정주가 + 수정거래량 |
| 소규모 테스트 | ✅ 성공 | 3종목 × 30일, 54개 레코드 |

### 💡 장점

1. **의존성 감소**: pykrx 제거로 외부 라이브러리 의존성 최소화
2. **일관성**: 모든 데이터를 네이버 금융에서 수집하여 일관된 데이터 소스
3. **유지보수성**: pykrx API 변경에 영향 받지 않음
4. **성능**: 네이버 직접 크롤링이 더 빠를 수 있음

### ⚠️ 주의사항

- 네이버 금융 페이지 구조 변경 시 수정 필요
- 투자자 거래 데이터는 현재 네이버 페이지 구조 변경으로 수집 불가 (추후 수정 예정)

### 📝 마이그레이션 가이드

**기존 코드 사용 중이라면**:

1. pykrx 제거:
   ```bash
   pip uninstall pykrx
   ```

2. 새로운 패키지 설치:
   ```bash
   pip install beautifulsoup4 lxml html5lib
   # 또는
   uv pip install -r requirements.txt
   ```

3. 코드 변경 불필요:
   - `bulk_collect.py`는 자동으로 네이버 방식 사용
   - 기존 사용법 동일

### 🔄 업그레이드 방법

```bash
# 1. 최신 코드 받기
git pull

# 2. 의존성 재설치
uv pip install -r requirements.txt

# 3. pykrx 제거 (선택)
uv pip uninstall pykrx

# 4. 테스트
uv run python bulk_collect.py --tickers 005930 --from 2024-10-01
```

### 📚 관련 문서

- [README.md](../README.md) - pykrx 제거 반영
- [IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) - Step 3 완료 업데이트

---

## [2024-10-17] Step 4 테스트 수집 완료

### 테스트 결과

- **소규모 테스트**: 3종목 (005930, 000660, 035720) × 30일
- **수집 레코드**: 54개 (하이브리드 주가 데이터)
- **데이터 품질**: NULL 0개, 중복 0개, 정상
- **하이브리드 검증**: 수정주가 + 수정거래량 정상 계산

### DB 구조

- 테이블: 7개 (stock_info, stock_price, market_data, investor_trading, data_collection_log, collection_progress, data_quality_check)
- DB 파일: `data/database/stock_data.db` (108KB)

---

## 다음 단계

- [ ] Step 5: 전체 종목 수집 (4,189종목 × 5년)
- [ ] 투자자 거래 데이터 수집 기능 복구
- [ ] 성능 최적화 및 모니터링
