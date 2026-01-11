"""Check /sports and /events endpoints for games."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("CHECKING /sports AND /events ENDPOINTS")
    print("=" * 80)
    
    # Check /sports endpoint
    print("\n" + "="*80)
    print("1. /sports ENDPOINT")
    print("="*80)
    
    sports_response = await fetcher._make_request("/sports", {})
    if sports_response and isinstance(sports_response, list):
        print(f"Found {len(sports_response)} sports")
        
        # Show first few
        for i, sport in enumerate(sports_response[:5], 1):
            print(f"\n{i}. Sport ID: {sport.get('id')}")
            print(f"   Sport: {sport.get('sport')}")
            print(f"   Tags: {sport.get('tags')}")
            print(f"   Series: {sport.get('series')}")
            print(f"   All keys: {list(sport.keys())}")
        
        # Check if we can get markets for a specific sport
        if len(sports_response) > 0:
            first_sport = sports_response[0]
            sport_id = first_sport.get('id')
            sport_name = first_sport.get('sport')
            
            print(f"\n{'='*80}")
            print(f"Trying to get markets for sport: {sport_name} (ID: {sport_id})")
            print(f"{'='*80}")
            
            # Try different ways to get markets for this sport
            endpoints_to_try = [
                (f"/sports/{sport_id}/markets", {}),
                (f"/sports/{sport_id}", {}),
                (f"/markets", {"sportId": sport_id}),
                (f"/markets", {"sport": sport_name}),
            ]
            
            for endpoint, params in endpoints_to_try:
                print(f"\nTrying: {endpoint} with {params}")
                response = await fetcher._make_request(endpoint, params)
                if response:
                    if isinstance(response, list):
                        print(f"  -> Found {len(response)} items")
                        if len(response) > 0:
                            first = response[0]
                            title = first.get('question') or first.get('title') or first.get('name') or 'NO TITLE'
                            print(f"  -> First: {title[:60]}")
                    elif isinstance(response, dict):
                        print(f"  -> Dict with keys: {list(response.keys())[:10]}")
                else:
                    print(f"  -> No response")
    
    # Check /events endpoint
    print(f"\n{'='*80}")
    print("2. /events ENDPOINT")
    print(f"{'='*80}")
    
    events_response = await fetcher._make_request("/events", {"closed": "false", "limit": 50})
    if events_response and isinstance(events_response, list):
        print(f"Found {len(events_response)} events")
        
        # Look for sports/game events
        sports_events = []
        for event in events_response:
            title = event.get('title') or event.get('ticker') or ''
            title_lower = title.lower()
            
            # Check if it's sports-related
            sports_keywords = ['nba', 'nfl', 'game', 'match', 'knicks', 'pistons', 'hawks', 'raptors']
            if any(kw in title_lower for kw in sports_keywords):
                sports_events.append(event)
        
        print(f"\nFound {len(sports_events)} sports-related events:")
        for i, event in enumerate(sports_events[:10], 1):
            title = event.get('title') or event.get('ticker') or 'NO TITLE'
            print(f"\n{i}. {title}")
            print(f"   ID: {event.get('id')}")
            print(f"   Slug: {event.get('slug')}")
            print(f"   All keys: {list(event.keys())[:15]}")
        
        # Check if events have markets
        if sports_events:
            first_event = sports_events[0]
            event_id = first_event.get('id')
            event_slug = first_event.get('slug')
            
            print(f"\n{'='*80}")
            print(f"Trying to get markets for event: {first_event.get('title')} (ID: {event_id})")
            print(f"{'='*80}")
            
            endpoints_to_try = [
                (f"/events/{event_id}/markets", {}),
                (f"/events/{event_slug}/markets", {}),
                (f"/markets", {"eventId": event_id}),
                (f"/markets", {"event": event_slug}),
            ]
            
            for endpoint, params in endpoints_to_try:
                print(f"\nTrying: {endpoint} with {params}")
                response = await fetcher._make_request(endpoint, params)
                if response:
                    if isinstance(response, list):
                        print(f"  -> Found {len(response)} markets")
                        if len(response) > 0:
                            first = response[0]
                            title = first.get('question') or first.get('title') or 'NO TITLE'
                            print(f"  -> First market: {title[:60]}")
                    elif isinstance(response, dict):
                        print(f"  -> Dict with keys: {list(response.keys())[:10]}")
                else:
                    print(f"  -> No response")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

