# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POTALE_STOCK is a Korean stock market analysis and AI learning program that implements a sophisticated **YAML-based dynamic block pattern detection system**. The project follows Clean Architecture principles with strict layer separation.

**Core Functionality**: Detects and analyzes stock price patterns using a **dynamic block system (Block1 → Block2 → Block3 → ... → BlockN)**, where blocks are defined in YAML configuration files with custom conditions evaluated by an expression engine. Supports unlimited block types without code changes.

## Essential Commands

### Testing
```bash
# Run all tests with coverage
.venv/Scripts/python.exe -m pytest

# Run specific test category
.venv/Scripts/python.exe -m pytest -m unit
.venv/Scripts/python.exe -m pytest -m integration
.venv/Scripts/python.exe -m pytest -m checker

# Run single test file
.venv/Scripts/python.exe -m pytest tests/unit/entities/test_dynamic_block_detection.py -v

# Run tests without coverage overhead (faster)
.venv/Scripts/python.exe -m pytest --no-cov
```

### Data Collection
```bash
# Collect single ticker (uses AsyncUnifiedCollector)
.venv/Scripts/python.exe scripts/data_collection/collect_single_ticker.py --ticker 025980 --from-date 2015-01-01

# Collect all tickers (4,189 stocks, async parallel)
.venv/Scripts/python.exe scripts/data_collection/collect_all_tickers.py --from-date 2015-01-01

# Force full re-collection (ignore incremental)
.venv/Scripts/python.exe scripts/data_collection/collect_single_ticker.py --ticker 025980 --force-full
```

### Pattern Detection (YAML-based Dynamic System)
```bash
# Detect patterns with YAML config (REQUIRED)
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/extended_pattern_example.yaml \
    --from-date 2020-01-01

# Multiple tickers
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980,005930,035720 \
    --config presets/examples/simple_pattern_example.yaml

# With verbose output
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/extended_pattern_example.yaml \
    --verbose

# Dry-run (don't save to DB)
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/simple_pattern_example.yaml \
    --dry-run
```

**Note**: `--config` parameter is **REQUIRED**. The system uses YAML files to define block detection logic.

### Database Operations
```bash
# Query dynamic_block_detection table
sqlite3 data/database/stock_data.db "SELECT * FROM dynamic_block_detection WHERE ticker='025980' LIMIT 5;"

# Count blocks by type
sqlite3 data/database/stock_data.db "SELECT block_type, COUNT(*) FROM dynamic_block_detection WHERE ticker='025980' GROUP BY block_type;"

# Check table schema
sqlite3 data/database/stock_data.db "PRAGMA table_info(dynamic_block_detection);"

# List all tables
sqlite3 data/database/stock_data.db ".tables"
```

### Database Migrations
```bash
# Run a migration (always create backup first!)
cp data/database/stock_data.db data/database/stock_data_backup.db
.venv/Scripts/python.exe migrations/migrate_*.py
```

## Architecture

### Clean Architecture Layers

