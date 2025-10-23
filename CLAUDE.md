# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POTALE_STOCK is a Korean stock market analysis and AI learning program that implements a sophisticated block-based pattern detection system. The project follows Clean Architecture principles with strict layer separation.

**Core Functionality**: Detects and analyzes stock price patterns using a 4-stage "block" system (Block1→Block2→Block3→Block4), where each block represents a phase in price movement with specific technical conditions.

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
.venv/Scripts/python.exe -m pytest tests/unit/entities/test_block1_detection.py -v

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

### Pattern Detection
```bash
# Detect patterns for a ticker
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980 --from-date 2015-01-01

# Multiple tickers
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980,005930,035720

# With verbose output
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980 --verbose

# Dry-run (don't save to DB)
.venv/Scripts/python.exe scripts/rule_based_detection/detect_patterns.py --ticker 025980 --dry-run
```

### Database Operations
```bash
# Query database directly
sqlite3 data/database/stock_data.db "SELECT * FROM block1_detection LIMIT 5;"

# Check table schema
sqlite3 data/database/stock_data.db "PRAGMA table_info(block1_detection);"

# List all tables
sqlite3 data/database/stock_data.db ".tables"
```

### Preset Management
```bash
# Update presets from YAML files to database
.venv/Scripts/python.exe scripts/preset_management/update_presets_from_yaml.py

# Dry-run to preview changes
.venv/Scripts/python.exe scripts/preset_management/update_presets_from_yaml.py --dry-run
```

### Database Migrations
```bash
# Run a migration (always create backup first!)
copy data\database\stock_data.db data\database\stock_data_backup.db
.venv/Scripts/python.exe migrations/migrate_*.py
```

## Architecture

### Clean Architecture Layers

