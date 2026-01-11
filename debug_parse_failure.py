"""Debug why main game markets are failing to parse."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("DEBUGGING PARSE FAILURE")
    print("=" * 80)
    
    # Get one event
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 1
    })
    
    if not events or not isinstance(events, list):
        print("No events")
        await fetcher.close()
        return
    
    event = events[0]
    event_id = event.get('id')
    event_title = event.get('title') or event.get('ticker')
    
    event_details = await fetcher._make_request(f"/events/{event_id}", {})
    if not event_details or not isinstance(event_details, dict):
        print("No event details")
        await fetcher.close()
        return
    
    markets = event_details.get('markets') or event_details.get('data', [])
    
    # Find main market
    main_market = None
    for market in markets:
        title = market.get('question') or market.get('title') or ''
        if title.lower() == event_title.lower() or 'moneyline' in title.lower():
            if not any(word in title.lower() for word in ['over', 'under', 'points']):
                main_market = market
                break
    
    if not main_market:
        print("No main market found")
        await fetcher.close()
        return
    
    print(f"\nMain market: {main_market.get('question') or main_market.get('title')}")
    print(f"\nMarket structure:")
    print(f"  ID: {main_market.get('id')}")
    print(f"  Active: {main_market.get('active')}")
    print(f"  Closed: {main_market.get('closed')}")
    
    # Check outcomes
    outcomes = main_market.get('outcomes')
    outcome_prices = main_market.get('outcomePrices')
    
    print(f"\n  Outcomes type: {type(outcomes)}")
    print(f"  OutcomePrices type: {type(outcome_prices)}")
    
    if isinstance(outcomes, str):
        print(f"  Outcomes string: {outcomes}")
        try:
            outcomes_parsed = json.loads(outcomes)
            print(f"  Parsed outcomes: {outcomes_parsed}")
        except Exception as e:
            print(f"  Failed to parse outcomes: {e}")
    
    if isinstance(outcome_prices, str):
        print(f"  OutcomePrices string: {outcome_prices}")
        try:
            prices_parsed = json.loads(outcome_prices)
            print(f"  Parsed prices: {prices_parsed}")
            
            # Check if prices are valid
            valid_prices = []
            for price in prices_parsed:
                try:
                    p = float(price)
                    if 0 < p < 1:
                        valid_prices.append(p)
                        print(f"    Valid price: {p}")
                    else:
                        print(f"    Invalid price: {p} (must be 0 < price < 1)")
                except:
                    print(f"    Could not convert: {price}")
            
            print(f"\n  Valid prices count: {len(valid_prices)}")
            if len(valid_prices) < 2:
                print(f"  -> NOT ENOUGH VALID PRICES (need 2, got {len(valid_prices)})")
                print(f"  -> This is why parsing fails!")
        except Exception as e:
            print(f"  Failed to parse prices: {e}")
    
    # Try to parse manually
    print(f"\n{'='*80}")
    print("MANUAL PARSING TEST")
    print(f"{'='*80}")
    
    parsed = fetcher._parse_market(main_market)
    if parsed:
        print(f"  -> SUCCESS! Parsed market:")
        print(f"     Title: {parsed.get('title')}")
        print(f"     Outcomes: {list(parsed.get('outcomes', {}).keys())}")
    else:
        print(f"  -> FAILED - checking why...")
        
        # Check what _parse_market checks
        market_id = main_market.get('id') or main_market.get('conditionId')
        question = main_market.get('question') or main_market.get('title')
        
        print(f"     Market ID: {market_id}")
        print(f"     Question: {question}")
        
        if not market_id or not question:
            print(f"     -> Missing ID or question!")
        
        # Check outcomes parsing
        outcomes_list = main_market.get('outcomes', [])
        outcome_prices_list = main_market.get('outcomePrices', [])
        
        if isinstance(outcomes_list, str):
            try:
                outcomes_list = json.loads(outcomes_list)
            except:
                outcomes_list = []
        
        if isinstance(outcome_prices_list, str):
            try:
                outcome_prices_list = json.loads(outcome_prices_list)
            except:
                outcome_prices_list = []
        
        print(f"     Outcomes list: {outcomes_list}")
        print(f"     Prices list: {outcome_prices_list}")
        
        if not outcomes_list or not outcome_prices_list:
            print(f"     -> Missing outcomes or prices!")
        elif len(outcomes_list) < 2:
            print(f"     -> Not enough outcomes (need 2, got {len(outcomes_list)})")
        else:
            # Check if prices convert to valid odds
            valid_odds = 0
            for i, price in enumerate(outcome_prices_list):
                try:
                    p = float(price)
                    if 0 < p < 1:
                        odds = fetcher._convert_price_to_odds(p)
                        if odds:
                            valid_odds += 1
                            print(f"       Outcome {i} ({outcomes_list[i]}): price={p} -> odds={odds}")
                        else:
                            print(f"       Outcome {i}: price={p} -> invalid odds")
                    else:
                        print(f"       Outcome {i}: price={p} -> out of range")
                except:
                    print(f"       Outcome {i}: could not convert price")
            
            print(f"     Valid odds count: {valid_odds}")
            if valid_odds < 2:
                print(f"     -> NOT ENOUGH VALID ODDS (need 2, got {valid_odds})")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

