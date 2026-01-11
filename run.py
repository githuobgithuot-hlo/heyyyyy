#!/usr/bin/env python3
"""
Quick start script for the arbitrage bot.
"""
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import main

if __name__ == "__main__":
    asyncio.run(main())

