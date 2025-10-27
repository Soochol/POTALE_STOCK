"""
Highlight-Centric Detector - Use Case (Phase 3)

Detects patterns using a highlight-first approach:
1. Scan for highlights (blocks with 2+ forward spots)
2. For each highlight, scan backward (30 days) to find true root
3. Scan forward (1125 days) to track long-term evolution
4. Analyze support/resistance behavior
"""

import logging
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from src.domain.entities.core import Stock
from src.domain.entities.block_graph import BlockGraph
from src.domain.entities.detections import DynamicBlockDetection
from src.domain.entities.patterns import (
    HighlightCentricPattern,
    BackwardScanResult,
    PatternStatus,
    create_highlight_centric_pattern
)
from src.application.services.highlight_detector import HighlightDetector
from src.application.services.support_resistance_analyzer import SupportResistanceAnalyzer
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.domain.entities.conditions import ExpressionEngine

logger = logging.getLogger(__name__)


class HighlightCentricDetector:
    """
    Highlight-first pattern detection use case.

    This detector implements Option D architecture - a new detection system
    that shares Application Services with the Sequential Detector.

    Detection Phases:
        Phase 1: Scan for highlights (entire period)
        Phase 2: Backward scan (30 days before each highlight)
        Phase 3: Forward scan (1125 days after each highlight)
        Phase 4: Support/resistance analysis

    Architecture:
        Domain ← Application Services ← Use Case (this class)
                     ↑
                     │ (shared)
                     │
                 Sequential Detector (existing)
    """

    def __init__(
        self,
        block_graph: BlockGraph,
        highlight_detector: HighlightDetector,
        support_resistance_analyzer: SupportResistanceAnalyzer,
        dynamic_block_detector: DynamicBlockDetector,
        expression_engine: ExpressionEngine
    ):
        """
        Initialize highlight-centric detector.

        Args:
            block_graph: Block graph from YAML configuration
            highlight_detector: Shared highlight detection service
            support_resistance_analyzer: Shared S/R analysis service
            dynamic_block_detector: Block detector (used internally)
            expression_engine: Expression evaluator
        """
        self.block_graph = block_graph
        self.highlight_detector = highlight_detector
        self.sr_analyzer = support_resistance_analyzer
        self.block_detector = dynamic_block_detector
        self.expression_engine = expression_engine

        # Pattern tracking
        self.patterns: List[HighlightCentricPattern] = []
        self.pattern_sequence: Dict[str, int] = {}  # ticker → sequence counter

        logger.debug("HighlightCentricDetector initialized")

    # ============================================================
    # Main Detection Workflow
    # ============================================================

    def detect_patterns(
        self,
        ticker: str,
        stocks: List[Stock],
        scan_from: date,
        scan_to: date,
        backward_days: int = 30,
        forward_days: int = 1125
    ) -> List[HighlightCentricPattern]:
        """
        Main detection workflow - highlight-first approach.

        Args:
            ticker: Stock ticker
            stocks: Historical price data (must cover full period)
            scan_from: Start date for highlight scanning
            scan_to: End date for highlight scanning
            backward_days: Days to scan backward from highlight (default: 30)
            forward_days: Days to scan forward from highlight (default: 1125 = 4.5 years)

        Returns:
            List of HighlightCentricPattern objects

        Workflow:
            1. Scan for highlights in [scan_from, scan_to]
            2. For each highlight:
               a) Backward scan (30 days) to find true root
               b) Forward scan (1125 days) to track evolution
               c) Support/resistance analysis
            3. Return completed patterns
        """
        logger.info(
            f"Starting highlight-centric detection for {ticker} "
            f"from {scan_from} to {scan_to}"
        )

        # Phase 1: Scan for highlights
        highlights = self._scan_for_highlights(
            ticker=ticker,
            stocks=stocks,
            scan_from=scan_from,
            scan_to=scan_to
        )

        logger.info(f"Found {len(highlights)} highlight(s) for {ticker}")

        if not highlights:
            logger.info("No highlights found, skipping pattern creation")
            return []

        # Process each highlight
        for idx, highlight in enumerate(highlights, start=1):
            logger.info(
                f"Processing highlight {idx}/{len(highlights)}: "
                f"date={highlight.started_at}, peak={highlight.peak_price}"
            )

            try:
                # Create pattern
                pattern = self._create_pattern_from_highlight(
                    ticker=ticker,
                    highlight=highlight
                )

                # Phase 2: Backward scan
                backward_result = self._backward_scan(
                    highlight=highlight,
                    stocks=stocks,
                    lookback_days=backward_days
                )

                if backward_result:
                    pattern.set_backward_scan_result(backward_result)
                    logger.info(
                        f"Backward scan: found_stronger_root={backward_result.found_stronger_root}"
                    )

                # Phase 3: Forward scan
                forward_blocks = self._forward_scan(
                    root_block=pattern.root_block,
                    stocks=stocks,
                    forward_days=forward_days
                )

                for block in forward_blocks:
                    pattern.add_forward_block(block)

                logger.info(
                    f"Forward scan: found {len(forward_blocks)} block(s), "
                    f"duration={pattern.get_pattern_duration_days()} days"
                )

                # Phase 4: Support/resistance analysis
                if forward_blocks:
                    sr_analysis = self._analyze_support_resistance(
                        root_block=pattern.root_block,
                        forward_blocks=forward_blocks,
                        stocks=stocks
                    )
                    pattern.set_sr_analysis(sr_analysis)
                    logger.info("Support/resistance analysis completed")

                # Complete pattern
                pattern.complete()
                self.patterns.append(pattern)

                logger.info(f"Pattern completed: {pattern.pattern_id}")

            except Exception as e:
                logger.error(
                    f"Error processing highlight at {highlight.started_at}: {e}",
                    exc_info=True
                )
                continue

        logger.info(
            f"Highlight-centric detection completed: {len(self.patterns)} pattern(s)"
        )
        return self.patterns

    # ============================================================
    # Phase 1: Highlight Scanning
    # ============================================================

    def _scan_for_highlights(
        self,
        ticker: str,
        stocks: List[Stock],
        scan_from: date,
        scan_to: date
    ) -> List[DynamicBlockDetection]:
        """
        Scan for highlight candidates (blocks with 2+ forward spots).

        Strategy:
            1. Use DynamicBlockDetector to detect all blocks in period
            2. Use HighlightDetector to filter for highlights
            3. Return only blocks meeting highlight criteria

        Args:
            ticker: Stock ticker
            stocks: Historical price data
            scan_from: Start date
            scan_to: End date

        Returns:
            List of highlight blocks sorted by date (earliest first)
        """
        logger.debug(
            f"Scanning for highlights: {ticker} from {scan_from} to {scan_to}"
        )

        # Filter stocks to scan period
        filtered_stocks = self._filter_stocks_by_date(stocks, scan_from, scan_to)

        if not filtered_stocks:
            logger.warning(f"No stock data in scan period {scan_from} to {scan_to}")
            return []

        # Step 1: Detect all blocks using sequential detector
        all_blocks = self.block_detector.detect_blocks(
            ticker=ticker,
            stocks=filtered_stocks
        )

        logger.debug(f"Sequential detection found {len(all_blocks)} block(s)")

        if not all_blocks:
            return []

        # Step 2: Check if highlight_condition is defined
        block1_node = self.block_graph.get_node('block1')
        if not block1_node or not block1_node.has_highlight_condition():
            logger.warning("No highlight_condition defined in BlockGraph")
            return []

        highlight_condition = block1_node.highlight_condition
        context = {'ticker': ticker, 'all_stocks': stocks}

        # Step 3: Filter for highlights
        highlights = self.highlight_detector.find_highlights(
            blocks=all_blocks,
            highlight_condition=highlight_condition,
            context=context
        )

        logger.debug(f"Filtered to {len(highlights)} highlight(s)")

        return highlights

    # ============================================================
    # Phase 2: Backward Detection
    # ============================================================

    def _backward_scan(
        self,
        highlight: DynamicBlockDetection,
        stocks: List[Stock],
        lookback_days: int = 30
    ) -> Optional[BackwardScanResult]:
        """
        Scan backward from highlight to find stronger root Block1.

        Why:
            - Highlight might be Block2, Block3, etc. in a larger pattern
            - True root Block1 might exist earlier but with lower volume
            - Example: Block1 (low volume) → Block2 (highlight with 2 spots)

        Args:
            highlight: The highlight block
            stocks: Historical price data
            lookback_days: Number of days to scan backward (default: 30)

        Returns:
            BackwardScanResult if scan performed, None if data insufficient
        """
        logger.debug(
            f"Backward scan: looking back {lookback_days} days from "
            f"{highlight.started_at}"
        )

        # Calculate backward period
        highlight_date = highlight.started_at
        scan_from = highlight_date - timedelta(days=lookback_days)
        scan_to = highlight_date - timedelta(days=1)  # Exclude highlight date

        # Check if we have data for backward period
        earliest_stock_date = min(s.date for s in stocks)
        if scan_from < earliest_stock_date:
            logger.warning(
                f"Insufficient data for backward scan: "
                f"need {scan_from}, have {earliest_stock_date}"
            )
            return BackwardScanResult.no_stronger_root(lookback_days=lookback_days)

        # Filter stocks to backward period
        filtered_stocks = self._filter_stocks_by_date(stocks, scan_from, scan_to)

        if not filtered_stocks:
            logger.warning(f"No stock data in backward period {scan_from} to {scan_to}")
            return BackwardScanResult.no_stronger_root(lookback_days=lookback_days)

        # Detect blocks in backward period
        try:
            backward_blocks = self.block_detector.detect_blocks(
                ticker=highlight.ticker,
                stocks=filtered_stocks
            )

            logger.debug(
                f"Backward scan found {len(backward_blocks)} block(s) in period"
            )

        except Exception as e:
            logger.error(f"Error in backward detection: {e}", exc_info=True)
            return BackwardScanResult.no_stronger_root(lookback_days=lookback_days)

        # Find Block1s with higher peak than highlight
        block1_blocks = [b for b in backward_blocks if b.block_type == 1]
        stronger_blocks = [
            b for b in block1_blocks
            if b.peak_price > highlight.peak_price
        ]

        logger.debug(
            f"Found {len(block1_blocks)} Block1(s), "
            f"{len(stronger_blocks)} stronger than highlight"
        )

        if not stronger_blocks:
            return BackwardScanResult.no_stronger_root(lookback_days=lookback_days)

        # Return the strongest Block1 (highest peak)
        strongest = max(stronger_blocks, key=lambda b: b.peak_price)

        logger.info(
            f"Found stronger root: date={strongest.started_at}, "
            f"peak={strongest.peak_price} (vs highlight {highlight.peak_price})"
        )

        return BackwardScanResult.with_stronger_root(
            stronger_block=strongest,
            highlight_peak_price=highlight.peak_price,
            lookback_days=lookback_days
        )

    # ============================================================
    # Phase 3: Forward Detection
    # ============================================================

    def _forward_scan(
        self,
        root_block: DynamicBlockDetection,
        stocks: List[Stock],
        forward_days: int = 1125
    ) -> List[DynamicBlockDetection]:
        """
        Scan forward from root block to track long-term pattern evolution.

        Tracks:
            - Subsequent blocks (Block2, Block3, ...)
            - Support/resistance behavior (Block1.high as support)
            - Major breakouts (price > 2x Block1.high)
            - Pattern failures (price < Block1.low)

        Args:
            root_block: Root Block1 of the pattern
            stocks: Historical price data
            forward_days: Number of days to scan forward (default: 1125 = 4.5 years)

        Returns:
            List of blocks in chronological order
        """
        logger.debug(
            f"Forward scan: looking forward {forward_days} days from "
            f"{root_block.started_at}"
        )

        root_date = root_block.started_at
        scan_from = root_date + timedelta(days=1)
        scan_to = root_date + timedelta(days=forward_days)

        # Check if we have data for forward period
        latest_stock_date = max(s.date for s in stocks)
        if scan_from > latest_stock_date:
            logger.warning(
                f"No data available for forward scan: "
                f"need {scan_from}, have {latest_stock_date}"
            )
            return []

        # Adjust scan_to if beyond available data
        actual_scan_to = min(scan_to, latest_stock_date)
        actual_forward_days = (actual_scan_to - root_date).days

        logger.debug(
            f"Adjusted forward period: {actual_forward_days} days "
            f"(requested: {forward_days})"
        )

        # Filter stocks to forward period
        filtered_stocks = self._filter_stocks_by_date(stocks, scan_from, actual_scan_to)

        if not filtered_stocks:
            logger.warning(f"No stock data in forward period {scan_from} to {actual_scan_to}")
            return []

        # Detect all subsequent blocks
        try:
            forward_blocks = self.block_detector.detect_blocks(
                ticker=root_block.ticker,
                stocks=filtered_stocks
            )

            logger.debug(f"Forward scan found {len(forward_blocks)} block(s)")

        except Exception as e:
            logger.error(f"Error in forward detection: {e}", exc_info=True)
            return []

        # Sort by date
        forward_blocks.sort(key=lambda b: b.started_at)

        return forward_blocks

    # ============================================================
    # Phase 4: Support/Resistance Analysis
    # ============================================================

    def _analyze_support_resistance(
        self,
        root_block: DynamicBlockDetection,
        forward_blocks: List[DynamicBlockDetection],
        stocks: List[Stock]
    ) -> Dict[str, Any]:
        """
        Perform support/resistance analysis using Block1 range.

        Uses:
            SupportResistanceAnalyzer.analyze() (implemented in Phase 1)

        Args:
            root_block: Root Block1 (defines support/resistance levels)
            forward_blocks: Blocks detected in forward scan
            stocks: Historical price data

        Returns:
            Analysis result as dictionary (for now)

        TODO: Return SupportResistanceAnalysis object once fully integrated
        """
        logger.debug("Performing support/resistance analysis")

        try:
            analysis = self.sr_analyzer.analyze(
                reference_block=root_block,
                forward_blocks=forward_blocks,
                all_stocks=stocks,
                analysis_period_days=1125  # 4.5 years
            )

            # Convert to dict for now (full integration in future)
            analysis_dict = {
                'level_type': analysis.level.level_type,
                'reference_high': analysis.level.reference_high,
                'reference_low': analysis.level.reference_low,
                'current_price': analysis.level.current_price,
                'distance_pct': analysis.level.distance_pct,
                'retest_count': len(analysis.retests),
                'has_flip': analysis.resistance_to_support_flip is not None,
                'analysis_date': analysis.level.analysis_date.isoformat()
            }

            logger.debug(f"S/R analysis: {analysis_dict['level_type']}")
            return analysis_dict

        except Exception as e:
            logger.error(f"Error in S/R analysis: {e}", exc_info=True)
            return {}

    # ============================================================
    # Helper Methods
    # ============================================================

    def _create_pattern_from_highlight(
        self,
        ticker: str,
        highlight: DynamicBlockDetection
    ) -> HighlightCentricPattern:
        """
        Create a new pattern from highlight block.

        Args:
            ticker: Stock ticker
            highlight: Highlight block

        Returns:
            New HighlightCentricPattern with auto-generated ID
        """
        # Get or initialize sequence for this ticker
        if ticker not in self.pattern_sequence:
            self.pattern_sequence[ticker] = 0

        self.pattern_sequence[ticker] += 1
        sequence = self.pattern_sequence[ticker]

        # Create pattern
        pattern = create_highlight_centric_pattern(
            ticker=ticker,
            highlight_block=highlight,
            sequence=sequence
        )

        logger.debug(f"Created pattern: {pattern.pattern_id}")
        return pattern

    def _filter_stocks_by_date(
        self,
        stocks: List[Stock],
        start_date: date,
        end_date: date
    ) -> List[Stock]:
        """
        Filter stock data by date range.

        Args:
            stocks: Historical price data
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered stock list
        """
        return [
            s for s in stocks
            if start_date <= s.date <= end_date
        ]

    def get_patterns(self) -> List[HighlightCentricPattern]:
        """Get all detected patterns."""
        return self.patterns.copy()

    def get_pattern_count(self) -> int:
        """Get total number of patterns detected."""
        return len(self.patterns)

    def get_patterns_by_status(
        self,
        status: PatternStatus
    ) -> List[HighlightCentricPattern]:
        """Get patterns filtered by status."""
        return [p for p in self.patterns if p.status == status]
