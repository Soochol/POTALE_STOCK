# Phase 3: Highlight-Centric Detector Specification

**Status**: 🚧 In Progress
**Created**: 2025-10-27
**Architecture**: Option D - Modular Coexistence

---

## Overview

The **Highlight-Centric Detector** is a new detection use case that takes a **highlight-first approach** to pattern discovery. Unlike the sequential detector (Block1 → Block2 → ...), this detector:

1. **Scans for highlights first** (blocks with 2+ forward spots)
2. **Looks backward** (30 days) to find the true root Block1
3. **Looks forward** (1125 days = 4.5 years) to track long-term outcomes

This approach is optimized for **ML/AI training data collection** where we want to:
- Focus on significant patterns (highlights are rare events)
- Capture long-term outcomes (1-4.5 years)
- Analyze support/resistance behavior over extended periods

---

## Architecture

### Use Case Layer

```python
# src/application/use_cases/highlight_centric_detector.py

class HighlightCentricDetector:
    """
    Highlight-first pattern detection use case.

    Detection Strategy:
    1. Scan entire period for highlight candidates (2+ forward spots)
    2. For each highlight:
       a) Backward scan (30 days) - find true root Block1
       b) Forward scan (1125 days) - track long-term pattern
       c) Support/resistance analysis
    """

    def __init__(
        self,
        block_graph: BlockGraph,
        highlight_detector: HighlightDetector,
        support_resistance_analyzer: SupportResistanceAnalyzer,
        dynamic_block_detector: DynamicBlockDetector,
        expression_engine: ExpressionEngine
    ):
        self.block_graph = block_graph
        self.highlight_detector = highlight_detector
        self.sr_analyzer = support_resistance_analyzer
        self.block_detector = dynamic_block_detector
        self.expression_engine = expression_engine

    def detect_patterns(
        self,
        ticker: str,
        stocks: List[Stock],
        scan_from: date,
        scan_to: date
    ) -> List[HighlightCentricPattern]:
        """
        Main detection workflow.

        Returns:
            List of patterns, each anchored to a highlight block.
        """
        pass
```

### Domain Entity (NEW)

```python
# src/domain/entities/patterns/highlight_centric_pattern.py

@dataclass
class HighlightCentricPattern:
    """
    Pattern discovered via highlight-centric detection.

    Key Differences from SeedPatternTree:
    - Always has a highlight (required)
    - Has backward_scan_result (optional - may find stronger Block1)
    - Has forward_scan_result (long-term tracking)
    - Has support_resistance_analysis (Block1 range analysis)
    """

    pattern_id: str  # Format: HIGHLIGHT_{TICKER}_{YYYYMMDD}_{SEQUENCE}
    ticker: str
    highlight_block: DynamicBlockDetection  # The anchor block (2+ spots)
    root_block: DynamicBlockDetection  # May be different from highlight if backward scan found stronger one

    # Backward scan result (30 days before highlight)
    backward_scan_result: Optional[BackwardScanResult] = None

    # Forward scan result (up to 1125 days after highlight)
    forward_blocks: List[DynamicBlockDetection] = field(default_factory=list)

    # Support/resistance analysis
    sr_analysis: Optional[SupportResistanceAnalysis] = None

    # Lifecycle
    status: PatternStatus = PatternStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
```

---

## Detection Workflow

### Phase 1: Highlight Scanning

**Goal**: Find all highlight candidates in the scan period.

```python
def _scan_for_highlights(
    self,
    ticker: str,
    stocks: List[Stock],
    scan_from: date,
    scan_to: date
) -> List[DynamicBlockDetection]:
    """
    Scan for blocks with 2+ forward spots.

    Process:
    1. Use DynamicBlockDetector to detect all blocks in period
    2. Use HighlightDetector.find_highlights() to filter
    3. Return only blocks meeting highlight criteria
    """

    # Step 1: Detect all blocks (sequential detection)
    all_blocks = self.block_detector.detect_blocks(
        ticker=ticker,
        stocks=stocks,
        start_date=scan_from,
        end_date=scan_to
    )

    # Step 2: Filter for highlights
    block1_node = self.block_graph.get_node('block1')
    if not block1_node or not block1_node.has_highlight_condition():
        return []

    highlight_condition = block1_node.highlight_condition
    context = {'ticker': ticker, 'all_stocks': stocks}

    highlights = self.highlight_detector.find_highlights(
        blocks=all_blocks,
        highlight_condition=highlight_condition,
        context=context
    )

    return highlights
```

