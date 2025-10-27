"""
Highlight-Centric Pattern - Domain Aggregate Root

Represents a pattern discovered via highlight-centric detection approach.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

if __name__ != "__main__":
    from src.domain.entities.detections import DynamicBlockDetection
    from src.domain.entities.patterns.backward_scan_result import BackwardScanResult
    from src.domain.entities.patterns.pattern_status import PatternStatus


@dataclass
class HighlightCentricPattern:
    """
    Pattern discovered via highlight-centric detection.

    Key Characteristics:
    - Always anchored to a highlight (block with 2+ forward spots)
    - May have a different root block (found via backward scan)
    - Tracks long-term evolution (up to 1125 days forward)
    - Includes support/resistance analysis

    Lifecycle:
    1. Created when highlight detected
    2. Backward scan may adjust root block
    3. Forward scan populates forward_blocks
    4. Completed when forward scan ends or pattern fails

    Invariants:
    - pattern_id format: HIGHLIGHT_{TICKER}_{YYYYMMDD}_{SEQUENCE}
    - highlight_block must have 2+ spots
    - root_block must be Block1 type
    - If backward_scan_result.found_stronger_root, root_block != highlight_block
    """

    # Identity
    pattern_id: str
    ticker: str

    # Core blocks (Aggregate Root owns these)
    highlight_block: 'DynamicBlockDetection'
    root_block: 'DynamicBlockDetection'

    # Detection results
    backward_scan_result: Optional[BackwardScanResult] = None
    forward_blocks: List['DynamicBlockDetection'] = field(default_factory=list)

    # Analysis (from SupportResistanceAnalyzer)
    sr_analysis: Optional[dict] = None  # Will use SupportResistanceAnalysis once implemented

    # Lifecycle
    status: PatternStatus = PatternStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate invariants."""
        # Validate pattern_id format
        if not self.pattern_id.startswith('HIGHLIGHT_'):
            raise ValueError(
                f"pattern_id must start with 'HIGHLIGHT_', got {self.pattern_id}"
            )

        # Validate highlight_block has metadata
        if not hasattr(self.highlight_block, 'metadata'):
            raise ValueError("highlight_block must have metadata attribute")

        # Validate root_block is Block1
        if self.root_block.block_type != 1:
            raise ValueError(
                f"root_block must be Block1 (type=1), got type={self.root_block.block_type}"
            )

        # Validate backward_scan_result consistency
        if self.backward_scan_result and self.backward_scan_result.found_stronger_root:
            if self.root_block.id == self.highlight_block.id:
                raise ValueError(
                    "If backward scan found stronger root, root_block should differ from highlight_block"
                )

    # ============================================================
    # Query Methods
    # ============================================================

    def is_highlight_root(self) -> bool:
        """
        Check if the highlight block is also the root block.

        Returns:
            True if highlight is the root (no stronger block found backward)
        """
        return self.highlight_block.id == self.root_block.id

    def has_backward_scan(self) -> bool:
        """Check if backward scan was performed."""
        return self.backward_scan_result is not None

    def has_forward_blocks(self) -> bool:
        """Check if forward blocks were detected."""
        return len(self.forward_blocks) > 0

    def has_sr_analysis(self) -> bool:
        """Check if support/resistance analysis was performed."""
        return self.sr_analysis is not None

    def get_all_blocks(self) -> List['DynamicBlockDetection']:
        """
        Get all blocks in chronological order.

        Returns:
            List starting with root_block, followed by forward_blocks
        """
        return [self.root_block] + self.forward_blocks

    def get_block_count(self) -> int:
        """Get total number of blocks in pattern."""
        return 1 + len(self.forward_blocks)  # root + forward blocks

    def get_pattern_duration_days(self) -> int:
        """
        Calculate pattern duration from root to last forward block.

        Returns:
            Number of days from root start to last block end, 0 if no forward blocks
        """
        if not self.forward_blocks:
            return 0

        last_block = self.forward_blocks[-1]
        if last_block.ended_at is None:
            return 0

        return (last_block.ended_at - self.root_block.started_at).days

    def get_highlight_spot_count(self) -> int:
        """
        Get the number of spots in the highlight block.

        Returns:
            Spot count from highlight_block metadata, 0 if not available
        """
        if not hasattr(self.highlight_block, 'custom_metadata'):
            return 0

        metadata = self.highlight_block.custom_metadata or {}
        return metadata.get('spot_count', 0)

    # ============================================================
    # Command Methods
    # ============================================================

    def add_forward_block(self, block: 'DynamicBlockDetection') -> None:
        """
        Add a block detected in forward scan.

        Args:
            block: Block to add

        Raises:
            ValueError: If block date is before root block or pattern is completed
        """
        if self.status == PatternStatus.COMPLETED:
            raise ValueError("Cannot add blocks to completed pattern")

        if block.started_at < self.root_block.started_at:
            raise ValueError(
                f"Forward block date ({block.started_at}) must be after "
                f"root block date ({self.root_block.started_at})"
            )

        # Add block in chronological order
        self.forward_blocks.append(block)
        self.forward_blocks.sort(key=lambda b: b.started_at)

    def set_backward_scan_result(self, result: BackwardScanResult) -> None:
        """
        Set the backward scan result and adjust root if needed.

        Args:
            result: Backward scan result

        Raises:
            ValueError: If pattern already has backward scan result
        """
        if self.backward_scan_result is not None:
            raise ValueError("Pattern already has backward scan result")

        self.backward_scan_result = result

        # If stronger root found, update root_block
        if result.found_stronger_root:
            self.root_block = result.stronger_block

    def set_sr_analysis(self, analysis: dict) -> None:
        """
        Set support/resistance analysis result.

        Args:
            analysis: S/R analysis result (dict format for now)

        Raises:
            ValueError: If pattern is not active
        """
        if self.status != PatternStatus.ACTIVE:
            raise ValueError("Can only set S/R analysis on active patterns")

        self.sr_analysis = analysis

    def complete(self) -> None:
        """
        Mark pattern as completed.

        Raises:
            ValueError: If pattern is already completed or archived
        """
        if self.status == PatternStatus.COMPLETED:
            raise ValueError("Pattern is already completed")

        if self.status == PatternStatus.ARCHIVED:
            raise ValueError("Cannot complete archived pattern")

        self.status = PatternStatus.COMPLETED
        self.completed_at = datetime.now()

    def archive(self) -> None:
        """
        Archive the pattern.

        Can archive from any status (ACTIVE or COMPLETED).
        """
        self.status = PatternStatus.ARCHIVED

    # ============================================================
    # Serialization
    # ============================================================

    def to_summary_dict(self) -> dict:
        """
        Convert to summary dictionary for display/logging.

        Returns:
            Dictionary with pattern summary
        """
        return {
            'pattern_id': self.pattern_id,
            'ticker': self.ticker,
            'status': self.status.value,
            'is_highlight_root': self.is_highlight_root(),
            'root_block_date': self.root_block.started_at.isoformat(),
            'highlight_block_date': self.highlight_block.started_at.isoformat(),
            'highlight_spot_count': self.get_highlight_spot_count(),
            'block_count': self.get_block_count(),
            'pattern_duration_days': self.get_pattern_duration_days(),
            'has_backward_scan': self.has_backward_scan(),
            'has_sr_analysis': self.has_sr_analysis(),
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        duration = self.get_pattern_duration_days()
        blocks = self.get_block_count()
        root_type = "highlight" if self.is_highlight_root() else "stronger"

        return (
            f"HighlightCentricPattern("
            f"id={self.pattern_id}, "
            f"ticker={self.ticker}, "
            f"status={self.status.value}, "
            f"root_type={root_type}, "
            f"blocks={blocks}, "
            f"duration={duration}d)"
        )


# ============================================================
# Factory Functions
# ============================================================

def create_highlight_centric_pattern(
    ticker: str,
    highlight_block: 'DynamicBlockDetection',
    sequence: int = 1
) -> HighlightCentricPattern:
    """
    Factory function to create a new highlight-centric pattern.

    Args:
        ticker: Stock ticker
        highlight_block: The highlight block (2+ spots)
        sequence: Sequence number for pattern_id (default: 1)

    Returns:
        New HighlightCentricPattern with auto-generated pattern_id

    Raises:
        ValueError: If highlight_block doesn't have required metadata
    """
    # Generate pattern_id: HIGHLIGHT_{TICKER}_{YYYYMMDD}_{SEQUENCE}
    date_str = highlight_block.started_at.strftime('%Y%m%d')
    pattern_id = f"HIGHLIGHT_{ticker}_{date_str}_{sequence:03d}"

    # Initially, root_block = highlight_block (may be adjusted by backward scan)
    return HighlightCentricPattern(
        pattern_id=pattern_id,
        ticker=ticker,
        highlight_block=highlight_block,
        root_block=highlight_block,  # Will be adjusted if backward scan finds stronger
        status=PatternStatus.ACTIVE,
        created_at=datetime.now()
    )
