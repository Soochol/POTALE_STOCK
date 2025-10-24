# Lookback Window Validation

**Status**: ✅ Implemented (Phase 2 Complete)
**Version**: 1.0
**Last Updated**: 2025-10-24

## Overview

Lookback window validation is a **backward-looking** block validation system that ensures previous blocks exist within a specified candle range when detecting new blocks. This complements the existing **forward-looking** `min/max_candles_from_block` checks.

## Motivation

### Problem

The existing `min/max_candles_from_block` validation works **forward** from the previous block's start date:

```
Block1 Start (2024-01-08)
    ↓
    +2 candles minimum
    +150 candles maximum
    ↓
Block2 must be between here and here
```

However, when we find a **Block2 candidate**, we need to verify **backward** that a Block1 exists within a reasonable range:

```
Block2 Candidate (2024-02-15)
    ↑
    Look back 2-150 candles
    ↑
Block1 must exist somewhere in this range
```

### Solution

Add **lookback validation** that checks backward from the candidate date to verify the previous block exists within the specified range. This provides:

1. **Bidirectional validation**: Both forward (from previous block) and backward (from candidate)
2. **Flexible filtering**: Optional parameters (null = skip check)
3. **Independent min/max**: Can set only minimum, only maximum, or both

## Implementation

### 1. Configuration (YAML)

**File**: `presets/seed_conditions.yaml`, `presets/redetection_conditions.yaml`

```yaml
block2:
  # ... other parameters ...

  # Forward-looking checks (from Block1 start)
  min_candles_from_block:     2         # Minimum candles from Block1 start
  max_candles_from_block:     150       # Maximum candles from Block1 start

  # Backward-looking checks (from Block2 candidate)
  lookback_min_candles:       null      # Lookback minimum range (null=skip)
  lookback_max_candles:       null      # Lookback maximum range (null=skip)
```

**Activation**:
```yaml
lookback_min_candles:       2         # Block1 must be at least 2 candles back
lookback_max_candles:       150       # Block1 must be at most 150 candles back
```

### 2. Database Schema

**Migration**: `migrations/migrate_add_lookback_candles.py`

Added columns to `seed_condition_preset` and `redetection_condition_preset`:

```sql
-- Block2
block2_lookback_min_candles INTEGER NULL
block2_lookback_max_candles INTEGER NULL

-- Block3
block3_lookback_min_candles INTEGER NULL
block3_lookback_max_candles INTEGER NULL

-- Block4-6 (similar)
```

### 3. Entity Classes

**Files**:
- `src/domain/entities/conditions/block_conditions.py`
- `src/domain/entities/conditions/seed_condition.py`
- `src/domain/entities/conditions/redetection_condition.py`

```python
@dataclass
class Block2Condition:
    # ... existing fields ...
    block2_lookback_min_candles: Optional[int] = None
    block2_lookback_max_candles: Optional[int] = None
```

### 4. Checker Implementation

**Files**: `src/application/services/checkers/block2_checker.py` (and block3-6)

```python
def check_lookback_window(
    self,
    current_date: date,
    prev_seed_block1: Optional[Block1Detection],
    lookback_min_candles: Optional[int],
    lookback_max_candles: Optional[int],
    all_stocks: List[Stock],
) -> bool:
    """
    Lookback validation: Check if Block1 exists in appropriate range from Block2 candidate date.

    Returns:
        True: Block1 is in valid range (or check skipped)
        False: Block1 is outside valid range
    """
    # Skip if both parameters are None
    if lookback_min_candles is None and lookback_max_candles is None:
        return True

    # Skip if no previous block
    if prev_seed_block1 is None:
        return True

    # Count candles from Block1 start to current date
    candles_count = self._count_candles_between(
        prev_seed_block1.started_at,
        current_date,
        all_stocks
    )

    # Check minimum range
    if lookback_min_candles is not None:
        if candles_count < lookback_min_candles:
            return False

    # Check maximum range
    if lookback_max_candles is not None:
        if candles_count > lookback_max_candles:
            return False

    return True
```

### 5. Use Case Integration

**Files**:
- `src/application/use_cases/block_detection/detect_block2.py`
- `src/application/use_cases/block_detection/detect_block3.py`

```python
# Validation sequence in can_start_block2()

# 1. Entry conditions check
# 2. Min start interval check
# 3. Additional conditions (volume_ratio, low_price_margin)
# 4. Min/max candles from block (forward check)
# 5. Lookback window check (backward check) ← NEW!

if not self.checker.check_lookback_window(
    stock.date,
    prev_block1,
    condition.block2_lookback_min_candles,
    condition.block2_lookback_max_candles,
    all_stocks
):
    return False
```