**Expected Output**:
- 40,000 patterns from 4,000 stocks → ~100 highlights (2-5% rate)

### Phase 2: Backward Detection (30 Days)

**Goal**: Find if there's a stronger Block1 before the highlight.

```python
def _backward_scan(
    self,
    highlight: DynamicBlockDetection,
    stocks: List[Stock],
    lookback_days: int = 30
) -> Optional[BackwardScanResult]:
    """
    Look backward 30 days from highlight to find stronger Block1.

    Why:
    - Highlight might be Block2, Block3, etc.
    - True root Block1 might exist earlier
    - Example: Block1 (low volume) → Block2 (highlight with 2 spots)

    Returns:
        BackwardScanResult with stronger Block1 if found, else None.
    """

    # Calculate backward period
    highlight_date = highlight.started_at
    scan_from = highlight_date - timedelta(days=lookback_days)
    scan_to = highlight_date - timedelta(days=1)  # Exclude highlight date

    # Detect blocks in backward period
    backward_blocks = self.block_detector.detect_blocks(
        ticker=highlight.ticker,
        stocks=stocks,
        start_date=scan_from,
        end_date=scan_to
    )

    # Find Block1s with higher peak than highlight
    stronger_blocks = [
        b for b in backward_blocks
        if b.block_type == 1 and b.peak_price > highlight.peak_price
    ]

    if not stronger_blocks:
        return None  # Highlight is the strongest root

    # Return the strongest Block1
    strongest = max(stronger_blocks, key=lambda b: b.peak_price)

    return BackwardScanResult(
        found_stronger_root=True,
        stronger_block=strongest,
        peak_price_ratio=strongest.peak_price / highlight.peak_price
    )
```

**Design Decision**:
- If stronger Block1 found → use it as root, highlight becomes secondary block
- If no stronger Block1 → highlight is the root

### Phase 3: Forward Detection (1125 Days)

**Goal**: Track long-term pattern evolution (up to 4.5 years).

```python
def _forward_scan(
    self,
    root_block: DynamicBlockDetection,
    stocks: List[Stock],
    forward_days: int = 1125  # 4.5 years
) -> List[DynamicBlockDetection]:
    """
    Track pattern evolution forward from root block.

    Process:
    1. Detect Block2, Block3, ... in forward period
    2. Track support/resistance behavior (Block1.high as support)
    3. Identify major breakouts (price > Block1.high * 2.0)
    4. Stop at forward_days limit or pattern failure

    Returns:
        List of blocks in chronological order.
    """

    root_date = root_block.started_at
    scan_from = root_date + timedelta(days=1)
    scan_to = root_date + timedelta(days=forward_days)

    # Detect all subsequent blocks
    forward_blocks = self.block_detector.detect_blocks(
        ticker=root_block.ticker,
        stocks=stocks,
        start_date=scan_from,
        end_date=scan_to
    )

    # Sort by date
    forward_blocks.sort(key=lambda b: b.started_at)

    return forward_blocks
```

**ML Features to Extract**:
- Days until major breakout (price > 2x Block1.high)
- Number of retests to Block1.high level
- Support strength (% of days above Block1.high)
- Maximum drawdown from Block1.high
- Final outcome (success/failure classification)

### Phase 4: Support/Resistance Analysis

**Goal**: Analyze Block1 range as support/resistance.

```python
def _analyze_support_resistance(
    self,
    root_block: DynamicBlockDetection,
    forward_blocks: List[DynamicBlockDetection],
    stocks: List[Stock]
) -> SupportResistanceAnalysis:
    """
    Perform long-term support/resistance analysis.

    Uses:
        SupportResistanceAnalyzer.analyze() (already implemented in Phase 1)
    """

    analysis = self.sr_analyzer.analyze(
        reference_block=root_block,
        forward_blocks=forward_blocks,
        all_stocks=stocks,
        analysis_period_days=1125  # 4.5 years
    )

    return analysis
```

---

## Data Structures

### BackwardScanResult

```python
@dataclass
class BackwardScanResult:
    """Result of backward scanning for stronger Block1."""
    found_stronger_root: bool
    stronger_block: Optional[DynamicBlockDetection] = None
    peak_price_ratio: float = 1.0  # stronger_peak / highlight_peak
    lookback_days: int = 30
```

