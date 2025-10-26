#!/usr/bin/env python
"""
Pattern Tree Structure Viewer

Display detected patterns in a beautiful tree format with colors and structure
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# ANSI Color Codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


# Tree drawing characters (ASCII-safe)
TREE_BRANCH = "|-- "
TREE_LAST = "`-- "
TREE_VERTICAL = "|   "
TREE_SPACE = "    "


def get_status_color(status):
    """Get color for pattern status"""
    status_colors = {
        'active': Colors.BRIGHT_YELLOW,
        'completed': Colors.BRIGHT_BLUE,
        'archived': Colors.BRIGHT_GREEN,
        'failed': Colors.BRIGHT_RED
    }
    return status_colors.get(status.lower(), Colors.WHITE)


def get_block_icon(block_type):
    """Get icon for block type"""
    icons = {
        1: "[B1]",  # Block1
        2: "[B2]",  # Block2
        3: "[B3]",  # Block3
        4: "[B4]",  # Block4
        5: "[B5]",  # Block5
        6: "[B6]",  # Block6
    }
    return icons.get(block_type, "[B?]")


def show_pattern_tree(ticker: str, db_path: str = "data/database/stock_data.db", limit: int = None):
    """
    Show pattern tree structure for a ticker with beautiful formatting

    Args:
        ticker: Ticker code
        db_path: Database path
        limit: Maximum number of patterns to display (None = all)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get patterns
    query = """
        SELECT
            pattern_name,
            detection_date,
            status,
            block_features
        FROM seed_pattern
        WHERE ticker = ?
        ORDER BY detection_date
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, (ticker,))
    patterns = cursor.fetchall()

    conn.close()

    if not patterns:
        print(f"\n{Colors.BRIGHT_RED}No patterns found for ticker '{ticker}'{Colors.RESET}\n")
        return

    # Header
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'=' * 75}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}          Pattern Tree Structure - {ticker}                          {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'=' * 75}{Colors.RESET}\n")

    # Summary
    status_counts = {}
    for _, _, status, _ in patterns:
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"{Colors.BOLD}Summary:{Colors.RESET}")
    print(f"   Total Patterns: {Colors.BRIGHT_YELLOW}{len(patterns)}{Colors.RESET}")

    status_parts = []
    for status, count in status_counts.items():
        color = get_status_color(status)
        status_parts.append(f"{color}{status.upper()}: {count}{Colors.RESET}")
    print(f"   {', '.join(status_parts)}\n")

    print(f"{Colors.BOLD}{'-' * 75}{Colors.RESET}")
    print()

    # Pattern Details
    for i, (pattern_name, detection_date, status, block_features_json) in enumerate(patterns, 1):
        blocks = json.loads(block_features_json)

        # Pattern header
        status_color = get_status_color(status)
        print(f"{Colors.BOLD}[Pattern #{i}]{Colors.RESET} {Colors.BRIGHT_WHITE}{pattern_name}{Colors.RESET}")
        print(f"   Date: {Colors.CYAN}{detection_date}{Colors.RESET}")
        print(f"   Status: {status_color}{status.upper()}{Colors.RESET}")
        print(f"   Blocks: {Colors.BRIGHT_MAGENTA}{len(blocks)}{Colors.RESET}")
        print()

        # Block tree - 날짜만 표시
        if blocks:
            # Group blocks by condition_name if available
            seed_blocks = []
            redetection_blocks = {}

            for block in blocks:
                condition = block.get('metadata', {}).get('condition_name', 'seed')
                if condition == 'seed':
                    seed_blocks.append(block)
                else:
                    # Redetection blocks grouped by parent
                    parent_id = block.get('metadata', {}).get('parent_block_id', 'unknown')
                    if parent_id not in redetection_blocks:
                        redetection_blocks[parent_id] = []
                    redetection_blocks[parent_id].append(block)

            # If no condition_name, treat all as seed blocks
            if not seed_blocks and not redetection_blocks:
                seed_blocks = blocks

            # Display seed blocks
            for block_idx, block in enumerate(seed_blocks):
                is_last_seed = block_idx == len(seed_blocks) - 1
                has_redetections = block.get('block_id', '') in redetection_blocks
                is_really_last = is_last_seed and not has_redetections

                # Tree prefix
                if block_idx == 0:
                    prefix = "   "
                    tree_char = TREE_LAST if len(seed_blocks) == 1 and not has_redetections else TREE_BRANCH
                else:
                    prefix = "   "
                    tree_char = TREE_LAST if is_really_last else TREE_BRANCH

                # Block info
                block_id = block.get('block_id', 'unknown')
                block_type = block.get('block_type', 0)
                started_at = block.get('started_at', 'N/A')
                ended_at = block.get('ended_at', 'N/A')
                duration = block.get('duration_candles', 0)

                # Block type color
                block_colors = {
                    1: Colors.BRIGHT_GREEN,
                    2: Colors.BRIGHT_BLUE,
                    3: Colors.BRIGHT_MAGENTA,
                    4: Colors.BRIGHT_YELLOW,
                    5: Colors.BRIGHT_RED,
                    6: Colors.BRIGHT_CYAN,
                }
                block_color = block_colors.get(block_type, Colors.WHITE)

                # Icon and block name
                icon = get_block_icon(block_type)
                print(f"{prefix}{tree_char}{icon} {block_color}{Colors.BOLD}{block_id.upper()}{Colors.RESET} {Colors.DIM}{started_at} -> {ended_at} ({duration} days){Colors.RESET}")

                # Show redetection blocks for this seed block
                if has_redetections:
                    redet_list = redetection_blocks[block_id]
                    detail_prefix = prefix + (TREE_SPACE if is_last_seed else TREE_VERTICAL)

                    for redet_idx, redet_block in enumerate(redet_list):
                        is_last_redet = redet_idx == len(redet_list) - 1
                        redet_tree_char = TREE_LAST if is_last_redet else TREE_BRANCH

                        redet_started = redet_block.get('started_at', 'N/A')
                        redet_ended = redet_block.get('ended_at', 'N/A')
                        redet_duration = redet_block.get('duration_candles', 0)

                        # Redetection shown with lighter color
                        print(f"{detail_prefix}{redet_tree_char}{Colors.BRIGHT_BLACK}[RE]{Colors.RESET} {Colors.DIM}{redet_started} -> {redet_ended} ({redet_duration} days){Colors.RESET}")

        # Separator
        if i < len(patterns):
            print(f"\n{Colors.DIM}{'-' * 75}{Colors.RESET}\n")


def show_summary(ticker: str, db_path: str = "data/database/stock_data.db"):
    """
    Show summary statistics with beautiful formatting

    Args:
        ticker: Ticker code
        db_path: Database path
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Pattern count by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM seed_pattern
        WHERE ticker = ?
        GROUP BY status
    """, (ticker,))

    status_counts = cursor.fetchall()

    # Total blocks
    cursor.execute("""
        SELECT SUM(json_array_length(block_features)) as total_blocks
        FROM seed_pattern
        WHERE ticker = ?
    """, (ticker,))

    total_blocks = cursor.fetchone()[0] or 0

    # Block distribution
    cursor.execute("""
        SELECT
            json_array_length(block_features) as block_count,
            COUNT(*) as pattern_count
        FROM seed_pattern
        WHERE ticker = ?
        GROUP BY block_count
        ORDER BY block_count
    """, (ticker,))

    block_distribution = cursor.fetchall()

    conn.close()

    # Display summary
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'=' * 75}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}                    Summary Statistics                                 {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'=' * 75}{Colors.RESET}\n")

    print(f"{Colors.BOLD}Ticker:{Colors.RESET} {Colors.BRIGHT_WHITE}{ticker}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Pattern Status Distribution:{Colors.RESET}")
    for status, count in status_counts:
        color = get_status_color(status)
        bar_length = min(count, 50)  # Max bar length 50
        bar = "#" * bar_length
        print(f"   {color}{status.upper():<12}{Colors.RESET} {color}{bar}{Colors.RESET} {Colors.BRIGHT_WHITE}{count}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Total Blocks:{Colors.RESET} {Colors.BRIGHT_YELLOW}{total_blocks}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Block Distribution:{Colors.RESET}")
    max_count = max([count for _, count in block_distribution], default=1)
    for block_count, pattern_count in block_distribution:
        bar_length = int((pattern_count / max_count) * 30)  # Max bar length 30
        bar = "=" * bar_length
        print(f"   {Colors.BRIGHT_CYAN}{block_count} block(s):{Colors.RESET} {Colors.BRIGHT_GREEN}{bar}{Colors.RESET} {Colors.BRIGHT_WHITE}{pattern_count} patterns{Colors.RESET}")

    print()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Display pattern tree structure with beautiful formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="Ticker code (e.g., 025980)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="data/database/stock_data.db",
        help="Database file path (default: data/database/stock_data.db)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of patterns to display (default: all)"
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show summary statistics only"
    )

    args = parser.parse_args()

    # Validate database exists
    if not Path(args.db).exists():
        print(f"{Colors.BRIGHT_RED}ERROR: Database file not found: {args.db}{Colors.RESET}")
        sys.exit(1)

    try:
        if args.summary_only:
            show_summary(args.ticker, args.db)
        else:
            show_pattern_tree(args.ticker, args.db, args.limit)
            show_summary(args.ticker, args.db)

    except Exception as e:
        print(f"\n{Colors.BRIGHT_RED}ERROR: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
