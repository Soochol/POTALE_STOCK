# Dynamic Block System - Quick Start Guide

**Goal**: Get started with the Dynamic Block System in 15 minutes.

---

## Prerequisites

- Python 3.10+ environment set up
- Virtual environment activated (`.venv`)
- Database initialized

---

## Step 1: Understand the Basics (3 min)

### What is a Block?

A **block** represents a phase in a stock price pattern. For example:
- **Block1**: Initial surge (price breaks above threshold with high volume)
- **Block2**: Continuation (price continues rising)
- **Block3**: Peak formation (price reaches maximum)

### What is the Dynamic System?

The **Dynamic Block System** lets you define unlimited block types and their relationships **purely in YAML**, without changing any code.

**Example**: Want to add Block5 and Block6? Just edit a YAML file!

---

## Step 2: Your First Pattern (5 min)

Create a simple pattern: **"Price surge above 10,000 won with high volume"**

### Create YAML File

Create `presets/patterns/my_first_pattern.yaml`:

```yaml
block_graph:
  root_node: "surge"

  nodes:
    surge:
      block_id: "surge"
      block_type: 1
      name: "Price Surge"
      description: "Initial price surge with high volume"

      entry_conditions:
        - "current.close >= 10000"
        - "current.volume >= 1000000"

      exit_conditions:
        - "current.close < 9000"
```

**Explanation**:
- **Entry conditions** (AND logic): Both `close >= 10000` AND `volume >= 1M` must be true
- **Exit conditions** (OR logic): If `close < 9000`, block completes

---

## Step 3: Run Detection (5 min)

### Python Script

```python
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.conditions import ExpressionEngine, function_registry
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl

# 1. Load pattern
loader = BlockGraphLoader()
graph = loader.load_from_file('presets/patterns/my_first_pattern.yaml')

# 2. Create detector
engine = ExpressionEngine(function_registry)
detector = DynamicBlockDetector(graph, engine)

# 3. Get stock data
db_engine = create_engine('sqlite:///data/database/stock_data.db')
Session = sessionmaker(bind=db_engine)
session = Session()

stock_repo = SqliteStockRepository(session)
stocks = stock_repo.find_by_ticker_and_date_range(
    '025980',
    date(2024, 1, 1),
    date(2024, 12, 31)
)

# 4. Detect blocks
detections = detector.detect_blocks(
    ticker='025980',
    stocks=stocks,
    condition_name='seed'
)

# 5. Print results
print(f"Found {len(detections)} blocks:")
for d in detections:
    print(f"  {d.block_id}: {d.started_at} → {d.ended_at}, peak={d.peak_price}")

# 6. Save to database
block_repo = DynamicBlockRepositoryImpl(session)
saved = block_repo.save_all(detections)
session.commit()

print(f"Saved {len(saved)} blocks to database")
```

### Run

```bash
.venv/Scripts/python.exe my_detection_script.py
```

**Output**:
```
Found 3 blocks:
  surge: 2024-01-15 → 2024-02-10, peak=12500
  surge: 2024-03-20 → 2024-04-05, peak=11800
  surge: 2024-07-10 → None, peak=10500
Saved 3 blocks to database
```

---

## Step 4: Add More Blocks (2 min)

Let's extend the pattern: **Surge → Continuation → Peak**

Edit `my_first_pattern.yaml`:

```yaml
block_graph:
  root_node: "surge"

  nodes:
    surge:
      block_id: "surge"
      block_type: 1
      name: "Initial Surge"
      entry_conditions:
        - "current.close >= 10000"
        - "current.volume >= 1000000"
      exit_conditions:
        - "current.close < 9000"

    continuation:  # NEW BLOCK!
      block_id: "continuation"
      block_type: 2
      name: "Continuation"
      entry_conditions:
        - "current.close >= 11000"
      exit_conditions:
        - "current.volume < 500000"

    peak:  # NEW BLOCK!
      block_id: "peak"
      block_type: 3
      name: "Peak Formation"
      entry_conditions:
        - "current.close >= 12000"
      exit_conditions:
        - "current.close < 11000"

  edges:
    - from_block: "surge"
      to_block: "continuation"

    - from_block: "continuation"
      to_block: "peak"
```

**Run the same script again** - no code changes needed!

**Output**:
```
Found 9 blocks:
  surge: 2024-01-15 → 2024-01-20, peak=10800
  continuation: 2024-01-20 → 2024-02-05, peak=11500
  peak: 2024-02-05 → 2024-02-10, peak=12500
  ...
```

---

## Common Expressions

### Price Conditions

```yaml
# Simple threshold
"current.close >= 10000"

# Relative to previous
"current.close > prev.close * 1.05"

# Moving average
"current.close >= ma(all_stocks, 120)"

# Price range
"in_range(current.close, 9000, 11000)"
```

### Volume Conditions

```yaml
# Absolute threshold
"current.volume >= 1000000"

# Relative to average
"current.volume >= avg(all_stocks, 'volume') * 3"

# Volume spike
"current.volume > ma(all_stocks, 20, 'volume') * 2"
```

