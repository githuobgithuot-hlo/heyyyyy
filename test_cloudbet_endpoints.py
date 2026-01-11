#!/usr/bin/env python3
"""Test Cloudbet API with X-API-Key header and multiple endpoints."""
import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from config_loader import load_config

async def test_endpoints():
    """Test various Cloudbet API endpoints."""
    config = load_config()
    api_key = config.apis.cloudbet.api_key
    base_url = config.apis.cloudbet.base_url
    
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    client = httpx.AsyncClient(timeout=10, headers=headers, follow_redirects=True)
    
    # Additional endpoints to try
    endpoints = [
        "/sports",
        "/events",
        "/markets",
        "/odds",
        "/v1/events",
        "/v1/odds/events",
        "/v1/sports",
        "/feed/events",
        "/feed/odds/events"
    ]
    
    print(f"Testing Cloudbet API endpoints with X-API-Key header...")
    print(f"Base URL: {base_url}\n")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = await client.get(url)
            print(f"{endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  SUCCESS! Response type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"  Keys: {list(data.keys())[:5]}")
                    elif isinstance(data, list):
                        print(f"  List with {len(data)} items")
                except:
                    print(f"  Response (first 200 chars): {response.text[:200]}")
            elif response.status_code == 401:
                print(f"  Authentication issue")
            elif response.status_code == 403:
                print(f"  Permission issue")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_endpoints())

