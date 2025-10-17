"""
TUI Workers - Background task execution for TUI
Handles data collection with progress callbacks
"""

from threading import Thread, Event
from typing import List, Callable, Optional
from datetime import date, datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class CollectionWorker(Thread):
    """Background worker for stock data collection"""

    def __init__(
        self,
        tickers: List[str],
        from_date: date,
        to_date: date,
        on_progress: Callable[[str, int, int, int], None],
        on_complete: Callable[[dict], None],
        on_error: Callable[[str], None],
        collect_price: bool = True,
        collect_investor: bool = True,
    ):
        """
        Initialize collection worker

        Args:
            tickers: List of ticker codes
            from_date: Start date
            to_date: End date
            on_progress: Callback for progress updates (ticker, current, total, records)
            on_complete: Callback for completion (stats dict)
            on_error: Callback for errors (error message)
            collect_price: Collect price data
            collect_investor: Collect investor data
        """
        super().__init__(daemon=True)
        self.tickers = tickers
        self.from_date = from_date
        self.to_date = to_date
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self.collect_price = collect_price
        self.collect_investor = collect_investor

        self._stop_event = Event()
        self._pause_event = Event()
        self._pause_event.set()  # Start unpaused

    def run(self) -> None:
        """Execute collection in background"""
        try:
            from src.infrastructure.database.connection import DatabaseConnection
            from src.infrastructure.collectors.bulk_collector import BulkCollector

            # Initialize database and collector
            db_path = "data/database/stock_data.db"
            db_conn = DatabaseConnection(db_path)
            collector = BulkCollector(db_conn, delay=0.2, use_hybrid=True)

            # Track stats
            total_tickers = len(self.tickers)
            completed = 0
            total_records = 0
            failed = 0

            # Collect each ticker
            for idx, ticker in enumerate(self.tickers, 1):
                # Check if stopped
                if self._stop_event.is_set():
                    self.on_error("Collection cancelled by user")
                    return

                # Wait if paused
                self._pause_event.wait()

                # Send progress update
                self.on_progress(ticker, idx, total_tickers, total_records)

                try:
                    # Collect price data
                    if self.collect_price:
                        result = collector.price_collector.collect(
                            ticker, self.from_date, self.to_date
                        )
                        if result.success:
                            total_records += result.record_count
                        else:
                            failed += 1

                    # Collect investor data
                    if self.collect_investor:
                        result = collector.investor_collector.collect(
                            ticker, self.from_date, self.to_date
                        )
                        if result.success:
                            total_records += result.record_count
                        else:
                            failed += 1

                    completed += 1

                except Exception as e:
                    failed += 1
                    # Continue with next ticker even if one fails
                    continue

            # Send completion stats
            stats = {
                "total_tickers": total_tickers,
                "completed": completed,
                "failed": failed,
                "total_records": total_records,
            }
            self.on_complete(stats)

        except Exception as e:
            self.on_error(f"Collection failed: {str(e)}")

    def stop(self) -> None:
        """Stop the collection"""
        self._stop_event.set()
        self._pause_event.set()  # Unpause to allow stopping

    def pause(self) -> None:
        """Pause the collection"""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume the collection"""
        self._pause_event.set()

    def is_paused(self) -> bool:
        """Check if paused"""
        return not self._pause_event.is_set()
