#!/usr/bin/env python3
"""Test Cloudbet API connection."""
import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from config_loader import load_config

async def test_cloudbet():
    """Test Cloudbet API connection using official endpoint."""
    config = load_config()
    api_key = config.apis.cloudbet.api_key
    base_url = config.apis.cloudbet.base_url
    
    print(f"Testing Cloudbet API...")
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print()
    
    # Cloudbet uses X-API-Key header (NOT Bearer token)
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    client = httpx.AsyncClient(timeout=10, headers=headers, follow_redirects=True)
    
    # Step 1: Test sports endpoint (lightweight check)
    print("\n=== Step 1: Testing Sports Endpoint ===")
    try:
        sports_response = await client.get(f"{base_url}/v2/odds/sports")
        print(f"/v2/odds/sports: Status {sports_response.status_code}")
        if sports_response.status_code == 200:
            print("  SUCCESS! API key is valid")
            try:
                data = sports_response.json()
                print(f"  Response type: {type(data)}")
                if isinstance(data, list):
                    print(f"  Sports count: {len(data)}")
                    if len(data) > 0:
                        print(f"  First sport: {data[0]}")
            except:
                print(f"  Response: {sports_response.text[:200]}")
        elif sports_response.status_code == 401:
            print("  ERROR: Authentication failed")
        elif sports_response.status_code == 403:
            print("  ERROR: Permission denied")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Step 2: Test events endpoint with required date parameters
    print("\n=== Step 2: Testing Events Endpoint ===")
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    params = {
        'from': now.isoformat() + 'Z',
        'to': (now + timedelta(days=7)).isoformat() + 'Z'
    }
    
    endpoints = [
        "/v2/odds/events",
        "/v2/odds/sports/politics"  # Try sport-specific if politics exists
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"\nTesting: {url}")
            print("  With params: sport=politics")
            response = await client.get(url, params={"sport": "politics"})
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"  Response keys: {list(data.keys())[:10]}")
                    if 'events' in data:
                        events = data['events']
                        print(f"  Events count: {len(events) if isinstance(events, list) else 'N/A'}")
                        if isinstance(events, list) and len(events) > 0:
                            print(f"  First event keys: {list(events[0].keys())[:10]}")
                            if 'markets' in events[0]:
                                markets = events[0]['markets']
                                print(f"  Markets in first event: {len(markets) if isinstance(markets, list) else 'N/A'}")
                                if isinstance(markets, list) and len(markets) > 0:
                                    print(f"  First market keys: {list(markets[0].keys())[:10]}")
                elif isinstance(data, list):
                    print(f"  Response is list with {len(data)} items")
                    if len(data) > 0:
                        print(f"  First item keys: {list(data[0].keys())[:10]}")
                
                print("\n  SUCCESS! API is working!")
                await client.aclose()
                return True
            else:
                if response.status_code == 401:
                    print("  ERROR: Authentication failed - check API key")
                elif response.status_code == 403:
                    print("  ERROR: Forbidden - check API key permissions")
                elif response.status_code == 301 or response.status_code == 302:
                    print(f"  WARNING: Redirect detected. Location: {response.headers.get('Location', 'N/A')}")
                else:
                    print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
    
    await client.aclose()
    print("\nNo working endpoint found.")
    return False

if __name__ == "__main__":
    asyncio.run(test_cloudbet())

