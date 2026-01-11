#!/usr/bin/env python3
"""Test Polymarket API connection."""
import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.config_loader import load_config
from src.polymarket_client import PolymarketClient

async def test_polymarket():
    """Test Polymarket API connection."""
    config = load_config()
    
    print("Testing Polymarket API...")
    print(f"Base URL: {config.apis.polymarket.base_url}")
    print()
    
    client = PolymarketClient(
        base_url=config.apis.polymarket.base_url,
        timeout=10,
        retry_attempts=2,
        retry_delay=1,
        debug_api=True
    )
    
    try:
        print("Fetching markets...")
        markets = await client.get_markets()
        
        if markets:
            print(f"\nSUCCESS! Fetched {len(markets)} markets")
            print(f"\nFirst market example:")
            if len(markets) > 0:
                first = markets[0]
                print(f"  Name: {first.get('name', 'N/A')}")
                print(f"  Outcomes: {len(first.get('outcomes', []))}")
                print(f"  URL: {first.get('url', 'N/A')}")
            return True
        else:
            print("\nWARNING: No markets returned")
            print("This could mean:")
            print("  - API endpoint needs adjustment")
            print("  - No active markets available")
            print("  - API response format differs")
            return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    success = asyncio.run(test_polymarket())
    sys.exit(0 if success else 1)

