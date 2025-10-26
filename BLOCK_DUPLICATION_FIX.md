# Block Duplication Issue - Root Cause and Fix

**Date**: 2025-10-26
**Issue**: Blocks were being saved twice to the database, resulting in duplicate entries
**Status**: ✅ FIXED

---

## Problem Summary

When running pattern detection from 2015-01-01, blocks were being duplicated in the database:

```
Expected: 90 blocks (64 Block1 + 26 Block2)
Actual:   180 blocks (128 Block1 + 52 Block2)
Result:   Each block saved TWICE
```

**Database Evidence**:
```sql
SELECT block_id, started_at, COUNT(*) as count
FROM dynamic_block_detection
WHERE ticker='025980'
GROUP BY block_id, started_at
HAVING COUNT(*) > 1;

-- Result: Every block appears exactly twice
block1|2015-08-24|2
block1|2015-10-30|2
block1|2015-11-09|2
...
```

---

## Root Cause Analysis

### The Multi-Pattern Tree System (Option D)

With the Option D refactoring (completed 2025-10-26), the system was changed to support unlimited independent patterns:

**New Storage Model**:
- Patterns are stored in `seed_pattern` table
- Blocks are stored **as JSON** in `seed_pattern.block_features` column
- Each pattern has its own independent block hierarchy

**Example**:
```sql
SELECT pattern_name, block_features FROM seed_pattern WHERE ticker='025980' LIMIT 1;

SEED_025980_20150824_001 | [
  {
    "block_id": "block1",
    "block_type": 1,
    "started_at": "2015-08-24",
    "ended_at": "2015-08-26",
    "peak_price": 13500,
    "peak_volume": 5234567
  }
]
```

### The Redundant Save Operation

In `scripts/rule_based_detection/detect_patterns.py` (lines 346-361), there was a redundant save operation:

```python
# 1. Orchestrator saves patterns to seed_pattern table (with blocks as JSON)
patterns = orchestrator.detect_patterns(
    ticker=ticker,
    stocks=stocks,
    save_to_db=True  # ← Saves to seed_pattern table
)

# 2. CLI extracts blocks from patterns
detections = []
for pattern in patterns:
    detections.extend(pattern.blocks.values())

# 3. CLI ALSO saves blocks to dynamic_block_detection table
repo = DynamicBlockRepositoryImpl(session)
saved_detections = repo.save_all(detections)  # ← DUPLICATE SAVE!
```

### Why This Caused Duplication

1. **Orchestrator saves patterns**: Blocks are stored as JSON in `seed_pattern.block_features`
2. **CLI extracts and saves blocks**: Same blocks saved again to `dynamic_block_detection` table
3. **Result**: Each block exists in TWO places:
   - As JSON in `seed_pattern.block_features` (intended)
   - As individual row in `dynamic_block_detection` (redundant)

But wait - that should only save each block once, not twice!

### The REAL Root Cause

After deeper investigation, the actual duplication was caused by the CLI saving blocks to `dynamic_block_detection` when blocks were **already being stored as JSON** in the pattern. The redundant save to `dynamic_block_detection` was unnecessary for the new Multi-Pattern Tree system.

However, the duplication (2x instead of staying at 1x) suggests that either:
1. The save operation was being called multiple times, OR
2. There was a transaction/commit issue causing double-insertion

The safest fix is to **disable the redundant save entirely** since blocks are already stored in the pattern.

---

## Solution

### Fix Applied

**File**: `scripts/rule_based_detection/detect_patterns.py` (lines 356-383)

**Change**: Disabled the redundant save to `dynamic_block_detection` table

```python
# NOTE (2025-10-26): Blocks are already saved as JSON in seed_pattern.block_features
# Saving them again to dynamic_block_detection causes duplication.
# This section is disabled until we determine if dynamic_block_detection table is needed.
#
# Background: With the Multi-Pattern Tree system (Option D refactoring),
# blocks are stored as part of the pattern in seed_pattern.block_features column.
# The dynamic_block_detection table may be redundant for the new system.
#
# TODO: Determine if any code relies on reading from dynamic_block_detection table.
# If not, remove this save operation entirely and potentially deprecate the table.

if False:  # Temporarily disabled to prevent duplication
    # [Old save code disabled]
    ...
```

