# Option D 리팩토링 완료 요약

**날짜**: 2025-10-26
**작업**: 멀티패턴 동시 탐지 지원을 위한 Option D 완전 리팩토링
**목표**: 여러 독립 패턴 동시 탐지 (패턴 간 간섭 제거)

---

## 문제 상황 (Before)

### 근본 원인
```python
# src/application/use_cases/dynamic_block_detector.py:80
active_blocks_map: Dict[str, DynamicBlockDetection] = {b.block_id: b for b in active_blocks}
```

**문제점**:
- `Dict[str, DynamicBlockDetection]` 구조는 `block_id`를 키로 사용
- 같은 `block_id`를 가진 블록은 **하나만 유지 가능**
- 새로운 Block1이 탐지되면 **이전 Block1을 덮어씌움**

### 실제 증상
```
아난티(025980) 2015-2025 데이터 탐지:
- Block1 조건 만족: 26회
- 실제 저장된 패턴: 1개 ❌
```

**데이터 손실**:
- 25개 패턴이 덮어씌워져 손실
- 마지막 패턴(2025-07-31)만 DB에 저장

---

## 해결 방안 (After - Option D)

### 설계 원칙: Clean Architecture + 책임 분리 (SRP)

**핵심 아이디어**: 패턴별 독립 컨텍스트 관리

```python
# 각 패턴이 독립적인 블록 맵 보유
active_pattern_contexts: List[PatternContext] = [
    PatternContext(
        pattern_id="SEED_025980_20180307_001",
        blocks={'block1': Block1_A, 'block2': Block2_A}
    ),
    PatternContext(
        pattern_id="SEED_025980_20200416_002",
        blocks={'block1': Block1_B, 'block2': Block2_B}
    ),
    # ... 무제한 패턴
]
```

### 아키텍처 변경

#### Before (단일 패턴)
```
DynamicBlockDetector
  ├─ active_blocks_map: Dict[str, Block]  # 하나의 block_id당 하나의 블록
  ├─ 블록 탐지 + 패턴 관리 (책임 과다)
  └─ detect_blocks() → List[Block]

Orchestrator
  ├─ detector.detect_blocks() 호출
  └─ _organize_blocks_into_patterns() (후처리)
```

#### After (멀티패턴)
```
DynamicBlockDetector (Stateless)
  ├─ evaluate_entry_condition(node, context) → bool
  ├─ evaluate_exit_condition(node, context) → Optional[str]
  └─ evaluate_spot_strategy(node, context) → Optional[Block]

Orchestrator (패턴 수명주기 관리)
  ├─ active_pattern_contexts: List[PatternContext]
  ├─ for each stock:
  │   ├─ Block1 체크 → 새 패턴 생성
  │   └─ for each pattern:
  │       ├─ context = build_pattern_context(pattern, stock)
  │       ├─ detector.evaluate_entry_condition()
  │       └─ 블록 생성/업데이트/완료
  └─ detect_patterns() → List[SeedPatternTree]
```

---

## 구현 세부사항

### Phase 1: PatternContext 클래스 추가

**파일**: `src/application/use_cases/pattern_detection_state.py` (Line 124-261)

```python
@dataclass
class PatternContext:
    """단일 패턴의 실행 컨텍스트"""
    pattern_id: str
    ticker: str
    blocks: Dict[str, DynamicBlockDetection]  # 이 패턴의 블록들
    block_graph: BlockGraph
    created_at: date
    detection_state: PatternDetectionState

    def get_next_target_nodes(self) -> List[BlockNode]:
        """다음에 탐지할 노드 목록 (엣지 기반)"""

    def is_completed(self) -> bool:
        """패턴 완료 여부 (모든 블록 completed)"""
```

**역할**: 각 패턴의 블록들을 독립적으로 격리 관리

---

### Phase 2: DynamicBlockDetector 리팩토링 (Stateless)

**파일**: `src/application/use_cases/dynamic_block_detector.py` (Line 151-257)

```python
class DynamicBlockDetector:
    """순수 조건 평가기 (stateless)"""

    def evaluate_entry_condition(self, node: BlockNode, context: dict) -> bool:
        """진입 조건만 평가 (상태 관리 없음)"""

    def evaluate_exit_condition(self, node: BlockNode, context: dict) -> Optional[str]:
        """종료 조건만 평가 (상태 관리 없음)"""

    def evaluate_spot_strategy(self, node: BlockNode, context: dict) -> Optional[Block]:
        """Spot 전략 평가 (상태 관리 없음)"""
```

**변경사항**:
- ✅ 새 API: `evaluate_*()` 메서드 추가 (stateless)
- ⚠️ 기존 API: `detect_blocks()` deprecated 표시 (하위 호환용 유지)

**책임 분리**:
- **Before**: 조건 평가 + 블록 생성 + 패턴 관리
- **After**: 조건 평가만 (순수 함수)

