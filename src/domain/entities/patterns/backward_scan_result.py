"""
Backward Scan Result - Domain Entity

Represents the result of scanning backward from a highlight to find stronger root Block1.
"""

from dataclasses import dataclass
from typing import Optional

if __name__ != "__main__":
    from src.domain.entities.detections import DynamicBlockDetection


@dataclass(frozen=True)
class BackwardScanResult:
    """
    Result of backward scanning for a stronger root Block1.

    When a highlight is detected, we scan backward (typically 30 days) to check if
    there's a stronger Block1 that should be the true root of the pattern.

    Example:
        Highlight at Day 50 (peak: 10,000)
        Backward scan finds Block1 at Day 30 (peak: 12,000)
        → Use Day 30 Block1 as root, highlight becomes secondary block

    Attributes:
        found_stronger_root: Whether a stronger Block1 was found
        stronger_block: The stronger Block1 if found (None if not found)
        peak_price_ratio: Ratio of stronger_peak / highlight_peak (>1.0 if stronger found)
        lookback_days: Number of days scanned backward (default: 30)
    """

    found_stronger_root: bool
    stronger_block: Optional['DynamicBlockDetection'] = None
    peak_price_ratio: float = 1.0
    lookback_days: int = 30

    def __post_init__(self):
        """Validate invariants."""
        # If stronger root found, must have stronger_block
        if self.found_stronger_root and self.stronger_block is None:
            raise ValueError(
                "found_stronger_root=True requires stronger_block to be provided"
            )

        # If stronger root found, ratio must be > 1.0
        if self.found_stronger_root and self.peak_price_ratio <= 1.0:
            raise ValueError(
                f"found_stronger_root=True requires peak_price_ratio > 1.0, got {self.peak_price_ratio}"
            )

        # If no stronger root, should not have stronger_block
        if not self.found_stronger_root and self.stronger_block is not None:
            raise ValueError(
                "found_stronger_root=False should not have stronger_block"
            )

        # Lookback days must be positive
        if self.lookback_days <= 0:
            raise ValueError(
                f"lookback_days must be positive, got {self.lookback_days}"
            )

    @classmethod
    def no_stronger_root(cls, lookback_days: int = 30) -> 'BackwardScanResult':
        """
        Factory method for when no stronger root is found.

        Args:
            lookback_days: Number of days scanned

        Returns:
            BackwardScanResult with found_stronger_root=False
        """
        return cls(
            found_stronger_root=False,
            stronger_block=None,
            peak_price_ratio=1.0,
            lookback_days=lookback_days
        )

    @classmethod
    def with_stronger_root(
        cls,
        stronger_block: 'DynamicBlockDetection',
        highlight_peak_price: float,
        lookback_days: int = 30
    ) -> 'BackwardScanResult':
        """
        Factory method for when a stronger root is found.

        Args:
            stronger_block: The stronger Block1 found
            highlight_peak_price: Peak price of the original highlight
            lookback_days: Number of days scanned

        Returns:
            BackwardScanResult with found_stronger_root=True

        Raises:
            ValueError: If stronger_block peak is not higher than highlight peak
        """
        if stronger_block.peak_price <= highlight_peak_price:
            raise ValueError(
                f"stronger_block peak ({stronger_block.peak_price}) must be higher "
                f"than highlight peak ({highlight_peak_price})"
            )

        ratio = stronger_block.peak_price / highlight_peak_price

        return cls(
            found_stronger_root=True,
            stronger_block=stronger_block,
            peak_price_ratio=ratio,
            lookback_days=lookback_days
        )

    def get_root_block(
        self,
        highlight_block: 'DynamicBlockDetection'
    ) -> 'DynamicBlockDetection':
        """
        Get the root block based on scan result.

        Args:
            highlight_block: The original highlight block

        Returns:
            stronger_block if found, otherwise highlight_block
        """
        if self.found_stronger_root:
            return self.stronger_block
        return highlight_block

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'found_stronger_root': self.found_stronger_root,
            'stronger_block_id': self.stronger_block.id if self.stronger_block else None,
            'peak_price_ratio': self.peak_price_ratio,
            'lookback_days': self.lookback_days
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.found_stronger_root:
            return (
                f"BackwardScanResult(found_stronger_root=True, "
                f"ratio={self.peak_price_ratio:.2f}x, "
                f"lookback={self.lookback_days}d)"
            )
        return f"BackwardScanResult(no_stronger_root, lookback={self.lookback_days}d)"
