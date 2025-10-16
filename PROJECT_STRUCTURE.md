# 프로젝트 구조 분석

## 현재 상태 (2025-10-17)

### ✅ 잘 구조화된 부분

```
src/
├── infrastructure/
│   ├── collectors/              ✅ 체계적인 수집기들
│   │   ├── base_collector.py           # 베이스 클래스
│   │   ├── naver_base_collector.py     # 네이버 금융 베이스 ✅ 신규
│   │   ├── naver_investor_collector.py # 네이버 투자자 수집 ✅ 신규
│   │   ├── investor_trading_collector.py # PyKRX 투자자 (사용 안함)
│   │   ├── stock_price_collector.py    # PyKRX 가격 수집
│   │   └── market_info_collector.py    # PyKRX 시장 정보
│   │
│   ├── repositories/            ✅ Repository 패턴
│   │   ├── sqlite_stock_repository.py
│   │   ├── pykrx_stock_repository.py
│   │   └── yaml_condition_repository.py
│   │
│   └── database/                ✅ DB 관리
│       ├── connection.py
│       └── models.py
│
├── domain/                      ✅ Clean Architecture
│   ├── entities/
│   │   ├── stock.py
│   │   ├── condition.py
│   │   └── detection_result.py
│   └── repositories/            # Interface (추상 클래스)
│       ├── stock_repository.py
│       └── condition_repository.py
│
├── application/                 ✅ Use Cases
│   ├── services/
│   │   ├── condition_checker.py
│   │   └── indicator_calculator.py
│   └── use_cases/
│       ├── collect_stock_data.py
│       ├── detect_condition.py
│       └── manage_condition.py
│
├── collector/                   ⚠️ 중복! (구버전)
│   └── stock_collector.py      # 사용 안함, 삭제 필요
│
├── condition/                   ⚠️ 중복! (구버전)
│   ├── condition_manager.py    # application/use_cases와 중복
│   └── detector.py             # application/services와 중복
│
└── learning/                    ✅ AI 학습
    ├── models.py
    └── trainer.py
```

---

## 문제점 및 개선 사항

### 🔴 문제 1: 중복된 디렉토리

**중복:**
- `src/collector/` ← 구버전 (Clean Architecture 적용 전)
- `src/infrastructure/collectors/` ← 신버전 ✅

**중복:**
- `src/condition/` ← 구버전
- `src/application/services/` + `src/application/use_cases/` ← 신버전 ✅

**해결:**
```bash
# 구버전 삭제 권장
rm -rf src/collector/
rm -rf src/condition/
```

---

### 🟡 문제 2: PyKRX vs 네이버 금융 혼재

**현재 상태:**
- `investor_trading_collector.py` (PyKRX) - 작동 안함 ❌
- `naver_investor_collector.py` (네이버) - 정상 작동 ✅

- `stock_price_collector.py` (PyKRX) - 일부 작동
- `market_info_collector.py` (PyKRX) - 일부 작동

**전략:**
1. **투자자 데이터**: 네이버 금융 사용 (PyKRX 차단됨)
2. **가격 데이터**: PyKRX 우선, 실패 시 네이버로 전환
3. **시장 데이터**: PyKRX 우선

---

## 권장 구조 (Clean Architecture)

