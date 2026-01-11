"""
Test award market matching specifically.
"""
import asyncio
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'src')

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.sports_matcher import SportEventMatcher, SportsMarketDetector
from src.config_loader import load_config


async def main():
    print("=" * 80)
    print("TESTING AWARD MARKET MATCHING WITH SPORT FILTERING")
    print("=" * 80)

    config = load_config()

    # Fetch data
    print("\nFetching data...")
    pm_fetcher = PolymarketFetcher(debug_api=False)
    cb_fetcher = CloudbetFetcher(api_key=config.apis.cloudbet.api_key, debug_api=False)

    pm_raw = await pm_fetcher.fetch_all_markets(limit=200)
    cb_raw = await cb_fetcher.fetch_all_markets()

    normalizer = MarketNormalizer()
    pm_markets = normalizer.normalize_polymarket(pm_raw)

    detector = SportsMarketDetector()
    matcher = SportEventMatcher(similarity_threshold=55.0)

    # Find NFL Offensive Rookie markets in Polymarket
    pm_offensive_rookie = []
    for m in pm_markets:
        if 'offensive rookie' in m.title.lower() and '2025-2026' in m.title:
            pm_offensive_rookie.append(m)

    print(f"\nPolymarket NFL Offensive Rookie Markets: {len(pm_offensive_rookie)}")
    if pm_offensive_rookie:
        print(f"Example: {pm_offensive_rookie[0].title}")
        pm_sport = detector.detect_sport(pm_offensive_rookie[0].title)
        print(f"Detected sport: {pm_sport}")

    # Find award events in Cloudbet
    cb_events = {}
    for outcome in cb_raw:
        event_name = outcome.get('event_name', '')
        if event_name not in cb_events:
            cb_events[event_name] = []
        cb_events[event_name].append(outcome)

    cb_award_events = {}
    for event_name, outcomes in cb_events.items():
        if 'Offensive Rookie' in event_name and outcomes[0].get('sport_key') == 'american-football':
            cb_award_events[event_name] = outcomes

    print(f"\nCloudbet NFL Offensive Rookie Events: {len(cb_award_events)}")
    if cb_award_events:
        event_name = list(cb_award_events.keys())[0]
        print(f"Event: {event_name}")
        print(f"Sport: {cb_award_events[event_name][0].get('sport_key')}")
        print(f"Players: {[o['outcome'][:30] for o in cb_award_events[event_name][:5]]}")

    # Try matching
    print("\n" + "=" * 80)
    print("MATCHING ATTEMPTS")
    print("=" * 80)

    if pm_offensive_rookie and cb_award_events:
        pm_title = pm_offensive_rookie[0].title
        cb_event_name = list(cb_award_events.keys())[0]

        print(f"\nPolymarket: {pm_title}")
        print(f"Cloudbet:   {cb_event_name}")

        similarity = matcher._calculate_event_similarity(pm_title, cb_event_name)
        print(f"Similarity: {similarity:.1f}%")

        if similarity >= 55.0:
            print("✓ MATCH!")
        else:
            print("✗ Below threshold (55%)")

        # Check sport filtering
        pm_sport = detector.detect_sport(pm_title)
        cb_sport = cb_award_events[cb_event_name][0].get('sport_key')
        print(f"\nSport check:")
        print(f"  PM detected: {pm_sport}")
        print(f"  CB sport: {cb_sport}")
        print(f"  Same sport: {pm_sport == cb_sport}")

    await pm_fetcher.close()
    await cb_fetcher.close()


if __name__ == '__main__':
    asyncio.run(main())
