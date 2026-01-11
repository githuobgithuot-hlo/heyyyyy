"""Check Cloudbet event formats."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.sports_matcher import SportEventMatcher
from src.config_loader import load_config

async def main():
    config = load_config()
    fetcher = CloudbetFetcher(api_key=config.apis.cloudbet.api_key)
    matcher = SportEventMatcher()
    
    outcomes = await fetcher.fetch_all_markets()
    events = matcher._group_cloudbet_by_event(outcomes)
    
    print("=" * 80)
    print(f"CLOUDBET EVENTS: {len(events)} total")
    print("=" * 80)
    
    # Show first 20 events
    for i, (event_name, event_data) in enumerate(list(events.items())[:20], 1):
        print(f"\n{i}. {event_name}")
        print(f"   Sport: {event_data.get('sport_key', 'unknown')}")
        outcomes_list = list(event_data.get('outcomes', {}).keys())[:5]
        print(f"   Outcomes: {outcomes_list}")
        if event_data.get('start_time'):
            print(f"   Time: {event_data['start_time']}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