### Block Dependencies

```yaml
# Check if block exists
"exists('block1')"

# Block completed
"exists('block1') and block1.status == 'completed'"

# Price above block peak
"current.close > block1.peak_price * 1.1"
```

### Combined Conditions

```yaml
# AND logic (in entry_conditions list)
entry_conditions:
  - "current.close >= 10000"
  - "current.volume >= 1000000"
  - "current.close > ma(all_stocks, 120)"

# OR logic (in exit_conditions list)
exit_conditions:
  - "current.close < 9000"
  - "current.volume < 500000"

# Complex expression
"(current.high - current.low) / current.low * 100 >= 5.0"
```

---

## Built-in Functions

| Function | Example | Description |
|----------|---------|-------------|
| `ma(stocks, period)` | `ma(all_stocks, 120)` | 120-day moving average |
| `avg(stocks, key)` | `avg(all_stocks, 'volume')` | Average volume |
| `max(stocks, key)` | `max(all_stocks[-20:], 'high')` | Max high in last 20 days |
| `min(stocks, key)` | `min(all_stocks[-20:], 'low')` | Min low in last 20 days |
| `sum(stocks, key)` | `sum(all_stocks[-5:], 'volume')` | Total volume in last 5 days |
| `count(stocks)` | `count(all_stocks)` | Count of candles |
| `exists(var)` | `exists('block1')` | Check if block1 exists |
| `in_range(val, min, max)` | `in_range(current.close, 9000, 11000)` | Value in range |
| `percent_change(old, new)` | `percent_change(prev.close, current.close)` | % change |

---

## Next Steps

### Learn More

- **Full Specification**: `docs/specification/DYNAMIC_BLOCK_SYSTEM.md`
- **Examples**: `presets/examples/simple_pattern_example.yaml`, `extended_pattern_example.yaml`
- **Tests**: `tests/integration/test_dynamic_block_system_e2e.py`

### Advanced Topics

1. **Conditional Branching**
   - Use `edge_type: "conditional"` for different paths based on conditions

2. **Multi-Parent Blocks**
   - A block can have multiple parent blocks (e.g., Block3 requires both Block1 AND Block2)

3. **Custom Functions**
   - Add your own functions via `@function_registry.register()`

4. **Incremental Detection**
   - Continue tracking active blocks across multiple batches

5. **Pattern Redetection**
   - Find similar patterns with relaxed conditions

### Try These Examples

1. **V-shaped recovery pattern**: Price drops, then rebounds
2. **Breakout pattern**: Price breaks above resistance with volume
3. **Consolidation pattern**: Price stabilizes in range before surge
4. **Multi-stage rally**: 4+ blocks of progressive price increases

---

## Troubleshooting

### "No blocks detected"

**Check**:
1. Entry conditions are too strict → Relax thresholds
2. Stock data is missing → Verify ticker and date range
3. Expression syntax error → Test expression with `expression_engine.evaluate()`

**Debug**:
```python
# Test single condition
result = engine.evaluate("current.close >= 10000", {'current': stock})
print(f"Condition result: {result}")
```

### "Block not completing"

**Check**:
1. Exit conditions never satisfied → Verify exit logic
2. Missing exit conditions → Add at least one exit condition

**Debug**:
```python
# Print active blocks
for block in detections:
    if block.is_active():
        print(f"{block.block_id} still active: started {block.started_at}")
```

### "Expression evaluation error"

**Common causes**:
1. Typo in variable name (`current.clos` instead of `current.close`)
2. Function doesn't exist → Check function registry
3. Wrong parameter types → Check function signature

**Fix**:
```python
# Validate expression before using
try:
    result = engine.evaluate(expr, context)
except Exception as e:
    print(f"Expression error: {e}")
```

---

## Cheat Sheet

### Minimal Pattern

```yaml
block_graph:
  root_node: "block1"
  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      name: "Block 1"
      entry_conditions:
        - "current.close >= 10000"
```

### Sequential Pattern

```yaml
block_graph:
  root_node: "block1"
  nodes:
    block1: { block_id: "block1", block_type: 1, name: "B1", entry_conditions: ["..."]}
    block2: { block_id: "block2", block_type: 2, name: "B2", entry_conditions: ["..."]}
  edges:
    - { from_block: "block1", to_block: "block2" }
```

### Conditional Branching

```yaml
edges:
  - from_block: "block1"
    to_block: "block2a"
    edge_type: "conditional"
    condition: "current.volume >= 1000000"
    priority: 1

  - from_block: "block1"
    to_block: "block2b"
    edge_type: "conditional"
    condition: "current.volume < 1000000"
    priority: 2
```

---

## Summary

✅ **What you learned**:
1. Create YAML pattern definition
2. Load pattern and detect blocks
3. Add unlimited blocks without code changes
4. Use expressions for flexible conditions
5. Save detections to database

✅ **Key takeaways**:
- YAML-driven: No code changes for new block types
- Expressions: Flexible condition logic
- Clean Architecture: Easy to extend and maintain
- Fully tested: 93 tests ensure reliability

**Happy pattern detecting! 🚀**