### HighlightCentricPattern (Full)

```python
@dataclass
class HighlightCentricPattern:
    """Complete pattern from highlight-centric detection."""

    # Identity
    pattern_id: str  # HIGHLIGHT_{TICKER}_{YYYYMMDD}_{SEQUENCE}
    ticker: str

    # Core blocks
    highlight_block: DynamicBlockDetection  # Anchor (2+ spots)
    root_block: DynamicBlockDetection  # Root (may differ from highlight)

    # Detection results
    backward_scan_result: Optional[BackwardScanResult] = None
    forward_blocks: List[DynamicBlockDetection] = field(default_factory=list)

    # Analysis
    sr_analysis: Optional[SupportResistanceAnalysis] = None

    # Metadata
    status: PatternStatus = PatternStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Computed properties
    def is_highlight_root(self) -> bool:
        """Check if highlight is the root block."""
        return self.highlight_block.id == self.root_block.id

    def get_all_blocks(self) -> List[DynamicBlockDetection]:
        """Get all blocks in chronological order."""
        return [self.root_block] + self.forward_blocks

    def get_pattern_duration_days(self) -> int:
        """Calculate pattern duration from root to last forward block."""
        if not self.forward_blocks:
            return 0
        last_block = self.forward_blocks[-1]
        return (last_block.ended_at - self.root_block.started_at).days
```

---

## Comparison: Sequential vs Highlight-Centric

| Aspect | Sequential (Existing) | Highlight-Centric (New) |
|--------|----------------------|-------------------------|
| **Starting Point** | Block1 entry conditions | Highlights (2+ spots) |
| **Direction** | Forward only (Block1 → Block2 → ...) | Backward (30d) + Forward (1125d) |
| **Pattern Count** | High (~40,000 from 4,000 stocks) | Low (~100 highlights, 2-5% rate) |
| **Focus** | All patterns (weak + strong) | Significant patterns only |
| **Use Case** | General pattern detection | ML training data (quality over quantity) |
| **Root Discovery** | Always first Block1 detected | May adjust root via backward scan |
| **Tracking Period** | Until Block exits or 180 days | Up to 1125 days (4.5 years) |
| **S/R Analysis** | Optional (not implemented) | Required (core feature) |

---

## Integration with Existing System

### Shared Components (No Changes)

✅ **Application Services** (reused):
- `HighlightDetector` - Finds highlights
- `SupportResistanceAnalyzer` - Analyzes support/resistance
- `DynamicBlockDetector` - Detects blocks (used internally)
- `BlockGraphLoader` - Loads YAML config

✅ **Domain Entities** (reused):
- `BlockGraph`, `BlockNode`, `BlockEdge`
- `DynamicBlockDetection`
- `HighlightCondition`
- `SupportResistanceAnalysis`

### New Components

🆕 **Domain Entities**:
- `HighlightCentricPattern` - Pattern container
- `BackwardScanResult` - Backward scan result

🆕 **Use Case**:
- `HighlightCentricDetector` - Main detection orchestrator

🆕 **Repository** (optional):
- `HighlightCentricPatternRepository` - Persistence

---

## YAML Configuration

The highlight-centric detector uses the **same YAML format** as sequential detector:

```yaml
block_graph:
  pattern_type: "seed"  # or "highlight_centric"
  root_node: "block1"

  nodes:
    block1:
      # ... standard Block1 definition

      # Highlight condition (REQUIRED for highlight-centric)
      highlight_condition:
        type: "forward_spot"
        enabled: true
        priority: 1
        parameters:
          required_spot_count: 2
          consecutive: true
          day_offsets: [1, 2]
```

---

## CLI Integration

### New Command Option

```bash
# Sequential detection (existing)
python scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/test1_alt.yaml \
    --from-date 2020-01-01

# Highlight-centric detection (new)
python scripts/rule_based_detection/detect_patterns.py \
    --ticker 025980 \
    --config presets/examples/test1_alt.yaml \
    --from-date 2020-01-01 \
    --mode highlight-centric \
    --backward-days 30 \
    --forward-days 1125
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/use_cases/test_highlight_centric_detector.py

class TestHighlightCentricDetector:
    def test_scan_for_highlights(self):
        """Test highlight scanning phase."""

    def test_backward_scan_finds_stronger_root(self):
        """Test backward scan finds stronger Block1."""

    def test_backward_scan_no_stronger_root(self):
        """Test backward scan when highlight is strongest."""

    def test_forward_scan_tracks_long_term(self):
        """Test forward scan up to 1125 days."""

    def test_support_resistance_analysis(self):
        """Test S/R analysis integration."""

    def test_pattern_id_generation(self):
        """Test HIGHLIGHT_{TICKER}_{DATE}_{SEQ} format."""
```

