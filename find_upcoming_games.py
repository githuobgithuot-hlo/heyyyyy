"""Find upcoming games (not finished)."""
import asyncio
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("FINDING UPCOMING GAMES")
    print("=" * 80)
    
    # Get NBA series_id
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    # Get events - try with different date filters
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    next_week = now + timedelta(days=7)
    
    print(f"\nCurrent time: {now}")
    print(f"Looking for games from now to {next_week}")
    
    # Try getting events with date range
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 100
    })
    
    if not events or not isinstance(events, list):
        print("No events")
        await fetcher.close()
        return
    
    print(f"\nFound {len(events)} events")
    
    # Check event dates
    upcoming_events = []
    for event in events:
        start_date = event.get('startDate') or event.get('start_time')
        end_date = event.get('endDate') or event.get('end_time')
        
        event_title = event.get('title') or event.get('ticker')
        
        if start_date:
            try:
                # Parse date
                if isinstance(start_date, str):
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_dt = start_date
                
                # Check if it's in the future
                if start_dt > now:
                    upcoming_events.append((event, start_dt))
                    print(f"\nUpcoming: {event_title}")
                    print(f"  Start: {start_dt}")
            except:
                pass
    
    print(f"\n{'='*80}")
    print(f"UPCOMING EVENTS: {len(upcoming_events)}")
    print(f"{'='*80}")
    
    # Check markets for upcoming events
    for event, start_dt in upcoming_events[:5]:
        event_id = event.get('id')
        event_title = event.get('title') or event.get('ticker')
        
        print(f"\n{'='*80}")
        print(f"Event: {event_title} (starts: {start_dt})")
        print(f"{'='*80}")
        
        event_details = await fetcher._make_request(f"/events/{event_id}", {})
        if not event_details or not isinstance(event_details, dict):
            continue
        
        markets = event_details.get('markets') or event_details.get('data', [])
        
        # Find main game market with valid prices
        for market in markets:
            title = market.get('question') or market.get('title') or ''
            title_lower = title.lower()
            
            is_prop = any(word in title_lower for word in ['over', 'under', 'points', 'rebounds', 'assists'])
            is_main = (title.lower() == event_title.lower() or 
                      ('moneyline' in title_lower and not is_prop) or
                      (not is_prop and (' vs ' in title_lower or ' v ' in title_lower)))
            
            if not is_main:
                continue
            
            # Check prices
            outcomes = market.get('outcomes')
            outcome_prices = market.get('outcomePrices')
            
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
            
            # Check for valid prices
            valid_prices = []
            for price in outcome_prices:
                try:
                    p = float(price)
                    if 0 < p < 1:
                        valid_prices.append(p)
                except:
                    pass
            
            if len(valid_prices) >= 2:
                print(f"\n[FOUND] Active main game market:")
                print(f"  Title: {title}")
                print(f"  Outcomes: {outcomes}")
                print(f"  Valid prices: {valid_prices}")
                break
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

