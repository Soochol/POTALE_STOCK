#!/usr/bin/env python
"""
POTALE Stock Data Collector
Professional CLI for Korean stock market data collection

Usage:
    python potale.py [COMMAND] [OPTIONS]

Examples:
    python potale.py collect stocks --all --from 2020-01-01
    python potale.py validate all
    python potale.py analyze summary
    python potale.py --help
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.app import app

if __name__ == "__main__":
    app()
