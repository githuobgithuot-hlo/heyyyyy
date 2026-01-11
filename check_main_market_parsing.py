"""Check if main game markets are being parsed."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("CHECKING MAIN GAME MARKET PARSING")
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
        "limit": 5
    })
    
    if not events or not isinstance(events, list):
        print("No events")
        await fetcher.close()
        return
    
    print(f"\nFound {len(events)} events")
    
    for event in events:
        event_title = event.get('title') or event.get('ticker')
        event_id = event.get('id')
        
        print(f"\n{'='*80}")
        print(f"Event: {event_title}")
        print(f"{'='*80}")
        
        event_details = await fetcher._make_request(f"/events/{event_id}", {})
        if not event_details or not isinstance(event_details, dict):
            continue
        
        markets = event_details.get('markets') or event_details.get('data', [])
        
        # Find main game market (same logic as fetcher)
        main_game_market = None
        for market in markets:
            market_title = market.get('question') or market.get('title') or ''
            market_lower = market_title.lower()
            
            is_prop = any(word in market_lower for word in ['over', 'under', 'points', 'rebounds', 'assists', 'spread'])
            
            if (market_title.lower() == event_title.lower() or 
                ('moneyline' in market_lower and not is_prop) or
                (not is_prop and (' vs ' in market_lower or ' v ' in market_lower))):
                main_game_market = market
                print(f"\nMain game market found: {market_title}")
                break
        
        if main_game_market:
            # Try to parse it
            print(f"\nAttempting to parse main game market...")
            parsed = fetcher._parse_market(main_game_market)
            
            if parsed:
                print(f"  -> SUCCESS! Parsed market:")
                print(f"     Title: {parsed.get('title')}")
                print(f"     Outcomes: {list(parsed.get('outcomes', {}).keys())}")
            else:
                print(f"  -> FAILED to parse")
                print(f"     Checking why...")
                
                # Check outcomes structure
                outcomes = main_game_market.get('outcomes')
                outcome_prices = main_game_market.get('outcomePrices')
                
                print(f"     Outcomes type: {type(outcomes)}")
                print(f"     OutcomePrices type: {type(outcome_prices)}")
                
                if isinstance(outcomes, str):
                    try:
                        outcomes = json.loads(outcomes)
                        print(f"     Parsed outcomes: {outcomes}")
                    except:
                        print(f"     Failed to parse outcomes JSON")
                
                if isinstance(outcome_prices, str):
                    try:
                        outcome_prices = json.loads(outcome_prices)
                        print(f"     Parsed outcomePrices: {outcome_prices}")
                        
                        # Check if prices are valid
                        valid_count = 0
                        for price in outcome_prices:
                            try:
                                p = float(price)
                                if 0 < p < 1:
                                    valid_count += 1
                                    print(f"       Valid price: {p}")
                                else:
                                    print(f"       Invalid price: {p} (not in 0-1 range)")
                            except:
                                print(f"       Invalid price format: {price}")
                        
                        print(f"     Valid prices: {valid_count}/{len(outcome_prices)}")
                        if valid_count < 2:
                            print(f"     -> This is why it's filtered out (need 2+ valid prices)")
                    except:
                        print(f"     Failed to parse outcomePrices JSON")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

