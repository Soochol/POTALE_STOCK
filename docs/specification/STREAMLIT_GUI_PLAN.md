# Streamlit GUI 프로토타입 개발 계획

## 📋 프로젝트 개요

**목표**: Python Streamlit을 사용하여 Claudia GUI 스타일의 웹 기반 대시보드 프로토타입 개발

**개발 기간**: 1주일 (Phase 1 MVP)

**배포 방식**: 로컬 실행 (localhost:8501)

**핵심 원칙**:
- Clean Architecture 유지 (기존 domain/application 레이어 재사용)
- 새로운 presentation 레이어 추가 (기존 코드 수정 없음)
- 기존 CLI/TUI와 병행 사용 가능

---

## 🎯 Phase 1: 핵심 기능 (1주일)

### 1. 대시보드 (Home)
- **시스템 상태**
  - 총 종목 수 (KOSPI/KOSDAQ)
  - 데이터 수집 기간 (최초일 ~ 최신일)
  - 데이터베이스 크기
  - 최근 업데이트 시간

- **통계 카드**
  - Block1/2/3 탐지 총 개수
  - 진행중/완료된 Block 개수
  - 최근 7일 탐지 현황

- **시각화**
  - 일별 탐지 현황 차트 (Bar chart)
  - Block 유형별 분포 (Pie chart)

### 2. Block 탐지 결과 조회
- **필터링 UI**
  - 종목 검색 (Ticker/이름)
  - Block 유형 선택 (Block1/2/3)
  - 날짜 범위 선택
  - 상태 필터 (active/completed)

- **결과 테이블**
  - 종목코드, 종목명, Block 유형
  - 시작일, 종료일, 지속기간
  - 진입가, 최고가, 수익률
  - 조건 이름
  - 정렬/페이징 지원

- **상세 보기**
  - 테이블 행 클릭 시 상세 페이지로 이동

### 3. 차트 분석 (Chart Analysis)
- **캔들스틱 차트**
  - Plotly를 사용한 인터랙티브 차트
  - OHLC 캔들스틱
  - 이동평균선 오버레이
  - Block 진입/종료 지점 마커 표시
  - 거래량 차트 (하단)

- **Block 정보 패널**
  - 선택된 Block의 상세 정보
  - 진입/종료 조건 표시
  - 성과 지표 (최고가, 수익률 등)

- **종목 선택 UI**
  - Sidebar에서 종목 검색
  - Block 탐지된 종목만 필터링 옵션

---

## 🏗️ 아키텍처 설계

### 디렉토리 구조

```
potale_stock/
├── src/
│   ├── domain/              # 기존 유지
│   ├── application/         # 기존 유지
│   ├── infrastructure/      # 기존 유지
│   ├── cli/                 # 기존 TUI 유지
│   └── presentation/        # 🆕 새로 추가
│       └── streamlit_app/
│           ├── app.py                    # 메인 앱 진입점
│           ├── config.py                 # Streamlit 설정
│           │
│           ├── pages/                    # 각 페이지
│           │   ├── 1_🏠_Home.py         # 대시보드
│           │   ├── 2_📊_Block_Detection.py  # Block 탐지 결과
│           │   └── 3_📈_Chart_Analysis.py   # 차트 분석
│           │
│           ├── components/               # 재사용 UI 컴포넌트
│           │   ├── filters.py           # 필터 UI
│           │   ├── tables.py            # 테이블 컴포넌트
│           │   ├── charts.py            # 차트 컴포넌트
│           │   └── metrics.py           # 메트릭 카드
│           │
│           ├── services/                 # Streamlit 전용 서비스
│           │   ├── data_loader.py       # 데이터 로딩 (캐싱)
│           │   └── chart_builder.py     # 차트 생성 헬퍼
│           │
│           └── utils/                    # 유틸리티
│               ├── session_state.py     # 세션 상태 관리
│               └── formatters.py        # 데이터 포맷팅
│
├── docs/
│   └── STREAMLIT_GUI_PLAN.md   # 🆕 본 개발 계획서
│
└── requirements.txt            # streamlit 추가
```

