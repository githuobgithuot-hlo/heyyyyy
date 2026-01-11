"""Find main game markets (moneyline) from events."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    print("=" * 80)
    print("FINDING MAIN GAME MARKETS")
    print("=" * 80)
    
    # Get NBA series_id
    sports = await fetcher._make_request("/sports", {})
    nba_series_id = None
    
    for sport in sports:
        if sport.get('sport', '').lower() == 'nba':
            nba_series_id = sport.get('series')
            break
    
    # Get one game event
    events = await fetcher._make_request("/events", {
        "series_id": nba_series_id,
        "tag_id": 100639,
        "active": "true",
        "closed": "false",
        "limit": 3
    })
    
    if not events or not isinstance(events, list):
        print("No events")
        await fetcher.close()
        return
    
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
        if not isinstance(markets, list):
            continue
        
        print(f"\nTotal markets: {len(markets)}")
        
        # Look for main game market (should have team names in title)
        main_markets = []
        for market in markets:
            title = market.get('question') or market.get('title') or ''
            title_lower = title.lower()
            
            # Check if it's a main game market (not a prop)
            is_prop = any(word in title_lower for word in ['points over', 'rebounds over', 'assists over', 'over', 'under'])
            has_teams = any(team in title_lower for team in ['nets', 'wizards', 'nuggets', 'cavaliers', 'hawks', 'knicks'])
            has_vs = ' vs ' in title_lower or ' v ' in title_lower
            
            # Main market should have team names or "vs" and not be a prop
            if (has_teams or has_vs) and not is_prop:
                main_markets.append(market)
        
        print(f"\nMain game markets found: {len(main_markets)}")
        for i, market in enumerate(main_markets[:5], 1):
            title = market.get('question') or market.get('title') or 'NO TITLE'
            active = market.get('active')
            closed = market.get('closed')
            print(f"\n{i}. {title}")
            print(f"   Active: {active}, Closed: {closed}")
            
            # Check outcomes
            outcomes = market.get('outcomes') or market.get('outcomePrices', {})
            if outcomes:
                if isinstance(outcomes, list):
                    print(f"   Outcomes: {outcomes}")
                elif isinstance(outcomes, dict):
                    print(f"   Outcomes: {list(outcomes.keys())}")
        
        # Also show event title - it might be the main market
        print(f"\nEvent title: {event_title}")
        teams = detector.extract_teams_from_title(event_title)
        print(f"Teams from event title: {teams}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

