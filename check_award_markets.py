"""
Check if Polymarket and Cloudbet have similar award/MVP markets.
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
    print("CHECKING AWARD/MVP MARKETS")
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
    matcher = SportEventMatcher(similarity_threshold=70.0)

    # Find MVP/Award markets in Polymarket
    pm_award_markets = []
    for m in pm_markets:
        title_lower = m.title.lower()
        if any(word in title_lower for word in ['mvp', 'award', 'coach', 'rookie', 'offensive', 'defensive']):
            pm_award_markets.append(m)

    print(f"\nPolymarket Award/MVP Markets: {len(pm_award_markets)}")
    for i, market in enumerate(pm_award_markets, 1):
        print(f"{i}. {market.title}")
        print(f"   Outcomes: {list(market.outcomes.keys())[:5]}")
        print()

    # Find award events in Cloudbet
    cb_events = {}
    for outcome in cb_raw:
        event_name = outcome.get('event_name', '')
        if event_name not in cb_events:
            cb_events[event_name] = []
        cb_events[event_name].append(outcome)

    cb_award_events = {}
    for event_name, outcomes in cb_events.items():
        event_lower = event_name.lower()
        if any(word in event_lower for word in ['award', 'mvp', 'most valuable', 'coach', 'rookie', 'offensive', 'defensive']):
            cb_award_events[event_name] = outcomes

    print(f"\nCloudbet Award/MVP Events: {len(cb_award_events)}")
    for i, (event_name, outcomes) in enumerate(list(cb_award_events.items())[:10], 1):
        print(f"{i}. {event_name}")
        print(f"   Sport: {outcomes[0].get('sport_key', 'unknown')}")
        print(f"   Outcomes: {[o['outcome'] for o in outcomes[:5]]}")
        print()

    # Try matching award markets
    print("=" * 80)
    print("MATCHING AWARD MARKETS")
    print("=" * 80)

    if pm_award_markets and cb_award_events:
        for pm_market in pm_award_markets:
            pm_title = pm_market.title
            print(f"\nPolymarket: {pm_title}")

            best_matches = []
            for cb_event_name in cb_award_events.keys():
                similarity = matcher._calculate_event_similarity(pm_title, cb_event_name)
                if similarity >= 50.0:  # Lower threshold to see possibilities
                    best_matches.append((cb_event_name, similarity))

            best_matches.sort(key=lambda x: x[1], reverse=True)

            if best_matches:
                print(f"  Best matches:")
                for cb_name, sim in best_matches[:3]:
                    status = "✓ MATCH" if sim >= 70.0 else "✗ Too low"
                    print(f"    {sim:5.1f}% - {status} - {cb_name}")
            else:
                print(f"  No matches >= 50%")

    await pm_fetcher.close()
    await cb_fetcher.close()


if __name__ == '__main__':
    asyncio.run(main())
