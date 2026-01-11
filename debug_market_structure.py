"""Debug market structure from events."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("DEBUGGING MARKET STRUCTURE FROM EVENTS")
    print("=" * 80)
    
    # Get NBA series_id
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    if not nba_series_id:
        print("NBA not found")
        await fetcher.close()
        return
    
    # Get one game event
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 1
    })
    
    if not events or not isinstance(events, list) or len(events) == 0:
        print("No events found")
        await fetcher.close()
        return
    
    event = events[0]
    event_id = event.get('id')
    event_title = event.get('title') or event.get('ticker')
    
    print(f"\nEvent: {event_title}")
    print(f"Event ID: {event_id}")
    
    # Get event details with markets
    event_details = await fetcher._make_request(f"/events/{event_id}", {})
    
    if not event_details or not isinstance(event_details, dict):
        print("No event details")
        await fetcher.close()
        return
    
    markets = event_details.get('markets') or event_details.get('data', [])
    
    if not isinstance(markets, list) or len(markets) == 0:
        print("No markets in event")
        await fetcher.close()
        return
    
    print(f"\nFound {len(markets)} markets")
    print(f"\nFirst market structure:")
    first_market = markets[0]
    print(json.dumps(first_market, indent=2)[:1000])
    
    print(f"\n{'='*80}")
    print("Checking closed status:")
    print(f"{'='*80}")
    
    closed_count = 0
    active_count = 0
    
    for market in markets[:10]:
        closed = market.get('closed')
        active = market.get('active')
        archived = market.get('archived')
        
        print(f"\nMarket: {market.get('question') or market.get('title') or 'NO TITLE'}")
        print(f"  closed: {closed}")
        print(f"  active: {active}")
        print(f"  archived: {archived}")
        
        if closed == True:
            closed_count += 1
        elif active == True or (closed != True and archived != True):
            active_count += 1
    
    print(f"\nSummary: {closed_count} closed, {active_count} active (in first 10)")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

