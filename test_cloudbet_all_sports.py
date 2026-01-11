#!/usr/bin/env python3
"""Test Cloudbet with all sports to find active events."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_config
from src.cloudbet_client import CloudbetClient

async def test_all_sports():
    """Test all Cloudbet sports to find active events."""
    print("Testing all Cloudbet sports for active events...\n")
    
    config = load_config()
    client = CloudbetClient(
        api_key=config.apis.cloudbet.api_key,
        base_url=config.apis.cloudbet.base_url,
        debug_api=False
    )
    
    try:
        # Get all sports
        import httpx
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        future = now + timedelta(days=365)
        from_ms = int(now.timestamp() * 1000)
        to_ms = int(future.timestamp() * 1000)
        
        headers = {
            "X-API-Key": config.apis.cloudbet.api_key,
            "Accept": "application/json"
        }
        
        # Get sports list
        async with httpx.AsyncClient(timeout=10, headers=headers) as http_client:
            sports_response = await http_client.get(f"{config.apis.cloudbet.base_url}/v2/odds/sports")
            if sports_response.status_code == 200:
                sports_data = sports_response.json()
                sports = sports_data.get('sports', [])
                print(f"Found {len(sports)} sports\n")
                
                # Test first 10 sports
                for sport in sports[:10]:
                    sport_key = sport.get('key') or sport.get('name')
                    if not sport_key:
                        continue
                    
                    print(f"Testing: {sport_key}...", end=" ")
                    url = f"{config.apis.cloudbet.base_url}/v2/odds/events"
                    params = {
                        'sport': sport_key,
                        'from': str(from_ms),
                        'to': str(to_ms)
                    }
                    
                    response = await http_client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        competitions = data.get('competitions', [])
                        total_events = sum(len(c.get('events', [])) for c in competitions if isinstance(c, dict))
                        print(f"✅ {total_events} events in {len(competitions)} competitions")
                        
                        if total_events > 0:
                            # Show sample
                            for comp in competitions:
                                events = comp.get('events', [])
                                if events:
                                    print(f"   Sample event: {events[0].get('name', 'N/A')[:50]}")
                                    break
                    else:
                        print(f"❌ Status {response.status_code}")
                    
                    await asyncio.sleep(0.2)  # Rate limiting
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_all_sports())

