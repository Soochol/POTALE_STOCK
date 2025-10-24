# YAML Schemas for Dynamic Condition System

이 디렉토리는 동적 조건 시스템의 YAML 스키마 파일들을 포함합니다.

## 📁 Schema Files

### 1. `data_schema.yaml`
**목적**: 표현식에서 사용 가능한 데이터 필드 정의

**내용**:
- Context 변수 (`current`, `prev`, `block1`, `all_stocks`, ...)
- Stock 객체 필드 (`ticker`, `date`, `open`, `high`, `low`, `close`, `volume`, `indicators`)
- Block Detection 객체 필드 (`started_at`, `ended_at`, `peak_price`, `peak_volume`, `status`)
- 자주 사용되는 표현식 패턴
- 표현식 작성 규칙 및 예시

**사용 방법**:
- 조건 표현식을 작성할 때 참고 문서로 활용
- 사용 가능한 필드와 변수 확인
- 표현식 작성 규칙 준수

### 2. `function_library.yaml`
**목적**: 표현식에서 사용 가능한 함수 라이브러리 문서

**내용**:
- Moving Average 함수: `ma()`, `volume_ma()`
- Time 함수: `candles_between()`, `days_since()`
- Price 함수: `within_range()`, `is_new_high()`
- Volume 함수: `is_volume_high()`
- Technical 함수: `rsi()`, `bollinger_upper()`, `bollinger_lower()`
- Block 함수: `EXISTS()`
- 함수 추가 가이드

**사용 방법**:
- 조건 표현식에서 사용할 함수 검색
- 각 함수의 파라미터와 반환값 확인
- 새로운 함수 추가 시 참고

### 3. `block_definitions_template.yaml`
**목적**: 블록 정의 YAML 템플릿

**내용**:
- BlockGraph 정의 구조
- BlockNode 정의 예시 (Block1, Block2, Block3)
- BlockEdge 정의 예시 (순차, 조건부, 분기)
- 고급 예제 (분기 및 병합)
- 검증 스키마
- 사용 가이드

**사용 방법**:
1. 템플릿을 복사하여 새 파일 생성
2. 블록 노드 정의 (조건, 파라미터)
3. 엣지 정의 (블록 간 관계)
4. YAML 검증 후 감지 실행

## 🚀 Quick Start

### 1. 데이터 필드 확인
```bash
# data_schema.yaml을 열어서 사용 가능한 필드 확인
cat presets/schemas/data_schema.yaml
```

### 2. 함수 라이브러리 확인
```bash
# function_library.yaml에서 사용 가능한 함수 확인
cat presets/schemas/function_library.yaml
```

### 3. 블록 정의 생성
```bash
# 템플릿 복사
cp presets/schemas/block_definitions_template.yaml presets/my_strategy.yaml

# 템플릿 편집
# ... (블록 조건 및 관계 정의)

# 검증 (TODO: 검증 스크립트 구현 후)
# python scripts/validate_block_definitions.py presets/my_strategy.yaml
```

### 4. 감지 실행 (TODO: 구현 후)
```bash
# python scripts/detect_patterns.py --config presets/my_strategy.yaml --ticker 025980
```

## 📖 Expression Writing Guide

### 기본 규칙

1. **논리 연산자는 소문자 사용**
   ```yaml
   # ✅ 올바름
   expression: "current.close >= 10000 and current.volume >= 1000000"

   # ❌ 잘못됨
   expression: "current.close >= 10000 AND current.volume >= 1000000"
   ```

2. **괄호로 우선순위 명확화**
   ```yaml
   # ✅ 올바름
   expression: "(current.close >= 10000) and (current.volume >= prev.volume * 2)"

   # ⚠️ 가능하지만 덜 명확함
   expression: "current.close >= 10000 and current.volume >= prev.volume * 2"
   ```

3. **복잡한 표현식은 여러 줄로 분리**
   ```yaml
   # ✅ 올바름 (multiline string)
   expression: |
     (current.close >= 10000) and
     (current.high >= ma(120)) and
     (current.volume >= volume_ma(20) * 3)
   ```

4. **함수 호출 시 파라미터 타입 확인**
   ```yaml
   # ✅ 올바름
   expression: "ma(120)"  # period는 int

   # ❌ 잘못됨
   expression: "ma('120')"  # 문자열은 불가
   ```

### 자주 사용되는 패턴

#### 1. MA 돌파
```yaml
expression: "(current.high >= ma(120)) and (current.close >= ma(120))"
```

#### 2. 거래량 급등
```yaml
expression: "current.volume >= volume_ma(20) * 3"
```

#### 3. Block 존재 확인
```yaml
expression: "EXISTS('block1')"
```

#### 4. Block 시간 윈도우
```yaml
expression: |
  candles_between(block1.started_at, current.date) >= 2 and
  candles_between(block1.started_at, current.date) <= 150
```

