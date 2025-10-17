#!/usr/bin/env python
"""
POTALE Stock Data Collector - TUI Main Entry Point

Interactive Terminal User Interface (TUI) powered by Textual
Claude Code style modern terminal interface

Usage:
    python main.py

Features:
    - Interactive menu navigation
    - Collect all stocks or specific tickers
    - Data validation
    - Analysis summary
    - Settings management

Controls:
    - Arrow keys or numbers to navigate
    - Enter to select
    - ESC to go back
    - Q to quit
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.tui_app import run_tui

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  POTALE Stock Data Collector - TUI")
    print("  Interactive Terminal User Interface")
    print("="*60 + "\n")

    try:
        run_tui()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nFor CLI usage, use: python potale.py --help")