### 파일별 책임

#### `app.py` (메인 진입점)
```python
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="POTALE Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 홈페이지 (대시보드)
# 나머지는 pages/ 폴더로 자동 멀티페이지
```

#### `pages/1_🏠_Home.py` (대시보드)
- Repository를 통해 DB 통계 조회
- 메트릭 카드 표시 (st.metric)
- 차트 표시 (st.plotly_chart)

#### `pages/2_📊_Block_Detection.py` (탐지 결과)
- 필터 UI (Sidebar)
- Block1/2/3 Repository에서 데이터 조회
- 테이블 표시 (st.dataframe)
- 행 클릭 시 차트 분석 페이지로 이동

#### `pages/3_📈_Chart_Analysis.py` (차트 분석)
- 종목 선택 UI
- StockRepository에서 가격 데이터 조회
- BlockRepository에서 탐지 결과 조회
- Plotly 캔들스틱 차트 생성
- Block 마커 오버레이

#### `components/charts.py` (차트 컴포넌트)
```python
def create_candlestick_chart(stocks, block_detections):
    """캔들스틱 차트 + Block 마커 생성"""
    # Plotly Candlestick
    # Block 진입/종료 지점에 annotation 추가
    # 이동평균선 추가
    return fig

def create_volume_chart(stocks):
    """거래량 차트 생성"""
    return fig
```

#### `services/data_loader.py` (데이터 로딩)
```python
@st.cache_data(ttl=300)  # 5분 캐싱
def load_all_blocks():
    """모든 Block 탐지 결과 로드"""
    # Block1/2/3 Repository 사용
    pass

@st.cache_data(ttl=60)
def load_stock_data(ticker, start_date, end_date):
    """종목 데이터 로드"""
    # StockRepository 사용
    pass
```

---

## 🔌 기존 시스템 통합

### Repository 재사용
```python
# Streamlit에서 기존 Repository 직접 사용
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.repositories.block2_repository import Block2Repository
from src.infrastructure.repositories.block3_repository import Block3Repository
from src.infrastructure.database.connection import DatabaseConnection

# 초기화
db_path = "data/database/stock_data.db"
db_conn = DatabaseConnection(db_path)

stock_repo = SqliteStockRepository(db_path)
block1_repo = Block1Repository(db_conn)
block2_repo = Block2Repository(db_conn)
block3_repo = Block3Repository(db_conn)
```

### Use Case 재사용 (필요시)
```python
# Block 탐지 실행 (Phase 2에서 추가)
from src.application.use_cases.detect_block1 import DetectBlock1UseCase

use_case = DetectBlock1UseCase(block1_repo)
detections = use_case.execute(condition, "my_condition", stocks)
```

---

## 📦 필요한 패키지 추가

### requirements.txt 업데이트
```txt
# 기존 패키지들...

# Streamlit GUI (새로 추가)
streamlit>=1.30.0
plotly>=5.18.0
```

---

## 🎨 UI/UX 디자인 가이드 (Claudia 스타일)

### 컬러 테마
```python
# Streamlit 설정 (.streamlit/config.toml)
[theme]
primaryColor = "#3b82f6"      # Blue (Claudia 스타일)
backgroundColor = "#0f172a"    # Dark background
secondaryBackgroundColor = "#1e293b"
textColor = "#f1f5f9"
font = "sans serif"
```

### 레이아웃 원칙
1. **Wide Layout** - 넓은 화면 활용
2. **Sidebar Navigation** - 좌측 사이드바로 페이지 이동
3. **Metrics First** - 상단에 주요 지표 카드
4. **Interactive Charts** - Plotly 인터랙티브 차트
5. **Clean & Minimal** - 깔끔한 디자인

---

## 📊 주요 화면 목업