#### 5. Block 가격 범위
```yaml
expression: "within_range(current.close, block1.peak_price, 10.0)"
```

## 🔧 Adding New Functions

### Step 1: Implement Function
```python
# src/domain/entities/conditions/builtin_functions.py

@function_registry.register(
    'my_custom_indicator',
    category='custom',
    description='내 커스텀 지표',
    params_schema={'threshold': float}
)
def my_custom_indicator(threshold: float, context: dict) -> bool:
    current = context['current']
    # 로직 구현
    return current.close > threshold
```

### Step 2: Document Function
```yaml
# presets/schemas/function_library.yaml

custom:
  my_custom_indicator:
    description: "내 커스텀 지표"
    parameters:
      - name: threshold
        type: float
        description: "임계값"
        required: true
    returns:
      type: bool
      description: "조건 만족 여부"
    usage: "my_custom_indicator(15000)"
```

### Step 3: Write Tests
```python
# tests/unit/entities/conditions/test_custom_functions.py

def test_my_custom_indicator():
    engine = ExpressionEngine(function_registry)
    context = {'current': MockStock(...)}
    result = engine.evaluate("my_custom_indicator(15000)", context)
    assert isinstance(result, bool)
```

## 📊 Block Definition Examples

### Simple Sequential Pattern
```yaml
# Block1 → Block2 → Block3 (순차 패턴)
block_graph:
  root_node: "block1"
  nodes:
    block1: { ... }
    block2: { ... }
    block3: { ... }
  edges:
    - from_block: "block1"
      to_block: "block2"
      edge_type: "sequential"
    - from_block: "block2"
      to_block: "block3"
      edge_type: "sequential"
```

### Branching Pattern
```yaml
# Block1 → [Block2A, Block2B] (분기)
edges:
  - from_block: "block1"
    to_block: "block2a"
    edge_type: "conditional"
    condition: "current.volume >= volume_ma(20) * 2"
    priority: 1

  - from_block: "block1"
    to_block: "block2b"
    edge_type: "conditional"
    condition: "current.volume < volume_ma(20) * 2"
    priority: 2
```

### Skip Pattern
```yaml
# Block1 → Block2 or Block1 → Block3 (스킵 가능)
edges:
  - from_block: "block1"
    to_block: "block2"
    edge_type: "sequential"
    priority: 1

  - from_block: "block1"
    to_block: "block3"
    edge_type: "optional"
    priority: 2
```

### Merge Pattern
```yaml
# [Block2A, Block2B] → Block3 (병합)
edges:
  - from_block: "block2a"
    to_block: "block3"
    edge_type: "sequential"

  - from_block: "block2b"
    to_block: "block3"
    edge_type: "sequential"
```

## 🛡️ Validation

### Manual Validation
```python
# Python에서 수동 검증
from src.domain.entities import BlockGraph, BlockNode, BlockEdge

graph = BlockGraph()
node1 = BlockNode("block1", 1, "Test", entry_conditions=["true"])
graph.add_node(node1)

errors = graph.validate()
if errors:
    print("Validation errors:", errors)
```

### Automated Validation (TODO)
```bash
# YAML 파일 자동 검증 (구현 예정)
# python scripts/validate_block_definitions.py my_strategy.yaml
```

## 📚 References

- [Expression Engine Implementation](../../src/domain/entities/conditions/expression_engine.py)
- [Function Registry](../../src/domain/entities/conditions/function_registry.py)
- [Builtin Functions](../../src/domain/entities/conditions/builtin_functions.py)
- [Block Graph](../../src/domain/entities/block_graph/)

## 🤝 Contributing

새로운 함수나 패턴을 추가할 때:
1. 함수 구현 (builtin_functions.py)
2. 문서화 (function_library.yaml)
3. 테스트 작성
4. 예제 추가 (이 README 또는 block_definitions_template.yaml)

## ⚠️ Common Pitfalls

1. ❌ **대문자 논리 연산자 사용**
   ```yaml
   # Wrong: "AND", "OR", "NOT"
   # Right: "and", "or", "not"
   ```

2. ❌ **인자 없는 함수 호출**
   ```yaml
   # Wrong: "ma()"
   # Right: "ma(120)"
   ```

3. ❌ **존재하지 않는 필드 참조**
   ```yaml
   # Wrong: "current.price" (Stock에 price 필드 없음)
   # Right: "current.close"
   ```

4. ❌ **순환 엣지 정의**
   ```yaml
   # Wrong: block1 → block2 → block1 (cycle!)
   # Right: block1 → block2 → block3 (DAG)
   ```

5. ❌ **잘못된 타입 전달**
   ```yaml
   # Wrong: candles_between("2024-01-01", "2024-01-31")  # 문자열
   # Right: candles_between(block1.started_at, current.date)  # date 객체
   ```