### 6. Service Integration

**Files**:
- `src/application/services/detectors/pattern_seed_detector.py` (Seed detection)
- `src/application/services/detectors/pattern_redetector.py` (Redetection)

Both seed and redetection workflows include lookback validation.

## Usage

### Example 1: Activate Lookback for Block2

**Edit**: `presets/seed_conditions.yaml`

```yaml
block2:
  lookback_min_candles:       2         # Block1 must be at least 2 candles ago
  lookback_max_candles:       150       # Block1 must be at most 150 candles ago
```

**Update Database**:
```bash
.venv/Scripts/python.exe scripts/preset_management/update_presets_from_yaml.py
```

**Run Detection**:
```bash
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980 --from-date 2015-01-01
```

### Example 2: Only Maximum Lookback

```yaml
block2:
  lookback_min_candles:       null      # No minimum
  lookback_max_candles:       100       # Block1 must be within 100 candles
```

### Example 3: Only Minimum Lookback

```yaml
block2:
  lookback_min_candles:       10        # Block1 must be at least 10 candles ago
  lookback_max_candles:       null      # No maximum
```

## Validation Logic

### Forward vs Backward Checks

| Check Type | Direction | Start Point | Validates |
|------------|-----------|-------------|-----------|
| `min_candles_from_block` | Forward ➡️ | Block1 start | "Block2 must be N+ candles after Block1 starts" |
| `max_candles_from_block` | Forward ➡️ | Block1 start | "Block2 must be within N candles from Block1 start" |
| `lookback_min_candles` | Backward ⬅️ | Block2 candidate | "Block1 must be at least N candles before Block2" |
| `lookback_max_candles` | Backward ⬅️ | Block2 candidate | "Block1 must be within N candles before Block2" |

### Example Scenario

**Configuration**:
```yaml
block2:
  min_candles_from_block:     2
  max_candles_from_block:     150
  lookback_min_candles:       2
  lookback_max_candles:       150
```

**Timeline**:
```
Block1 Start: 2024-01-08
    ↓
    +2 candles minimum (forward)
    ↓
2024-01-10 ← Earliest Block2 (forward check)
    ...
2024-06-05 ← Latest Block2 (forward check: 150 candles)
    ↓
    +150 candles maximum (forward)


Block2 Candidate: 2024-02-15
    ↑
    2-150 candles lookback (backward)
    ↑
2024-01-08 ← Block1 (must exist here)
```

**Validation**:
1. **Forward check**: Block1 (2024-01-08) → Block2 candidate (2024-02-15) = ~30 candles
   - ✅ 30 > 2 (min)
   - ✅ 30 < 150 (max)

2. **Backward check**: Block2 candidate (2024-02-15) → Block1 (2024-01-08) = ~30 candles
   - ✅ 30 >= 2 (lookback min)
   - ✅ 30 <= 150 (lookback max)

Both checks pass! ✅

## Candle Counting

### Trading Day Based

Lookback validation counts **trading days only** (excludes weekends/holidays automatically):

```python
def _count_candles_between(
    self, start_date: date, end_date: date, all_stocks: List[Stock]
) -> int:
    """
    Count actual trading day candles between two dates.

    - start_date and end_date are both INCLUSIVE
    - Only counts days with actual stock data (trading days)
    - Weekends/holidays automatically excluded
    """
    count = 0
    for stock in all_stocks:
        if start_date <= stock.date <= end_date:
            count += 1
    return count
```

### Example

```
Calendar days: 2024-01-08 to 2024-01-12 (5 days)
Trading days:  Mon 1/8, Tue 1/9, Wed 1/10, Thu 1/11, Fri 1/12 (5 days)

→ candles_count = 5

Calendar days: 2024-01-08 to 2024-01-14 (7 days)
Trading days:  Mon 1/8, Tue 1/9, Wed 1/10, Thu 1/11, Fri 1/12 (5 days)
               (Sat 1/13, Sun 1/14 excluded)

→ candles_count = 5 (not 7!)
```

## Block Coverage

| Block | Lookback Validation | Status |
|-------|---------------------|--------|
| Block1 | N/A (no previous block) | - |
| Block2 | ✅ Implemented | Checks Block1 lookback |
| Block3 | ✅ Implemented | Checks Block2 lookback |
| Block4 | ✅ Implemented | Checks Block3 lookback |
| Block5 | ✅ Implemented (checker only) | Infrastructure ready, no workflow |
| Block6 | ✅ Implemented (checker only) | Infrastructure ready, no workflow |

