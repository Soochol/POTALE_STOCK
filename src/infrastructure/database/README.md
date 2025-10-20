# Database Package

SQLAlchemy 기반 데이터베이스 레이어

## 폴더 구조

```
src/infrastructure/database/
├── models/                  # SQLAlchemy ORM Models (분리된 도메인별 모델)
│   ├── __init__.py         # 모든 모델 중앙 export
│   ├── base.py             # Base declarative (6 lines)
│   ├── stock.py            # 주식 기본 데이터 모델 (144 lines)
│   ├── blocks.py           # Block1/2/3/4 탐지 모델 (263 lines)
│   ├── patterns.py         # 패턴 재탐지 시스템 (50 lines)
│   ├── presets.py          # Seed/Redetection 조건 프리셋 (202 lines)
│   └── monitoring.py       # 데이터 수집 로그 및 품질 체크 (92 lines)
├── connection.py           # DatabaseConnection 클래스 (137 lines)
├── queries.py              # 증분 수집용 쿼리 헬퍼 (320 lines)
└── README.md               # 이 파일
```

**총 라인 수**: 기존 719줄 → 826줄 (모듈화로 인한 imports/docstrings 증가)

## 주요 개선 사항 (2025-10-20 리팩토링)

### 1. 모델 파일 분리
- **기존**: 단일 `models.py` (719줄, 14개 클래스)
- **개선**: 도메인별 6개 파일로 분리

### 2. AI 친화적 구조
- **작은 파일 크기**: 평균 100-150줄 (AI 컨텍스트 최적)
- **명확한 관심사 분리**: stock, blocks, patterns, presets, monitoring
- **독립적인 수정**: 한 도메인 변경 시 다른 도메인 영향 최소화

### 3. Import 경로 하위 호환성 유지
```python
# 기존 코드 변경 없이 동일하게 동작
from src.infrastructure.database.models import StockInfo, Block1Detection
from src.infrastructure.database.connection import DatabaseConnection
```

### 4. 타입 안정성 개선
- `connection.py`에 `Optional` 타입 힌팅 추가
- 전역 변수 타입 명시

## 모델 분류

### stock.py - 주식 기본 데이터 (4개 모델)
- `StockInfo`: 종목 정보
- `StockPrice`: OHLCV 가격 데이터 (수정주가)
- `MarketData`: 시가총액, PER, PBR 등
- `InvestorTrading`: 투자자별 매매 데이터

### blocks.py - 블록 탐지 결과 (4개 모델)
- `Block1Detection`: 블록1 탐지 결과
- `Block2Detection`: 블록2 탐지 결과
- `Block3Detection`: 블록3 탐지 결과
- `Block4Detection`: 블록4 탐지 결과

### patterns.py - 패턴 시스템 (1개 모델)
- `BlockPattern`: 재탐지 패턴 관리

### presets.py - 조건 프리셋 (2개 모델)
- `SeedConditionPreset`: Seed 탐지 조건 (엄격)
- `RedetectionConditionPreset`: 재탐지 조건 (완화)

### monitoring.py - 모니터링 (3개 모델)
- `DataCollectionLog`: 데이터 수집 로그
- `CollectionProgress`: 수집 진행 상황
- `DataQualityCheck`: 데이터 품질 체크

## 사용 예시

### 모델 Import
```python
# 개별 모델 import
from src.infrastructure.database.models import StockInfo, StockPrice

# 여러 모델 한 번에 import
from src.infrastructure.database.models import (
    Block1Detection,
    Block2Detection,
    SeedConditionPreset
)

# Base import (마이그레이션용)
from src.infrastructure.database.models import Base
```

### 데이터베이스 연결
```python
from src.infrastructure.database.connection import DatabaseConnection

# 연결 생성
db = DatabaseConnection("data/database/stock_data.db")

# 테이블 생성
db.create_tables()

# 세션 사용
with db.session_scope() as session:
    stocks = session.query(StockPrice).filter_by(ticker='005930').all()
```

### 쿼리 헬퍼 사용
```python
from src.infrastructure.database.queries import get_latest_dates_bulk

with db.session_scope() as session:
    latest = get_latest_dates_bulk(session, ['005930', '000660'])
    print(latest)  # {'005930': date(2024, 12, 31), '000660': date(2024, 12, 30)}
```

## 개발 가이드

### 새 모델 추가 시
1. 해당 도메인 파일에 모델 클래스 추가 (예: `stock.py`)
2. `models/__init__.py`의 import 및 `__all__`에 추가
3. Repository 생성 (필요시)

### 모델 수정 시
1. 해당 도메인 파일만 수정
2. 관계(relationship) 변경 시 관련 모델도 확인
3. 마이그레이션 스크립트 작성 (필요시)

### 테스트
```bash
# Import 테스트
python -c "from src.infrastructure.database.models import Base; print('OK')"

# 테이블 생성 테스트
python -c "from src.infrastructure.database.connection import DatabaseConnection; db = DatabaseConnection(':memory:'); db.create_tables(); print('OK')"
```

## 마이그레이션 히스토리

- **2025-10-20**: models.py 분리 (719줄 → 6개 파일)
- **2025-10-19**: Block4 추가, Preset 컬럼 재정렬
- **2025-10-18**: BaseEntryCondition composition 패턴 적용

## 참고 문서

- [BLOCK_DETECTION.md](../../../docs/implementation/BLOCK_DETECTION.md): 블록 탐지 상세
- [DATABASE_SCHEMA.md](../../../docs/architecture/DATABASE_SCHEMA.md): DB 스키마 문서
