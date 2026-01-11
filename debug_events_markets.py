"""Debug if markets from events are being added."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("DEBUGGING EVENTS -> MARKETS FLOW")
    print("=" * 80)
    
    # Get sports
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    print(f"\nNBA series_id: {nba_series_id}")
    
    # Get events
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 5  # Just 5 for testing
    })
    
    if not events or not isinstance(events, list):
        print("No events")
        await fetcher.close()
        return
    
    print(f"\nFound {len(events)} events")
    
    all_markets = []
    
    for event in events:
        event_title = event.get('title') or event.get('ticker')
        event_id = event.get('id')
        
        print(f"\n  Event: {event_title} (ID: {event_id})")
        
        event_details = await fetcher._make_request(f"/events/{event_id}", {})
        if not event_details or not isinstance(event_details, dict):
            print(f"    -> No event details")
            continue
        
        markets = event_details.get('markets') or event_details.get('data', [])
        if not isinstance(markets, list):
            print(f"    -> Markets not a list: {type(markets)}")
            continue
        
        print(f"    -> Found {len(markets)} markets in event")
        
        # Find main game market
        main_market = None
        for market in markets:
            title = market.get('question') or market.get('title') or ''
            title_lower = title.lower()
            
            is_prop = any(word in title_lower for word in ['over', 'under', 'points', 'rebounds', 'assists'])
            is_main = (title.lower() == event_title.lower() or 
                      ('moneyline' in title_lower and not is_prop) or
                      (not is_prop and (' vs ' in title_lower or ' v ' in title_lower)))
            
            if is_main:
                main_market = market
                print(f"    -> Main market: {title}")
                break
        
        if main_market:
            all_markets.append(main_market)
            print(f"    -> Added to all_markets (total: {len(all_markets)})")
        else:
            print(f"    -> No main market found")
    
    print(f"\n{'='*80}")
    print(f"TOTAL MARKETS FROM EVENTS: {len(all_markets)}")
    print(f"{'='*80}")
    
    # Check if they would parse
    print(f"\nTesting _parse_market on first few:")
    for i, market in enumerate(all_markets[:5], 1):
        title = market.get('question') or market.get('title') or 'NO TITLE'
        print(f"\n{i}. {title}")
        parsed = fetcher._parse_market(market)
        if parsed:
            print(f"   -> PARSED: {list(parsed.get('outcomes', {}).keys())}")
        else:
            print(f"   -> FAILED TO PARSE")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

