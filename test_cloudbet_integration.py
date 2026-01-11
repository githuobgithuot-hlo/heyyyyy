#!/usr/bin/env python3
"""Test Cloudbet client integration."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cloudbet_client import CloudbetClient
from src.config_loader import load_config

async def test():
    """Test Cloudbet client."""
    config = load_config()
    client = CloudbetClient(
        api_key=config.apis.cloudbet.api_key,
        base_url=config.apis.cloudbet.base_url,
        debug_api=True
    )
    
    print("Testing Cloudbet client...")
    print(f"Base URL: {config.apis.cloudbet.base_url}")
    
    # Test with politics sport
    markets = await client.get_markets(sport='politics')
    print(f"\nFetched {len(markets)} outcomes from politics")
    
    if markets:
        print(f"\nFirst outcome sample:")
        for key, value in list(markets[0].items())[:5]:
            print(f"  {key}: {value}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test())

