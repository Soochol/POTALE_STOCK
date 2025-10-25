# Multi-Pattern Tree Management Migration Guide

**Date**: 2025-10-25
**Version**: 1.0
**Author**: POTALE_STOCK Team

## Overview

This guide explains how to migrate from the old single-pattern detection system to the new multi-pattern tree management system.

## What Changed?

### Old System (Before 2025-10-25)

**Problem**: The system used `active_blocks_map: Dict[str, DynamicBlockDetection]` which could only maintain **ONE block per `block_id`**.

```python
# OLD: Using DynamicBlockDetector directly
detector = DynamicBlockDetector(block_graph, expression_engine)
detections = detector.detect_blocks(ticker, stocks, "seed")

# Problem: active_blocks_map overwrites blocks
# When new Block1 detected → previous Block1 lost ❌
active_blocks_map = {
    'block1': Block1_B  # Block1_A was overwritten and lost!
}
```

**Consequences**:
- ❌ Data loss when new Block1 detected
- ❌ Cannot track multiple independent patterns
- ❌ No pattern lifecycle management
- ❌ No unique pattern identifiers

### New System (After 2025-10-25)

**Solution**: Multi-Pattern Tree Manager manages unlimited independent patterns with unique IDs.

```python
# NEW: Using SeedPatternDetectionOrchestrator
orchestrator = SeedPatternDetectionOrchestrator(
    block_graph=block_graph,
    expression_engine=expression_engine,
    seed_pattern_repository=repo
)
patterns = orchestrator.detect_patterns(ticker, stocks, "seed")

# Result: Multiple independent patterns ✅
Pattern #1: SEED_025980_20180307_001 → Block1 → Block2 → COMPLETED
Pattern #2: SEED_025980_20180521_002 → Block1 → Block2 → ACTIVE
Pattern #3: SEED_025980_20180921_003 → Block1 → ACTIVE
```

**Benefits**:
- ✅ No data loss
- ✅ Unlimited independent patterns
- ✅ Auto-generated unique `pattern_id`
- ✅ FSM-based lifecycle (ACTIVE → COMPLETED → ARCHIVED)
- ✅ Clear pattern hierarchy (Block1 → Block2 → ... → BlockN)

## Migration Steps

### Step 1: Update Imports

**Before**:
```python
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.detections import DynamicBlockDetection
```

**After**:
```python
from src.application.use_cases.seed_pattern_detection_orchestrator import (
    SeedPatternDetectionOrchestrator
)
from src.domain.entities.patterns import SeedPatternTree
from src.infrastructure.repositories.seed_pattern_repository_impl import (
    SeedPatternRepositoryImpl
)
```

### Step 2: Update Detection Code

**Before**:
```python
# Old approach: Direct DynamicBlockDetector usage
detector = DynamicBlockDetector(block_graph, expression_engine)
detections = detector.detect_blocks(
    ticker="025980",
    stocks=stocks,
    condition_name="seed"
)

# detections: List[DynamicBlockDetection]
for detection in detections:
    print(f"{detection.block_id}: {detection.started_at}")
```

**After**:
```python
# New approach: Use Orchestrator
seed_pattern_repo = SeedPatternRepositoryImpl(session)  # Optional
orchestrator = SeedPatternDetectionOrchestrator(
    block_graph=block_graph,
    expression_engine=expression_engine,
    seed_pattern_repository=seed_pattern_repo
)

patterns = orchestrator.detect_patterns(
    ticker="025980",
    stocks=stocks,
    condition_name="seed",
    save_to_db=True
)

# patterns: List[SeedPatternTree]
for pattern in patterns:
    print(f"Pattern: {pattern.pattern_id}")
    print(f"  Status: {pattern.status.value}")
    print(f"  Blocks: {', '.join(pattern.blocks.keys())}")

    # Access individual blocks
    for block_id, block in pattern.blocks.items():
        print(f"    {block_id}: {block.started_at}")
```

### Step 3: Update Return Type Handling

**Before**:
```python
def process_detections(detections: List[DynamicBlockDetection]) -> None:
    for detection in detections:
        if detection.block_id == 'block1':
            # Process Block1
            pass
```

**After**:
```python
def process_patterns(patterns: List[SeedPatternTree]) -> None:
    for pattern in patterns:
        # Access all blocks in pattern
        if 'block1' in pattern.blocks:
            block1 = pattern.blocks['block1']
            # Process Block1
            pass

        # Or iterate all blocks
        for block_id, block in pattern.blocks.items():
            # Process each block
            pass
```

### Step 4: Extract Blocks from Patterns (If Needed)

If you need a flat list of blocks for compatibility:

