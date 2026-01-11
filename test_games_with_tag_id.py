"""Test fetching games using series_id and tag_id=100639."""
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
    print("TESTING GAMES FETCHING WITH tag_id=100639")
    print("=" * 80)
    
    # Step 1: Get sports
    print("\n1. Getting sports list...")
    sports = await fetcher._make_request("/sports", {})
    
    if not sports or not isinstance(sports, list):
        print("No sports found")
        await fetcher.close()
        return
    
    print(f"Found {len(sports)} sports")
    
    # Find NBA and NFL
    nba_series_id = None
    nfl_series_id = None
    
    for sport in sports:
        sport_name = sport.get('sport', '').lower()
        series = sport.get('series')
        
        print(f"  Sport: {sport_name}, Series: {series}")
        
        if sport_name == 'nba' and series:
            nba_series_id = series
            print(f"  -> Found NBA! series_id: {nba_series_id}")
        elif sport_name == 'nfl' and series:
            nfl_series_id = series
            print(f"  -> Found NFL! series_id: {nfl_series_id}")
    
    # Step 2: Get game events using tag_id=100639
    GAME_TAG_ID = 100639
    
    print(f"\n2. Getting game events (tag_id={GAME_TAG_ID})...")
    
    for league_name, series_id in [("NBA", nba_series_id), ("NFL", nfl_series_id)]:
        if not series_id:
            print(f"\n{league_name}: No series_id found, skipping")
            continue
        
        print(f"\n{league_name} (series_id={series_id}):")
        
        events = await fetcher._make_request("/events", {
            "series_id": series_id,
            "tag_id": GAME_TAG_ID,
            "active": "true",
            "closed": "false",
            "limit": 50
        })
        
        if not events or not isinstance(events, list):
            print(f"  -> No events found")
            continue
        
        print(f"  -> Found {len(events)} game events!")
        
        # Show first few events
        for i, event in enumerate(events[:5], 1):
            title = event.get('title') or event.get('ticker') or 'NO TITLE'
            print(f"    {i}. {title}")
        
        # Get markets from first event
        if len(events) > 0:
            first_event = events[0]
            event_id = first_event.get('id')
            event_title = first_event.get('title') or first_event.get('ticker') or 'NO TITLE'
            
            print(f"\n  Getting markets for: {event_title}")
            event_details = await fetcher._make_request(f"/events/{event_id}", {})
            
            if event_details and isinstance(event_details, dict):
                markets = event_details.get('markets') or event_details.get('data', [])
                if isinstance(markets, list):
                    print(f"  -> Found {len(markets)} markets")
                    for j, market in enumerate(markets[:3], 1):
                        market_title = market.get('question') or market.get('title') or 'NO TITLE'
                        print(f"      {j}. {market_title[:70]}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