**Domain Layer** (`src/domain/`)
- **entities/**: Core business entities
  - `conditions/`: ExpressionEngine, FunctionRegistry, builtin_functions
  - `block_graph/`: BlockGraph, BlockNode, BlockEdge
  - `detections/`: DynamicBlockDetection, BlockStatus
  - `patterns/`: SeedPattern, RedetectionConfig
  - `core/`: Stock, Condition, DetectionResult
- **repositories/**: Repository interfaces (abstract base classes)
  - `dynamic_block_repository.py`: Interface for dynamic block storage
  - `seed_pattern_repository.py`: Interface for seed pattern storage
- Zero external dependencies

**Application Layer** (`src/application/`)
- **use_cases/**: Business logic orchestration
  - `dynamic_block_detector.py`: Core detection engine (YAML → BlockGraph → Detection)
  - `data_collection/`: Data collection workflows
- **services/**: Application services
  - `block_graph_loader.py`: YAML → BlockGraph converter
  - `indicators/`: Technical indicator calculators
- Depends only on domain layer

**Infrastructure Layer** (`src/infrastructure/`)
- **repositories/**: Repository implementations
  - `dynamic_block_repository_impl.py`: SQLAlchemy-based dynamic block storage
  - `seed_pattern_repository_impl.py`: Seed pattern storage
  - `stock/sqlite_stock_repository.py`: Stock data access
- **collectors/**: Data collection from Naver Finance
  - `AsyncUnifiedCollector`: High-performance async collector
  - `NaverHybridCollector`: Adjusted price + adjusted volume calculator
- **database/**: Database models and connection management
- **utils/**: Price utilities, data validation

**Presentation Layer** (`src/cli/`)
- CLI commands and TUI interface
- Orchestrates use cases

### Critical Architectural Concepts

#### Dynamic Block Detection System (YAML-based)

The system uses **YAML configuration files** to define block detection logic **without code changes**:

```yaml
# presets/examples/simple_pattern_example.yaml
block_graph:
  root_node: "block1"

  nodes:
    block1:
      block_id: "block1"
      block_type: 1
      entry_conditions:
        - expression: "current.close >= 10000"
        - expression: "current.volume >= 1000000"
      exit_conditions:
        - expression: "current.close < 9000"

  edges:
    - from_block: "block1"
      to_block: "block2"
      edge_type: "sequential"
```

**Key Components**:
1. **BlockGraph**: Directed graph of blocks (nodes) and transitions (edges)
2. **ExpressionEngine**: Evaluates conditions like `current.close >= ma(120)`
3. **FunctionRegistry**: Built-in functions (ma, volume_ma, candles_between, etc.)
4. **DynamicBlockDetector**: Traverses BlockGraph and detects patterns

**Benefits**:
- ✅ Unlimited block types (Block1~Block99+) without code changes
- ✅ Flexible conditions using Python expressions
- ✅ Easy experimentation (just edit YAML)
- ✅ Version control for detection strategies

#### Expression System

Conditions are evaluated using Python expressions with custom functions:

**Available Variables**:
- `current`: Current stock candle (close, high, low, volume, etc.)
- `prev`: Previous candle
- `block1`, `block2`, etc.: Active block objects
- `all_stocks`: Historical price data

**Built-in Functions**:
- `ma(period)`: Moving average
- `volume_ma(period)`: Volume moving average
- `candles_between(date1, date2)`: Count trading days
- `within_range(value, base, tolerance_pct)`: Price range check
- `is_new_high(period)`: New high detection
- `EXISTS('blockN')`: Check if block exists

**Examples**:
```python
"current.close >= 10000"
"current.high >= ma(120)"
"current.volume >= volume_ma(20) * 3"
"candles_between(block1.started_at, current.date) >= 2"
"within_range(current.close, block1.peak_price, 10.0)"
```

See `presets/schemas/function_library.yaml` and `presets/schemas/data_schema.yaml` for complete reference.

#### Block Independence

**Key Insight**: Each block can be detected independently OR as a sequence. When Block2 starts while Block1 is active, Block1 automatically ends the day before Block2 starts.

Blocks support:
- **Sequential transitions**: Block1 → Block2 → Block3
- **Independent detection**: Block2 can start without Block1
- **Conditional edges**: Transitions with custom conditions
- **Parent tracking**: Blocks store references to parent blocks (JSON array)

### Database Schema

**Key Tables**:
- `stock_price`: OHLCV data with adjusted prices/volumes from Naver Finance
- `stock_info`: Stock metadata (ticker, name, market)
- **`dynamic_block_detection`**: **Main detection table** (replaces block1~6_detection)
  - Columns: `id`, `block_id`, `block_type`, `ticker`, `started_at`, `ended_at`, `peak_price`, `peak_volume`, `status`, `parent_blocks` (JSON), `custom_metadata` (JSON)
- `collection_progress`: Tracks incremental collection state
- `investor_trading`: Investor type trading data

**Deleted Tables** (as of 2025-10-24):
- ~~`block1_detection`~~, ~~`block2_detection`~~, ~~`block3_detection`~~, ~~`block4_detection`~~ → Replaced by `dynamic_block_detection`
- ~~`block5_detection`~~, ~~`block6_detection`~~ → Replaced by `dynamic_block_detection`
- ~~`block_pattern`~~ → Pattern tracking moved to `dynamic_block_detection.pattern_id`
- ~~`block_label`~~ → ML labels (deleted)
- ~~`seed_condition_preset`~~, ~~`redetection_condition_preset`~~ → Replaced by YAML files

**Important Indexes**: Heavy indexing on ticker + date combinations for query performance.

## Development Workflow

### Creating Custom Detection Logic

1. **Copy an example YAML**:
   ```bash
   cp presets/examples/simple_pattern_example.yaml presets/my_pattern.yaml
   ```

2. **Edit block conditions**:
   ```yaml
   nodes:
     block1:
       entry_conditions:
         - expression: "current.close >= 15000"  # Custom threshold
         - expression: "current.volume >= volume_ma(20) * 5"  # Custom volume
   ```

3. **Run detection**:
   ```bash
   .venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py \
       --ticker 025980 \
       --config presets/my_pattern.yaml
   ```

4. **Query results**:
   ```bash
   sqlite3 data/database/stock_data.db "SELECT * FROM dynamic_block_detection WHERE ticker='025980';"
   ```

### Adding New Block Types

Just add a new node in YAML - **no code changes required**:

```yaml
nodes:
  block7:  # NEW BLOCK!
    block_id: "block7"
    block_type: 7
    entry_conditions:
      - expression: "current.close >= 20000"
    exit_conditions:
      - expression: "current.close < 18000"

edges:
  - from_block: "block6"
    to_block: "block7"
    edge_type: "sequential"
```

### Adding New Expression Functions

1. **Implement function** in `src/domain/entities/conditions/builtin_functions.py`:
   ```python
   @function_registry.register(
       name='my_function',
       category='custom',
       description='My custom function',
       params_schema={'param1': {'type': 'int'}}
   )
   def my_function(param1: int, context: dict) -> float:
       # Implementation
       return result
   ```

2. **Document in** `presets/schemas/function_library.yaml`:
   ```yaml
   custom:
     my_function:
       description: "My custom function"
       parameters:
         - name: param1
           type: int
   ```

3. **Use in YAML**:
   ```yaml
   entry_conditions:
     - expression: "my_function(10) >= 100"
   ```

### Making Schema Changes

1. **Create a migration script** in `migrations/`:
   - Name format: `migrate_<description>.py`
   - Always create a backup before running

2. **Test migration**:
   ```bash
   cp data/database/stock_data.db data/database/stock_data_backup.db
   .venv/Scripts/python.exe migrations/migrate_your_change.py
   ```

3. **Update repository classes** in `src/infrastructure/repositories/`

4. **Update entity classes** in `src/domain/entities/`

## Important Conventions

### Field Naming
- **Block fields**: `block_id`, `block_type`, `started_at`, `ended_at`, `peak_price`, `peak_volume`
- **Status values**: `active`, `completed`, `failed`
- **JSON fields**: `parent_blocks` (array of parent block IDs), `custom_metadata` (dict)

### Testing Strategy
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Unit tests should not touch the database
- Integration tests use a test database or transactions that rollback
- Test files mirror source structure

### Repository Pattern
- All database access goes through repositories
- Repositories are injected via dependency injection
- Domain layer defines repository interfaces
- Infrastructure layer implements them
- Use SQLAlchemy ORM, not raw SQL (except for complex queries)

### Async Collection
Data collection is async for performance:
- Use `AsyncUnifiedCollector` for new collection code
- Concurrent limit is configurable (default: 10 tickers in parallel)
- Incremental collection is enabled by default (checks `collection_progress` table)

## Key Files Reference

**Core Detection System**:
- `src/application/use_cases/dynamic_block_detector.py`: Main detection engine
- `src/application/services/block_graph_loader.py`: YAML → BlockGraph converter
- `src/domain/entities/conditions/expression_engine.py`: Expression evaluator
- `src/domain/entities/conditions/builtin_functions.py`: Built-in functions
- `src/domain/entities/block_graph/`: BlockGraph, BlockNode, BlockEdge entities
- `src/infrastructure/repositories/dynamic_block_repository_impl.py`: Database persistence

**YAML Examples**:
- `presets/examples/simple_pattern_example.yaml`: Block1~3 example
- `presets/examples/extended_pattern_example.yaml`: Block1~6 example
- `presets/schemas/function_library.yaml`: Available functions reference
- `presets/schemas/data_schema.yaml`: Available data fields reference

**Scripts**:
- `scripts/rule_based_detection/detect_patterns.py`: Main detection script (YAML-based)

**Legacy Files** (Archived 2025-10-24):
- `docs/archive/legacy_scripts/`: Old block1~4 detection scripts (no longer work)
- `docs/archive/legacy_scripts/README.md`: Migration guide from legacy system

## Documentation

Extensive documentation in `docs/`:
- **specification/**: Feature specs
- **architecture/**: System structure, database design
- **guides/**: Performance optimization, database maintenance
- **archive/**: Legacy scripts and documentation

**Essential Guides**:
- `USER_GUIDE.md`: Step-by-step usage guide
- `docs/archive/legacy_scripts/README.md`: Legacy system migration guide

## AI/ML System

### Overview

The project includes an **AI-based block pattern detection system** alongside the rule-based system. This ML system learns from manually labeled block patterns.

### Essential Commands

#### ML Pipeline
```bash
# Generate synthetic labels for testing
.venv/Scripts/python.exe scripts/ml_system/generate_synthetic_labels.py \
    --tickers 025980,005930,035720 \
    --blocks-per-ticker 3 \
    --output data/labels/synthetic_labels.csv

# Build ML dataset from labels
.venv/Scripts/python.exe scripts/ml_system/build_block_dataset.py \
    --labels data/labels/block_labels.csv \
    --feature-config presets/feature_configs/block_classifier_v1.yaml \
    --output data/ml/dataset_v1.pkl

# Train classifier
.venv/Scripts/python.exe scripts/ml_system/train_block_classifier.py \
    --dataset data/ml/dataset_v1.pkl \
    --output models/block_classifier_v1.h5 \
    --epochs 100
```

### ML Architecture

**Learning Module** (`src/learning/`):
- **feature_engineering/**: Feature extraction (50+ features)
- **models/**: ML models (Dense, LSTM, CNN)
- **training/**: Training pipeline
- **evaluation/**: Metrics, confusion matrix

### Feature Categories
- **Price** (10): Normalized close, change rates, new highs
- **Volume** (12): Normalized, MA ratios, spike detection
- **Trading Value** (5): Billion won, MA ratio, thresholds
- **Moving Averages** (9): MA5/20/60/120, deviations
- **Technical** (5): RSI, MACD, Bollinger bands
- **Block Relations** (4): Block1 ratios, support distance

Total: **50 features**

## Common Pitfalls

1. **YAML config is REQUIRED**: `detect_patterns.py` requires `--config` parameter
2. **Always backup DB before migrations**: `cp data/database/stock_data.db data/database/stock_data_backup.db`
3. **Use dynamic_block_detection table**: Old block1~6_detection tables no longer exist
4. **YAML syntax matters**: Indentation must be correct, use spaces not tabs
5. **Expression syntax**: Use lowercase `and`, `or`, `not` (not `AND`, `OR`, `NOT`)
6. **Windows paths**: This project uses Windows paths (`\` separators)
7. **Virtual environment**: Always use `.venv/Scripts/python.exe`
8. **Block independence**: Blocks can start independently
9. **Timezone**: All dates are naive datetimes (KST assumed)
10. **Legacy scripts don't work**: Old scripts in `docs/archive/legacy_scripts/` are for reference only

## System Migration (2025-10-24)

**Major Update**: The system was migrated from fixed block1~6_detection tables to a dynamic YAML-based system.

**What Changed**:
- ✅ Single `dynamic_block_detection` table (replaces 6+ tables)
- ✅ YAML configuration files (replaces database presets)
- ✅ Unlimited block types (not limited to Block1~6)
- ✅ Expression-based conditions (more flexible)
- ✅ JSON storage for parent_blocks and metadata

**What Stayed**:
- ✅ Data collection system (unchanged)
- ✅ Stock price data (unchanged)
- ✅ ML system (unchanged)
- ✅ Clean Architecture (unchanged)

**Migration Path**: See `docs/archive/legacy_scripts/README.md` for migration guide from old system.
