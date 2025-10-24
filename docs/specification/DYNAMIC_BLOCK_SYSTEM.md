# Dynamic Block System Specification

**Status**: ✅ Implemented (Phase 5-6 Complete)
**Version**: 1.0
**Last Updated**: 2024-10-24

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Components](#core-components)
- [YAML Configuration](#yaml-configuration)
- [Usage Guide](#usage-guide)
- [Examples](#examples)
- [Testing](#testing)
- [Migration from Static System](#migration-from-static-system)

---

## Overview

The **Dynamic Block System** is a YAML-driven, expression-based pattern detection framework that replaces the previous static block detection system. It enables unlimited block types (Block1, Block2, ..., BlockN) to be defined purely through configuration without any code changes.

### Key Benefits

✅ **No Code Changes**: Add new block types via YAML only
✅ **Unlimited Blocks**: Support Block1 through BlockN
✅ **Flexible Relationships**: Sequential, conditional, optional, multi-parent edges
✅ **Expression-Based**: Safe AST-based condition evaluation
✅ **Clean Architecture**: Domain-driven design with clear layer separation
✅ **Fully Tested**: 93 comprehensive tests covering all scenarios

### Comparison: Static vs Dynamic

| Aspect | Static System | Dynamic System |
|--------|---------------|----------------|
| Block Types | Hardcoded (Block1-4) | Unlimited (YAML-defined) |
| Adding Blocks | 6+ file changes | 1 YAML edit |
| Conditions | Python code | YAML expressions |
| Relationships | Fixed sequence | DAG with edges |
| Extensibility | Low | High |
| Testability | Moderate | High |

---

## Architecture

The system follows **Clean Architecture** principles with strict layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│              (CLI, Scripts, API - Future)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ Use Cases        │  │ Services                       │  │
│  │ - DynamicBlock   │  │ - BlockGraphLoader             │  │
│  │   Detector       │  │ - ExpressionEngine             │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Domain Layer                             │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ Entities         │  │ Repository Interfaces          │  │
│  │ - BlockGraph     │  │ - DynamicBlockRepository       │  │
│  │ - BlockNode      │  │                                │  │
│  │ - DynamicBlock   │  │                                │  │
│  │   Detection      │  │                                │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                Infrastructure Layer                          │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ Repository       │  │ Database                       │  │
│  │ Implementation   │  │ - SQLAlchemy Models            │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
YAML File
   ↓
BlockGraphLoader (parse YAML)
   ↓
BlockGraph (in-memory DAG)
   ↓
DynamicBlockDetector (detect patterns)
   ↓
DynamicBlockDetection entities
   ↓
DynamicBlockRepository (persist)
   ↓
Database
```

---

## Core Components

### 1. BlockGraph

**Purpose**: Represents the block pattern structure as a Directed Acyclic Graph (DAG).

**File**: `src/domain/entities/block_graph/block_graph.py`

**Key Features**:
- Stores nodes (BlockNode) and edges (BlockEdge)
- Validates graph structure (no cycles, valid edges)
- Provides graph traversal methods
- Supports topological sorting

**Example**:
```python
graph = BlockGraph()
graph.add_node(BlockNode('block1', 1, 'Initial Surge', ...))
graph.add_node(BlockNode('block2', 2, 'Continuation', ...))
graph.add_edge(BlockEdge('block1', 'block2'))

# Validation
errors = graph.validate()
if errors:
    print("Graph errors:", errors)

# Topological sort
order = graph.topological_sort()  # ['block1', 'block2']
```

### 2. BlockNode

**Purpose**: Defines a single block's properties and conditions.

**File**: `src/domain/entities/block_graph/block_node.py`

**Attributes**:
- `block_id` (str): Unique identifier (e.g., "block1")
- `block_type` (int): Type number (1, 2, 3, ...)
- `name` (str): Human-readable name
- `description` (str): Optional description
- `entry_conditions` (List[str]): AND logic - all must be true
- `exit_conditions` (List[str]): OR logic - any triggers completion
- `parameters` (dict): Custom parameters
- `metadata` (dict): Custom metadata

**Example**:
```python
node = BlockNode(
    block_id='block1',
    block_type=1,
    name='Initial Surge',
    entry_conditions=[
        'current.close >= 10000',
        'current.volume >= 1000000'
    ],
    exit_conditions=[
        'current.close < 9000'
    ],
    parameters={'min_duration': 1},
    metadata={'color': '#FF6B6B'}
)
```

### 3. BlockEdge

**Purpose**: Defines relationships between blocks.

**File**: `src/domain/entities/block_graph/block_edge.py`

**Edge Types**:
- `SEQUENTIAL`: Standard Block1 → Block2 transition
- `CONDITIONAL`: Transition only if condition is met
- `OPTIONAL`: Optional transition (can be skipped)

**Attributes**:
- `from_block_id` (str): Source block
- `to_block_id` (str): Destination block
- `edge_type` (EdgeType): Edge type (default: SEQUENTIAL)
- `condition` (str): Expression for CONDITIONAL edges
- `priority` (int): Order when multiple edges exist

**Example**:
```python
# Sequential edge
edge1 = BlockEdge('block1', 'block2')

# Conditional edge
edge2 = BlockEdge(
    'block1', 'block2a',
    edge_type=EdgeType.CONDITIONAL,
    condition='current.volume >= 1000000',
    priority=1
)
```

### 4. ExpressionEngine

**Purpose**: Safely evaluates condition expressions using AST parsing.

**File**: `src/domain/entities/conditions/expression_engine.py`

**Supported Operations**:
- **Comparisons**: `>=`, `>`, `<=`, `<`, `==`, `!=`
- **Boolean Logic**: `and`, `or`, `not`
- **Arithmetic**: `+`, `-`, `*`, `/`, `%`, `**`
- **Functions**: Via FunctionRegistry (ma, sum, avg, etc.)
- **Attributes**: `current.close`, `prev.volume`, `block1.peak_price`

**Example**:
```python
engine = ExpressionEngine(function_registry)

context = {
    'current': Stock(...),
    'prev': Stock(...),
    'block1': DynamicBlockDetection(...)
}

result = engine.evaluate(
    'current.close >= ma(all_stocks, 120) and current.volume > prev.volume * 3',
    context
)
```

### 5. FunctionRegistry

**Purpose**: Extensible registry of functions available in expressions.

**File**: `src/domain/entities/conditions/function_registry.py`

**Built-in Functions** (12 total):
- `ma(stocks, period)`: Moving average
- `sum(stocks, key)`: Sum of attribute
- `avg(stocks, key)`: Average of attribute
- `max(stocks, key)`: Maximum value
- `min(stocks, key)`: Minimum value
- `count(stocks)`: Count elements
- `exists(var)`: Check if variable exists
- `in_range(val, min, max)`: Range check
- `any_of(*conditions)`: OR logic
- `all_of(*conditions)`: AND logic
- `within_days(date1, date2, days)`: Date difference check
- `percent_change(old, new)`: Percentage change

**Custom Functions**: Use `@function_registry.register()` decorator

**Example**:
```python
@function_registry.register('custom_indicator')
def custom_indicator(stocks: List[Stock], param: int) -> float:
    # Custom logic
    return result

# Use in YAML:
# expression: "custom_indicator(all_stocks, 20) > 0.5"
```

### 6. DynamicBlockDetector

**Purpose**: Core use case that detects blocks from stock data.

**File**: `src/application/use_cases/dynamic_block_detector.py`

**Algorithm**:
1. Iterate through stock data sequentially
2. Build evaluation context (current, prev, all_stocks, active blocks)
3. Update active blocks:
   - Update peak price/volume
   - Check exit conditions (OR logic)
   - Complete blocks if exit condition met
4. Detect new blocks:
   - Check entry conditions (AND logic)
   - Create new DynamicBlockDetection
   - Link parent blocks via graph edges
5. Return all detections (active + completed)

**Example**:
```python
detector = DynamicBlockDetector(block_graph, expression_engine)

detections = detector.detect_blocks(
    ticker='025980',
    stocks=stock_list,
    condition_name='seed',
    active_blocks=[]  # or existing active blocks
)

for detection in detections:
    print(f"{detection.block_id}: {detection.started_at} → {detection.ended_at}")
```

### 7. DynamicBlockDetection

**Purpose**: Entity representing a detected block instance.

**File**: `src/domain/entities/detections/dynamic_block_detection.py`

**Attributes**:
- `id`: Database ID (None if not persisted)
- `block_id`: Block identifier from graph (e.g., "block1")
- `block_type`: Block type number (1, 2, 3, ...)
- `ticker`: Stock ticker code
- `pattern_id`: Optional pattern ID (for grouping)
- `condition_name`: "seed" or "redetection"
- `started_at`: Start date
- `ended_at`: End date (None if active)
- `status`: ACTIVE, COMPLETED, or FAILED
- `peak_price`: Highest price during block
- `peak_volume`: Highest volume during block
- `peak_date`: Date of peak price
- `parent_blocks`: List of parent block IDs
- `metadata`: Custom metadata

**Lifecycle Methods**:
```python
# Create
block = DynamicBlockDetection(block_id='block1', block_type=1, ...)

# Start
block.start(date(2024, 1, 15))

# Update peak
block.update_peak(date(2024, 1, 16), price=12000, volume=1500000)

# Complete
block.complete(date(2024, 1, 20))

# Check status
if block.is_active():
    print("Block is active")
```

### 8. BlockGraphLoader

**Purpose**: Loads/saves BlockGraph from/to YAML files.

**File**: `src/application/services/block_graph_loader.py`

**Methods**:
- `load_from_file(path)`: Load graph from YAML file
- `load_from_dict(data)`: Load graph from dictionary
- `save_to_file(graph, path)`: Save graph to YAML file
- `save_to_dict(graph)`: Convert graph to dictionary

**Example**:
```python
loader = BlockGraphLoader()

# Load from YAML
graph = loader.load_from_file('presets/examples/simple_pattern_example.yaml')

# Save to YAML
loader.save_to_file(graph, 'output/my_pattern.yaml')
```

### 9. DynamicBlockRepository

**Purpose**: Persistence interface for DynamicBlockDetection entities.

**File**: `src/domain/repositories/dynamic_block_repository.py` (interface)
**Implementation**: `src/infrastructure/repositories/dynamic_block_repository_impl.py`

**Methods**:
- `save(detection)`: Create or update single detection
- `save_all(detections)`: Batch save
- `find_by_id(id)`: Find by primary key
- `find_by_ticker(ticker, condition_name)`: Find all for ticker
- `find_active_blocks(ticker)`: Find active blocks for ticker
- `find_by_pattern_id(pattern_id)`: Find all for pattern
- `find_by_date_range(ticker, start, end)`: Find in date range
- `delete_by_id(id)`: Delete single detection
- `delete_by_ticker(ticker)`: Delete all for ticker

**Example**:
```python
repo = DynamicBlockRepositoryImpl(session)

# Save
saved = repo.save(detection)

# Query active blocks
active = repo.find_active_blocks('025980')

# Query by date range
blocks = repo.find_by_date_range('025980', date(2024, 1, 1), date(2024, 12, 31))
```

---

## YAML Configuration

### Schema Structure

```yaml
block_graph:
  root_node: "block1"  # Starting block ID

  nodes:
    block_id:
      block_id: "block1"           # Must match key
      block_type: 1                # Integer type
      name: "Block Name"           # Human-readable name
      description: "..."           # Optional description

      entry_conditions:            # AND logic - all must be true
        - name: "condition_name"   # Optional name
          expression: "..."        # Expression string
          description: "..."       # Optional description
        - "simple expression"      # Can be just a string

      exit_conditions:             # OR logic - any triggers completion
        - "expression 1"
        - "expression 2"

      parameters:                  # Custom parameters
        min_duration: 1
        max_duration: 100

      metadata:                    # Custom metadata
        color: "#FF6B6B"
        priority: 1

  edges:
    - from_block: "block1"
      to_block: "block2"
      edge_type: "sequential"      # sequential, conditional, optional
      condition: "..."             # For conditional edges
      priority: 1                  # Order when multiple edges
      description: "..."           # Optional description
```

### Condition Expression Syntax

**Variables**:
- `current`: Current stock candle
- `prev`: Previous stock candle
- `all_stocks`: List of all stocks up to current
- `block1`, `block2`, ...: Active block detections

**Attributes**:
- Stock: `open`, `high`, `low`, `close`, `volume`, `date`
- Block: `started_at`, `ended_at`, `peak_price`, `peak_volume`, `status`

**Operators**:
- Comparison: `>=`, `>`, `<=`, `<`, `==`, `!=`
- Boolean: `and`, `or`, `not`
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`

**Functions**: See FunctionRegistry section

**Examples**:
```yaml
# Simple price check
"current.close >= 10000"

# Multiple conditions
"current.close >= 10000 and current.volume >= 1000000"

# Moving average
"current.close >= ma(all_stocks, 120)"

# Relative to previous
"current.volume > prev.volume * 3"

# Block dependency
"exists('block1') and current.close > block1.peak_price * 1.1"

# Complex expression
"(current.high - current.low) / current.low * 100 >= 5.0 and current.volume >= avg(all_stocks[-20:], 'volume') * 2"
```

---

## Usage Guide

### 1. Define Pattern in YAML

Create a YAML file in `presets/examples/` or `presets/patterns/`:

```yaml
# my_pattern.yaml
block_graph:
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Surge"
      entry_conditions:
        - "current.close >= 10000"
        - "current.volume >= 1000000"
      exit_conditions:
        - "current.close < 9000"

    block2:
      block_id: "block2"
      block_type: 2
      name: "Continuation"
      entry_conditions:
        - "current.close >= 11000"
      exit_conditions:
        - "current.volume < 500000"

  edges:
    - from_block: "block1"
      to_block: "block2"
```

### 2. Load and Detect

```python
from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.conditions import ExpressionEngine, function_registry
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl

# Load graph
loader = BlockGraphLoader()
graph = loader.load_from_file('presets/examples/my_pattern.yaml')

# Create detector
engine = ExpressionEngine(function_registry)
detector = DynamicBlockDetector(graph, engine)

# Detect blocks
detections = detector.detect_blocks(
    ticker='025980',
    stocks=stock_data,
    condition_name='seed'
)

# Save to database
repo = DynamicBlockRepositoryImpl(session)
saved = repo.save_all(detections)
```

### 3. Incremental Detection

```python
# First batch
detections_batch1 = detector.detect_blocks('025980', first_batch_stocks)
repo.save_all(detections_batch1)

# Second batch - continue tracking active blocks
active_blocks = repo.find_active_blocks('025980')
detections_batch2 = detector.detect_blocks(
    '025980',
    second_batch_stocks,
    active_blocks=active_blocks
)
repo.save_all(detections_batch2)
```

### 4. Custom Functions

```python
from src.domain.entities.conditions.function_registry import function_registry

@function_registry.register('rsi')
def rsi(stocks: List[Stock], period: int) -> float:
    # Calculate RSI
    return rsi_value

# Use in YAML:
# "rsi(all_stocks, 14) > 70"
```

---

## Examples

### Example 1: Simple 3-Block Pattern

**File**: `presets/examples/simple_pattern_example.yaml`

**Pattern**: Block1 (Initial Surge) → Block2 (Continuation) → Block3 (Further Advancement)

**Use Case**: Basic sequential pattern detection

### Example 2: Extended 6-Block Pattern

**File**: `presets/examples/extended_pattern_example.yaml`

**Pattern**: Block1 → Block2 → Block3 → Block4 → Block5 → Block6

**Use Case**: Validates unlimited block support

### Example 3: Branching Pattern

```yaml
# Conditional branching based on volume
block_graph:
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Initial Surge"
      entry_conditions:
        - "current.close >= 10000"

    block2_high_volume:
      block_id: "block2_high_volume"
      block_type: 2
      name: "High Volume Continuation"
      entry_conditions:
        - "current.close >= 11000"

    block2_low_volume:
      block_id: "block2_low_volume"
      block_type: 2
      name: "Low Volume Continuation"
      entry_conditions:
        - "current.close >= 11000"

  edges:
    - from_block: "block1"
      to_block: "block2_high_volume"
      edge_type: "conditional"
      condition: "current.volume >= 1000000"
      priority: 1

    - from_block: "block1"
      to_block: "block2_low_volume"
      edge_type: "conditional"
      condition: "current.volume < 1000000"
      priority: 2
```

### Example 4: Multi-Parent Pattern

```yaml
# Block3 requires both Block1 and Block2
block_graph:
  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Price Surge"
      entry_conditions:
        - "current.close >= 10000"

    block2:
      block_id: "block2"
      block_type: 2
      name: "Volume Spike"
      entry_conditions:
        - "current.volume >= 1000000"

    block3:
      block_id: "block3"
      block_type: 3
      name: "Combined Signal"
      entry_conditions:
        - "exists('block1')"
        - "exists('block2')"
        - "current.close >= 12000"

  edges:
    - from_block: "block1"
      to_block: "block3"
    - from_block: "block2"
      to_block: "block3"
```

---

## Testing

### Test Coverage

**Total Tests**: 93 (Phase 5: 83, Phase 6: 10)

**Test Categories**:
1. **Unit Tests - BlockGraph** (36 tests)
   - `tests/unit/entities/block_graph/test_block_node.py` (9 tests)
   - `tests/unit/entities/block_graph/test_block_edge.py` (10 tests)
   - `tests/unit/entities/block_graph/test_block_graph.py` (17 tests)

2. **Unit Tests - BlockGraphLoader** (13 tests)
   - `tests/unit/services/test_block_graph_loader.py`

3. **Unit Tests - DynamicBlockDetector** (11 tests)
   - `tests/unit/use_cases/test_dynamic_block_detector.py`

4. **Integration Tests - Repository** (18 tests)
   - `tests/integration/repositories/test_dynamic_block_repository.py`

5. **Integration Tests - E2E** (7 tests)
   - `tests/integration/test_dynamic_block_system_e2e.py`

6. **Integration Tests - Extended Blocks** (10 tests)
   - `tests/integration/test_extended_blocks.py`

### Running Tests

```bash
# All dynamic system tests
.venv/Scripts/python.exe -m pytest tests/unit/entities/block_graph/ tests/unit/services/test_block_graph_loader.py tests/unit/use_cases/test_dynamic_block_detector.py tests/integration/repositories/test_dynamic_block_repository.py tests/integration/test_dynamic_block_system_e2e.py tests/integration/test_extended_blocks.py -v

# Specific category
.venv/Scripts/python.exe -m pytest tests/integration/test_extended_blocks.py -v

# With coverage
.venv/Scripts/python.exe -m pytest tests/integration/ --cov=src/application --cov=src/domain
```

---

## Migration from Static System

### What Changed

**Removed** (backed up to `backup/old_system/`):
- `Block1Checker`, `Block2Checker`, `Block3Checker`, `Block4Checker`
- `Block1Detector`, `Block2Detector`, `Block3Detector`, `Block4Detector`
- `Block1Detection`, `Block2Detection`, `Block3Detection`, `Block4Detection` (static entities)
- `Block1Repository`, `Block2Repository`, etc.
- `SeedConditionPreset`, `RedetectionConditionPreset` (static presets)

**Added**:
- `BlockGraph`, `BlockNode`, `BlockEdge` (domain entities)
- `DynamicBlockDetection` (unified entity)
- `DynamicBlockDetector` (unified use case)
- `DynamicBlockRepository` (unified repository)
- `BlockGraphLoader` (YAML loader)
- `ExpressionEngine`, `FunctionRegistry` (condition evaluation)

### Migration Path

**For Users**:
1. Define your pattern in YAML (see examples)
2. Use `DynamicBlockDetector` instead of old detectors
3. Use `DynamicBlockRepository` for persistence
4. Old detection data remains in `block1_detection`, `block2_detection`, etc. tables

**For Developers**:
1. All new block types use YAML configuration
2. No more hardcoded block logic
3. Add custom functions via `FunctionRegistry`
4. Extend `BlockGraph` for advanced graph operations

---

## Future Enhancements

### Planned Features

1. **Performance Optimization**
   - Parallel block detection for multiple tickers
   - Incremental graph updates
   - Caching of expression evaluation

2. **Advanced Expressions**
   - User-defined variables
   - Lambda expressions
   - Time-series operators (lag, lead, diff)

3. **Pattern Templates**
   - Reusable sub-patterns
   - Pattern inheritance
   - Pattern composition

4. **Visualization**
   - Graph visualization tool
   - Detection timeline viewer
   - Condition debugger

5. **Monitoring**
   - Pattern performance metrics
   - Detection statistics dashboard
   - Alert system for pattern matches

### Extensibility Points

- **Custom Functions**: Add via `@function_registry.register()`
- **Custom Edge Types**: Extend `EdgeType` enum
- **Custom Validators**: Implement `BlockGraph.validate()` extensions
- **Custom Metadata**: Use `metadata` dict in nodes/edges

---

## Troubleshooting

### Common Issues

**Issue**: "Cycle detected in graph"
**Solution**: Check edges for circular dependencies. Use `graph.topological_sort()` to identify cycles.

**Issue**: "Expression evaluation error"
**Solution**: Check expression syntax. Use `expression_engine.evaluate()` with test context to debug.

**Issue**: "Block not detected"
**Solution**:
- Verify entry conditions are correct
- Check context variables (current, prev, all_stocks)
- Add debug logging to `DynamicBlockDetector`

**Issue**: "Peak values incorrect"
**Solution**: Ensure blocks are completing properly (check exit conditions)

---

## References

- **Source Code**: `src/domain/entities/block_graph/`, `src/application/use_cases/dynamic_block_detector.py`
- **Examples**: `presets/examples/simple_pattern_example.yaml`, `extended_pattern_example.yaml`
- **Tests**: `tests/integration/test_dynamic_block_system_e2e.py`
- **Related Docs**: `BLOCK_DETECTION.md` (static system, deprecated)

---

## Appendix

### Complete Function Reference

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `ma(stocks, period)` | stocks: List[Stock], period: int | float | Moving average |
| `sum(stocks, key)` | stocks: List[Stock], key: str | float | Sum of attribute |
| `avg(stocks, key)` | stocks: List[Stock], key: str | float | Average of attribute |
| `max(stocks, key)` | stocks: List[Stock], key: str | float | Maximum value |
| `min(stocks, key)` | stocks: List[Stock], key: str | float | Minimum value |
| `count(stocks)` | stocks: List[Stock] | int | Count elements |
| `exists(var)` | var: str | bool | Check if variable exists |
| `in_range(val, min, max)` | val: float, min: float, max: float | bool | Range check |
| `any_of(*conditions)` | *conditions: bool | bool | OR logic |
| `all_of(*conditions)` | *conditions: bool | bool | AND logic |
| `within_days(date1, date2, days)` | date1: date, date2: date, days: int | bool | Date difference |
| `percent_change(old, new)` | old: float, new: float | float | Percentage change |

### Database Schema

**Table**: `dynamic_block_detection`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| block_id | VARCHAR(50) | Block identifier |
| block_type | INTEGER | Block type number |
| ticker | VARCHAR(20) | Stock ticker |
| pattern_id | INTEGER | Pattern ID (nullable) |
| condition_name | VARCHAR(50) | "seed" or "redetection" |
| started_at | DATE | Start date |
| ended_at | DATE | End date (nullable) |
| status | VARCHAR(20) | ACTIVE, COMPLETED, FAILED |
| peak_price | FLOAT | Highest price |
| peak_volume | INTEGER | Highest volume |
| peak_date | DATE | Date of peak price |
| parent_blocks | JSON | List of parent block IDs |
| custom_metadata | JSON | Custom metadata |

**Indexes**:
- `idx_block_id` on (block_id)
- `idx_ticker` on (ticker)
- `idx_pattern_id` on (pattern_id)
- `idx_condition_name` on (condition_name)
- `idx_status` on (status)
- `idx_started_at` on (started_at)

---

**Document Version**: 1.0
**Last Updated**: 2024-10-24
**Maintained By**: POTALE_STOCK Team
