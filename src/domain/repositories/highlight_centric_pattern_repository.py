"""
Highlight-Centric Pattern Repository Interface

Domain layer repository interface for highlight-centric patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

if __name__ != "__main__":
    from src.domain.entities.patterns import HighlightCentricPattern, PatternStatus


class HighlightCentricPatternRepository(ABC):
    """
    Repository interface for highlight-centric patterns.

    This interface defines the contract for persisting and retrieving
    highlight-centric patterns. Infrastructure layer implements this.
    """

    @abstractmethod
    def save(self, pattern: 'HighlightCentricPattern') -> None:
        """
        Save or update a highlight-centric pattern.

        Args:
            pattern: Pattern to save

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def save_all(self, patterns: List['HighlightCentricPattern']) -> None:
        """
        Save or update multiple patterns (batch operation).

        Args:
            patterns: List of patterns to save

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def find_by_id(self, pattern_id: str) -> Optional['HighlightCentricPattern']:
        """
        Find pattern by pattern_id.

        Args:
            pattern_id: Pattern identifier (e.g., "HIGHLIGHT_025980_20200414_001")

        Returns:
            Pattern if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_ticker(
        self,
        ticker: str,
        status: Optional[PatternStatus] = None
    ) -> List['HighlightCentricPattern']:
        """
        Find all patterns for a ticker.

        Args:
            ticker: Stock ticker
            status: Optional status filter (None = all statuses)

        Returns:
            List of patterns (may be empty)
        """
        pass

    @abstractmethod
    def find_by_date_range(
        self,
        ticker: str,
        from_date: date,
        to_date: date
    ) -> List['HighlightCentricPattern']:
        """
        Find patterns within a date range.

        Args:
            ticker: Stock ticker
            from_date: Start date (inclusive)
            to_date: End date (inclusive)

        Returns:
            List of patterns (may be empty)
        """
        pass

    @abstractmethod
    def find_all(
        self,
        status: Optional[PatternStatus] = None,
        limit: Optional[int] = None
    ) -> List['HighlightCentricPattern']:
        """
        Find all patterns (with optional filters).

        Args:
            status: Optional status filter
            limit: Optional limit on number of results

        Returns:
            List of patterns (may be empty)
        """
        pass

    @abstractmethod
    def count_by_ticker(
        self,
        ticker: str,
        status: Optional[PatternStatus] = None
    ) -> int:
        """
        Count patterns for a ticker.

        Args:
            ticker: Stock ticker
            status: Optional status filter

        Returns:
            Number of patterns
        """
        pass

    @abstractmethod
    def delete(self, pattern_id: str) -> bool:
        """
        Delete a pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        pass

    @abstractmethod
    def exists(self, pattern_id: str) -> bool:
        """
        Check if pattern exists.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if exists, False otherwise
        """
        pass