### 1. 대시보드 (Home)
```
┌─────────────────────────────────────────────────────┐
│  🏠 POTALE Stock Analysis Dashboard                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [📊 4,189 종목] [📅 2020-01-01 ~ 2024-12-31]      │
│  [💾 2.3 GB]     [🔄 2시간 전 업데이트]             │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Block1   │ │ Block2   │ │ Block3   │            │
│  │  1,245   │ │   432    │ │   189    │            │
│  │  ↑ 12%   │ │  ↑ 8%    │ │  ↓ 3%    │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│                                                      │
│  ┌─ 일별 탐지 현황 ─────────────────────┐          │
│  │                                        │          │
│  │  [Bar Chart - 최근 30일]              │          │
│  │                                        │          │
│  └────────────────────────────────────────┘          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 2. Block 탐지 결과
```
┌─────────────────────────────────────────────────────┐
│  📊 Block Detection Results                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Sidebar Filters]                                  │
│   🔍 종목 검색: [_______]                           │
│   📌 Block 유형: [All ▼]                            │
│   📅 기간: [2024-01-01] ~ [2024-12-31]             │
│   ✓ 진행중만 보기                                    │
│                                                      │
│  ┌─ 탐지 결과 테이블 ──────────────────┐           │
│  │ Ticker │ Name  │ Type │ Start  │ ... │           │
│  ├────────┼───────┼──────┼────────┼─────┤           │
│  │ 005930 │ 삼성  │ B1   │ 01-15  │ ... │           │
│  │ 000660 │ SK   │ B2   │ 01-20  │ ... │           │
│  │ ...                                    │           │
│  └────────────────────────────────────────┘           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 3. 차트 분석
```
┌─────────────────────────────────────────────────────┐
│  📈 Chart Analysis - 삼성전자 (005930)              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Sidebar]                                          │
│   🔍 종목: [삼성전자 ▼]                             │
│   📅 기간: [최근 3개월 ▼]                           │
│                                                      │
│  ┌─ Candlestick Chart ───────────────┐             │
│  │                                     │             │
│  │  [Interactive Plotly Chart]        │             │
│  │  - Candlestick                     │             │
│  │  - Moving Average                  │             │
│  │  - Block1 Entry Marker (🟢)       │             │
│  │  - Block1 Exit Marker (🔴)        │             │
│  │                                     │             │
│  └─────────────────────────────────────┘             │
│                                                      │
│  ┌─ Volume Chart ─────────────────────┐             │
│  │  [Bar Chart]                        │             │
│  └─────────────────────────────────────┘             │
│                                                      │
│  ┌─ Block Info ───────────────────────┐             │
│  │  Block1 #abc123                     │             │
│  │  시작: 2024-01-15                   │             │
│  │  종료: 2024-02-20 (37일)            │             │
│  │  진입가: 75,000원                   │             │
│  │  최고가: 85,000원 (+13.3%)          │             │
│  └─────────────────────────────────────┘             │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 구현 순서

### Day 1-2: 기본 구조 및 대시보드
1. Streamlit 설치 및 프로젝트 구조 생성
2. `app.py` 메인 앱 생성
3. `1_🏠_Home.py` 대시보드 페이지 구현
   - Repository 연결
   - 통계 쿼리 작성
   - 메트릭 카드 표시
   - 기본 차트 (막대 그래프)

### Day 3-4: Block 탐지 결과 페이지
1. `2_📊_Block_Detection.py` 페이지 구현
2. 필터 UI 구현 (Sidebar)
3. Block1/2/3 Repository 통합
4. 결과 테이블 표시
5. 페이징/정렬 구현

### Day 5-6: 차트 분석 페이지
1. `3_📈_Chart_Analysis.py` 페이지 구현
2. Plotly 캔들스틱 차트 생성
3. Block 마커 오버레이
4. 이동평균선 추가
5. 거래량 차트 추가
6. Block 정보 패널 구현

### Day 7: 통합 테스트 및 최적화
1. 전체 기능 테스트
2. 캐싱 최적화 (@st.cache_data)
3. 에러 핸들링 추가
4. 문서 작성 (README 업데이트)
5. 실행 가이드 작성

---

## 🧪 테스트 계획

### 기능 테스트
- [ ] 대시보드 통계가 정확한가?
- [ ] Block 탐지 결과 필터링이 작동하는가?
- [ ] 차트가 올바르게 표시되는가?
- [ ] Block 마커가 정확한 위치에 있는가?
- [ ] 캐싱이 작동하는가?

### 성능 테스트
- [ ] 1,000개 이상 Block 탐지 결과 로딩 속도
- [ ] 차트 렌더링 속도
- [ ] 메모리 사용량

### 사용성 테스트
- [ ] 직관적인 네비게이션
- [ ] 필터 사용이 쉬운가?
- [ ] 차트 인터랙션이 부드러운가?

---

## 📝 실행 방법

### 설치
```bash
# 패키지 설치
pip install streamlit plotly