**Domain Layer** (`src/domain/`)
- **entities/**: Core business entities (Block1Detection, Block2Detection, Pattern, Conditions, etc.)
  - `conditions/`: BaseEntryCondition, ExitCondition, SeedCondition, RedetectionCondition
  - `patterns/`: BlockPattern entity
  - `detections/`: Block1Detection, Block2Detection, Block3Detection, Block4Detection
  - `core/`: Stock, Condition, DetectionResult
- **repositories/**: Repository interfaces (abstract base classes)
- Zero external dependencies

**Application Layer** (`src/application/`)
- **use_cases/**: Business logic orchestration
  - `block_detection/`: Block1-4 detection use cases
  - `pattern_detection/`: Pattern lifecycle management
  - `data_collection/`: Data collection workflows
- **services/**: Application services
  - `checkers/`: Block condition checkers
  - `detectors/`: Block detectors
  - `indicators/`: Technical indicator calculators
- Depends only on domain layer

**Infrastructure Layer** (`src/infrastructure/`)
- **repositories/**: Repository implementations (SQLAlchemy-based)
  - Pattern: `block_pattern_repository.py`, `detection_repository.py`
  - Data: `stock_repository.py`, `investor_repository.py`
  - Config: `seed_condition_preset_repository.py`, `redetection_condition_preset_repository.py`
- **collectors/**: Data collection from Naver Finance
  - `AsyncUnifiedCollector`: High-performance async collector
  - `NaverHybridCollector`: Adjusted price + adjusted volume calculator
- **database/**: SQLAlchemy models and connection management
- **utils/**: Price utilities, data validation

**Presentation Layer** (`src/cli/`)
- CLI commands and TUI interface
- Orchestrates use cases

### Critical Architectural Concepts

#### Block Detection System
The system detects 4-stage patterns in stock prices:
- **Block1**: Initial surge detection (entry: surge rate + MA breakout + volume spike)
- **Block2**: Continuation after Block1 (can start independently)
- **Block3**: Further continuation after Block2 (can start independently)
- **Block4**: Final stage after Block3

**Key Insight**: Each block can be detected independently OR as a sequence. When Block2 starts while Block1 is active, Block1 automatically ends the day before Block2 starts.

#### Seed vs Redetection
- **Seed Detection**: Initial strict pattern discovery with tight conditions (e.g., entry_surge_rate=8.0%)
- **Redetection**: Find similar patterns with relaxed conditions (e.g., entry_surge_rate=4.0%, tolerance ranges for price matching)

This 2-phase approach finds high-quality seed patterns, then discovers similar historical occurrences for ML training.

#### Preset System
Conditions are managed via presets stored in:
- **YAML source**: `presets/seed_conditions.yaml`, `presets/redetection_conditions.yaml`
- **Database tables**: `seed_condition_preset`, `redetection_condition_preset`

Workflow: Edit YAML → Run `update_presets_from_yaml.py` → Changes reflected in DB → Detection scripts use DB presets

#### Condition Independence (Post-Refactoring)
All blocks share the same condition structure (`BaseEntryCondition`), but each block can have different parameter values:
- Block1: `entry_surge_rate=8.0%`, `entry_ma_period=120`
- Block2: `entry_surge_rate=5.0%`, `entry_ma_period=60`

This enables per-block optimization while maintaining code reusability.

### Database Schema

**Key Tables**:
- `stock_price`: OHLCV data with adjusted prices/volumes from Naver Finance
- `block1_detection`, `block2_detection`, `block3_detection`, `block4_detection`: Detection records
- `block_pattern`: Links blocks into complete patterns, tracks pattern lifecycle
- `seed_condition_preset`, `redetection_condition_preset`: Preset configurations
- `collection_progress`: Tracks incremental collection state
- `investor_trading`: Investor type trading data

**Important Indexes**: Heavy indexing on ticker + date combinations for query performance.

## Development Workflow

### Making Schema Changes

1. **Create a migration script** in `migrations/`:
   - Name format: `migrate_<description>.py`
   - Always create a backup before running
   - Check for existing similar migrations

2. **Test migration**:
   ```bash
   copy data\database\stock_data.db data\database\stock_data_backup.db
   .venv/Scripts/python.exe migrations/migrate_your_change.py
   ```

3. **Update ORM models** in `src/infrastructure/database/models.py`

4. **Update repository classes** in `src/infrastructure/repositories/`

5. **Update entity classes** in `src/domain/entities/`

6. **Update preset YAML if needed** in `presets/`

### Working with Presets

Presets define detection conditions. To modify:

1. Edit YAML files in `presets/seed_conditions.yaml` or `redetection_conditions.yaml`
2. Run `python scripts/preset_management/update_presets_from_yaml.py --dry-run` to preview
3. Run `python scripts/preset_management/update_presets_from_yaml.py` to apply
4. Detection scripts automatically use updated presets from DB

### Adding New Block Conditions

When adding new condition parameters:

1. Update `BaseEntryCondition` in `src/domain/entities/conditions/base_entry_condition.py`
2. Update YAML preset files with new parameters
3. Create migration to add columns to `seed_condition_preset` and `redetection_condition_preset` tables
4. Update preset repositories to handle new fields
5. Update checker logic in `src/application/services/checkers/`
6. Add tests for new condition

## Important Conventions

### Field Naming
- **Entry conditions**: Prefixed with `entry_` (e.g., `entry_surge_rate`, `entry_ma_period`)
- **Exit conditions**: Prefixed with `exit_` (e.g., `exit_ma_period`)
- **Block-specific**: Prefixed with `blockN_` where N is block number (e.g., `block2_volume_ratio`)
- **Time periods**: Use `_days` or `_months` suffix (e.g., `min_start_interval_days`, `volume_high_months`)

### Testing Strategy
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.checker`
- Unit tests should not touch the database
- Integration tests use a test database or transactions that rollback
- Test files mirror source structure: `tests/unit/entities/test_block1_detection.py` tests `src/domain/entities/detections/block1_detection.py`

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

- `src/domain/entities/conditions/base_entry_condition.py`: Core condition definition shared by all blocks
- `src/application/services/checkers/block1_checker.py` through `block4_checker.py`: Condition validation logic
- `src/application/use_cases/pattern_detection/detect_seed_patterns.py`: Seed detection orchestration
- `src/infrastructure/repositories/detection/block1_repository.py`: Block1 persistence (similar for Block2-4)
- `docs/specification/BLOCK_DETECTION.md`: Complete block detection system specification
- `presets/seed_conditions.yaml`: Seed preset source of truth

## Documentation

Extensive documentation in `docs/`:
- **specification/**: Feature specs, especially `BLOCK_DETECTION.md` (complete block system guide)
- **architecture/**: System structure, database design, project organization
- **implementation/**: Roadmap, refactoring TODOs, session notes
- **guides/**: Performance optimization, database maintenance
- **analysis/**: Code analysis, improvement proposals

**Always check** `docs/specification/BLOCK_DETECTION.md` when working with block detection logic.

## AI/ML System (New!)

### Overview

The project now includes an **AI-based block pattern detection system** alongside the rule-based system. This ML system learns from manually labeled block patterns and can detect Block1/2/3 automatically.

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

# Test full pipeline
.venv/Scripts/python.exe scripts/ml_system/test_full_pipeline.py --quick-test
```

#### Label Management
```bash
# Import labels from CSV to database
.venv/Scripts/python.exe scripts/ml_system/import_block_labels.py \
    --csv data/labels/block_labels.csv
```

### ML Architecture

**Learning Module** (`src/learning/`):
- **feature_engineering/**: Feature extraction system
  - `registry.py`: Feature Registry pattern (50+ features)
  - `technical_indicators.py`: RSI, MACD, etc.
  - `block_features.py`: All feature functions
  - `dataset_builder.py`: Creates training datasets
- **models/**: ML models
  - `block_classifier.py`: BlockClassifier (Dense layers)
- **training/**, **inference/**, **evaluation/**: TODO

**Preset Configs** (`presets/`):
- **feature_configs/**: Feature selection (YAML)
  - `block_classifier_v1.yaml`: Baseline 50 features

**Scripts** (`scripts/`):
- `generate_synthetic_labels.py`: Creates fake labels for testing
- `import_block_labels.py`: CSV → Database
- `build_block_dataset.py`: Labels + Stock Data → ML Dataset
- `train_block_classifier.py`: Train classifier model
- `test_full_pipeline.py`: End-to-end test

### Key Concepts

#### Feature Registry Pattern
Features are registered using decorators and can be enabled/disabled via YAML config:

```python
@feature_registry.register('volume_spike_ratio', category='volume')
def volume_spike_ratio(df: pd.DataFrame) -> pd.Series:
    ma20 = calculate_moving_average(df['volume'], 20)
    return (df['volume'] / ma20).fillna(1.0)
```

Add to config:
```yaml
# presets/feature_configs/block_classifier_v2.yaml
features:
  - volume_spike_ratio  # Add new feature!
```

#### Block Labels
Stored in `block_label` table:
- `ticker`, `block_type` (1/2/3), `sequence`, `started_at`, `ended_at`
- `spot_volume_candles` (JSON): Spot volume candle dates
- `spot_price_center`: Block1 spot candle center price
- `support_price_type`: 'top'/'middle'/'bottom'

CSV format:
```csv
ticker,block_type,sequence,started_at,ended_at,spot_candles,spot_center,support_type,notes
025980,1,1,2020-01-15,2020-02-10,"2020-01-17,2020-01-18",5500,middle,"Strong surge"
```

#### Feature Categories (v1)
- **Price** (10): Normalized close, change rates, new highs
- **Volume** (12): Normalized, MA ratios, spike detection, new highs
- **Trading Value** (5): Billion won, MA ratio, threshold flags
- **Moving Averages** (9): MA5/20/60/120, deviations, alignment
- **Technical** (5): RSI, MACD, Bollinger bands
- **Block Relations** (4): Block1 ratios, support distance (Block2/3 only)

Total: **50 features**

### Development Workflow

#### Adding New Features
1. Write feature function in `src/learning/feature_engineering/block_features.py`
2. Add to YAML: `presets/feature_configs/block_classifier_vX.yaml`
3. Rebuild dataset: `python scripts/ml_system/build_block_dataset.py ...`
4. Retrain model: `python scripts/ml_system/train_block_classifier.py ...`

#### Experimenting with Features
```bash
# List all features
python -c "from src.learning.feature_engineering.registry import feature_registry; feature_registry.print_summary()"

# Create new config version
cp presets/feature_configs/block_classifier_v1.yaml \
   presets/feature_configs/block_classifier_v2.yaml

# Edit v2.yaml, then rebuild
python scripts/ml_system/build_block_dataset.py \
    --feature-config presets/feature_configs/block_classifier_v2.yaml \
    --output data/ml/dataset_v2.pkl
```

### Documentation

- **[AI_BLOCK_DETECTION.md](docs/specification/AI_BLOCK_DETECTION.md)**: Complete ML system specification
- **[BLOCK_DETECTION.md](docs/specification/BLOCK_DETECTION.md)**: Rule-based system (original)

### ML System Status

**Implemented (MVP)**:
- ✅ Feature Registry system (50+ features)
- ✅ Dataset Builder (labels → training data)
- ✅ BlockClassifier model (Dense layers)
- ✅ Training pipeline
- ✅ Synthetic label generation
- ✅ Label import/export

**TODO (Phase 2)**:
- ⏳ Model Registry (multiple architectures)
- ⏳ Evaluation system (metrics, confusion matrix)
- ⏳ Inference system (batch prediction, ticker scanning)
- ⏳ Preprocessing configs
- ⏳ Training configs (callbacks, augmentation)

**TODO (Phase 3)**:
- ⏳ Ensemble models
- ⏳ Signal generation (buy/sell)
- ⏳ Auto ML / Hyperparameter optimization

## Common Pitfalls

1. **Don't modify presets directly in DB**: Edit YAML files and run `update_presets_from_yaml.py`
2. **Always backup DB before migrations**: `copy data\database\stock_data.db data\database\stock_data_backup.db`
3. **Check for nullable fields**: Many condition fields are now nullable (optional conditions)
4. **Understand Seed vs Redetection**: They have different purposes and different condition strictness
5. **Windows paths**: This project uses Windows paths (`\` separators), not Unix paths
6. **Virtual environment**: Always use `.venv/Scripts/python.exe`, not global Python
7. **Block independence**: Blocks can start independently; they don't require prior blocks to exist
8. **Timezone**: All dates are naive datetimes (no timezone), assumed KST (Korea Standard Time)
9. **ML Feature changes require dataset rebuild**: When modifying features, rebuild the dataset before retraining
10. **Label data format**: CSV must follow exact format (see AI_BLOCK_DETECTION.md)