### Integration Tests

```python
# tests/integration/test_highlight_centric_detection_integration.py

def test_end_to_end_highlight_centric_detection():
    """Full workflow: scan → backward → forward → S/R analysis."""

def test_multiple_highlights_in_period():
    """Handle multiple highlights independently."""

def test_highlight_centric_vs_sequential_comparison():
    """Compare results between two detection modes."""
```

---

## Performance Considerations

### Expected Volumes

- **Input**: 4,000 stocks × 10 years = 40,000,000 candles
- **Highlights**: ~100 (2-5% of 40,000 patterns)
- **Backward scans**: 100 × 30 days = 3,000 candles
- **Forward scans**: 100 × 1125 days = 112,500 candles

**Total**: Much less than sequential detection (processes only highlights)

### Optimization Strategies

1. **Lazy loading**: Load price data only for highlight periods
2. **Parallel processing**: Process highlights independently
3. **Caching**: Cache S/R analysis results
4. **Database indexes**: Index on (ticker, date) for fast range queries

---

## Database Schema (Optional)

```sql
-- Optional: Store highlight-centric patterns separately
CREATE TABLE highlight_centric_pattern (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT UNIQUE NOT NULL,  -- HIGHLIGHT_{TICKER}_{YYYYMMDD}_{SEQ}
    ticker TEXT NOT NULL,

    -- Blocks
    highlight_block_id INTEGER NOT NULL,  -- FK to dynamic_block_detection
    root_block_id INTEGER NOT NULL,       -- FK to dynamic_block_detection

    -- Scan results
    found_stronger_root BOOLEAN DEFAULT FALSE,
    backward_lookback_days INTEGER DEFAULT 30,
    forward_scan_days INTEGER DEFAULT 1125,

    -- Metadata
    status TEXT DEFAULT 'active',  -- active, completed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    FOREIGN KEY (highlight_block_id) REFERENCES dynamic_block_detection(id),
    FOREIGN KEY (root_block_id) REFERENCES dynamic_block_detection(id)
);

CREATE INDEX idx_hcp_ticker_date ON highlight_centric_pattern(ticker, created_at);
CREATE INDEX idx_hcp_status ON highlight_centric_pattern(status);
```

---

## Implementation Plan

### Step 1: Domain Entities ✅ (Ready)
- [x] `BackwardScanResult` dataclass
- [x] `HighlightCentricPattern` dataclass

### Step 2: Use Case Implementation (Next)
- [ ] `HighlightCentricDetector.__init__()`
- [ ] `_scan_for_highlights()`
- [ ] `_backward_scan()`
- [ ] `_forward_scan()`
- [ ] `_analyze_support_resistance()`
- [ ] `detect_patterns()` (main workflow)

### Step 3: Testing
- [ ] Unit tests (20+ tests)
- [ ] Integration tests (5+ tests)
- [ ] Real data validation

### Step 4: CLI Integration
- [ ] Add `--mode highlight-centric` option
- [ ] Add `--backward-days`, `--forward-days` options
- [ ] Update output formatting

### Step 5: Documentation
- [ ] Update USER_GUIDE.md
- [ ] Update CLAUDE.md
- [ ] Create examples in presets/

---

## Success Criteria

✅ Phase 3 is complete when:

1. **Functionality**:
   - [ ] HighlightCentricDetector detects highlights
   - [ ] Backward scan finds stronger roots
   - [ ] Forward scan tracks 1125 days
   - [ ] S/R analysis integrated

2. **Testing**:
   - [ ] 20+ unit tests passing
   - [ ] 5+ integration tests passing
   - [ ] Real data validation (Ananti stock)

3. **Performance**:
   - [ ] Processes 100 highlights in < 5 minutes
   - [ ] Memory usage < 500MB

4. **Documentation**:
   - [ ] API documentation complete
   - [ ] Usage examples provided
   - [ ] Architecture diagrams updated

---

**Next**: Implement domain entities (BackwardScanResult, HighlightCentricPattern)