```python
# Extract all blocks from all patterns
all_blocks = []
for pattern in patterns:
    all_blocks.extend(pattern.blocks.values())

# all_blocks: List[DynamicBlockDetection]
```

### Step 5: Update Database Queries

**No database schema changes required!** The new system still uses `dynamic_block_detection` table.

However, if you want to query patterns by `pattern_id`:

```python
# Query blocks belonging to a specific pattern
sqlite3 data/database/stock_data.db "
    SELECT * FROM dynamic_block_detection
    WHERE custom_metadata LIKE '%SEED_025980_20180307_001%';
"
```

## API Reference

### SeedPatternDetectionOrchestrator

**Constructor**:
```python
orchestrator = SeedPatternDetectionOrchestrator(
    block_graph: BlockGraph,
    expression_engine: ExpressionEngine,
    seed_pattern_repository: Optional[SeedPatternRepository] = None
)
```

**Main Method**:
```python
patterns = orchestrator.detect_patterns(
    ticker: str,
    stocks: List[Stock],
    condition_name: str = "seed",
    save_to_db: bool = True,
    auto_archive: bool = True
) -> List[SeedPatternTree]
```

**Parameters**:
- `ticker`: Stock ticker code (e.g., "025980")
- `stocks`: Historical stock data
- `condition_name`: Detection condition name (default: "seed")
- `save_to_db`: Auto-save completed patterns to database
- `auto_archive`: Auto-archive after saving (COMPLETED → ARCHIVED)

**Returns**: List of detected patterns (both ACTIVE and COMPLETED)

### SeedPatternTree

**Key Attributes**:
```python
pattern.pattern_id         # PatternId: SEED_025980_20180307_001
pattern.ticker             # str: "025980"
pattern.root_block         # DynamicBlockDetection: Block1 instance
pattern.blocks             # Dict[str, DynamicBlockDetection]
pattern.status             # PatternStatus: ACTIVE/COMPLETED/ARCHIVED
pattern.created_at         # datetime
pattern.completed_at       # Optional[datetime]
```

**Key Methods**:
```python
pattern.get_block_count()  # int: Number of blocks in pattern
pattern.check_completion() # bool: All blocks completed?
pattern.complete()         # Transition to COMPLETED state
pattern.archive()          # Transition to ARCHIVED state
```

### PatternId

**Format**: `SEED_{TICKER}_{YYYYMMDD}_{SEQUENCE}`

**Example**: `SEED_025980_20180307_001`

**Generation**:
```python
pattern_id = PatternId.generate(
    ticker="025980",
    detection_date=date(2018, 3, 7),
    sequence=1
)
```

### PatternStatus

**States**:
- `ACTIVE`: Pattern can add blocks
- `COMPLETED`: All blocks completed, no further modifications
- `ARCHIVED`: Saved to database

**Transitions**:
```
ACTIVE → COMPLETED → ARCHIVED
```

## Example: Complete Migration

**Before (Old System)**:
```python
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.application.services.block_graph_loader import BlockGraphLoader
from src.domain.entities.conditions import ExpressionEngine, function_registry

# Load YAML
loader = BlockGraphLoader()
block_graph = loader.load_from_yaml("presets/examples/test1_alt.yaml")

# Detect blocks
engine = ExpressionEngine(function_registry)
detector = DynamicBlockDetector(block_graph, engine)
detections = detector.detect_blocks("025980", stocks, "seed")

# Process
for d in detections:
    print(f"{d.block_id}: {d.started_at}")
```

**After (New System)**:
```python
from src.application.use_cases.seed_pattern_detection_orchestrator import (
    SeedPatternDetectionOrchestrator
)
from src.application.services.block_graph_loader import BlockGraphLoader
from src.domain.entities.conditions import ExpressionEngine, function_registry
from src.infrastructure.repositories.seed_pattern_repository_impl import (
    SeedPatternRepositoryImpl
)

# Load YAML
loader = BlockGraphLoader()
block_graph = loader.load_from_yaml("presets/examples/test1_alt.yaml")

# Detect patterns
engine = ExpressionEngine(function_registry)
repo = SeedPatternRepositoryImpl(session)
orchestrator = SeedPatternDetectionOrchestrator(block_graph, engine, repo)
orchestrator.set_yaml_config_path("presets/examples/test1_alt.yaml")

patterns = orchestrator.detect_patterns("025980", stocks, "seed")

# Process
for pattern in patterns:
    print(f"Pattern: {pattern.pattern_id} ({pattern.status.value})")
    for block_id, block in pattern.blocks.items():
        print(f"  {block_id}: {block.started_at}")
```

## Common Patterns

### Pattern 1: Get All Active Patterns

```python
active_patterns = [p for p in patterns if p.status == PatternStatus.ACTIVE]
```

### Pattern 2: Get Latest Pattern for Ticker

