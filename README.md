# 주식 분석 및 AI 학습 프로그램

한국 주식 시장 데이터를 수집하고 조건을 설정하여 탐지한 후 AI 학습을 수행하는 CLI 프로그램입니다.

클린 아키텍처(Clean Architecture)를 적용하여 구현되었습니다.

## 주요 기능

1. **데이터 수집**: 네이버 금융 하이브리드 수집 (수정주가 + 수정거래량)
2. **조건 설정**: 사용자 정의 조건 설정 (기술적 지표, 가격 범위 등)
3. **조건 탐지**: 설정된 조건에 부합하는 종목 탐지
4. **AI 학습**: 수집된 데이터로 AI 모델 학습 (LSTM, 분류 모델)

## 데이터 수집 방식

### 하이브리드 수집 (NaverHybridCollector)

액면분할/병합 등 기업 행동을 자동으로 반영하여 일관성 있는 데이터 수집:

1. **수정주가 수집** (fchart API)
   - 액면분할/병합이 자동 반영된 조정 가격
   - OHLC (시가/고가/저가/종가)

2. **원본 데이터 수집** (sise_day.nhn)
   - 실제 거래된 원본 가격과 거래량
   - 조정 비율 계산용

3. **수정거래량 자동 계산**
   ```python
   # 액면분할 전: 거래량 조정
   if price_ratio > 1.05:
       adjusted_volume = raw_volume × (raw_close / adj_close)
   # 액면분할 후: 조정 불필요
   else:
       adjusted_volume = raw_volume
   ```

4. **저장되는 데이터**
   - 수정주가 (open, high, low, close)
   - 수정거래량 (volume)
   - 거래대금 (trading_value = close × volume)
   - 조정 비율 (adjustment_ratio)
   - 원본 참고 데이터 (raw_close, raw_volume)

### 장점

- ✅ 액면분할/병합 자동 반영
- ✅ 모든 날짜의 데이터 일관성 보장
- ✅ 거래대금 정확성 검증
- ✅ 기술적 분석 신뢰성 향상

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 1. 대량 데이터 수집 (하이브리드 모드)

**bulk_collect.py**를 사용하여 수정주가와 수정거래량을 동시에 수집:

```bash
# 특정 종목 수집 (하이브리드 모드)
python bulk_collect.py --tickers 005930,000660,035720 --from 2024-01-01 --to 2024-12-31

# 전체 종목 수집 (KOSPI + KOSDAQ)
python bulk_collect.py --all --from 2020-01-01 --to 2024-12-31

# 이어서 수집 (중단된 지점부터)
python bulk_collect.py --all --from 2020-01-01 --resume

# 투자자 정보도 함께 수집
python bulk_collect.py --all --from 2024-01-01 --investor

# 레거시 모드 (원본 주가만)
python bulk_collect.py --tickers 005930 --from 2024-01-01 --legacy

# 옵션 전체 보기
python bulk_collect.py --help
```

**주요 옵션**:
- `--all`: 전체 종목 수집 (KOSPI + KOSDAQ, ~2,500종목)
- `--tickers`: 특정 종목 코드 (쉼표로 구분)
- `--from`: 시작 날짜 (YYYY-MM-DD)
- `--to`: 종료 날짜 (기본값: 오늘)
- `--investor`: 투자자별 거래 정보도 수집
- `--resume`: 중단된 지점부터 이어서 수집
- `--legacy`: 레거시 모드 (하이브리드 비활성화)
- `--delay`: API 대기 시간 (초, 기본값: 0.2)
- `--db`: 데이터베이스 경로

### 2. 개별 데이터 수집 (레거시)

```bash
# 특정 종목 수집
python main.py collect stocks -t 005930 -t 000660 -s 2023-01-01 -e 2024-12-31

# 시가총액 상위 50개 종목 수집
python main.py collect stocks --market KOSPI --top-n 50 -s 2023-01-01

# KOSDAQ 전체 수집
python main.py collect stocks --market KOSDAQ -s 2024-01-01
```

### 3. 조건 관리

```bash
# 조건 목록 조회
python main.py condition list

# 새로운 조건 생성 (대화형)
python main.py condition create -n "골든크로스" -d "5일선이 20일선 상향 돌파"

# 조건 삭제
python main.py condition delete "골든크로스"
```

### 4. 조건 탐지

```bash
# 특정 조건으로 탐지 (시가총액 상위 100개)
python main.py detect -c "골든크로스" --market KOSPI --top-n 100

# 특정 종목에서 탐지
python main.py detect -c "RSI_과매도" -t 005930 -t 000660 -s 2024-01-01

# 날짜 범위 지정
python main.py detect -c "거래량_급증" --market KOSDAQ --top-n 50 -s 2024-01-01 -e 2024-12-31
```

### 5. AI 학습

```bash
# LSTM 모델 학습 (특정 종목 가격 예측)
python main.py train lstm -t 005930 -s 2022-01-01 --epochs 100

# 분류 모델 학습 (상승/하락 예측)
python main.py train classification --market KOSPI --top-n 50 --epochs 50

# 저장된 모델 목록
python main.py train list-models
```