```
src/
├── domain/                      # 핵심 비즈니스 로직 (Framework 독립)
│   ├── entities/                # 엔티티
│   │   ├── stock.py
│   │   ├── investor_trading.py
│   │   └── condition.py
│   │
│   └── repositories/            # Repository 인터페이스 (추상)
│       ├── stock_repository.py
│       └── condition_repository.py
│
├── application/                 # Use Cases (비즈니스 규칙)
│   ├── services/                # 도메인 서비스
│   │   ├── condition_checker.py
│   │   └── indicator_calculator.py
│   │
│   └── use_cases/               # 애플리케이션 로직
│       ├── collect_stock_data.py
│       ├── detect_condition.py
│       └── manage_condition.py
│
├── infrastructure/              # 외부 의존성 (Framework, DB, API)
│   ├── collectors/              # 데이터 수집 (외부 API)
│   │   ├── base_collector.py
│   │   ├── naver/               # 네이버 금융
│   │   │   ├── naver_base_collector.py
│   │   │   ├── naver_investor_collector.py
│   │   │   ├── naver_price_collector.py  ← 추가 예정
│   │   │   └── naver_market_collector.py ← 추가 예정
│   │   │
│   │   └── pykrx/               # PyKRX (참고용/백업)
│   │       ├── investor_trading_collector.py
│   │       ├── stock_price_collector.py
│   │       └── market_info_collector.py
│   │
│   ├── repositories/            # Repository 구현
│   │   ├── sqlite_stock_repository.py
│   │   └── yaml_condition_repository.py
│   │
│   └── database/                # DB 관리
│       ├── connection.py
│       └── models.py
│
├── presentation/                # CLI/UI (예정)
│   └── cli/
│       └── commands.py
│
└── learning/                    # AI 학습 모듈
    ├── models.py
    └── trainer.py
```

---

## 데이터 수집 파일 현황

### ✅ 완성된 수집기

| 파일 | 상태 | 데이터 소스 | 용도 |
|------|------|------------|------|
| `naver_base_collector.py` | ✅ 완료 | 네이버 금융 | 베이스 클래스 |
| `naver_investor_collector.py` | ✅ 완료 | 네이버 금융 | 투자자 거래 |

### 🔜 구현 예정

| 파일 | 우선순위 | 데이터 소스 | 용도 |
|------|---------|------------|------|
| `naver_price_collector.py` | P0 (최우선) | 네이버 금융 | OHLCV 가격 |
| `naver_market_collector.py` | P1 | 네이버 금융 | 시가총액, 재무지표 |
| `bulk_collector.py` | P0 (최우선) | - | 대량 일괄 수집 |

### ⚠️ 참고용 (PyKRX)

| 파일 | 상태 | 비고 |
|------|------|------|
| `investor_trading_collector.py` | ❌ 작동 안함 | KRX 403 차단 |
| `stock_price_collector.py` | △ 일부 작동 | OHLCV는 작동 |
| `market_info_collector.py` | △ 일부 작동 | 시가총액은 작동 |

---

## 즉시 해야 할 작업

### 1. 중복 디렉토리 정리 (5분)

```bash
# 구버전 삭제
git rm -rf src/collector/
git rm -rf src/condition/

# 또는 수동 삭제
rm -rf src/collector/
rm -rf src/condition/

git commit -m "refactor: Remove legacy collector and condition directories"
```

### 2. Collectors 디렉토리 재구성 (10분)

```bash
cd src/infrastructure/collectors/

# 네이버 금융 전용 디렉토리 생성
mkdir naver/
mv naver_*.py naver/

# PyKRX 참고용 디렉토리 생성
mkdir pykrx/
mv investor_trading_collector.py pykrx/
mv stock_price_collector.py pykrx/
mv market_info_collector.py pykrx/
```

### 3. 다음 구현 (우선순위)

**P0 (즉시):**
1. `naver_price_collector.py` - OHLCV 데이터 수집
2. `bulk_collector.py` - 대량 수집 관리

**P1 (1주일 내):**
3. `naver_market_collector.py` - 시가총액, PER, PBR
4. CLI 명령어 추가

---

## 요약

### ✅ 현재 잘되고 있는 것
1. Clean Architecture 구조 적용 완료
2. 네이버 금융 수집기 구현 완료 (투자자 거래)
3. DB 모델 확장 완료
4. Repository 패턴 적용

### 🔧 개선 필요
1. 중복 디렉토리 삭제 (`src/collector/`, `src/condition/`)
2. Collectors 재구성 (naver/, pykrx/ 분리)
3. 추가 수집기 구현 필요 (가격, 시가총액)

### 🎯 다음 목표
1. 중복 디렉토리 정리
2. `naver_price_collector.py` 구현
3. `bulk_collector.py` 구현
4. 전체 데이터 수집 시작

---

**결론: 전반적으로 체계적이지만, 구버전 파일 정리와 추가 수집기 구현이 필요합니다.**