---

### Phase 3: Orchestrator 수정 (패턴 수명주기 관리)

**파일**: `src/application/use_cases/seed_pattern_detection_orchestrator.py`

#### 3.1. `detect_patterns()` 완전 재작성 (Line 77-223)

```python
def detect_patterns(self, ticker, stocks):
    active_pattern_contexts: List[PatternContext] = []

    # 데이터 1회 순회 (효율적)
    for i, current_stock in enumerate(stocks):
        prev_stock = self._find_last_valid_day(stocks, i)

        # 1. Block1 조건 체크 (패턴 무관)
        if self._should_start_new_pattern(ticker, current_stock, prev_stock, stocks[:i+1]):
            new_pattern = self._create_pattern_context(ticker, current_stock, ...)
            active_pattern_contexts.append(new_pattern)

        # 2. 각 패턴마다 진행
        for pattern_ctx in active_pattern_contexts:
            # 패턴별 컨텍스트 구축
            context = self._build_pattern_context(pattern_ctx, current_stock, ...)

            # 활성 블록 peak 갱신
            self._update_active_blocks(pattern_ctx, current_stock)

            # 다음 블록 진입 체크
            self._check_and_create_next_blocks(pattern_ctx, context, ...)

            # 종료 조건 체크
            self._check_and_complete_blocks(pattern_ctx, context, ...)

    # 3. PatternContext → SeedPatternTree 변환
    self._convert_to_pattern_trees(ticker, active_pattern_contexts)

    return self.pattern_manager.get_all_patterns()
```

#### 3.2. 새 헬퍼 메서드 (Line 495-859)

```python
def _should_start_new_pattern(...) -> bool:
    """Block1 진입 조건 평가 (패턴 무관)"""

def _create_pattern_context(...) -> PatternContext:
    """새 패턴 컨텍스트 생성 + Block1 추가"""

def _build_pattern_context(...) -> dict:
    """패턴별 평가 컨텍스트 구축 (핵심!)"""
    context = {
        'current': current_stock,
        'prev': prev_stock,
        'all_stocks': all_stocks,
        'pattern_id': pattern.pattern_id,
        'active_blocks': pattern.blocks,  # Spot 전략용
    }
    # 이 패턴의 블록들 추가
    for block_id, block in pattern.blocks.items():
        context[block_id] = block  # ✅ 패턴별로 독립된 block1, block2, ...
    return context

def _update_active_blocks(...):
    """활성 블록 peak 갱신"""

def _check_and_create_next_blocks(...):
    """다음 블록 진입 조건 체크 및 생성"""

def _check_and_complete_blocks(...):
    """활성 블록 종료 조건 체크"""

def _convert_to_pattern_trees(...):
    """PatternContext → SeedPatternTree 변환"""
```

---

## 검증 결과

### Mock 데이터 테스트 (50일, 3개 패턴)

**시나리오**:
- 2020-01-10: Pattern #1 시작 (거래대금 330억)
- 2020-01-20: Pattern #2 시작 (거래대금 420억) ← Pattern #1과 독립
- 2020-02-01: Pattern #3 시작 (거래대금 520억) ← Pattern #1, #2와 독립

**결과**: ✅ **3개 패턴 모두 탐지**

```
Pattern #1:
  - ID: SEED_TEST001_20200110_001
  - Blocks: block1 (2020-01-10), block2 (2020-02-01)

Pattern #2:
  - ID: SEED_TEST001_20200120_002
  - Blocks: block1 (2020-01-20), block2 (2020-02-01)

Pattern #3:
  - ID: SEED_TEST001_20200201_003
  - Blocks: block1 (2020-02-01)
```

**검증 항목**:
- ✅ 예상 패턴 개수 일치 (3개)
- ✅ 모든 패턴이 Block1 포함
- ✅ 모든 pattern_id가 고유함
- ✅ pattern_id 형식 정확 (`SEED_{ticker}_{YYYYMMDD}_{seq}`)

---

## 핵심 개선사항

### 1. 패턴별 독립 평가
```python
# Before: 전역 컨텍스트 (모든 패턴이 같은 block1 참조)
context = {'block1': active_blocks_map.get('block1')}  # ❌ 어느 패턴의 block1?

# After: 패턴별 컨텍스트
for pattern in active_patterns:
    context = {'block1': pattern.blocks['block1']}  # ✅ 이 패턴의 block1
    detector.evaluate_entry_condition(node, context)
```

### 2. 무제한 동시 패턴
```python
# Before: block_id당 하나의 블록만 유지
active_blocks_map = {'block1': Block1_최신것}  # ❌ 이전 Block1 덮어씌워짐

# After: 무제한 패턴 동시 관리
active_pattern_contexts = [
    Pattern#1(blocks={'block1': Block1_A}),
    Pattern#2(blocks={'block1': Block1_B}),
    Pattern#3(blocks={'block1': Block1_C}),
    # ... 메모리가 허용하는 한 무제한
]
```

