"""Check raw events data for actual games."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("CHECKING RAW EVENTS FOR GAMES")
    print("=" * 80)
    
    # Get events
    events = await fetcher._make_request("/events", {
        "closed": "false",
        "limit": 500
    })
    
    if not events or not isinstance(events, list):
        print("No events found")
        await fetcher.close()
        return
    
    print(f"\nFound {len(events)} events")
    
    # Look for events that might be games
    potential_games = []
    
    for event in events:
        title = event.get('title') or event.get('ticker') or ''
        title_lower = title.lower()
        
        # Check for game indicators
        has_vs = ' vs ' in title_lower or ' v ' in title_lower
        has_nba_nfl = 'nba' in title_lower or 'nfl' in title_lower
        has_teams = any(team in title_lower for team in ['knicks', 'pistons', 'hawks', 'raptors', 'steelers', 'ravens'])
        has_abbr = any(abbr in title for abbr in ['NYK', 'DET', 'ATL', 'TOR', 'PIT', 'BAL'])
        
        # Skip props/futures
        is_prop = any(word in title_lower for word in ['winner', 'mvp', 'rookie', 'coach', 'player of the year'])
        
        if (has_vs or (has_teams and not is_prop) or (has_abbr and not is_prop)) and has_nba_nfl:
            potential_games.append((title, event))
    
    print(f"\n{'='*80}")
    print(f"POTENTIAL GAME EVENTS: {len(potential_games)}")
    print(f"{'='*80}")
    
    for i, (title, event) in enumerate(potential_games[:20], 1):
        print(f"\n{i}. {title}")
        print(f"   ID: {event.get('id')}")
        print(f"   Slug: {event.get('slug')}")
        
        # Get markets for this event
        event_id = event.get('id')
        event_details = await fetcher._make_request(f"/events/{event_id}", {})
        
        if event_details and isinstance(event_details, dict):
            markets = event_details.get('markets') or event_details.get('data', [])
            if isinstance(markets, list) and len(markets) > 0:
                print(f"   Markets: {len(markets)}")
                # Show first few market titles
                for j, market in enumerate(markets[:3], 1):
                    market_title = market.get('question') or market.get('title') or 'NO TITLE'
                    print(f"      {j}. {market_title[:70]}")
    
    # Also show all event titles with 'vs'
    print(f"\n{'='*80}")
    print("ALL EVENTS WITH 'vs' OR 'v' (First 30):")
    print(f"{'='*80}")
    
    vs_events = []
    for event in events:
        title = event.get('title') or event.get('ticker') or ''
        if ' vs ' in title.lower() or ' v ' in title.lower():
            vs_events.append(title)
    
    if vs_events:
        for i, title in enumerate(vs_events[:30], 1):
            print(f"{i}. {title}")
    else:
        print("No events with 'vs' or 'v' found")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

