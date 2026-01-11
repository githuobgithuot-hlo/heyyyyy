"""Check /events endpoint for games as per Polymarket documentation."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    print("=" * 80)
    print("CHECKING /events ENDPOINT FOR GAMES")
    print("=" * 80)
    
    # Fetch events as per documentation
    print("\nFetching events with: closed=false&limit=200")
    events_response = await fetcher._make_request("/events", {
        "closed": "false",
        "limit": 200
    })
    
    if not events_response:
        print("No response from /events endpoint")
        await fetcher.close()
        return
    
    if not isinstance(events_response, list):
        print(f"Unexpected response type: {type(events_response)}")
        if isinstance(events_response, dict):
            print(f"Keys: {list(events_response.keys())}")
        await fetcher.close()
        return
    
    print(f"\nFound {len(events_response)} events")
    
    # Analyze events
    sports_events = []
    game_events = []
    futures_events = []
    
    for event in events_response:
        title = event.get('title') or event.get('ticker') or ''
        
        if detector.is_sports_market(title):
            sports_events.append(event)
            
            # Extract teams
            teams = detector.extract_teams_from_title(title)
            
            if teams[0] and teams[1]:
                game_events.append((title, teams, event))
            elif teams[0] and not teams[1]:
                futures_events.append((title, teams[0], event))
    
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")
    print(f"Sports events: {len(sports_events)}")
    print(f"  - Game events (2 teams): {len(game_events)}")
    print(f"  - Futures/props (1 team): {len(futures_events)}")
    
    # Show game events
    if game_events:
        print(f"\n{'='*80}")
        print("GAME EVENTS FOUND (First 10):")
        print(f"{'='*80}")
        for i, (title, teams, event) in enumerate(game_events[:10], 1):
            print(f"\n{i}. {title}")
            print(f"   Team 1: {teams[0]}")
            print(f"   Team 2: {teams[1]}")
            print(f"   Event ID: {event.get('id')}")
            print(f"   Slug: {event.get('slug')}")
            print(f"   Active: {event.get('active')}")
            print(f"   Closed: {event.get('closed')}")
    else:
        print("\nNo game events found in /events endpoint")
    
    # Check if events have markets
    if game_events:
        print(f"\n{'='*80}")
        print("CHECKING IF EVENTS HAVE MARKETS")
        print(f"{'='*80}")
        
        first_game = game_events[0]
        event = first_game[2]
        event_id = event.get('id')
        event_slug = event.get('slug')
        
        print(f"\nChecking event: {first_game[0]}")
        print(f"ID: {event_id}, Slug: {event_slug}")
        
        # Try to get markets for this event
        endpoints_to_try = [
            (f"/events/{event_id}", {}),
            (f"/events/slug/{event_slug}", {}),
            (f"/markets", {"eventId": event_id}),
            (f"/markets", {"event": event_slug}),
        ]
        
        for endpoint, params in endpoints_to_try:
            print(f"\nTrying: {endpoint} with {params}")
            response = await fetcher._make_request(endpoint, params)
            
            if response:
                if isinstance(response, dict):
                    # Check if it has markets
                    markets = response.get('markets') or response.get('data')
                    if markets:
                        print(f"  -> Found markets in response")
                        if isinstance(markets, list):
                            print(f"  -> {len(markets)} markets")
                            if len(markets) > 0:
                                first_market = markets[0]
                                market_title = first_market.get('question') or first_market.get('title') or 'NO TITLE'
                                print(f"  -> First market: {market_title[:60]}")
                    else:
                        print(f"  -> Response keys: {list(response.keys())[:10]}")
                elif isinstance(response, list):
                    print(f"  -> List with {len(response)} items")
                    if len(response) > 0:
                        first = response[0]
                        title = first.get('question') or first.get('title') or first.get('name') or 'NO TITLE'
                        print(f"  -> First: {title[:60]}")
            else:
                print(f"  -> No response")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

