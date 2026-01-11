#!/usr/bin/env python3
"""Diagnostic test to see raw API responses."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_config
from src.polymarket_client import PolymarketClient
from src.cloudbet_client import CloudbetClient

async def test_polymarket_raw():
    """Test Polymarket API and show raw response."""
    print("\n" + "="*60)
    print("POLYMARKET RAW RESPONSE")
    print("="*60)
    
    config = load_config()
    client = PolymarketClient(
        base_url=config.apis.polymarket.base_url,
        debug_api=True
    )
    
    try:
        import httpx
        url = f"{config.apis.polymarket.base_url}/markets"
        params = {"active": "true", "limit": 5}
        
        async with httpx.AsyncClient(timeout=10) as http_client:
            response = await http_client.get(url, params=params)
            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nResponse type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    print(f"\nFirst 1000 chars of response:")
                    print(json.dumps(data, indent=2)[:1000])
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
                    if len(data) > 0:
                        print(f"\nFirst item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                        print(f"\nFirst item sample:")
                        print(json.dumps(data[0], indent=2)[:500])
            else:
                print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

async def test_cloudbet_raw():
    """Test Cloudbet API and show raw response."""
    print("\n" + "="*60)
    print("CLOUDBET RAW RESPONSE")
    print("="*60)
    
    config = load_config()
    
    try:
        import httpx
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        future = now + timedelta(days=365)
        from_ms = int(now.timestamp() * 1000)
        to_ms = int(future.timestamp() * 1000)
        
        url = f"{config.apis.cloudbet.base_url}/v2/odds/events"
        params = {
            'sport': 'politics',
            'from': str(from_ms),
            'to': str(to_ms)
        }
        
        headers = {
            "X-API-Key": config.apis.cloudbet.api_key,
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10, headers=headers) as http_client:
            response = await http_client.get(url, params=params)
            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\nResponse type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    print(f"\nFirst 2000 chars of response:")
                    print(json.dumps(data, indent=2)[:2000])
                    
                    # Check competitions structure
                    if 'competitions' in data:
                        comps = data['competitions']
                        print(f"\nCompetitions type: {type(comps)}, length: {len(comps) if isinstance(comps, list) else 'N/A'}")
                        if isinstance(comps, list) and len(comps) > 0:
                            print(f"First competition keys: {list(comps[0].keys())}")
                            if 'events' in comps[0]:
                                events = comps[0]['events']
                                print(f"Events in first competition: {len(events) if isinstance(events, list) else 'N/A'}")
                else:
                    print(f"Response: {str(data)[:500]}")
            else:
                print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_polymarket_raw()
    await test_cloudbet_raw()

if __name__ == "__main__":
    asyncio.run(main())