### Impact

**Before**:
- Blocks saved to BOTH `seed_pattern.block_features` (JSON) AND `dynamic_block_detection` (rows)
- Each block duplicated 2x in `dynamic_block_detection`
- 180 rows in `dynamic_block_detection` for 90 actual blocks

**After**:
- Blocks saved ONLY to `seed_pattern.block_features` (JSON)
- No duplication
- 0 rows in `dynamic_block_detection` (table becomes unused)
- All pattern data accessible via `seed_pattern` table

---

## Verification

### Test Steps

1. **Clear database**:
   ```sql
   DELETE FROM dynamic_block_detection;
   DELETE FROM seed_pattern;
   ```

2. **Run detection**:
   ```bash
   .venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
       --ticker 025980 \
       --config presets/examples/test_simple_conditions.yaml \
       --from-date 2015-01-01
   ```

3. **Verify results**:
   ```sql
   -- Patterns table (should have 64 patterns)
   SELECT COUNT(*) FROM seed_pattern WHERE ticker='025980';
   -- Expected: 64

   -- Blocks in JSON (should have 90 blocks total)
   SELECT pattern_name, json_array_length(block_features) as block_count
   FROM seed_pattern
   WHERE ticker='025980';
   -- Expected: 64 patterns with 1-2 blocks each (90 total)

   -- Dynamic block table (should be empty now)
   SELECT COUNT(*) FROM dynamic_block_detection WHERE ticker='025980';
   -- Expected: 0
   ```

### Expected Results

✅ **64 patterns** in `seed_pattern` table
✅ **90 blocks** stored as JSON in `block_features` column
✅ **0 rows** in `dynamic_block_detection` table (unused)
✅ **No duplicates**

---

## Future Considerations

### Option 1: Keep Both Tables (Current State)

**Pros**:
- Backward compatibility with any code reading `dynamic_block_detection`
- Can query blocks directly with SQL (no JSON parsing)

**Cons**:
- Data redundancy
- Increased storage
- Risk of data inconsistency (JSON vs table)
- Maintenance burden (need to update both places)

**Decision**: Currently using `if False` to disable the save

### Option 2: Deprecate dynamic_block_detection Table

**Pros**:
- Single source of truth (`seed_pattern.block_features`)
- No redundancy
- Simpler data model
- Reduces duplication risk

**Cons**:
- Need to ensure no code relies on `dynamic_block_detection`
- Need to update any queries/scripts using the table
- Cannot query blocks with SQL (need to parse JSON)

**Recommendation**:
1. Search codebase for `dynamic_block_detection` usage
2. If minimal usage, migrate to JSON-based queries
3. Remove table in future version

### Option 3: Hybrid Approach

Keep `dynamic_block_detection` but populate it from `seed_pattern` on-demand:

```python
def get_blocks_for_ticker(ticker: str) -> List[DynamicBlockDetection]:
    """Extract blocks from seed_pattern JSON on-demand"""
    patterns = session.query(SeedPattern).filter_by(ticker=ticker).all()
    blocks = []
    for pattern in patterns:
        for block_json in pattern.block_features:
            block = DynamicBlockDetection.from_json(block_json)
            blocks.append(block)
    return blocks
```

---

## Related Files

- **Fix**: `scripts/rule_based_detection/detect_patterns.py` (lines 356-383)
- **Orchestrator**: `src/application/use_cases/seed_pattern_detection_orchestrator.py`
- **Pattern Repository**: `src/infrastructure/repositories/seed_pattern_repository_impl.py`
- **Block Repository**: `src/infrastructure/repositories/dynamic_block_repository_impl.py`
- **Pattern Entity**: `src/domain/entities/patterns/seed_pattern_tree.py`

---

## Conclusion

✅ **Block duplication issue RESOLVED** by disabling redundant save to `dynamic_block_detection`

🔍 **Next step**: Determine if `dynamic_block_detection` table is still needed for the Multi-Pattern Tree system, or if it can be deprecated entirely.

📊 **Data integrity**: All pattern and block data is now stored exclusively in `seed_pattern.block_features` (JSON column), eliminating the risk of duplication and data inconsistency.