### 3. Pattern ID 자동 생성
```python
# 형식: SEED_{ticker}_{YYYYMMDD}_{sequence}
"SEED_025980_20180307_001"
"SEED_025980_20200416_002"
"SEED_025980_20250731_026"
```

### 4. 책임 분리 (SRP)
- **DynamicBlockDetector**: 조건 평가만 (stateless)
- **Orchestrator**: 패턴 수명주기 관리
- **PatternManager**: 패턴 상태 관리
- **명확한 책임 분리** ✅

### 5. 효율성
- **데이터 순회**: 1회만 (O(M * N))
  - M = 캔들 개수
  - N = 활성 패턴 개수 (보통 작음, 1~10개)
- **지표 계산**: 공통화 가능 (MA, volume_ma 등)

---

## Breaking Changes

### 1. API 변경

#### DynamicBlockDetector
```python
# Deprecated (하위 호환용 유지)
detector.detect_blocks(ticker, stocks, condition_name)

# New API (권장)
detector.evaluate_entry_condition(node, context)
detector.evaluate_exit_condition(node, context)
detector.evaluate_spot_strategy(node, context)
```

#### Orchestrator
```python
# 변경 없음 (내부 로직만 완전 재작성)
orchestrator.detect_patterns(ticker, stocks)
```

### 2. 필요 조치

**기존 코드 마이그레이션**:
- `DynamicBlockDetector.detect_blocks()`를 직접 사용하는 코드
  → `SeedPatternDetectionOrchestrator.detect_patterns()` 사용

**RedetectionDetector**:
- 현재는 영향 없음
- 향후 동일한 방식으로 리팩토링 필요 (별도 작업)

---

## 예상 효과 (실제 데이터)

### 아난티(025980) 2015-2025 탐지 시

#### Before
```
Block1 조건 만족: 26회
저장된 패턴: 1개 ❌
손실률: 96.2% (25/26)
```

#### After (예상)
```
Block1 조건 만족: 26회
저장된 패턴: 26개 ✅
손실률: 0%
```

**개선율**: **2,500%** (1개 → 26개)

---

## 변경 파일 목록

1. **src/application/use_cases/pattern_detection_state.py**
   - ✅ `PatternContext` 클래스 추가 (124-261줄)

2. **src/application/use_cases/dynamic_block_detector.py**
   - ✅ Stateless API 추가 (151-257줄)
   - ⚠️ `detect_blocks()` deprecated 표시

3. **src/application/use_cases/seed_pattern_detection_orchestrator.py**
   - ✅ `detect_patterns()` 완전 재작성 (77-223줄)
   - ✅ 헬퍼 메서드 추가 (495-859줄)

**총 변경**: 3개 파일, 약 700줄 추가/수정

---

## 다음 단계

### 실제 데이터 테스트

```bash
# 1. 의존성 설치
pip install aiohttp

# 2. 데이터 수집
venv/Scripts/python.exe scripts/data_collection/collect_single_ticker.py \
    --ticker 025980 --from-date 2015-01-01

# 3. 패턴 탐지 (26개 패턴 예상)
venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/test1_alt.yaml \
    --from-date 2015-01-01

# 4. 결과 확인
sqlite3 data/database/stock_data.db \
    "SELECT COUNT(*) as '패턴 개수' FROM seed_pattern WHERE ticker='025980';"
```

### 추가 개선사항

1. **RedetectionDetector 리팩토링**
   - 현재: 기존 방식 사용 (단일 패턴)
   - 개선: Option D 방식 적용 (멀티패턴)

2. **성능 최적화**
   - 지표 계산 캐싱 (MA, volume_ma 등)
   - 패턴 컨텍스트 풀링

3. **테스트 보강**
   - 통합 테스트 추가
   - 엣지 케이스 검증

---

## 결론

### 문제 해결
✅ **근본 원인**: `Dict[str, Block]` 구조 → `List[PatternContext]` 구조로 변경
✅ **데이터 손실**: 96.2% 손실 → 0% 손실 (예상)
✅ **패턴 간섭**: 완전 제거 (독립 컨텍스트)

### 설계 품질
✅ **Clean Architecture**: 책임 분리 (SRP) 준수
✅ **확장성**: 무제한 동시 패턴 지원
✅ **효율성**: 데이터 1회 순회
✅ **유지보수성**: 명확한 구조, 테스트 가능

### 검증 완료
✅ **Mock 데이터**: 3개 패턴 탐지 성공
✅ **코드 품질**: 모든 모듈 import 성공
✅ **API 설계**: Stateless 평가기 + 패턴 관리자

**Option D 리팩토링 성공적으로 완료!** 🎉