```python
latest_pattern = max(
    patterns,
    key=lambda p: p.root_block.started_at
)
```

### Pattern 3: Count Patterns by Status

```python
from collections import Counter

status_counts = Counter(p.status for p in patterns)
print(f"Active: {status_counts[PatternStatus.ACTIVE]}")
print(f"Completed: {status_counts[PatternStatus.COMPLETED]}")
```

### Pattern 4: Extract All Block1s

```python
block1s = [p.root_block for p in patterns]
```

### Pattern 5: Find Pattern by ID

```python
pattern_id = "SEED_025980_20180307_001"
pattern = next(
    (p for p in patterns if str(p.pattern_id) == pattern_id),
    None
)
```

## Backward Compatibility

### DynamicBlockDetector Still Available

The old `DynamicBlockDetector` class is still available and unchanged. It's used internally by `SeedPatternDetectionOrchestrator`.

If you need low-level block detection without pattern management:

```python
detector = DynamicBlockDetector(block_graph, expression_engine)
blocks = detector.detect_blocks(ticker, stocks, "seed")
```

However, **this approach does NOT provide pattern management benefits** and should only be used for:
- Legacy code compatibility
- Low-level testing
- Custom pattern organization logic

### Extracting Blocks from Patterns

For compatibility with code expecting `List[DynamicBlockDetection]`:

```python
# Detect patterns
patterns = orchestrator.detect_patterns(ticker, stocks, "seed")

# Extract blocks for legacy code
blocks = []
for pattern in patterns:
    blocks.extend(pattern.blocks.values())

# Now `blocks` can be used with legacy code
legacy_function(blocks)
```

## Troubleshooting

### Issue: "Pattern already has block 'block2'"

**Cause**: Trying to add a block that already exists in the pattern.

**Solution**: Check if block exists before adding:
```python
if block_id not in pattern.blocks:
    pattern.add_block(block)
```

### Issue: "Cannot add block in COMPLETED state"

**Cause**: Trying to add blocks to a completed pattern.

**Solution**: Patterns are immutable after completion. Create a new pattern instead.

### Issue: "Root block must be 'block1'"

**Cause**: Trying to create a pattern with non-Block1 as root.

**Solution**: Always start patterns with Block1:
```python
if block.block_id == 'block1':
    pattern = manager.create_new_pattern(ticker, block, date)
```

## Testing

### Unit Tests

```python
from src.domain.entities.patterns import SeedPatternTree, PatternId, PatternStatus

def test_pattern_creation():
    pattern_id = PatternId("SEED_025980_20180307_001")
    pattern = SeedPatternTree(
        pattern_id=pattern_id,
        ticker="025980",
        root_block=block1,
        blocks={}
    )

    assert pattern.status == PatternStatus.ACTIVE
    assert pattern.get_block_count() == 1  # root_block auto-added
```

### Integration Tests

```python
def test_orchestrator_detect_patterns():
    orchestrator = SeedPatternDetectionOrchestrator(
        block_graph=block_graph,
        expression_engine=engine
    )

    patterns = orchestrator.detect_patterns(
        ticker="025980",
        stocks=test_stocks,
        save_to_db=False
    )

    assert len(patterns) > 0
    assert all(isinstance(p, SeedPatternTree) for p in patterns)
```

## Performance Considerations

1. **Memory Usage**: Patterns are kept in memory for speed. For large datasets, use `clear_completed_patterns()`:
   ```python
   manager.clear_completed_patterns()  # Free memory
   ```

2. **Database Saves**: Auto-save only completed patterns to reduce DB writes:
   ```python
   patterns = orchestrator.detect_patterns(
       ticker="025980",
       stocks=stocks,
       save_to_db=True  # Only saves COMPLETED patterns
   )
   ```

3. **Pattern Cleanup**: Archive patterns after saving to free memory:
   ```python
   patterns = orchestrator.detect_patterns(
       ticker="025980",
       stocks=stocks,
       save_to_db=True,
       auto_archive=True  # COMPLETED → ARCHIVED
   )
   ```

## Further Reading

- [CLAUDE.md](../../CLAUDE.md) - Project overview and architecture
- [Pattern Detection System](../specification/) - System specifications
- [SeedPatternTree API](../../src/domain/entities/patterns/seed_pattern_tree.py) - Domain entity source code
- [SeedPatternDetectionOrchestrator API](../../src/application/use_cases/seed_pattern_detection_orchestrator.py) - Use case source code

## Support

For questions or issues, please:
1. Check existing documentation in `docs/`
2. Review code examples in this guide
3. Examine test files in `tests/unit/entities/`
4. Create an issue in the repository

---

**Version History**:
- 1.0 (2025-10-25): Initial release