# 또는 requirements.txt 업데이트 후
pip install -r requirements.txt
```

### 실행
```bash
# Streamlit 앱 실행
streamlit run src/presentation/streamlit_app/app.py

# 브라우저 자동 오픈: http://localhost:8501
```

### 옵션
```bash
# 포트 변경
streamlit run src/presentation/streamlit_app/app.py --server.port 8502

# 자동 리로드 비활성화
streamlit run src/presentation/streamlit_app/app.py --server.runOnSave false
```

---

## 🔮 Phase 2: 향후 확장 계획 (선택)

### 4. 조건 설정/관리 페이지
- Block1/2/3 조건 파라미터 GUI 편집
- 슬라이더로 파라미터 조정
- 조건 프리셋 저장/로드 (YAML)
- 실시간 미리보기

### 5. 데이터 수집 페이지
- 종목 선택 UI (멀티셀렉트)
- 날짜 범위 선택
- 수집 시작 버튼
- 진행 상황 프로그레스바
- 로그 스트리밍

### 6. 백테스팅 페이지
- 조건 비교 UI
- 성과 지표 차트
- 승률, 평균 수익률, MDD 등
- 조건별 비교 테이블

### 7. 고급 기능
- 알림 설정 (새 Block 탐지 시)
- 엑셀/CSV 내보내기
- 사용자 설정 저장
- 다크 모드 토글

---

## ⚠️ 제약사항 및 주의사항

### 제약사항
1. **실시간 업데이트 제한**: Streamlit은 폴링 기반 (자동 새로고침 필요)
2. **멀티유저 제한**: 세션 상태가 사용자별로 분리됨
3. **대용량 데이터**: 10만 건 이상은 페이징 필수

### 주의사항
1. **캐싱 전략**: @st.cache_data로 불필요한 DB 쿼리 방지
2. **메모리 관리**: 큰 DataFrame은 Pandas 최적화 필요
3. **에러 핸들링**: try-except로 사용자 친화적 에러 메시지

---

## 📚 참고 자료

### Streamlit 공식 문서
- https://docs.streamlit.io/
- https://docs.streamlit.io/library/api-reference/charts/st.plotly_chart

### Plotly 차트 예제
- https://plotly.com/python/candlestick-charts/
- https://plotly.com/python/financial-charts/

### 유사 프로젝트
- Streamlit Finance Dashboard Examples
- Stock Analysis Streamlit Apps

---

## ✅ 성공 기준

Phase 1 완료 시:
- [ ] Streamlit 앱이 정상 실행됨
- [ ] 대시보드에서 시스템 상태 확인 가능
- [ ] Block 탐지 결과를 필터링하여 조회 가능
- [ ] 종목별 차트에서 Block 진입/종료 지점 확인 가능
- [ ] 모든 페이지가 3초 이내 로딩
- [ ] 기존 CLI/TUI와 병행 사용 가능

---

## 🎉 기대 효과

1. **사용성 향상**: CLI/TUI 대비 직관적인 시각화
2. **빠른 분석**: 차트로 한눈에 패턴 파악
3. **접근성**: 브라우저만 있으면 사용 가능
4. **확장성**: Phase 2로 기능 추가 용이
5. **학습 도구**: Streamlit으로 Python GUI 학습

---

**개발 시작 준비 완료!** 🚀
