"""Find active markets with valid prices."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("FINDING ACTIVE MARKETS WITH VALID PRICES")
    print("=" * 80)
    
    # Get NBA series_id
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    # Get multiple events
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 10
    })
    
    if not events or not isinstance(events, list):
        print("No events")
        await fetcher.close()
        return
    
    print(f"\nFound {len(events)} events")
    
    active_markets_found = []
    
    for event in events:
        event_title = event.get('title') or event.get('ticker')
        event_id = event.get('id')
        
        event_details = await fetcher._make_request(f"/events/{event_id}", {})
        if not event_details or not isinstance(event_details, dict):
            continue
        
        markets = event_details.get('markets') or event_details.get('data', [])
        
        # Find main game market with valid prices
        for market in markets:
            title = market.get('question') or market.get('title') or ''
            title_lower = title.lower()
            
            # Check if main game market
            is_prop = any(word in title_lower for word in ['over', 'under', 'points', 'rebounds', 'assists'])
            is_main = (title.lower() == event_title.lower() or 
                      ('moneyline' in title_lower and not is_prop) or
                      (not is_prop and (' vs ' in title_lower or ' v ' in title_lower)))
            
            if not is_main:
                continue
            
            # Check prices
            outcomes = market.get('outcomes')
            outcome_prices = market.get('outcomePrices')
            
            # Parse if strings
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except:
                    outcomes = []
            
            if isinstance(outcome_prices, str):
                try:
                    outcome_prices = json.loads(outcome_prices)
                except:
                    outcome_prices = []
            
            # Check if prices are valid (between 0 and 1, exclusive)
            if isinstance(outcomes, list) and isinstance(outcome_prices, list):
                valid_prices = []
                for price in outcome_prices:
                    try:
                        p = float(price)
                        if 0 < p < 1:  # Valid price range
                            valid_prices.append(p)
                    except:
                        pass
                
                if len(valid_prices) >= 2:  # Need at least 2 valid prices
                    active_markets_found.append((event_title, title, outcomes, valid_prices))
                    print(f"\n[FOUND] Active market found:")
                    print(f"  Event: {event_title}")
                    print(f"  Market: {title}")
                    print(f"  Outcomes: {outcomes}")
                    print(f"  Valid prices: {valid_prices}")
                    break  # Found one for this event, move to next
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: Found {len(active_markets_found)} active markets with valid prices")
    print(f"{'='*80}")
    
    if len(active_markets_found) == 0:
        print("\nNo active markets found - all games might be finished/closed")
        print("This is normal if games have already ended")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