**Note**: Block5/6 have lookback checkers implemented but are not integrated into detection workflows.

## Performance

**Time Complexity**: O(n) per validation (n = number of stocks)

**Optimization**: Candle counting could be optimized with:
- Binary search (O(log n))
- Precomputed index mapping

Current implementation is acceptable for most use cases (< 3000 candles per ticker).

## Testing

### Unit Tests

Test file: `tests/unit/services/checkers/test_block2_checker_lookback.py` (TODO)

```python
def test_lookback_window_validation():
    """Test lookback validation logic"""
    # Test cases:
    # 1. Both min/max None → returns True (skip)
    # 2. prev_block1 None → returns True (skip)
    # 3. Count < min → returns False
    # 4. Count > max → returns False
    # 5. Count in range → returns True
```

### Integration Test

Run actual pattern detection:

```bash
# Test 1: With lookback enabled
# Edit YAML to set lookback values
.venv/Scripts/python.exe scripts/preset_management/update_presets_from_yaml.py
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980

# Test 2: Without lookback (null)
# Edit YAML to set lookback to null
.venv/Scripts/python.exe scripts/preset_management/update_presets_from_yaml.py
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980

# Compare results
```

## Migration Guide

### From Previous Version (Without Lookback)

**Step 1**: Pull latest code
```bash
git pull origin master
```

**Step 2**: Run database migration
```bash
.venv/Scripts/python.exe migrations/migrate_add_lookback_candles.py
```

**Step 3**: Update presets from YAML
```bash
.venv/Scripts/python.exe scripts/preset_management/update_presets_from_yaml.py
```

**Step 4**: (Optional) Activate lookback
- Edit `presets/seed_conditions.yaml` or `presets/redetection_conditions.yaml`
- Set `lookback_min_candles` and/or `lookback_max_candles` for desired blocks
- Re-run preset update script

### Backward Compatibility

✅ **Fully backward compatible**:
- Default values: `null` (skip validation)
- Existing workflows unchanged
- No breaking changes

## Troubleshooting

### Issue: No Block2 detected with lookback enabled

**Diagnosis**:
```bash
# Check current lookback settings
sqlite3 data/database/stock_data.db "
SELECT block2_lookback_min_candles, block2_lookback_max_candles
FROM seed_condition_preset
WHERE name='default_seed';
"
```

**Possible Causes**:
1. Lookback range too narrow (e.g., min=100, max=120)
2. Combined with strict `min/max_candles_from_block` (double filtering)
3. Entry conditions too strict (unrelated to lookback)

**Solution**:
- Widen lookback range or set to null
- Check other detection conditions (entry_surge_rate, volume_ratio, etc.)

### Issue: ORM error "object has no attribute 'lookback'"

**Diagnosis**: ORM models not updated

**Solution**:
```bash
# Verify migration was run
sqlite3 data/database/stock_data.db "PRAGMA table_info(seed_condition_preset);" | grep lookback

# Should show:
# 18|block2_lookback_min_candles|INTEGER|0||0
# 19|block2_lookback_max_candles|INTEGER|0||0
# ...

# If missing, run migration:
.venv/Scripts/python.exe migrations/migrate_add_lookback_candles.py
```

## Related Documentation

- [BLOCK_DETECTION.md](../specification/BLOCK_DETECTION.md) - Block detection system overview
- [Parameter Renaming](../implementation/PARAMETER_RENAME.md) - Phase 1: min_candles_after_block → min_candles_from_block
- [Database Schema](../architecture/DATABASE_SCHEMA.md) - Full database schema

## Future Enhancements

### Potential Improvements

1. **Asymmetric Lookback**: Different min/max for redetection vs seed
2. **Dynamic Lookback**: Adjust range based on market volatility
3. **Performance**: Binary search for candle counting
4. **Metrics**: Track lookback filter effectiveness

### Block5/6 Integration

Currently Block5/6 have lookback infrastructure but no workflow integration. To activate:

1. Create `detect_block5.py`, `detect_block6.py` use cases
2. Integrate into `pattern_seed_detector.py`
3. Add redetection support in `pattern_redetector.py`
4. Update documentation

## Changelog

### v1.0 (2025-10-24)
- ✅ Initial implementation
- ✅ Block2-6 checker support
- ✅ Seed detection integration (Block2-4)
- ✅ Redetection integration (Block2-4)
- ✅ Database migration
- ✅ YAML configuration
- ✅ Documentation

## License

Internal project documentation. All rights reserved.
