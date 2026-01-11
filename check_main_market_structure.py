"""Check structure of main game market."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("CHECKING MAIN GAME MARKET STRUCTURE")
    print("=" * 80)
    
    # Get NBA series_id
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    # Get one event
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 1
    })
    
    if not events or not isinstance(events, list) or len(events) == 0:
        print("No events")
        await fetcher.close()
        return
    
    event = events[0]
    event_id = event.get('id')
    event_title = event.get('title') or event.get('ticker')
    
    print(f"\nEvent: {event_title}")
    
    # Get event details
    event_details = await fetcher._make_request(f"/events/{event_id}", {})
    if not event_details or not isinstance(event_details, dict):
        print("No event details")
        await fetcher.close()
        return
    
    markets = event_details.get('markets') or event_details.get('data', [])
    print(f"\nTotal markets in event: {len(markets)}")
    
    # Find main game market
    print(f"\n{'='*80}")
    print("LOOKING FOR MAIN GAME MARKET")
    print(f"{'='*80}")
    
    main_markets = []
    for market in markets:
        title = market.get('question') or market.get('title') or ''
        title_lower = title.lower()
        
        # Check if it's main game market
        is_prop = any(word in title_lower for word in ['over', 'under', 'points', 'rebounds', 'assists'])
        is_main = (title.lower() == event_title.lower() or 
                  'moneyline' in title_lower or
                  (not is_prop and (' vs ' in title_lower or ' v ' in title_lower)))
        
        if is_main:
            main_markets.append(market)
            print(f"\nMain market found: {title}")
            print(f"  ID: {market.get('id')}")
            print(f"  Active: {market.get('active')}")
            print(f"  Closed: {market.get('closed')}")
            
            # Check outcomes structure
            outcomes = market.get('outcomes')
            outcome_prices = market.get('outcomePrices')
            
            print(f"  Outcomes type: {type(outcomes)}")
            print(f"  OutcomePrices type: {type(outcome_prices)}")
            
            if isinstance(outcomes, list):
                print(f"  Outcomes list: {outcomes}")
            elif isinstance(outcomes, dict):
                print(f"  Outcomes dict keys: {list(outcomes.keys())[:10]}")
            elif isinstance(outcomes, str):
                print(f"  Outcomes string: {outcomes[:200]}")
            
            if isinstance(outcome_prices, list):
                print(f"  OutcomePrices list: {outcome_prices}")
            elif isinstance(outcome_prices, dict):
                print(f"  OutcomePrices dict: {list(outcome_prices.keys())[:10]}")
            elif isinstance(outcome_prices, str):
                print(f"  OutcomePrices string: {outcome_prices[:200]}")
            
            # Check if _parse_market would accept it
            print(f"\n  Testing _parse_market...")
            parsed = fetcher._parse_market(market)
            if parsed:
                print(f"  -> PARSED SUCCESSFULLY!")
                print(f"     Title: {parsed.get('title')}")
                print(f"     Outcomes: {list(parsed.get('outcomes', {}).keys())}")
            else:
                print(f"  -> FAILED TO PARSE")
                print(f"     (This is why it's being filtered out)")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