## 프로젝트 구조 (클린 아키텍처)

```
potale_stock/
├── main.py                          # CLI 진입점
├── requirements.txt                 # 의존성 패키지
├── config/                          # 설정 파일
│   ├── config.yaml
│   └── conditions.yaml
├── src/
│   ├── domain/                      # Domain Layer
│   │   ├── entities/                # 비즈니스 엔티티
│   │   │   ├── stock.py
│   │   │   ├── condition.py
│   │   │   └── detection_result.py
│   │   └── repositories/            # Repository 인터페이스
│   │       ├── stock_repository.py
│   │       └── condition_repository.py
│   │
│   ├── application/                 # Application Layer
│   │   ├── use_cases/               # Use Cases
│   │   │   ├── collect_stock_data.py
│   │   │   ├── detect_condition.py
│   │   │   └── manage_condition.py
│   │   └── services/                # Application Services
│   │       ├── indicator_calculator.py
│   │       └── condition_checker.py
│   │
│   ├── infrastructure/              # Infrastructure Layer
│   │   └── repositories/            # Repository 구현체
│   │       ├── pykrx_stock_repository.py
│   │       └── yaml_condition_repository.py
│   │
│   ├── learning/                    # AI/ML 모듈
│   │   ├── models.py                # AI 모델 정의
│   │   └── trainer.py               # 학습 관리
│   │
│   ├── collector/                   # Legacy (호환용)
│   └── condition/                   # Legacy (호환용)
│
├── data/                            # 수집된 데이터
└── models/                          # 학습된 모델
```

## 아키텍처 설명

### 클린 아키텍처 레이어

1. **Domain Layer** (최상위 레이어)
   - 비즈니스 로직과 엔티티
   - 외부 의존성 없음
   - Stock, Condition, DetectionResult 등의 엔티티

2. **Application Layer**
   - Use Cases: 비즈니스 규칙 실행
   - Services: 도메인 서비스
   - Repository 인터페이스 의존

3. **Infrastructure Layer**
   - 외부 라이브러리, API 통합
   - Repository 인터페이스 구현
   - pykrx, YAML 파일 등 실제 데이터 소스 연결

4. **Presentation Layer**
   - CLI 인터페이스 (main.py)
   - Use Cases 호출

### 의존성 규칙

- 외부 레이어는 내부 레이어에 의존
- 내부 레이어는 외부 레이어를 알지 못함
- 의존성 역전 원칙(DIP) 적용

## 주요 특징

- Clean Architecture 적용으로 테스트 용이성 확보
- Repository 패턴으로 데이터 소스 추상화
- Use Case 패턴으로 비즈니스 로직 캡슐화
- 확장 가능한 구조 (새로운 데이터 소스, 조건 타입 추가 용이)

## 조건 타입

1. **Cross Over**: 골든크로스/데드크로스
2. **Indicator Threshold**: RSI, MACD 등 지표 임계값
3. **Volume Increase**: 거래량 급증
4. **Price Change**: 가격 변화율

## AI 모델

1. **LSTM**: 시계열 가격 예측
   - 60일 시퀀스 기반
   - 다음날 종가 예측

2. **Classification**: 상승/하락 분류
   - 기술적 지표 기반
   - 이진 분류 (상승/하락)

## 문서

### 사용자 가이드
- **[프로젝트 구조 상세 설명](docs/STRUCTURE.md)**: 클린 아키텍처 레이어별 설명, 워크플로우
- **[PyKRX 데이터 가이드](docs/PYKRX_DATA_GUIDE.md)**: PyKRX로 수집 가능한 모든 데이터 정리 (13개 테이블)

### 개발자 가이드 (2015년부터 전체 데이터 수집)
- **[데이터베이스 설계서](docs/DATABASE_DESIGN.md)**: 전체 16개 테이블 스키마, 인덱스 전략, 성능 최적화
- **[대량 수집 시스템 설계](docs/BULK_COLLECTION_DESIGN.md)**: 2015년부터 전체 데이터 수집 전략, API 최적화, 재개 기능
- **[구현 로드맵](docs/IMPLEMENTATION_ROADMAP.md)**: 단계별 구현 계획, 예상 일정, 체크리스트

## 로드맵

### Phase 1: 핵심 데이터 ✅ 완료
- [x] stock_info, stock_price, market_data
- [x] **NaverHybridCollector**: 수정주가 + 수정거래량 자동 계산
- [x] **BulkCollector 통합**: 대량 수집 시스템
- [x] **bulk_collect.py CLI**: 명령행 인터페이스

### Phase 2: 확장 데이터 (진행 중)
- [ ] investor_trading (투자자별 매매) - 가장 중요!
- [ ] 전체 종목 수집 (2,500+ 종목)
- [ ] 대량 수집 성능 최적화

### Phase 3: 고급 데이터 (계획)
- [ ] short_selling (공매도)
- [ ] index_data (지수)
- [ ] margin_trading, foreign_limit, ETF

## 라이센스

MIT
